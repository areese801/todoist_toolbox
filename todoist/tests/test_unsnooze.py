"""Tests for the unsnooze recipe."""

import argparse
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from todoist.tests.helpers import make_task, make_due, make_comment
from todoist.tui.snooze import build_snooze_comment


_TEST_CONFIG = {
    "work_label": "Work",
    "project_color": "sky_blue",
    "no_robots_label": "_no_robots",
    "timezone": "America/Denver",
    "friday_cutoff_hour": 18,
}


def _patch_config():
    return patch(
        "todoist.recipes.unsnooze.get_config",
        return_value=_TEST_CONFIG,
    )


def _make_snooze_comment(
    wake_time=None,
    original_due_date="2026-04-16",
    original_due_string="every day",
    is_recurring=True,
    comment_id="com_snooze",
    task_id="1001",
):
    """
    Create a mock comment containing snooze metadata.

    Args:
        wake_time: When the snooze expires. Defaults to 1 hour ago.
        original_due_date: Original due date string.
        original_due_string: Original due string.
        is_recurring: Whether the original task was recurring.
        comment_id: The comment ID.
        task_id: The task ID this comment belongs to.

    Returns:
        A mock Comment object with snooze metadata content.
    """
    if wake_time is None:
        wake_time = datetime.now() - timedelta(hours=1)

    content = build_snooze_comment(
        original_due_date=original_due_date,
        original_due_string=original_due_string,
        wake_time=wake_time,
        is_recurring=is_recurring,
    )
    return make_comment(
        comment_id=comment_id,
        content=content,
        task_id=task_id,
    )


class TestUnsnoozeDryRun:
    """Tests for dry-run mode (default)."""

    def test_dry_run_finds_snoozed_tasks(self, capsys):
        """Snoozed tasks past wake_time are printed in dry-run."""
        from todoist.recipes.unsnooze import run

        task = make_task(task_id="1001", content="Snoozed task", labels=[])
        snooze_comment = _make_snooze_comment(task_id="1001")

        mock_api = MagicMock()
        mock_api.get_comments.return_value = [snooze_comment]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[task],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        mock_api.update_task.assert_not_called()
        mock_api.delete_comment.assert_not_called()
        output = capsys.readouterr().out
        assert "Snoozed task" in output
        assert "DRY RUN" in output

    def test_dry_run_no_snoozed_tasks(self, capsys):
        """When no snoozed tasks exist, print message."""
        from todoist.recipes.unsnooze import run

        task = make_task(task_id="1001", content="Normal task", labels=[])
        normal_comment = make_comment(
            comment_id="com_1",
            content="Just a note",
            task_id="1001",
        )

        mock_api = MagicMock()
        mock_api.get_comments.return_value = [normal_comment]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[task],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "no snoozed" in output.lower() or "0" in output.lower()

    def test_future_wake_time_not_included(self, capsys):
        """Tasks whose wake_time is in the future are not included."""
        from todoist.recipes.unsnooze import run

        task = make_task(task_id="1001", content="Still sleeping", labels=[])
        future_wake = datetime.now() + timedelta(hours=2)
        snooze_comment = _make_snooze_comment(
            wake_time=future_wake,
            task_id="1001",
        )

        mock_api = MagicMock()
        mock_api.get_comments.return_value = [snooze_comment]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[task],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "Still sleeping" not in output


class TestUnsnoozeExecute:
    """Tests for execute mode (--execute)."""

    def test_execute_restores_due_string(self, capsys):
        """Execute mode restores recurring task's due_string."""
        from todoist.recipes.unsnooze import run

        task = make_task(task_id="1001", content="Wake up", labels=[])
        snooze_comment = _make_snooze_comment(
            task_id="1001",
            original_due_string="every day",
            is_recurring=True,
            comment_id="com_snz",
        )

        mock_api = MagicMock()
        mock_api.get_comments.return_value = [snooze_comment]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[task],
            ),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        mock_api.update_task.assert_called_once_with(
            "1001", due_string="every day"
        )
        mock_api.delete_comment.assert_called_once_with("com_snz")

    def test_execute_restores_due_date(self, capsys):
        """Execute mode restores non-recurring task's due_date."""
        from todoist.recipes.unsnooze import run

        task = make_task(task_id="1001", content="One-time task", labels=[])
        snooze_comment = _make_snooze_comment(
            task_id="1001",
            original_due_date="2026-04-20",
            original_due_string=None,
            is_recurring=False,
            comment_id="com_snz",
        )

        mock_api = MagicMock()
        mock_api.get_comments.return_value = [snooze_comment]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[task],
            ),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        mock_api.update_task.assert_called_once_with(
            "1001", due_date="2026-04-20"
        )

    def test_execute_continues_on_failure(self, capsys):
        """If one unsnooze fails, the recipe continues with the rest."""
        from todoist.recipes.unsnooze import run

        t1 = make_task(task_id="1001", content="Failing task", labels=[])
        t2 = make_task(task_id="1002", content="OK task", labels=[])

        snz1 = _make_snooze_comment(task_id="1001", comment_id="com_1")
        snz2 = _make_snooze_comment(task_id="1002", comment_id="com_2")

        mock_api = MagicMock()
        mock_api.get_comments.side_effect = lambda task_id: {
            "1001": [snz1],
            "1002": [snz2],
        }[task_id]
        mock_api.update_task.side_effect = [Exception("API error"), None]
        mock_api.delete_comment.return_value = None

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[t1, t2],
            ),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        assert mock_api.update_task.call_count == 2
        output = capsys.readouterr().out
        assert "1 failure" in output.lower()


class TestUnsnoozeNoRobots:
    """Tests for _no_robots label skipping in unsnooze."""

    def test_no_robots_tasks_skipped(self, capsys):
        """Tasks with _no_robots label should be excluded."""
        from todoist.recipes.unsnooze import run

        task = make_task(
            task_id="1001",
            content="Protected task",
            labels=["_no_robots"],
        )

        mock_api = MagicMock()
        # Should never get_comments since the task is skipped
        mock_api.get_comments.return_value = []

        with (
            _patch_config(),
            patch(
                "todoist.recipes.unsnooze.get_active_tasks",
                return_value=[task],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "Skipping 1 task(s)" in output
