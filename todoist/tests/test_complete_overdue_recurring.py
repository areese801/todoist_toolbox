"""Tests for the complete-overdue-recurring recipe."""

import argparse
from unittest.mock import MagicMock, patch, call
from datetime import date, timedelta

from todoist.cache import MISS
from todoist.tests.helpers import make_task, make_due


def _patch_cache_with(data: dict):
    """
    Return a context manager that patches load_cache to return `data`
    and save_cache to no-op, so tests skip real disk I/O and probing.
    """
    return patch.multiple(
        "todoist.recipes.complete_overdue_recurring",
        load_cache=MagicMock(return_value=data),
        save_cache=MagicMock(),
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
        cache_data = {"every day": 1, "every month": 30}

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1, t2],
            ),
            _patch_cache_with(cache_data),
        ):
            args = argparse.Namespace(execute=False, clear_cache=False)
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
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[],
            ),
            _patch_cache_with({}),
        ):
            args = argparse.Namespace(execute=False, clear_cache=False)
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
        cache_data = {"every month": 30}

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1],
            ),
            _patch_cache_with(cache_data),
        ):
            args = argparse.Namespace(execute=False, clear_cache=False)
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
        cache_data = {"every day": 1, "every 2 days": 2}

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1, t2],
            ),
            _patch_cache_with(cache_data),
        ):
            args = argparse.Namespace(execute=True, clear_cache=False)
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
        cache_data = {"every day": 1}

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1, t2],
            ),
            _patch_cache_with(cache_data),
        ):
            args = argparse.Namespace(execute=True, clear_cache=False)
            run(args, api=mock_api)

        assert mock_api.complete_task.call_count == 2
        output = capsys.readouterr().out
        assert "1 failure" in output.lower()
        assert "Closed 1 of 2" in output


class TestCacheIntegration:
    """Tests for persistent cache integration in the recipe."""

    def test_cache_hit_skips_probing(self, capsys):
        """When all intervals are cached, no probing occurs."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)
        tasks = [
            make_task(
                task_id="1",
                content="Task 1",
                due=make_due(
                    due_date=yesterday, due_string="every day", is_recurring=True
                ),
            ),
            make_task(
                task_id="2",
                content="Task 2",
                due=make_due(
                    due_date=yesterday, due_string="every week", is_recurring=True
                ),
            ),
        ]

        mock_api = MagicMock()
        cache_data = {"every day": 1, "every week": 7}

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=tasks,
            ),
            _patch_cache_with(cache_data),
            patch(
                "todoist.recipes.complete_overdue_recurring._probe_next_due_date_with_retry"
            ) as mock_probe,
        ):
            args = argparse.Namespace(execute=False, clear_cache=False)
            run(args, api=mock_api)

        mock_probe.assert_not_called()
        output = capsys.readouterr().out
        assert "found in cache" in output.lower()

    def test_cache_miss_probes_and_saves(self, capsys):
        """When cache is empty, probing occurs and results are saved."""
        from todoist.recipes.complete_overdue_recurring import run

        yesterday = date.today() - timedelta(days=1)
        t1 = make_task(
            task_id="1",
            content="Daily task",
            due=make_due(due_date=yesterday, due_string="every day", is_recurring=True),
        )

        mock_api = MagicMock()
        mock_save = MagicMock()

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[t1],
            ),
            patch(
                "todoist.recipes.complete_overdue_recurring.load_cache", return_value={}
            ),
            patch("todoist.recipes.complete_overdue_recurring.save_cache", mock_save),
            patch(
                "todoist.recipes.complete_overdue_recurring._probe_next_due_date_with_retry",
                return_value=1,
            ),
        ):
            args = argparse.Namespace(execute=False, clear_cache=False)
            run(args, api=mock_api)

        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert saved_data["every day"] == 1

    def test_clear_cache_flag(self, capsys):
        """--clear-cache should reset the cache before running."""
        from todoist.recipes.complete_overdue_recurring import run

        mock_api = MagicMock()
        mock_save = MagicMock()

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=[],
            ),
            patch(
                "todoist.recipes.complete_overdue_recurring.load_cache", return_value={}
            ),
            patch("todoist.recipes.complete_overdue_recurring.save_cache", mock_save),
        ):
            args = argparse.Namespace(execute=False, clear_cache=True)
            run(args, api=mock_api)

        # save_cache({}) should be called for the clear
        mock_save.assert_any_call({})
        output = capsys.readouterr().out
        assert "cache cleared" in output.lower()

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

        with (
            patch(
                "todoist.recipes.complete_overdue_recurring.get_overdue_recurring_tasks",
                return_value=tasks,
            ),
            patch(
                "todoist.recipes.complete_overdue_recurring.load_cache", return_value={}
            ),
            patch("todoist.recipes.complete_overdue_recurring.save_cache"),
            patch(
                "todoist.recipes.complete_overdue_recurring._probe_next_due_date_with_retry",
                return_value=1,
            ) as mock_probe,
        ):
            args = argparse.Namespace(execute=False, clear_cache=False)
            run(args, api=mock_api)

        # Should only be called once despite 3 tasks with same due.string
        mock_probe.assert_called_once_with(mock_api, "every day")
