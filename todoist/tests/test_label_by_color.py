"""Tests for the label-by-color recipe."""

import os
from unittest.mock import patch, MagicMock

from todoist.tests.helpers import make_task, make_due


def _make_project(project_id="proj_1", color="sky_blue", name="Work"):
    """Create a mock Project object."""
    proj = MagicMock()
    proj.id = project_id
    proj.color = color
    proj.name = name
    return proj


class TestLabelByColorConfigResolution:
    """Tests for resolving --color and --label from args or env vars."""

    def test_args_take_precedence_over_env(self, capsys):
        """CLI args should override env vars."""
        from todoist.recipes.label_by_color import _resolve_config

        args = MagicMock()
        args.color = "red"
        args.label = "personal"

        with patch.dict(
            os.environ,
            {"TODOIST_LABEL_COLOR": "sky_blue", "TODOIST_LABEL_NAME": "work"},
        ):
            color, label = _resolve_config(args)

        assert color == "red"
        assert label == "personal"

    def test_falls_back_to_env_vars(self):
        """When args are None, should use env vars."""
        from todoist.recipes.label_by_color import _resolve_config

        args = MagicMock()
        args.color = None
        args.label = None

        with patch.dict(
            os.environ,
            {"TODOIST_LABEL_COLOR": "sky_blue", "TODOIST_LABEL_NAME": "work"},
        ):
            color, label = _resolve_config(args)

        assert color == "sky_blue"
        assert label == "work"

    def test_error_when_color_missing(self):
        """Should raise SystemExit when color is not provided anywhere."""
        from todoist.recipes.label_by_color import _resolve_config
        import pytest

        args = MagicMock()
        args.color = None
        args.label = "work"

        empty_config = {"project_color": None, "work_label": None}
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("todoist.recipes.label_by_color.get_config", return_value=empty_config),
            pytest.raises(SystemExit),
        ):
            _resolve_config(args)

    def test_error_when_label_missing(self):
        """Should raise SystemExit when label is not provided anywhere."""
        from todoist.recipes.label_by_color import _resolve_config
        import pytest

        args = MagicMock()
        args.color = "sky_blue"
        args.label = None

        empty_config = {"project_color": None, "work_label": None}
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("todoist.recipes.label_by_color.get_config", return_value=empty_config),
            pytest.raises(SystemExit),
        ):
            _resolve_config(args)


