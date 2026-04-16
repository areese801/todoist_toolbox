"""
Custom Textual widgets for the Todoist TUI.

Provides the sidebar navigation, task list, and task row widgets.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView, Static

from todoist.tui.snooze import extract_url
from todoist.tui.theme import (
    BLUE,
    CYAN,
    DIM_TEXT,
    FG_DEFAULT,
    GREEN,
    ORANGE,
    RED,
    TEAL,
    YELLOW,
)

# Priority display: Todoist uses 1=p4(low), 4=p1(urgent). We invert for display.
PRIORITY_MARKERS = {
    4: f"[{RED}]!!![/]",   # p1 urgent
    3: f"[{ORANGE}]!! [/]",  # p2
    2: f"[{BLUE}]!  [/]",   # p3
    1: "",                    # p4 normal
}


def format_due_date(due_obj) -> str:
    """
    Format a Due object's date for display.

    Args:
        due_obj: A Todoist Due object (or mock) with .date attribute.

    Returns:
        Formatted date string with color markup.
    """
    if due_obj is None:
        return ""

    due_val = due_obj.date
    if isinstance(due_val, datetime):
        due_date = due_val.date()
    elif isinstance(due_val, date):
        due_date = due_val
    else:
        return f"[{YELLOW}]{due_val}[/]"

    today = date.today()
    delta = (due_date - today).days

    if delta < 0:
        return f"[{RED}]{due_date.strftime('%b %d')}[/]"
    elif delta == 0:
        return f"[{GREEN}]today[/]"
    elif delta == 1:
        return f"[{YELLOW}]tomorrow[/]"
    elif delta < 7:
        return f"[{YELLOW}]{due_date.strftime('%A')}[/]"
    else:
        return f"[{DIM_TEXT}]{due_date.strftime('%b %d')}[/]"


def format_labels(labels: list[str]) -> str:
    """
    Format task labels for display.

    Args:
        labels: List of label name strings.

    Returns:
        Formatted label string with color markup.
    """
    if not labels:
        return ""
    tags = " ".join(f"[{TEAL}]@{lbl}[/]" for lbl in labels)
    return f" {tags}"


class SidebarItem(Static):
    """
    A clickable item in the sidebar navigation.
    """

    class Selected(Message):
        """
        Posted when a sidebar item is clicked.
        """

        def __init__(self, view_id: str, label: str) -> None:
            super().__init__()
            self.view_id = view_id
            self.label = label

    def __init__(
        self,
        label: str,
        view_id: str,
        icon: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.label_text = label
        self.view_id = view_id
        self.icon = icon
        self.add_class("sidebar-item")

    def render(self) -> str:
        """
        Render the sidebar item text.
        """
        prefix = f"{self.icon} " if self.icon else ""
        return f"{prefix}{self.label_text}"

    def on_click(self) -> None:
        """
        Handle click on sidebar item.
        """
        self.post_message(self.Selected(self.view_id, self.label_text))

    def set_active(self, active: bool) -> None:
        """
        Toggle the active visual state.

        Args:
            active: Whether this item should appear active.
        """
        if active:
            self.add_class("--active")
        else:
            self.remove_class("--active")


class Sidebar(Vertical):
    """
    Persistent sidebar with navigation items.
    """

    def compose(self) -> ComposeResult:
        """
        Compose sidebar content.
        """
        yield Static(f"[bold {BLUE}]Todoist[/]", classes="sidebar-item")
        yield Static("", classes="sidebar-item")  # spacer
        yield SidebarItem("today", "Today", icon="\u2606", id="nav-today")
        yield SidebarItem("inbox", "Inbox", icon="\u2709", id="nav-inbox")
        yield Static("", classes="sidebar-item")  # spacer
        yield Static(f"[{DIM_TEXT}]Projects[/]", classes="sidebar-item")
        # Projects are populated dynamically by the app
        yield Vertical(id="project-list")
        yield Static("", classes="sidebar-item")  # spacer
        yield Static(f"[{DIM_TEXT}]Labels[/]", classes="sidebar-item")
        yield Vertical(id="label-list")

    def set_active_view(self, view_id: str) -> None:
        """
        Highlight the active navigation item.

        Args:
            view_id: The view identifier to activate.
        """
        for item in self.query(SidebarItem):
            item.set_active(item.view_id == view_id)


class TaskRow(Static):
    """
    A single task row in the main task list.
    """

    class Selected(Message):
        """
        Posted when a task row is selected/clicked.
        """

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    def __init__(self, task, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task = task
        self.task_id = task.id
        self.add_class("task-row")
        # Add priority class
        priority = getattr(task, "priority", 1)
        self.add_class(f"priority-{priority}")

    def render(self) -> str:
        """
        Render the task row with priority, content, due date, and labels.
        """
        task = self.task
        priority = getattr(task, "priority", 1)
        marker = PRIORITY_MARKERS.get(priority, "")

        content = task.content
        due_str = format_due_date(task.due)
        labels = format_labels(getattr(task, "labels", []))

        parts = []
        if marker:
            parts.append(marker)
        parts.append(content)
        if due_str:
            parts.append(f"  {due_str}")
        if labels:
            parts.append(labels)

        return " ".join(parts) if parts else content

    def on_click(self) -> None:
        """
        Handle click on task row.
        """
        self.post_message(self.Selected(self.task_id))


class TaskList(Vertical):
    """
    The main task list widget.

    Manages a list of TaskRow widgets with keyboard navigation.
    """

    selected_index: reactive[int] = reactive(0)

    class TaskAction(Message):
        """
        Posted when an action is requested on the selected task.
        """

        def __init__(self, task_id: str, action: str) -> None:
            super().__init__()
            self.task_id = task_id
            self.action = action

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tasks: list = []

    def set_tasks(self, tasks: list) -> None:
        """
        Replace the task list with new tasks.

        Args:
            tasks: List of Todoist Task objects (or mocks).
        """
        self._tasks = list(tasks)
        self.selected_index = 0
        self._rebuild()

    def _rebuild(self) -> None:
        """
        Remove all children and rebuild from current task list.
        """
        self.remove_children()
        for i, task in enumerate(self._tasks):
            row = TaskRow(task, id=f"task-{task.id}")
            if i == self.selected_index:
                row.add_class("--selected")
            self.mount(row)

    def watch_selected_index(self, old_value: int, new_value: int) -> None:
        """
        React to selection changes by updating row highlighting.
        """
        rows = list(self.query(TaskRow))
        if not rows:
            return
        if 0 <= old_value < len(rows):
            rows[old_value].remove_class("--selected")
        if 0 <= new_value < len(rows):
            rows[new_value].add_class("--selected")
            rows[new_value].scroll_visible()

    def move_selection(self, delta: int) -> None:
        """
        Move the selection by delta rows.

        Args:
            delta: Number of rows to move (negative = up, positive = down).
        """
        if not self._tasks:
            return
        new_idx = max(0, min(len(self._tasks) - 1, self.selected_index + delta))
        self.selected_index = new_idx

    def get_selected_task(self):
        """
        Return the currently selected task object.

        Returns:
            The selected Task, or None if list is empty.
        """
        if not self._tasks or not (0 <= self.selected_index < len(self._tasks)):
            return None
        return self._tasks[self.selected_index]

    def get_selected_url(self) -> Optional[str]:
        """
        Extract a URL from the selected task's content or description.

        Returns:
            The first URL found, or None.
        """
        task = self.get_selected_task()
        if task is None:
            return None

        # Check content first
        url = extract_url(task.content)
        if url:
            return url

        # Check description
        desc = getattr(task, "description", None)
        if desc:
            url = extract_url(desc)
            if url:
                return url

        return None

    @property
    def task_count(self) -> int:
        """
        Return the number of tasks in the list.
        """
        return len(self._tasks)


class StatusBar(Static):
    """
    Bottom status bar showing current view info and hints.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._view_name = "Today"
        self._task_count = 0
        self._status_text = ""

    def update_view(
        self,
        view_name: str,
        task_count: int,
        status_text: str = "",
    ) -> None:
        """
        Update the status bar display.

        Args:
            view_name: Name of the current view.
            task_count: Number of tasks displayed.
            status_text: Optional additional status text.
        """
        self._view_name = view_name
        self._task_count = task_count
        self._status_text = status_text
        self.refresh()

    def render(self) -> str:
        """
        Render the status bar content.
        """
        left = f"[{BLUE}]{self._view_name}[/]  {self._task_count} tasks"
        right = self._status_text or f"[{DIM_TEXT}]? help  qq quit[/]"
        return f"{left}  {right}"
