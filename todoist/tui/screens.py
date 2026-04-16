"""
Modal screens for the Todoist TUI.

Provides quick-add, task edit, snooze, label picker, project picker,
date input, search, and help modals.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Static, Button

from todoist.tui.theme import (
    BG_DEFAULT,
    BG_HIGHLIGHT,
    BG_VISUAL,
    BLUE,
    CYAN,
    DIM_TEXT,
    FG_DEFAULT,
    GREEN,
    MAGENTA,
    ORANGE,
    RED,
    YELLOW,
)
from todoist.tui.snooze import SNOOZE_PRESETS


class HelpScreen(ModalScreen):
    """
    Modal showing all keybindings.
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("question_mark", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """
        Compose the help modal content.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Keyboard Shortcuts[/]", classes="modal-title")
            yield Static("")
            yield Static(f"[{YELLOW}]Navigation[/]")
            yield Static(f"  [{CYAN}]j/k[/]      Move down/up")
            yield Static(f"  [{CYAN}]g/G[/]      Jump to top/bottom")
            yield Static(f"  [{CYAN}]t[/]        Today view")
            yield Static(f"  [{CYAN}]i[/]        Inbox view")
            yield Static("")
            yield Static(f"[{YELLOW}]Actions[/]")
            yield Static(f"  [{CYAN}]a/q[/]      Quick-add task")
            yield Static(f"  [{CYAN}]e[/]        Edit selected task")
            yield Static(f"  [{CYAN}]x[/]        Complete selected task")
            yield Static(f"  [{CYAN}]d/r[/]      Reschedule (change due date)")
            yield Static(f"  [{CYAN}]l[/]        Change labels")
            yield Static(f"  [{CYAN}]p[/]        Move to project")
            yield Static(f"  [{CYAN}]1-4[/]      Set priority (1=urgent)")
            yield Static("")
            yield Static(f"[{YELLOW}]Snooze[/]")
            yield Static(f"  [{CYAN}]b/z[/]      Snooze selected task")
            yield Static("")
            yield Static(f"[{YELLOW}]URLs[/]")
            yield Static(f"  [{CYAN}]o/u[/]      Open URL in browser")
            yield Static("")
            yield Static(f"[{YELLOW}]Other[/]")
            yield Static(f"  [{CYAN}]/[/]        Search tasks")
            yield Static(f"  [{CYAN}]?[/]        This help screen")
            yield Static(f"  [{CYAN}]qq[/]       Quit")
            yield Static(f"  [{CYAN}]Ctrl+C[/]   Quit")
            yield Static("")
            yield Static(f"[{DIM_TEXT}]Press Escape or ? to close[/]")


class QuickAddScreen(ModalScreen[Optional[str]]):
    """
    Modal for quickly adding a new task.

    Returns the task content string, or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """
        Compose the quick-add modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Quick Add Task[/]", classes="modal-title")
            yield Input(
                placeholder="Task content...",
                id="quick-add-input",
                classes="search-input",
            )
            yield Static(f"[{DIM_TEXT}]Enter to add \u2022 Escape to cancel[/]")

    def on_mount(self) -> None:
        """
        Focus the input on mount.
        """
        self.query_one("#quick-add-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle input submission.
        """
        value = event.value.strip()
        if value:
            self.dismiss(value)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """
        Cancel the quick-add.
        """
        self.dismiss(None)


class TaskEditScreen(ModalScreen[Optional[dict]]):
    """
    Modal for editing a task's content and description.

    Returns a dict with updated fields, or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        task_content: str = "",
        task_description: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._task_content = task_content
        self._task_description = task_description

    def compose(self) -> ComposeResult:
        """
        Compose the edit modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Edit Task[/]", classes="modal-title")
            yield Static("Content:")
            yield Input(
                value=self._task_content,
                id="edit-content",
                classes="search-input",
            )
            yield Static("Description:")
            yield Input(
                value=self._task_description,
                id="edit-description",
                classes="search-input",
            )
            yield Static(
                f"[{DIM_TEXT}]Tab to switch fields \u2022 "
                f"Enter to save \u2022 Escape to cancel[/]"
            )

    def on_mount(self) -> None:
        """
        Focus the content input on mount.
        """
        self.query_one("#edit-content", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle input submission — save the edit.
        """
        content = self.query_one("#edit-content", Input).value.strip()
        description = self.query_one("#edit-description", Input).value.strip()
        if content:
            self.dismiss({"content": content, "description": description})
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """
        Cancel the edit.
        """
        self.dismiss(None)


class DateInputScreen(ModalScreen[Optional[str]]):
    """
    Modal for entering a due date string.

    Returns the due string, or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_due: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_due = current_due

    def compose(self) -> ComposeResult:
        """
        Compose the date input modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Set Due Date[/]", classes="modal-title")
            if self._current_due:
                yield Static(f"Current: [{YELLOW}]{self._current_due}[/]")
            yield Input(
                placeholder="e.g. today, tomorrow, every monday, jan 15...",
                id="date-input",
                classes="search-input",
            )
            yield Static(f"[{DIM_TEXT}]Enter to set \u2022 Escape to cancel[/]")

    def on_mount(self) -> None:
        """
        Focus the input on mount.
        """
        self.query_one("#date-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle date input submission.
        """
        value = event.value.strip()
        self.dismiss(value if value else None)

    def action_cancel(self) -> None:
        """
        Cancel the date input.
        """
        self.dismiss(None)


class SnoozeScreen(ModalScreen[Optional[str]]):
    """
    Modal for snoozing a task with preset or custom duration.

    Returns the selected preset string (e.g. "30m", "1h", "afternoon"),
    or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected = 0
        self._presets = list(SNOOZE_PRESETS.keys()) + ["custom"]

    def compose(self) -> ComposeResult:
        """
        Compose the snooze modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Snooze Task[/]", classes="modal-title")
            yield Static("")
            for i, preset in enumerate(self._presets):
                marker = f"[{CYAN}]\u25b6[/] " if i == 0 else "  "
                cls = "snooze-preset --selected" if i == 0 else "snooze-preset"
                yield Static(
                    f"{marker}{preset}",
                    id=f"snooze-{i}",
                    classes=cls,
                )
            yield Static("")
            yield Input(
                placeholder="Or type custom duration (e.g. 45m, 3h)...",
                id="snooze-custom-input",
                classes="search-input",
            )
            yield Static(
                f"[{DIM_TEXT}]j/k to select \u2022 Enter to confirm \u2022 "
                f"Escape to cancel[/]"
            )

    def on_key(self, event) -> None:
        """
        Handle keyboard navigation in snooze preset list.
        """
        if event.key == "j" or event.key == "down":
            self._move_selection(1)
            event.prevent_default()
            event.stop()
        elif event.key == "k" or event.key == "up":
            self._move_selection(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            # If custom input has focus and text, use that
            custom_input = self.query_one("#snooze-custom-input", Input)
            if custom_input.has_focus and custom_input.value.strip():
                self.dismiss(custom_input.value.strip())
            else:
                self.dismiss(self._presets[self._selected])
            event.prevent_default()
            event.stop()

    def _move_selection(self, delta: int) -> None:
        """
        Move the preset selection.

        Args:
            delta: Direction to move (-1 up, +1 down).
        """
        old_idx = self._selected
        new_idx = max(0, min(len(self._presets) - 1, old_idx + delta))
        if old_idx != new_idx:
            old_widget = self.query_one(f"#snooze-{old_idx}", Static)
            old_widget.remove_class("--selected")
            old_widget.update(f"  {self._presets[old_idx]}")

            new_widget = self.query_one(f"#snooze-{new_idx}", Static)
            new_widget.add_class("--selected")
            new_widget.update(f"[{CYAN}]\u25b6[/] {self._presets[new_idx]}")

            self._selected = new_idx

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle custom duration input submission.
        """
        value = event.value.strip()
        if value:
            self.dismiss(value)

    def action_cancel(self) -> None:
        """
        Cancel the snooze.
        """
        self.dismiss(None)


class SearchScreen(ModalScreen[Optional[str]]):
    """
    Modal for fuzzy-searching tasks.

    Returns the selected task ID, or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, tasks: list, **kwargs) -> None:
        super().__init__(**kwargs)
        self._all_tasks = tasks
        self._filtered_tasks: list = []
        self._selected = 0

    def compose(self) -> ComposeResult:
        """
        Compose the search modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Search Tasks[/]", classes="modal-title")
            yield Input(
                placeholder="Type to search...",
                id="search-input",
                classes="search-input",
            )
            yield Vertical(id="search-results")
            yield Static(
                f"[{DIM_TEXT}]Type to filter \u2022 Enter to select \u2022 "
                f"Escape to cancel[/]"
            )

    def on_mount(self) -> None:
        """
        Focus the search input on mount.
        """
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Filter tasks as the user types using fuzzy matching.
        """
        query = event.value.strip()
        results_container = self.query_one("#search-results", Vertical)
        results_container.remove_children()

        if not query:
            self._filtered_tasks = []
            self._selected = 0
            return

        try:
            from thefuzz import fuzz
        except ImportError:
            # Fallback to simple substring matching
            self._filtered_tasks = [
                t for t in self._all_tasks
                if query.lower() in t.content.lower()
            ]
        else:
            scored = []
            for t in self._all_tasks:
                score = fuzz.partial_ratio(query.lower(), t.content.lower())
                if score >= 50:
                    scored.append((score, t))
            scored.sort(key=lambda x: x[0], reverse=True)
            self._filtered_tasks = [t for _, t in scored[:15]]

        self._selected = 0
        for i, task in enumerate(self._filtered_tasks):
            marker = f"[{CYAN}]\u25b6[/] " if i == 0 else "  "
            results_container.mount(
                Static(f"{marker}{task.content}", id=f"result-{i}")
            )

    def on_key(self, event) -> None:
        """
        Handle keyboard navigation in search results.
        """
        if event.key in ("j", "down"):
            if self._filtered_tasks:
                self._selected = min(
                    len(self._filtered_tasks) - 1, self._selected + 1
                )
                self._update_result_highlight()
            event.prevent_default()
            event.stop()
        elif event.key in ("k", "up"):
            if self._filtered_tasks:
                self._selected = max(0, self._selected - 1)
                self._update_result_highlight()
            event.prevent_default()
            event.stop()

    def _update_result_highlight(self) -> None:
        """
        Update visual highlighting in search results.
        """
        results = self.query_one("#search-results", Vertical)
        for i, child in enumerate(results.children):
            task = self._filtered_tasks[i]
            if i == self._selected:
                child.update(f"[{CYAN}]\u25b6[/] {task.content}")
            else:
                child.update(f"  {task.content}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Select the highlighted search result.
        """
        if self._filtered_tasks and 0 <= self._selected < len(self._filtered_tasks):
            self.dismiss(self._filtered_tasks[self._selected].id)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """
        Cancel the search.
        """
        self.dismiss(None)


class LabelPickerScreen(ModalScreen[Optional[list[str]]]):
    """
    Modal for toggling labels on a task.

    Returns the updated label list, or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        available_labels: list[str],
        current_labels: list[str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._available = available_labels
        self._current = set(current_labels)
        self._selected = 0

    def compose(self) -> ComposeResult:
        """
        Compose the label picker modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Toggle Labels[/]", classes="modal-title")
            yield Vertical(id="label-options")
            yield Static(
                f"[{DIM_TEXT}]j/k navigate \u2022 Space toggle \u2022 "
                f"Enter confirm \u2022 Escape cancel[/]"
            )

    def on_mount(self) -> None:
        """
        Populate label options.
        """
        container = self.query_one("#label-options", Vertical)
        for i, label in enumerate(self._available):
            check = f"[{GREEN}]\u2713[/]" if label in self._current else " "
            marker = f"[{CYAN}]\u25b6[/]" if i == 0 else " "
            container.mount(
                Static(f"{marker} [{check}] {label}", id=f"label-{i}")
            )

    def on_key(self, event) -> None:
        """
        Handle keyboard navigation and toggling.
        """
        if event.key in ("j", "down"):
            self._selected = min(len(self._available) - 1, self._selected + 1)
            self._refresh_labels()
            event.prevent_default()
            event.stop()
        elif event.key in ("k", "up"):
            self._selected = max(0, self._selected - 1)
            self._refresh_labels()
            event.prevent_default()
            event.stop()
        elif event.key == "space":
            label = self._available[self._selected]
            if label in self._current:
                self._current.remove(label)
            else:
                self._current.add(label)
            self._refresh_labels()
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            self.dismiss(sorted(self._current))
            event.prevent_default()
            event.stop()

    def _refresh_labels(self) -> None:
        """
        Update the visual state of all label options.
        """
        for i, label in enumerate(self._available):
            widget = self.query_one(f"#label-{i}", Static)
            check = f"[{GREEN}]\u2713[/]" if label in self._current else " "
            marker = f"[{CYAN}]\u25b6[/]" if i == self._selected else " "
            widget.update(f"{marker} [{check}] {label}")

    def action_cancel(self) -> None:
        """
        Cancel the label picker.
        """
        self.dismiss(None)


class ProjectPickerScreen(ModalScreen[Optional[str]]):
    """
    Modal for selecting a project to move a task to.

    Returns the project ID, or None if cancelled.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, projects: list, **kwargs) -> None:
        super().__init__(**kwargs)
        self._projects = projects
        self._selected = 0

    def compose(self) -> ComposeResult:
        """
        Compose the project picker modal.
        """
        with Vertical(classes="modal-container"):
            yield Static(f"[bold {BLUE}]Move to Project[/]", classes="modal-title")
            yield Vertical(id="project-options")
            yield Static(
                f"[{DIM_TEXT}]j/k navigate \u2022 Enter select \u2022 "
                f"Escape cancel[/]"
            )

    def on_mount(self) -> None:
        """
        Populate project options.
        """
        container = self.query_one("#project-options", Vertical)
        for i, project in enumerate(self._projects):
            marker = f"[{CYAN}]\u25b6[/] " if i == 0 else "  "
            container.mount(
                Static(f"{marker}{project.name}", id=f"proj-{i}")
            )

    def on_key(self, event) -> None:
        """
        Handle keyboard navigation.
        """
        if event.key in ("j", "down"):
            self._move(1)
            event.prevent_default()
            event.stop()
        elif event.key in ("k", "up"):
            self._move(-1)
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            if self._projects:
                self.dismiss(self._projects[self._selected].id)
            else:
                self.dismiss(None)
            event.prevent_default()
            event.stop()

    def _move(self, delta: int) -> None:
        """
        Move selection in project list.
        """
        old = self._selected
        new = max(0, min(len(self._projects) - 1, old + delta))
        if old != new:
            old_w = self.query_one(f"#proj-{old}", Static)
            old_w.update(f"  {self._projects[old].name}")
            new_w = self.query_one(f"#proj-{new}", Static)
            new_w.update(f"[{CYAN}]\u25b6[/] {self._projects[new].name}")
            self._selected = new

    def action_cancel(self) -> None:
        """
        Cancel the project picker.
        """
        self.dismiss(None)
