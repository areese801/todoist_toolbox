"""Tests for todoist.mcp_server MCP tool functions."""

from unittest.mock import MagicMock, patch
from datetime import date

import pytest

from todoist.tests.helpers import make_task, make_due


def _make_project(project_id="proj_1", name="Work", color="sky_blue",
                  is_favorite=False, url="https://todoist.com/project/1"):
    """Create a mock Todoist Project object."""
    p = MagicMock()
    p.id = project_id
    p.name = name
    p.color = color
    p.is_favorite = is_favorite
    p.url = url
    return p


# --------------------------------------------------------------------------- #
# _task_to_dict
# --------------------------------------------------------------------------- #

class TestTaskToDict:
    """Tests for the _task_to_dict helper."""

    def test_basic_fields(self):
        from todoist.mcp_server import _task_to_dict

        task = make_task(
            task_id="42",
            content="Buy milk",
            description="2%",
            priority=1,
            labels=["Errands"],
            is_completed=False,
            created_at="2026-01-01T00:00:00Z",
            project_id="proj_1",
            _no_due=True,
        )

        result = _task_to_dict(task)

        assert result["id"] == "42"
        assert result["content"] == "Buy milk"
        assert result["description"] == "2%"
        assert result["priority"] == 1
        assert result["labels"] == ["Errands"]
        assert result["is_completed"] is False
        assert result["url"] == "https://app.todoist.com/app/task/42"
        assert result["due"] is None

    def test_with_project_map(self):
        from todoist.mcp_server import _task_to_dict

        task = make_task(task_id="1", content="Task", project_id="proj_1", _no_due=True)
        project_map = {"proj_1": "Work"}

        result = _task_to_dict(task, project_map)

        assert result["project_name"] == "Work"
        assert result["project_id"] == "proj_1"

    def test_unknown_project_id(self):
        from todoist.mcp_server import _task_to_dict

        task = make_task(task_id="1", content="Task", project_id="missing", _no_due=True)
        project_map = {"proj_1": "Work"}

        result = _task_to_dict(task, project_map)

        assert result["project_name"] == "Unknown"

    def test_with_due_date(self):
        from todoist.mcp_server import _task_to_dict

        due = make_due(due_date=date(2026, 4, 10), due_string="tomorrow", is_recurring=False)
        task = make_task(task_id="1", content="Task", due=due, project_id="proj_1")

        result = _task_to_dict(task)

        assert result["due"]["date"] == str(date(2026, 4, 10))
        assert result["due"]["is_recurring"] is False
        assert result["due"]["string"] == "tomorrow"


# --------------------------------------------------------------------------- #
# _project_to_dict
# --------------------------------------------------------------------------- #

class TestProjectToDict:
    """Tests for the _project_to_dict helper."""

    def test_converts_project(self):
        from todoist.mcp_server import _project_to_dict

        project = _make_project(project_id="p1", name="Personal", color="red",
                                is_favorite=True, url="https://todoist.com/p1")

        result = _project_to_dict(project)

        assert result == {
            "id": "p1",
            "name": "Personal",
            "color": "red",
            "is_favorite": True,
            "url": "https://todoist.com/p1",
        }


# --------------------------------------------------------------------------- #
# get_tasks (MCP tool)
# --------------------------------------------------------------------------- #

