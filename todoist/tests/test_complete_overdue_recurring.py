"""Tests for the complete-overdue-recurring recipe."""

import argparse
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from todoist.tests.helpers import make_task, make_due


_TEST_CONFIG = {
    "work_label": "Work",
    "project_color": "sky_blue",
    "no_robots_label": "_no_robots",
    "timezone": "America/Denver",
    "friday_cutoff_hour": 18,
}


def _patch_config():
    return patch(
        "todoist.recipes.complete_overdue_recurring.get_config",
        return_value=_TEST_CONFIG,
    )


def _patch_probes_with(intervals: dict[str, int | None]):
    """
    Return a context manager that patches _probe_intervals_parallel to
    return the given intervals dict, so tests skip real API probing.
    """
    return patch(
        "todoist.recipes.complete_overdue_recurring._probe_intervals_parallel",
        return_value=intervals,
    )


class TestCompleteOverdueDryRun:
    """Tests for dry-run mode (default)."""

    def test_dry_run_prints_qualifying_tasks(self, capsys):
        """In dry-run mode, qualifying tasks are printed but not completed."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)

        t1 = make_task(
            task_id="1",
            content="Daily standup",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
        )
        t2 = make_task(
            task_id="2",
            content="Monthly review",
            due=make_due(
                due_date=yesterday, due_string="every month", is_recurring=True
            ),
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1, t2],
            ),
            _patch_probes_with({"every day": 1, "every month": 30}),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        mock_api.complete_task.assert_not_called()
        output = capsys.readouterr().out
        assert "Daily standup" in output
        assert "Monthly review" not in output  # 30 > 7, excluded

    def test_dry_run_no_overdue_tasks(self, capsys):
        """When no overdue tasks exist, print a message saying so."""
        from todoist.recipes.complete_overdue_recurring import run

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[],
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "no" in output.lower() or "0" in output.lower()

    def test_dry_run_no_qualifying_tasks(self, capsys):
        """When overdue tasks exist but none qualify (all > 7 days), print message."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)
        t1 = make_task(
            task_id="1",
            content="Monthly review",
            due=make_due(
                due_date=yesterday, due_string="every month", is_recurring=True
            ),
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1],
            ),
            _patch_probes_with({"every month": 30}),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "no qualifying" in output.lower() or "none" in output.lower()


class TestCompleteOverdueExecute:
    """Tests for execute mode (--execute)."""

    def test_execute_calls_complete_task(self, capsys):
        """In execute mode, complete_task is called for each qualifying task."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)

        t1 = make_task(
            task_id="1",
            content="Daily standup",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
        )
        t2 = make_task(
            task_id="2",
            content="Check mailbox",
            due=make_due(
                due_date=yesterday, due_string="every 2 days", is_recurring=True
            ),
        )

        mock_api = MagicMock()
        mock_api.complete_task.return_value = True

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1, t2],
            ),
            _patch_probes_with({"every day": 1, "every 2 days": 2}),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        assert mock_api.complete_task.call_count == 2
        mock_api.complete_task.assert_any_call("1")
        mock_api.complete_task.assert_any_call("2")

        output = capsys.readouterr().out
        assert "Closed 2 of 2" in output

    def test_execute_continues_on_individual_failure(self, capsys):
        """If one complete_task fails, the recipe continues with the rest."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)

        t1 = make_task(
            task_id="1",
            content="Failing task",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
        )
        t2 = make_task(
            task_id="2",
            content="OK task",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
        )

        mock_api = MagicMock()
        mock_api.complete_task.side_effect = [Exception("API down"), True]

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1, t2],
            ),
            _patch_probes_with({"every day": 1}),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        assert mock_api.complete_task.call_count == 2
        output = capsys.readouterr().out
        assert "1 failure" in output.lower()
        assert "Closed 1 of 2" in output


class TestNoRobotsLabel:
    """Tests for _no_robots label skipping."""

    def test_tasks_with_no_robots_label_are_skipped(self, capsys):
        """Tasks with the _no_robots label should be excluded from processing."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)

        robot_task = make_task(
            task_id="1",
            content="Automated standup",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
            labels=[],
        )
        no_robot_task = make_task(
            task_id="2",
            content="Manual review",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
            labels=["_no_robots"],
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[robot_task, no_robot_task],
            ),
            _patch_probes_with({"every day": 1}),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "Automated standup" in output
        assert "Manual review" not in output
        assert "Skipping 1 task(s)" in output

    def test_all_tasks_with_no_robots_label_yields_no_qualifying(self, capsys):
        """If all overdue tasks have _no_robots, none should qualify."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)

        t1 = make_task(
            task_id="1",
            content="No robots task",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
            labels=["_no_robots"],
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1],
            ),
            _patch_probes_with({}),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "Skipping 1 task(s)" in output
        mock_api.complete_task.assert_not_called()

    def test_no_robots_tasks_not_closed_in_execute_mode(self, capsys):
        """In execute mode, _no_robots tasks should not be closed."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)

        normal_task = make_task(
            task_id="1",
            content="Normal task",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
            labels=[],
        )
        no_robot_task = make_task(
            task_id="2",
            content="Protected task",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
            labels=["_no_robots"],
        )

        mock_api = MagicMock()
        mock_api.complete_task.return_value = True

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[normal_task, no_robot_task],
            ),
            _patch_probes_with({"every day": 1}),
        ):
            args = argparse.Namespace(execute=True)
            run(args, api=mock_api)

        mock_api.complete_task.assert_called_once_with("1")
        output = capsys.readouterr().out
        assert "Closed 1 of 1" in output


class TestProbeDeduplication:
    """Tests for in-memory probe deduplication."""

    def test_duplicate_due_strings_probed_once(self, capsys):
        """Three tasks with the same due.string should trigger only one probe."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)
        tasks = [
            make_task(
                task_id=str(i),
                content=f"Task {i}",
                due=make_due(
                    due_date=yesterday, due_string="every day", is_recurring=True
                ),
            )
            for i in range(3)
        ]

        mock_api = MagicMock()
        mock_probe_parallel = MagicMock(return_value={"every day": 1})

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=tasks,
            ),
            patch(
                "todoist.recipes.complete_overdue_recurring._probe_intervals_parallel",
                mock_probe_parallel,
            ),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        # _probe_intervals_parallel should receive only 1 unique due string
        call_args = mock_probe_parallel.call_args
        due_strings_arg = call_args[0][1]
        assert len(due_strings_arg) == 1
        assert "every day" in due_strings_arg

    def test_failed_probe_excludes_task(self, capsys):
        """Tasks whose probe returns None are excluded from qualifying list."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)
        t1 = make_task(
            task_id="1",
            content="Broken task",
            due=make_due(
                due_date=yesterday, due_string="weird schedule", is_recurring=True
            ),
        )

        mock_api = MagicMock()

        with (
            _patch_config(),
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1],
            ),
            _patch_probes_with({"weird schedule": None}),
        ):
            args = argparse.Namespace(execute=False)
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "no qualifying" in output.lower() or "none" in output.lower()
