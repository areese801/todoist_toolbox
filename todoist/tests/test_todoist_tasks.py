"""Tests for todoist.todoist_tasks library functions."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime, timedelta

from todoist.tests.helpers import make_task, make_due


class TestGetApiToken:
    """Tests for _get_api_token()."""

    def test_returns_literal_value(self):
        """When env var is a plain string (not a file path), return it directly."""
        from todoist.todoist_tasks import _get_api_token

        with (
            patch("todoist.todoist_tasks.load_dotenv"),
            patch.dict(os.environ, {"TODOIST_API_TOKEN": "abc123token"}),
        ):
            result = _get_api_token()

        assert result == "abc123token"

    def test_reads_from_file(self):
        """When env var points to an existing file, read the token from that file."""
        from todoist.todoist_tasks import _get_api_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("secret-token-from-file")
            f.flush()
            token_path = f.name

        try:
            with (
                patch("todoist.todoist_tasks.load_dotenv"),
                patch.dict(os.environ, {"TODOIST_API_TOKEN": token_path}),
            ):
                result = _get_api_token()

            assert result == "secret-token-from-file"
        finally:
            os.unlink(token_path)

    def test_strips_trailing_newlines_from_file(self):
        """Token file with trailing newlines should have them stripped."""
        from todoist.todoist_tasks import _get_api_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("my-token\n\n\n")
            f.flush()
            token_path = f.name

        try:
            with (
                patch("todoist.todoist_tasks.load_dotenv"),
                patch.dict(os.environ, {"TODOIST_API_TOKEN": token_path}),
            ):
                result = _get_api_token()

            assert result == "my-token"
        finally:
            os.unlink(token_path)

    def test_raises_when_empty(self):
        """When env var is empty or unset, raise ValueError."""
        from todoist.todoist_tasks import _get_api_token

        with (
            patch("todoist.todoist_tasks.load_dotenv"),
            patch.dict(os.environ, {"TODOIST_API_TOKEN": ""}, clear=False),
        ):
            with pytest.raises(ValueError, match="Failed to resolve Todoist API token"):
                _get_api_token()

    def test_raises_when_unset(self):
        """When env var is completely unset, raise ValueError."""
        from todoist.todoist_tasks import _get_api_token

        env_copy = os.environ.copy()
        env_copy.pop("TODOIST_API_TOKEN", None)

        with (
            patch("todoist.todoist_tasks.load_dotenv"),
            patch.dict(os.environ, env_copy, clear=True),
        ):
            with pytest.raises(ValueError, match="Failed to resolve Todoist API token"):
                _get_api_token()


class TestGetActiveTasks:
    """Tests for get_active_tasks()."""

    def test_get_active_tasks_with_injected_api(self):
        """When an api instance is passed, it should use it instead of creating one."""
        from todoist.todoist_tasks import get_active_tasks

        mock_api = MagicMock()
        task1 = make_task(task_id="1", content="Task 1")
        task2 = make_task(task_id="2", content="Task 2")
        mock_api.get_tasks.return_value = iter([[task1, task2]])

        result = get_active_tasks(api=mock_api)

        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"
        mock_api.get_tasks.assert_called_once()

    def test_get_active_tasks_without_api_creates_one(self):
        """When no api is passed, it should create one internally (backward compat)."""
        from todoist.todoist_tasks import get_active_tasks

        mock_task = make_task(task_id="99", content="Solo task")
        mock_api_instance = MagicMock()
        mock_api_instance.get_tasks.return_value = iter([[mock_task]])

        with (
            patch("todoist.todoist_tasks._get_api_token", return_value="fake-token"),
            patch("todoist.todoist_tasks.TodoistAPI", return_value=mock_api_instance),
        ):
            result = get_active_tasks()

        assert len(result) == 1
        assert result[0].id == "99"


class TestGetOverdueRecurringTasks:
    """Tests for get_overdue_recurring_tasks()."""

    def test_filters_to_overdue_recurring_only(self):
        """Should return only tasks that are both overdue and recurring."""
        from todoist.todoist_tasks import get_overdue_recurring_tasks

        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        t1 = make_task(
            task_id="1",
            content="Overdue recurring",
            due=make_due(due_date=yesterday, is_recurring=True),
        )
        t2 = make_task(
            task_id="2",
            content="Overdue one-time",
            due=make_due(due_date=yesterday, is_recurring=False),
        )
        t3 = make_task(
            task_id="3",
            content="Future recurring",
            due=make_due(due_date=tomorrow, is_recurring=True),
        )
        t4 = make_task(task_id="4", content="No due", _no_due=True)

        mock_api = MagicMock()
        mock_api.get_tasks.return_value = iter([[t1, t2, t3, t4]])

        result = get_overdue_recurring_tasks(api=mock_api)

        assert len(result) == 1
        assert result[0].id == "1"


class TestGetOverdueNonRecurringTasks:
    """Tests for get_overdue_non_recurring_tasks()."""

    def test_filters_to_overdue_non_recurring_only(self):
        """Should return only tasks that are both overdue and non-recurring."""
        from todoist.todoist_tasks import get_overdue_non_recurring_tasks

        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        t1 = make_task(
            task_id="1",
            content="Overdue recurring",
            due=make_due(due_date=yesterday, is_recurring=True),
        )
        t2 = make_task(
            task_id="2",
            content="Overdue non-recurring",
            due=make_due(due_date=yesterday, is_recurring=False),
        )
        t3 = make_task(
            task_id="3",
            content="Future non-recurring",
            due=make_due(due_date=tomorrow, is_recurring=False),
        )
        t4 = make_task(task_id="4", content="No due", _no_due=True)

        mock_api = MagicMock()
        mock_api.get_tasks.return_value = iter([[t1, t2, t3, t4]])

        result = get_overdue_non_recurring_tasks(api=mock_api)

        assert len(result) == 1
        assert result[0].id == "2"


class TestProbeNextDueDate:
    """Tests for _probe_next_due_date()."""

    def test_daily_task_returns_1_day_interval(self):
        """A task with 'every day' should return an interval of 1."""
        from todoist.todoist_tasks import _probe_next_due_date

        mock_api = MagicMock()

        # add_task returns a temp task with initial due date of today
        today = date.today()
        temp_task = make_task(
            task_id="tmp-1",
            content="__probe__",
            due=make_due(due_date=today),
        )
        mock_api.add_task.return_value = temp_task

        # complete_task succeeds
        mock_api.complete_task.return_value = True

        # get_task returns the task with due date advanced by 1 day
        tomorrow = today + timedelta(days=1)
        advanced_task = make_task(
            task_id="tmp-1",
            content="__probe__",
            due=make_due(due_date=tomorrow),
        )
        mock_api.get_task.return_value = advanced_task

        # delete_task succeeds
        mock_api.delete_task.return_value = True

        result = _probe_next_due_date(mock_api, "every day")

        assert result == 1
        mock_api.add_task.assert_called_once_with(
            content="__probe__", due_string="every day"
        )
        mock_api.complete_task.assert_called_once_with("tmp-1")
        mock_api.get_task.assert_called_once_with("tmp-1")
        mock_api.delete_task.assert_called_once_with("tmp-1")

    def test_weekly_task_returns_7_day_interval(self):
        """A task with 'every week' should return an interval of 7."""
        from todoist.todoist_tasks import _probe_next_due_date

        mock_api = MagicMock()

        today = date.today()
        temp_task = make_task(
            task_id="tmp-2",
            content="__probe__",
            due=make_due(due_date=today),
        )
        mock_api.add_task.return_value = temp_task
        mock_api.complete_task.return_value = True

        next_week = today + timedelta(days=7)
        advanced_task = make_task(
            task_id="tmp-2",
            content="__probe__",
            due=make_due(due_date=next_week),
        )
        mock_api.get_task.return_value = advanced_task
        mock_api.delete_task.return_value = True

        result = _probe_next_due_date(mock_api, "every week")

        assert result == 7

    def test_cleanup_on_failure(self):
        """If complete_task fails, the temp task should still be deleted."""
        from todoist.todoist_tasks import _probe_next_due_date

        mock_api = MagicMock()

        temp_task = make_task(
            task_id="tmp-3",
            content="__probe__",
            due=make_due(due_date=date.today()),
        )
        mock_api.add_task.return_value = temp_task
        mock_api.complete_task.side_effect = Exception("API error")
        mock_api.delete_task.return_value = True

        result = _probe_next_due_date(mock_api, "every day")

        assert result is None
        mock_api.delete_task.assert_called_once_with("tmp-3")

    def test_returns_none_when_no_due_after_complete(self):
        """If the advanced task has no due date, return None."""
        from todoist.todoist_tasks import _probe_next_due_date

        mock_api = MagicMock()

        temp_task = make_task(
            task_id="tmp-4",
            content="__probe__",
            due=make_due(due_date=date.today()),
        )
        mock_api.add_task.return_value = temp_task
        mock_api.complete_task.return_value = True

        advanced_task = make_task(task_id="tmp-4", content="__probe__", _no_due=True)
        mock_api.get_task.return_value = advanced_task
        mock_api.delete_task.return_value = True

        result = _probe_next_due_date(mock_api, "every day")

        assert result is None

    def test_handles_datetime_due_date(self):
        """If due dates are datetimes (not dates), normalize and compute interval."""
        from todoist.todoist_tasks import _probe_next_due_date

        mock_api = MagicMock()

        today = date.today()
        today_dt = datetime.combine(today, datetime.min.time())
        temp_task = make_task(
            task_id="tmp-5",
            content="__probe__",
            due=make_due(due_date=today_dt),
        )
        mock_api.add_task.return_value = temp_task
        mock_api.complete_task.return_value = True

        # Return a datetime instead of a date
        tomorrow = today + timedelta(days=1)
        tomorrow_dt = datetime.combine(tomorrow, datetime.min.time())
        advanced_task = make_task(
            task_id="tmp-5",
            content="__probe__",
            due=make_due(due_date=tomorrow_dt),
        )
        mock_api.get_task.return_value = advanced_task
        mock_api.delete_task.return_value = True

        result = _probe_next_due_date(mock_api, "every day")

        assert result == 1


class TestResolveRecurrenceIntervalWithRetry:
    """Tests for _probe_next_due_date_with_retry()."""

    def _make_429_error(self, retry_after=2):
        """Create a mock HTTPError with 429 status and Retry-After header."""
        from requests.exceptions import HTTPError

        response = MagicMock()
        response.status_code = 429
        response.headers = {"Retry-After": str(retry_after)}
        error = HTTPError(response=response)
        return error

    def _make_500_error(self):
        """Create a mock HTTPError with 500 status."""
        from requests.exceptions import HTTPError

        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        error = HTTPError(response=response)
        return error

    def test_retry_on_429_succeeds_after_retry(self):
        """First call hits 429, second call succeeds."""
        from todoist.todoist_tasks import _probe_next_due_date_with_retry

        mock_api = MagicMock()
        expected_date = date.today() + timedelta(days=3)

        with (
            patch("todoist.todoist_tasks._probe_next_due_date") as mock_resolve,
            patch("todoist.todoist_tasks.time.sleep") as mock_sleep,
        ):
            mock_resolve.side_effect = [self._make_429_error(), expected_date]

            result = _probe_next_due_date_with_retry(mock_api, "every 3 days")

        assert result == expected_date
        assert mock_resolve.call_count == 2
        mock_sleep.assert_called_once_with(2)

    def test_retry_exhausted_returns_none(self):
        """When all attempts hit 429, return None."""
        from todoist.todoist_tasks import _probe_next_due_date_with_retry

        mock_api = MagicMock()

        with (
            patch("todoist.todoist_tasks._probe_next_due_date") as mock_resolve,
            patch("todoist.todoist_tasks.time.sleep"),
        ):
            mock_resolve.side_effect = [
                self._make_429_error(),
                self._make_429_error(),
                self._make_429_error(),
            ]

            result = _probe_next_due_date_with_retry(
                mock_api, "every day", max_retries=3
            )

        assert result is None
        assert mock_resolve.call_count == 3

    def test_non_429_error_propagates(self):
        """A 500 error should re-raise immediately, not retry."""
        from todoist.todoist_tasks import _probe_next_due_date_with_retry
        from requests.exceptions import HTTPError

        mock_api = MagicMock()

        with (
            patch("todoist.todoist_tasks._probe_next_due_date") as mock_resolve,
            patch("todoist.todoist_tasks.time.sleep") as mock_sleep,
        ):
            mock_resolve.side_effect = self._make_500_error()

            with pytest.raises(HTTPError):
                _probe_next_due_date_with_retry(mock_api, "every day")

        mock_sleep.assert_not_called()


class TestGetProjects:
    """Tests for get_projects()."""

    def test_get_projects_returns_list(self):
        """get_projects should return a flat list of projects."""
        from todoist.todoist_tasks import get_projects

        mock_api = MagicMock()
        p1 = MagicMock()
        p1.id = "proj_1"
        p1.color = "sky_blue"
        p2 = MagicMock()
        p2.id = "proj_2"
        p2.color = "red"

        mock_api.get_projects.return_value = [p1, p2]

        result = get_projects(api=mock_api)

        assert len(result) == 2
        assert result[0].id == "proj_1"
        mock_api.get_projects.assert_called_once()

    def test_get_projects_with_no_api_creates_one(self):
        """When no api is passed, get_projects should create one from the token."""
        from todoist.todoist_tasks import get_projects

        with (
            patch("todoist.todoist_tasks._get_api_token", return_value="fake-token"),
            patch("todoist.todoist_tasks.TodoistAPI") as MockAPI,
        ):
            mock_instance = MagicMock()
            mock_instance.get_projects.return_value = []
            MockAPI.return_value = mock_instance

            result = get_projects()

            MockAPI.assert_called_once_with("fake-token")
            assert result == []