class TestLabelByColorDryRun:
    """Tests for dry-run mode of label-by-color."""

    def test_dry_run_prints_qualifying_tasks(self, capsys):
        """Dry-run should print tasks that would be labeled."""
        from todoist.recipes.label_by_color import run

        proj = _make_project(project_id="proj_1", color="sky_blue", name="Work")
        t1 = make_task(task_id="1", content="Review PR", project_id="proj_1", labels=[])
        t2 = make_task(
            task_id="2", content="Deploy app", project_id="proj_1", labels=["urgent"]
        )

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch("todoist.recipes.label_by_color.get_projects", return_value=[proj]),
            patch(
                "todoist.recipes.label_by_color.get_active_tasks", return_value=[t1, t2]
            ),
        ):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "DRY RUN" in output
        assert "Review PR" in output
        assert "Deploy app" in output
        mock_api.update_task.assert_not_called()

    def test_dry_run_skips_already_labeled_tasks(self, capsys):
        """Tasks that already have the label should be excluded."""
        from todoist.recipes.label_by_color import run

        proj = _make_project(project_id="proj_1", color="sky_blue", name="Work")
        t1 = make_task(
            task_id="1", content="Already labeled", project_id="proj_1", labels=["work"]
        )
        t2 = make_task(
            task_id="2", content="Needs label", project_id="proj_1", labels=[]
        )

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch("todoist.recipes.label_by_color.get_projects", return_value=[proj]),
            patch(
                "todoist.recipes.label_by_color.get_active_tasks", return_value=[t1, t2]
            ),
        ):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "Needs label" in output
        assert "Already labeled" not in output

    def test_no_matching_projects(self, capsys):
        """When no projects match the color, print message and return."""
        from todoist.recipes.label_by_color import run

        proj = _make_project(project_id="proj_1", color="red", name="Personal")

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch("todoist.recipes.label_by_color.get_projects", return_value=[proj]),
            patch("todoist.recipes.label_by_color.get_active_tasks", return_value=[]),
        ):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "No projects found with color" in output

    def test_no_tasks_need_labeling(self, capsys):
        """When all tasks already have the label, print message and return."""
        from todoist.recipes.label_by_color import run

        proj = _make_project(project_id="proj_1", color="sky_blue", name="Work")
        t1 = make_task(
            task_id="1", content="Done", project_id="proj_1", labels=["work"]
        )

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch("todoist.recipes.label_by_color.get_projects", return_value=[proj]),
            patch("todoist.recipes.label_by_color.get_active_tasks", return_value=[t1]),
        ):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert (
            "All tasks already labeled" in output or "No tasks need labeling" in output
        )

    def test_tasks_in_non_matching_projects_excluded(self, capsys):
        """Tasks in projects with a different color should not be included."""
        from todoist.recipes.label_by_color import run

        proj_match = _make_project(project_id="proj_1", color="sky_blue", name="Work")
        proj_other = _make_project(project_id="proj_2", color="red", name="Personal")
        t1 = make_task(task_id="1", content="Work task", project_id="proj_1", labels=[])
        t2 = make_task(
            task_id="2", content="Personal task", project_id="proj_2", labels=[]
        )

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = False
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch(
                "todoist.recipes.label_by_color.get_projects",
                return_value=[proj_match, proj_other],
            ),
            patch(
                "todoist.recipes.label_by_color.get_active_tasks", return_value=[t1, t2]
            ),
        ):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "Work task" in output
        assert "Personal task" not in output


class TestLabelByColorExecute:
    """Tests for execute mode of label-by-color."""

    def test_execute_calls_update_task_with_labels(self, capsys):
        """Execute should call api.update_task with existing + new label."""
        from todoist.recipes.label_by_color import run

        proj = _make_project(project_id="proj_1", color="sky_blue", name="Work")
        t1 = make_task(
            task_id="1", content="Task A", project_id="proj_1", labels=["urgent"]
        )
        t2 = make_task(task_id="2", content="Task B", project_id="proj_1", labels=[])

        mock_api = MagicMock()
        args = MagicMock()
        args.execute = True
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch("todoist.recipes.label_by_color.get_projects", return_value=[proj]),
            patch(
                "todoist.recipes.label_by_color.get_active_tasks", return_value=[t1, t2]
            ),
        ):
            run(args, api=mock_api)

        assert mock_api.update_task.call_count == 2
        # Task A should keep "urgent" and gain "work"
        mock_api.update_task.assert_any_call(task_id="1", labels=["urgent", "work"])
        # Task B should gain "work"
        mock_api.update_task.assert_any_call(task_id="2", labels=["work"])

        output = capsys.readouterr().out
        assert "Labeled 2 of 2" in output

    def test_execute_continues_on_individual_failure(self, capsys):
        """If one task fails, the rest should still be attempted."""
        from todoist.recipes.label_by_color import run

        proj = _make_project(project_id="proj_1", color="sky_blue", name="Work")
        t1 = make_task(task_id="1", content="Fails", project_id="proj_1", labels=[])
        t2 = make_task(task_id="2", content="Succeeds", project_id="proj_1", labels=[])

        mock_api = MagicMock()
        mock_api.update_task.side_effect = [Exception("API error"), None]
        args = MagicMock()
        args.execute = True
        args.color = "sky_blue"
        args.label = "work"

        with (
            patch("todoist.recipes.label_by_color.get_projects", return_value=[proj]),
            patch(
                "todoist.recipes.label_by_color.get_active_tasks", return_value=[t1, t2]
            ),
        ):
            run(args, api=mock_api)

        output = capsys.readouterr().out
        assert "FAILED:" in output and "Fails" in output
        assert "Labeled:" in output and "Succeeds" in output
        assert "Labeled 1 of 2" in output
        assert "1 failure(s)" in output
