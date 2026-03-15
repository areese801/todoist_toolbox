"""Tests for the reschedule-overdue-nonrecurring recipe."""
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

from todoist.tests.helpers import make_task, make_due


class TestRescheduleOverdueDryRun:
    """Tests for dry-run mode of reschedule-overdue-nonrecurring."""

    def test_dry_run_prints_qualifying_tasks(self, capsys):
        """Dry-run should print qualifying tasks and not call update_task."""
        from todoist.recipes.reschedule_overdue_nonrecurring import run

        yesterday = date.today() - timedelta(days=1)
        t1 = make_task(task_id="1", content="Buy groceries",
                       due=make_due(due_date=yesterday, is_recurring=False))
        t2 = make_task(task_id="2", content="File taxes",
                       due=make_due(due_date=yesterday, is_recurring=False))

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False

        with patch("todoist.recipes.reschedule_overdue_nonrecurring.get_overdue_non_recurring_tasks",
                   return_value=[t1, t2]):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "DRY RUN" in output
        assert "Buy groceries" in output
        assert "File taxes" in output
        mock_api.update_task.assert_not_called()

    def test_dry_run_no_overdue_tasks(self, capsys):
        """When no overdue tasks exist, print a message and return."""
        from todoist.recipes.reschedule_overdue_nonrecurring import run

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False

        with patch("todoist.recipes.reschedule_overdue_nonrecurring.get_overdue_non_recurring_tasks",
                   return_value=[]):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "No overdue non-recurring tasks found." in output


class TestRescheduleOverdueExecute:
    """Tests for execute mode of reschedule-overdue-nonrecurring."""

    def test_execute_calls_update_task(self, capsys):
        """Execute should call api.update_task with due_string='today' per task."""
        from todoist.recipes.reschedule_overdue_nonrecurring import run

        yesterday = date.today() - timedelta(days=1)
        t1 = make_task(task_id="1", content="Buy groceries",
                       due=make_due(due_date=yesterday, is_recurring=False))
        t2 = make_task(task_id="2", content="File taxes",
                       due=make_due(due_date=yesterday, is_recurring=False))

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = True

        with patch("todoist.recipes.reschedule_overdue_nonrecurring.get_overdue_non_recurring_tasks",
                   return_value=[t1, t2]):
            run(args, api=mock_api)

        assert mock_api.update_task.call_count == 2
        mock_api.update_task.assert_any_call("1", due_string="today")
        mock_api.update_task.assert_any_call("2", due_string="today")

        output = capsys.readouterr().out
        assert "Rescheduled 2 of 2" in output

    def test_execute_continues_on_individual_failure(self, capsys):
        """If one task fails, the rest should still be attempted."""
        from todoist.recipes.reschedule_overdue_nonrecurring import run

        yesterday = date.today() - timedelta(days=1)
        t1 = make_task(task_id="1", content="Fails",
                       due=make_due(due_date=yesterday, is_recurring=False))
        t2 = make_task(task_id="2", content="Succeeds",
                       due=make_due(due_date=yesterday, is_recurring=False))

        mock_api = MagicMock()
        mock_api.update_task.side_effect = [Exception("API error"), None]
        args = MagicMock()
        args.execute = True

        with patch("todoist.recipes.reschedule_overdue_nonrecurring.get_overdue_non_recurring_tasks",
                   return_value=[t1, t2]):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "FAILED:" in output and "Fails" in output
        assert "Rescheduled:" in output and "Succeeds" in output
        assert "Rescheduled 1 of 2" in output
        assert "1 failure(s)" in output