class TestGetTasks:
    """Tests for the get_tasks MCP tool."""

    def _patch_api_and_projects(self, tasks, projects):
        """Return context managers that patch _get_api and _get_projects_from_api."""
        mock_api = MagicMock()
        return (
            patch("todoist.mcp_server._get_api", return_value=mock_api),
            patch("todoist.mcp_server._get_projects_from_api", return_value=projects),
            patch("todoist.mcp_server.get_active_tasks", return_value=tasks),
            mock_api,
        )

    def test_returns_all_active_tasks(self):
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        task = make_task(
            task_id="1", content="Do stuff", project_id="p1",
            description="", priority=1, labels=[], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )

        api_patch, proj_patch, tasks_patch, _ = self._patch_api_and_projects([task], [proj])

        with api_patch, proj_patch, tasks_patch:
            result = get_tasks()

        assert len(result) == 1
        assert result[0]["content"] == "Do stuff"
        assert result[0]["project_name"] == "Work"

    def test_filter_by_project_name(self):
        from todoist.mcp_server import get_tasks

        proj_work = _make_project(project_id="p1", name="Work")
        proj_personal = _make_project(project_id="p2", name="Personal")
        task1 = make_task(
            task_id="1", content="Work task", project_id="p1",
            description="", priority=1, labels=[], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )
        task2 = make_task(
            task_id="2", content="Personal task", project_id="p2",
            description="", priority=1, labels=[], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )

        api_patch, proj_patch, tasks_patch, _ = self._patch_api_and_projects(
            [task1, task2], [proj_work, proj_personal]
        )

        with api_patch, proj_patch, tasks_patch:
            result = get_tasks(project_name="personal")

        assert len(result) == 1
        assert result[0]["content"] == "Personal task"

    def test_filter_by_label(self):
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        task1 = make_task(
            task_id="1", content="Labeled", project_id="p1",
            description="", priority=1, labels=["Work"], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )
        task2 = make_task(
            task_id="2", content="Not labeled", project_id="p1",
            description="", priority=1, labels=[], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )

        api_patch, proj_patch, tasks_patch, _ = self._patch_api_and_projects(
            [task1, task2], [proj]
        )

        with api_patch, proj_patch, tasks_patch:
            result = get_tasks(label="Work")

        assert len(result) == 1
        assert result[0]["content"] == "Labeled"

    def test_excludes_completed_by_default(self):
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        task = make_task(
            task_id="1", content="Done", project_id="p1",
            description="", priority=1, labels=[], is_completed=True,
            created_at="2026-01-01", _no_due=True,
        )

        api_patch, proj_patch, tasks_patch, _ = self._patch_api_and_projects([task], [proj])

        with api_patch, proj_patch, tasks_patch:
            result = get_tasks()

        assert len(result) == 0

    def test_includes_completed_when_requested(self):
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        task = make_task(
            task_id="1", content="Done", project_id="p1",
            description="", priority=1, labels=[], is_completed=True,
            created_at="2026-01-01", _no_due=True,
        )

        api_patch, proj_patch, tasks_patch, _ = self._patch_api_and_projects([task], [proj])

        with api_patch, proj_patch, tasks_patch:
            result = get_tasks(include_completed=True)

        assert len(result) == 1
        assert result[0]["content"] == "Done"

    def test_uses_todoist_filter(self):
        """When a filter string is provided, it should use api.filter_tasks(query=...)."""
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        task = make_task(
            task_id="1", content="Today task", project_id="p1",
            description="", priority=1, labels=[], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )

        mock_api = MagicMock()
        mock_api.filter_tasks.return_value = [[task]]  # paginator returns pages

        with (
            patch("todoist.mcp_server._get_api", return_value=mock_api),
            patch("todoist.mcp_server._get_projects_from_api", return_value=[proj]),
        ):
            result = get_tasks(filter="today")

        mock_api.filter_tasks.assert_called_once_with(query="today")
        assert len(result) == 1

    def test_filter_error_returns_error_dict(self):
        """When the Todoist filter API fails, return an error dict instead of raising."""
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        mock_api = MagicMock()
        mock_api.filter_tasks.side_effect = Exception("bad filter")

        with (
            patch("todoist.mcp_server._get_api", return_value=mock_api),
            patch("todoist.mcp_server._get_projects_from_api", return_value=[proj]),
        ):
            result = get_tasks(filter="invalid!!")

        assert len(result) == 1
        assert "error" in result[0]
        assert "bad filter" in result[0]["error"]

    def test_calls_get_projects_from_api_not_mcp_tool(self):
        """Regression: get_tasks must call _get_projects_from_api (todoist_tasks),
        not the MCP tool get_projects which doesn't accept api=."""
        from todoist.mcp_server import get_tasks

        proj = _make_project(project_id="p1", name="Work")
        task = make_task(
            task_id="1", content="Task", project_id="p1",
            description="", priority=1, labels=[], is_completed=False,
            created_at="2026-01-01", _no_due=True,
        )

        mock_api = MagicMock()

        with (
            patch("todoist.mcp_server._get_api", return_value=mock_api),
            patch("todoist.mcp_server._get_projects_from_api", return_value=[proj]) as mock_gp,
            patch("todoist.mcp_server.get_active_tasks", return_value=[task]),
        ):
            get_tasks()

        mock_gp.assert_called_once_with(api=mock_api)


