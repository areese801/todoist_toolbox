"""
Main Textual application for the Todoist TUI.

Provides a keyboard-driven interface for managing Todoist tasks with
a persistent sidebar, main task list, and modal dialogs.
"""

from __future__ import annotations

import webbrowser
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.worker import Worker, WorkerState

from todoist.todoist_tasks import (
    get_active_tasks,
    get_labels,
    get_projects,
)
from todoist.tui.screens import (
    DateInputScreen,
    HelpScreen,
    LabelPickerScreen,
    ProjectPickerScreen,
    QuickAddScreen,
    SearchScreen,
    SnoozeScreen,
    TaskEditScreen,
)
from todoist.tui.snooze import (
    build_snooze_comment,
    resolve_preset_wake_time,
)
from todoist.tui.theme import APP_CSS, BLUE, DIM_TEXT, GREEN, RED
from todoist.tui.widgets import Sidebar, SidebarItem, StatusBar, TaskList


class TodoistApp(App):
    """
    Keyboard-driven Todoist TUI application.
    """

    CSS = APP_CSS

    BINDINGS = [
        ("ctrl+c", "quit_app", "Quit"),
    ]

    def __init__(self, api=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._api = api
        self._all_tasks: list = []
        self._projects: list = []
        self._labels: list = []
        self._current_view = "today"
        self._last_q_time: float = 0.0  # For qq double-tap quit
        self._q_timer = None  # Timer for delayed quick-add on single q
        self._project_map: dict = {}  # project_id -> project

    def compose(self) -> ComposeResult:
        """
        Compose the main application layout.
        """
        with Horizontal():
            yield Sidebar(id="sidebar")
            with Vertical(id="main-pane"):
                yield Static(
                    f"[bold {BLUE}]Today[/]",
                    id="view-title",
                )
                yield TaskList(id="task-list")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        """
        Initialize the app: load data from Todoist API.
        """
        sidebar = self.query_one(Sidebar)
        sidebar.set_active_view("today")
        self._load_data()

    def _load_data(self) -> None:
        """
        Trigger background workers to load tasks, projects, and labels.
        """
        self._update_status("Loading...")
        self.run_worker(self._fetch_all_data(), name="fetch_data", exclusive=True)

    async def _fetch_all_data(self) -> None:
        """
        Fetch tasks, projects, and labels from the API.
        """
        try:
            if self._api:
                self._all_tasks = get_active_tasks(api=self._api)
                self._projects = get_projects(api=self._api)
                self._labels = get_labels(api=self._api)
            else:
                self._all_tasks = []
                self._projects = []
                self._labels = []

            self._project_map = {p.id: p for p in self._projects}
            self._populate_sidebar()
            self._apply_view_filter()
            self._update_status("")
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _populate_sidebar(self) -> None:
        """
        Populate sidebar with dynamic project and label lists.
        """
        # Projects
        project_list = self.query_one("#project-list", Vertical)
        project_list.remove_children()
        for project in self._projects:
            item = SidebarItem(
                project.name,
                f"project:{project.id}",
                icon="\u25cf",
            )
            project_list.mount(item)

        # Labels
        label_list = self.query_one("#label-list", Vertical)
        label_list.remove_children()
        for label in self._labels:
            item = SidebarItem(
                label.name,
                f"label:{label.name}",
                icon="@",
            )
            label_list.mount(item)

    def _apply_view_filter(self) -> None:
        """
        Filter tasks based on the current view and update the task list.
        """
        from datetime import date

        view = self._current_view
        filtered = []

        if view == "today":
            today = date.today()
            for task in self._all_tasks:
                if task.due is None:
                    continue
                due_val = task.due.date
                if isinstance(due_val, datetime):
                    due_date = due_val.date()
                elif isinstance(due_val, date):
                    due_date = due_val
                else:
                    continue
                if due_date <= today:
                    filtered.append(task)
            view_name = "Today"

        elif view == "inbox":
            for task in self._all_tasks:
                project_id = getattr(task, "project_id", None)
                if project_id:
                    project = self._project_map.get(project_id)
                    if project and getattr(project, "inbox_project", False):
                        filtered.append(task)
                        continue
                # Fallback: tasks without a project or in the first project
                if not project_id:
                    filtered.append(task)
            # If no inbox detection worked, show all tasks without due dates
            # as a reasonable inbox heuristic
            if not filtered:
                filtered = [t for t in self._all_tasks if t.due is None]
            view_name = "Inbox"

        elif view.startswith("project:"):
            project_id = view.split(":", 1)[1]
            filtered = [
                t for t in self._all_tasks
                if getattr(t, "project_id", None) == project_id
            ]
            project = self._project_map.get(project_id)
            view_name = project.name if project else "Project"

        elif view.startswith("label:"):
            label_name = view.split(":", 1)[1]
            filtered = [
                t for t in self._all_tasks
                if label_name in getattr(t, "labels", [])
            ]
            view_name = f"@{label_name}"

        else:
            filtered = self._all_tasks
            view_name = "All Tasks"

        # Sort: overdue first, then by due date, then by priority
        def sort_key(task):
            """
            Generate a sort key for task ordering.
            """
            priority = -(getattr(task, "priority", 1))
            if task.due:
                due_val = task.due.date
                if isinstance(due_val, datetime):
                    due_date = due_val.date()
                elif isinstance(due_val, date):
                    due_date = due_val
                else:
                    due_date = date.max
            else:
                due_date = date.max
            return (due_date, priority)

        filtered.sort(key=sort_key)

        task_list = self.query_one("#task-list", TaskList)
        task_list.set_tasks(filtered)

        title = self.query_one("#view-title", Static)
        title.update(f"[bold {BLUE}]{view_name}[/]")

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_view(view_name, len(filtered))

    def _update_status(self, text: str) -> None:
        """
        Update the status bar with a message.

        Args:
            text: Status text to display.
        """
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_view(
            self._current_view.split(":")[-1].title(),
            self.query_one("#task-list", TaskList).task_count,
            text,
        )

    def _switch_view(self, view_id: str) -> None:
        """
        Switch to a different view.

        Args:
            view_id: The view identifier (e.g. "today", "inbox", "project:123").
        """
        self._current_view = view_id
        sidebar = self.query_one(Sidebar)
        sidebar.set_active_view(view_id)
        self._apply_view_filter()

    # -- Event handlers --

    def on_sidebar_item_selected(self, message: SidebarItem.Selected) -> None:
        """
        Handle sidebar navigation click.
        """
        self._switch_view(message.view_id)

    def _on_q_timeout(self) -> None:
        """
        Called 0.5s after a single q press if no second q arrived.
        Triggers quick-add.
        """
        self._q_timer = None
        self._show_quick_add()

    def on_key(self, event) -> None:
        """
        Handle global keyboard shortcuts.
        """
        task_list = self.query_one("#task-list", TaskList)
        key = event.key

        # qq double-tap quit / single q quick-add
        if key == "q":
            import time
            now = time.time()
            if now - self._last_q_time < 0.5:
                # Second q within window — cancel timer and quit
                if self._q_timer is not None:
                    self._q_timer.stop()
                    self._q_timer = None
                self.exit()
                return
            self._last_q_time = now
            # Schedule quick-add after timeout
            self._q_timer = self.set_timer(0.5, self._on_q_timeout)
            return

        self._last_q_time = 0.0  # Reset on any other key

        # Navigation
        if key == "j" or key == "down":
            task_list.move_selection(1)
        elif key == "k" or key == "up":
            task_list.move_selection(-1)
        elif key == "g":
            task_list.selected_index = 0
        elif key == "G" or key == "shift+g":
            if task_list.task_count > 0:
                task_list.selected_index = task_list.task_count - 1

        # View switching
        elif key == "t":
            self._switch_view("today")
        elif key == "i":
            self._switch_view("inbox")

        # Priority keys (1=p1/urgent=API priority 4, etc.)
        elif key in ("1", "2", "3", "4"):
            self._set_priority(int(key))

        # Actions
        elif key == "a":
            self._show_quick_add()
        elif key == "e":
            self._show_edit()
        elif key == "x":
            self._complete_task()
        elif key in ("d", "r"):
            self._show_date_input()
        elif key == "l":
            self._show_label_picker()
        elif key == "p":
            self._show_project_picker()
        elif key in ("b", "z"):
            self._show_snooze()
        elif key in ("o", "u"):
            self._open_url()
        elif key == "slash":
            self._show_search()
        elif key == "question_mark":
            self.push_screen(HelpScreen())

    def action_quit_app(self) -> None:
        """
        Quit the application.
        """
        self.exit()

    # -- Modal actions --

    def _show_quick_add(self) -> None:
        """
        Show the quick-add task modal.
        """
        def on_result(content: Optional[str]) -> None:
            """
            Handle quick-add result.
            """
            if content and self._api:
                self.run_worker(
                    self._do_quick_add(content),
                    name="quick_add",
                )

        self.push_screen(QuickAddScreen(), callback=on_result)

    async def _do_quick_add(self, content: str) -> None:
        """
        Create a new task via the API.

        Args:
            content: Task content string.
        """
        try:
            self._api.add_task(content=content)
            self._update_status(f"[{GREEN}]Added: {content}[/]")
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _show_edit(self) -> None:
        """
        Show the task edit modal for the selected task.
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task:
            return

        def on_result(result: Optional[dict]) -> None:
            """
            Handle edit result.
            """
            if result and self._api:
                self.run_worker(
                    self._do_edit(task.id, result),
                    name="edit_task",
                )

        self.push_screen(
            TaskEditScreen(
                task_content=task.content,
                task_description=getattr(task, "description", "") or "",
            ),
            callback=on_result,
        )

    async def _do_edit(self, task_id: str, updates: dict) -> None:
        """
        Update a task via the API.

        Args:
            task_id: The task ID to update.
            updates: Dict of fields to update.
        """
        try:
            self._api.update_task(task_id, **updates)
            self._update_status(f"[{GREEN}]Updated task[/]")
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _complete_task(self) -> None:
        """
        Complete the selected task.
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task or not self._api:
            return

        self.run_worker(
            self._do_complete(task.id, task.content),
            name="complete_task",
        )

    async def _do_complete(self, task_id: str, content: str) -> None:
        """
        Mark a task as complete via the API.

        Args:
            task_id: The task ID to complete.
            content: The task content (for status message).
        """
        try:
            self._api.complete_task(task_id)
            self._update_status(f"[{GREEN}]Completed: {content}[/]")
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _show_date_input(self) -> None:
        """
        Show the date input modal for the selected task.
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task:
            return

        current = ""
        if task.due:
            current = getattr(task.due, "string", "") or str(task.due.date)

        def on_result(due_string: Optional[str]) -> None:
            """
            Handle date input result.
            """
            if due_string and self._api:
                self.run_worker(
                    self._do_set_date(task.id, due_string),
                    name="set_date",
                )

        self.push_screen(DateInputScreen(current_due=current), callback=on_result)

    async def _do_set_date(self, task_id: str, due_string: str) -> None:
        """
        Set a task's due date via the API.

        Args:
            task_id: The task ID to update.
            due_string: The new due string.
        """
        try:
            self._api.update_task(task_id, due_string=due_string)
            self._update_status(f"[{GREEN}]Due date updated[/]")
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _show_label_picker(self) -> None:
        """
        Show the label picker modal for the selected task.
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task:
            return

        available = [lbl.name for lbl in self._labels]
        current = getattr(task, "labels", []) or []

        def on_result(labels: Optional[list[str]]) -> None:
            """
            Handle label picker result.
            """
            if labels is not None and self._api:
                self.run_worker(
                    self._do_set_labels(task.id, labels),
                    name="set_labels",
                )

        self.push_screen(
            LabelPickerScreen(available_labels=available, current_labels=current),
            callback=on_result,
        )

    async def _do_set_labels(self, task_id: str, labels: list[str]) -> None:
        """
        Set a task's labels via the API.

        Args:
            task_id: The task ID to update.
            labels: The new label list.
        """
        try:
            self._api.update_task(task_id, labels=labels)
            self._update_status(f"[{GREEN}]Labels updated[/]")
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _show_project_picker(self) -> None:
        """
        Show the project picker modal for moving a task.
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task:
            return

        def on_result(project_id: Optional[str]) -> None:
            """
            Handle project picker result.
            """
            if project_id and self._api:
                self.run_worker(
                    self._do_move_task(task.id, project_id),
                    name="move_task",
                )

        self.push_screen(
            ProjectPickerScreen(projects=self._projects),
            callback=on_result,
        )

    async def _do_move_task(self, task_id: str, project_id: str) -> None:
        """
        Move a task to a different project via the API.

        Args:
            task_id: The task ID to move.
            project_id: The target project ID.
        """
        try:
            self._api.move_task(task_id, project_id=project_id)
            self._update_status(f"[{GREEN}]Task moved[/]")
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Error: {e}[/]")

    def _show_snooze(self) -> None:
        """
        Show the snooze modal for the selected task.
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task:
            return

        def on_result(preset: Optional[str]) -> None:
            """
            Handle snooze preset selection.
            """
            if preset and self._api:
                self.run_worker(
                    self._do_snooze(task, preset),
                    name="snooze_task",
                )

        self.push_screen(SnoozeScreen(), callback=on_result)

    async def _do_snooze(self, task, preset: str) -> None:
        """
        Snooze a task: write a snooze comment and reschedule to tomorrow.

        Args:
            task: The task object to snooze.
            preset: The snooze preset string.
        """
        try:
            wake_time = resolve_preset_wake_time(preset)

            # Build original due info
            original_due_date = ""
            original_due_string = ""
            is_recurring = False
            if task.due:
                due_val = task.due.date
                if isinstance(due_val, datetime):
                    original_due_date = due_val.date().isoformat()
                else:
                    original_due_date = str(due_val)
                original_due_string = getattr(task.due, "string", "") or ""
                is_recurring = getattr(task.due, "is_recurring", False)

            # Create snooze comment
            comment = build_snooze_comment(
                original_due_date=original_due_date,
                original_due_string=original_due_string,
                wake_time=wake_time,
                is_recurring=is_recurring,
            )
            self._api.add_comment(task_id=task.id, content=comment)

            # Reschedule to tomorrow
            self._api.update_task(task.id, due_string="tomorrow")

            self._update_status(
                f"[{GREEN}]Snoozed until {wake_time.strftime('%H:%M')}[/]"
            )
            await self._fetch_all_data()
        except Exception as e:
            self._update_status(f"[{RED}]Snooze error: {e}[/]")

    def _set_priority(self, key_number: int) -> None:
        """
        Set priority on the selected task.

        Key mapping: 1=p1(urgent, API priority 4), 2=p2(API 3),
        3=p3(API 2), 4=p4(normal, API 1).

        Args:
            key_number: The key pressed (1-4).
        """
        task_list = self.query_one("#task-list", TaskList)
        task = task_list.get_selected_task()
        if not task or not self._api:
            return
        # Todoist API: priority 4 = p1/urgent, 1 = p4/normal
        api_priority = 5 - key_number
        self.run_worker(
            self._do_edit(task.id, {"priority": api_priority}),
            name="set_priority",
        )

    def _open_url(self) -> None:
        """
        Open the first URL found in the selected task's content/description.
        """
        task_list = self.query_one("#task-list", TaskList)
        url = task_list.get_selected_url()
        if url:
            webbrowser.open(url)
            self._update_status(f"[{GREEN}]Opened URL[/]")
        else:
            self._update_status(f"[{DIM_TEXT}]No URL found in task[/]")

    def _show_search(self) -> None:
        """
        Show the search modal.
        """
        def on_result(task_id: Optional[str]) -> None:
            """
            Handle search result — scroll to selected task.
            """
            if task_id:
                task_list = self.query_one("#task-list", TaskList)
                for i, t in enumerate(task_list._tasks):
                    if t.id == task_id:
                        task_list.selected_index = i
                        break

        self.push_screen(
            SearchScreen(tasks=self._all_tasks),
            callback=on_result,
        )


def run_tui(api=None) -> None:
    """
    Launch the Todoist TUI.

    Args:
        api: An optional TodoistAPI instance. If not provided, the TUI
             will start with empty data.
    """
    app = TodoistApp(api=api)
    app.run()
