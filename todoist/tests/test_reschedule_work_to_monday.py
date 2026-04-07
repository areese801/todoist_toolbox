"""Tests for the reschedule-work-to-monday recipe."""

import argparse
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from todoist.tests.helpers import make_task, make_due


_TEST_CONFIG = {
    "work_label": "Work",
    "project_color": "sky_blue",
    "no_robots_label": "_no_robots",
    "timezone": "America/Denver",
    "friday_cutoff_hour": 18,
}


def _patch_config(**overrides):
    config = {**_TEST_CONFIG, **overrides}
    return patch(
        "todoist.recipes.reschedule_work_to_monday.get_config",
        return_value=config,
    )


class TestDayTimeGuardrails:
    """Tests for day/time safety checks."""

    def test_exits_on_wednesday_without_force(self, capsys):
        """Running on a Wednesday without --force should exit early."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 8, 10, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "use --force" in output.lower()

    def test_runs_on_friday_after_cutoff(self, capsys):
        """Running on Friday at 7 PM should proceed normally."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 10, 19, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[]),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "use --force" not in output.lower()

    def test_exits_on_friday_before_cutoff(self, capsys):
        """Running on Friday at 2 PM (before 6 PM cutoff) should exit early."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 10, 14, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "use --force" in output.lower()

    def test_runs_on_saturday(self, capsys):
        """Running on Saturday should proceed normally (weekend)."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 11, 10, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[]),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "use --force" not in output.lower()

    def test_runs_on_sunday(self, capsys):
        """Running on Sunday should proceed normally (weekend)."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 12, 10, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[]),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "use --force" not in output.lower()

    def test_force_overrides_day_check(self, capsys):
        """--force should bypass the day/time check."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 7, 10, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[]),
        ):
            args = argparse.Namespace(execute=False, force=True)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "use --force" not in output.lower()


class TestNextMonday:
    """Tests for _next_monday calculation."""

    def test_friday_returns_following_monday(self):
        from todoist.recipes.reschedule_work_to_monday import _next_monday
        assert _next_monday(date(2026, 4, 10)) == date(2026, 4, 13)

    def test_saturday_returns_following_monday(self):
        from todoist.recipes.reschedule_work_to_monday import _next_monday
        assert _next_monday(date(2026, 4, 11)) == date(2026, 4, 13)

    def test_sunday_returns_following_monday(self):
        from todoist.recipes.reschedule_work_to_monday import _next_monday
        assert _next_monday(date(2026, 4, 12)) == date(2026, 4, 13)

    def test_monday_returns_next_monday(self):
        from todoist.recipes.reschedule_work_to_monday import _next_monday
        assert _next_monday(date(2026, 4, 13)) == date(2026, 4, 20)


class TestRescheduleWorkToMonday:
    """Tests for the rescheduling logic."""

    def test_only_work_labeled_tasks_are_rescheduled(self, capsys):
        """Only tasks with the work label should be rescheduled."""
        from todoist.recipes.reschedule_work_to_monday import run

        yesterday = date.today() - timedelta(days=1)
        work_task = make_task(
            task_id="1", content="Finish report",
            due=make_due(due_date=yesterday, is_recurring=False),
            labels=["Work"],
        )
        personal_task = make_task(
            task_id="2", content="Buy groceries",
            due=make_due(due_date=yesterday, is_recurring=False),
            labels=["Personal"],
        )

        fake_now = datetime(2026, 4, 10, 19, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[work_task, personal_task]),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "Finish report" in output
        assert "Buy groceries" not in output

    def test_no_robots_tasks_are_skipped(self, capsys):
        """Tasks with both work label and _no_robots should be skipped."""
        from todoist.recipes.reschedule_work_to_monday import run

        yesterday = date.today() - timedelta(days=1)
        protected = make_task(
            task_id="1", content="Protected task",
            due=make_due(due_date=yesterday, is_recurring=False),
            labels=["Work", "_no_robots"],
        )

        fake_now = datetime(2026, 4, 10, 19, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[protected]),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "Skipping 1 task(s)" in output
        assert "Protected task" not in output

    def test_execute_reschedules_to_monday(self, capsys):
        """In execute mode, tasks should be rescheduled to the calculated Monday."""
        from todoist.recipes.reschedule_work_to_monday import run

        yesterday = date.today() - timedelta(days=1)
        task = make_task(
            task_id="1", content="Ship feature",
            due=make_due(due_date=yesterday, is_recurring=False),
            labels=["Work"],
        )

        mock_api = MagicMock()
        # Friday April 10, 7 PM -> next Monday is April 13
        fake_now = datetime(2026, 4, 10, 19, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[task]),
        ):
            args = argparse.Namespace(execute=True, force=False)
            run(args, api=mock_api)

        mock_api.update_task.assert_called_once_with("1", due_date="2026-04-13")
        output = capsys.readouterr().out
        assert "Rescheduled 1 of 1" in output

    def test_no_overdue_work_tasks(self, capsys):
        """When no overdue work tasks exist, print a message."""
        from todoist.recipes.reschedule_work_to_monday import run

        fake_now = datetime(2026, 4, 10, 19, 0, tzinfo=ZoneInfo("America/Denver"))

        with (
            _patch_config(),
            patch("todoist.recipes.reschedule_work_to_monday._now_in_tz",
                  return_value=fake_now),
            patch("todoist.recipes.reschedule_work_to_monday.get_overdue_non_recurring_tasks",
                  return_value=[]),
        ):
            args = argparse.Namespace(execute=False, force=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "no overdue" in output.lower()
