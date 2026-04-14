"""Factory helpers for creating mock Todoist Task and Due objects in tests."""

from datetime import date, timedelta
from unittest.mock import MagicMock


def make_due(
    due_date=None,
    due_string="every day",
    is_recurring=True,
    lang="en",
    timezone=None,
):
    """Create a mock Due object."""
    due = MagicMock()
    due.date = due_date if due_date is not None else date.today() - timedelta(days=1)
    due.string = due_string
    due.is_recurring = is_recurring
    due.lang = lang
    due.timezone = timezone
    return due


def make_label(
    label_id="lab_1",
    name="Work",
    color="sky_blue",
    is_favorite=False,
):
    """Create a mock Label object."""
    label = MagicMock()
    label.id = label_id
    label.name = name
    label.color = color
    label.is_favorite = is_favorite
    return label


def make_section(
    section_id="sec_1",
    name="Next Actions",
    project_id="proj_1",
):
    """Create a mock Section object."""
    section = MagicMock()
    section.id = section_id
    section.name = name
    section.project_id = project_id
    return section


def make_comment(
    comment_id="com_1",
    content="Note",
    task_id="1001",
    posted_at="2026-01-01T00:00:00Z",
):
    """Create a mock Comment object."""
    comment = MagicMock()
    comment.id = comment_id
    comment.content = content
    comment.task_id = task_id
    comment.posted_at = posted_at
    return comment


def make_task(
    task_id="1001",
    content="Test task",
    due=None,
    **overrides,
):
    """Create a mock Task object with sensible defaults.

    If `due` is not provided, creates a default overdue recurring Due.
    Pass `due=None` explicitly and `_no_due=True` in overrides to get a task with no due date.
    """
    task = MagicMock()
    task.id = task_id
    task.content = content

    if due is not None:
        task.due = due
    elif overrides.pop("_no_due", False):
        task.due = None
    else:
        task.due = make_due()

    for key, value in overrides.items():
        setattr(task, key, value)

    return task