# --------------------------------------------------------------------------- #
# get_projects (MCP tool)
# --------------------------------------------------------------------------- #

class TestGetProjects:
    """Tests for the get_projects MCP tool."""

    def test_returns_project_dicts_from_list(self):
        from todoist.mcp_server import get_projects

        proj = _make_project(project_id="p1", name="Work", color="sky_blue")
        mock_api = MagicMock()
        mock_api.get_projects.return_value = [proj]

        with patch("todoist.mcp_server._get_api", return_value=mock_api):
            result = get_projects()

        assert len(result) == 1
        assert result[0]["name"] == "Work"
        assert result[0]["color"] == "sky_blue"

    def test_handles_paginated_response(self):
        from todoist.mcp_server import get_projects

        p1 = _make_project(project_id="p1", name="Work")
        p2 = _make_project(project_id="p2", name="Personal")

        mock_api = MagicMock()
        # Simulate paginator: not a list, but an iterable of pages
        paginator = MagicMock()
        paginator.__iter__ = MagicMock(return_value=iter([[p1], [p2]]))
        paginator.__class__ = type("Paginator", (), {})  # not a list
        mock_api.get_projects.return_value = paginator

        with patch("todoist.mcp_server._get_api", return_value=mock_api):
            result = get_projects()

        assert len(result) == 2
        assert result[0]["name"] == "Work"
        assert result[1]["name"] == "Personal"


# --------------------------------------------------------------------------- #
# get_task_summary (MCP tool)
# --------------------------------------------------------------------------- #

class TestGetTaskSummary:
    """Tests for the get_task_summary MCP tool."""

    def test_basic_summary(self):
        from todoist.mcp_server import get_task_summary

        proj = _make_project(project_id="p1", name="Work")

        overdue_task = make_task(
            task_id="1", content="Overdue",
            due=make_due(due_date=date(2026, 4, 1), is_recurring=False),
            project_id="p1", priority=4, is_completed=False,
        )
        today_task = make_task(
            task_id="2", content="Today",
            due=make_due(due_date=date.today(), is_recurring=False),
            project_id="p1", priority=1, is_completed=False,
        )
        no_due_task = make_task(
            task_id="3", content="Someday",
            project_id="p1", priority=1, is_completed=False,
            _no_due=True,
        )

        mock_api = MagicMock()
        mock_api.get_projects.return_value = [proj]

        with (
            patch("todoist.mcp_server._get_api", return_value=mock_api),
            patch("todoist.mcp_server.get_active_tasks",
                  return_value=[overdue_task, today_task, no_due_task]),
        ):
            result = get_task_summary()

        assert result["total_open_tasks"] == 3
        assert result["overdue_count"] == 1
        assert result["overdue_tasks"] == ["Overdue"]
        assert result["due_today_count"] == 1
        assert result["due_today_tasks"] == ["Today"]
        assert result["no_due_date_count"] == 1
        assert result["by_project"]["Work"] == 3
        assert result["by_priority"]["p1_urgent"] == 1  # priority 4
        assert result["by_priority"]["p4_normal"] == 2  # priority 1


# --------------------------------------------------------------------------- #
# get_config_info (MCP tool)
# --------------------------------------------------------------------------- #

class TestGetConfigInfo:
    """Tests for the get_config_info MCP tool."""

    def test_returns_config(self):
        from todoist.mcp_server import get_config_info

        fake_config = {"work_label": "Work", "project_color": "sky_blue"}

        with patch("todoist.mcp_server.get_config", return_value=fake_config):
            result = get_config_info()

        assert result == fake_config
