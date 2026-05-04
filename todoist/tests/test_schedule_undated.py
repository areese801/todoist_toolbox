"""Tests for the schedule-undated recipe."""

import argparse
from datetime import date
from unittest.mock import MagicMock, patch

from todoist.tests.helpers import make_task, make_due


_TEST_CONFIG = {
    "work_label": "Work",
    "project_color": "sky_blue",
    "no_robots_label": "_no_robots",
    "no_due_date_label": "_NoDueDate",
    "timezone": "America/Denver",
    "friday_cutoff_hour": 18,
}


def _patch_config(**overrides):
    config = {**_TEST_CONFIG, **overrides}
    return patch(
        "todoist.recipes.schedule_undated.get_config",
        return_value=config,
    )


class TestNextBusinessDay:
    """Tests for _next_business_day calculation."""

    def test_sunday_returns_monday_tomorrow(self):
        from todoist.recipes.schedule_undated import _next_business_day

        # Sunday April 12, 2026 -> Monday April 13
        assert _next_business_day(date(2026, 4, 12)) == date(2026, 4, 13)

    def test_monday_returns_tuesday(self):
        from todoist.recipes.schedule_undated import _next_business_day

        # Monday April 13, 2026 -> Tuesday April 14
        assert _next_business_day(date(2026, 4, 13)) == date(2026, 4, 14)

    def test_thursday_returns_friday(self):
        from todoist.recipes.schedule_undated import _next_business_day

        # Thursday April 16, 2026 -> Friday April 17
        assert _next_business_day(date(2026, 4, 16)) == date(2026, 4, 17)

    def test_friday_returns_following_monday(self):
        from todoist.recipes.schedule_undated import _next_business_day

        # Friday April 17, 2026 -> Saturday is weekend, skip to Monday April 20
        assert _next_business_day(date(2026, 4, 17)) == date(2026, 4, 20)

    def test_saturday_returns_following_monday(self):
        from todoist.recipes.schedule_undated import _next_business_day

        # Saturday April 18, 2026 -> Sunday is weekend, skip to Monday April 20
        assert _next_business_day(date(2026, 4, 18)) == date(2026, 4, 20)


class TestRunFiltering:
    """Tests for run() filtering logic."""

    def test_dated_tasks_are_excluded(self, capsys):
        """Tasks that already have a due date are not touched."""
        from todoist.recipes.schedule_undated import run

        dated_task = make_task(
            task_id="1",
            content="Already scheduled",
            due=make_due(due_date=date(2026, 5, 1), is_recurring=False),
            labels=[],
        )

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[dated_task],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "Already scheduled" not in output
        assert "No undated tasks" in output

    def test_no_due_date_label_tasks_are_skipped(self, capsys):
        """Tasks with the _NoDueDate label are excluded and reported."""
        from todoist.recipes.schedule_undated import run

        opted_out = make_task(
            task_id="1",
            content="Opted out task",
            due=None,
            _no_due=True,
            labels=["_NoDueDate"],
        )

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[opted_out],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "Skipping 1 task(s) with '_NoDueDate' label" in output
        assert "Opted out task" not in output

    def test_no_robots_tasks_are_skipped(self, capsys):
        """Undated tasks with _no_robots are excluded and reported."""
        from todoist.recipes.schedule_undated import run

        protected = make_task(
            task_id="1",
            content="Protected undated",
            due=None,
            _no_due=True,
            labels=["_no_robots"],
        )

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[protected],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "Skipping 1 task(s) with '_no_robots' label" in output
        assert "Protected undated" not in output

    def test_eligible_tasks_are_listed(self, capsys):
        """Undated tasks with neither label are listed in dry-run."""
        from todoist.recipes.schedule_undated import run

        eligible = make_task(
            task_id="1",
            content="Needs a date",
            due=None,
            _no_due=True,
            labels=[],
        )

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[eligible],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=MagicMock())

        output = capsys.readouterr().out
        assert "Needs a date" in output


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_call_api(self, capsys):
        """In dry-run mode, api.update_task should not be called."""
        from todoist.recipes.schedule_undated import run

        eligible = make_task(
            task_id="1",
            content="Needs a date",
            due=None,
            _no_due=True,
            labels=[],
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[eligible],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        mock_api.update_task.assert_not_called()
        output = capsys.readouterr().out
        assert "DRY RUN" in output
        assert "--execute" in output


class TestExecute:
    """Tests for execute mode."""

    def test_execute_calls_update_task_per_eligible(self, capsys):
        """Execute mode should call update_task once per eligible task."""
        from todoist.recipes.schedule_undated import run

        task_a = make_task(
            task_id="1", content="Task A", due=None, _no_due=True, labels=[]
        )
        task_b = make_task(
            task_id="2", content="Task B", due=None, _no_due=True, labels=[]
        )

        mock_api = MagicMock()

        # Wednesday April 15, 2026 -> next business day is Thursday April 16
        fake_now = MagicMock()
        fake_now.date.return_value = date(2026, 4, 15)

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated._now_in_tz",
                return_value=fake_now,
            ),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[task_a, task_b],
            ),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        assert mock_api.update_task.call_count == 2
        mock_api.update_task.assert_any_call("1", due_date="2026-04-16")
        mock_api.update_task.assert_any_call("2", due_date="2026-04-16")

        output = capsys.readouterr().out
        assert "Scheduled 2 of 2" in output

    def test_execute_handles_per_task_exceptions(self, capsys):
        """A failing update_task call should not abort the loop; it should be counted."""
        from todoist.recipes.schedule_undated import run

        task_ok = make_task(
            task_id="1", content="Good task", due=None, _no_due=True, labels=[]
        )
        task_bad = make_task(
            task_id="2", content="Bad task", due=None, _no_due=True, labels=[]
        )

        mock_api = MagicMock()
        # First call succeeds, second raises
        mock_api.update_task.side_effect = [None, RuntimeError("API down")]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[task_ok, task_bad],
            ),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        assert mock_api.update_task.call_count == 2
        output = capsys.readouterr().out
        assert "FAILED" in output
        assert "1 failure(s)" in output
        assert "Scheduled 1 of 2" in output


class TestEmptyEligible:
    """Tests for when no eligible tasks exist."""

    def test_no_undated_tasks(self, capsys):
        """When all tasks are dated, print a message and don't call the API."""
        from todoist.recipes.schedule_undated import run

        dated = make_task(
            task_id="1",
            content="Already scheduled",
            due=make_due(due_date=date(2026, 5, 1), is_recurring=False),
            labels=[],
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.schedule_undated.get_active_tasks",
                return_value=[dated],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        mock_api.update_task.assert_not_called()
        output = capsys.readouterr().out
        assert "No undated tasks" in output
