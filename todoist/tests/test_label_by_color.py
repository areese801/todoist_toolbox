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

        with patch.dict(os.environ, {"TODOIST_LABEL_COLOR": "sky_blue", "TODOIST_LABEL_NAME": "work"}):
            color, label = _resolve_config(args)

        assert color == "red"
        assert label == "personal"

    def test_falls_back_to_env_vars(self):
        """When args are None, should use env vars."""
        from todoist.recipes.label_by_color import _resolve_config

        args = MagicMock()
        args.color = None
        args.label = None

        with patch.dict(os.environ, {"TODOIST_LABEL_COLOR": "sky_blue", "TODOIST_LABEL_NAME": "work"}):
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

        with patch.dict(os.environ, {}, clear=True), \
             pytest.raises(SystemExit):
            _resolve_config(args)

    def test_error_when_label_missing(self):
        """Should raise SystemExit when label is not provided anywhere."""
        from todoist.recipes.label_by_color import _resolve_config
        import pytest

        args = MagicMock()
        args.color = "sky_blue"
        args.label = None

        with patch.dict(os.environ, {}, clear=True), \
             pytest.raises(SystemExit):
            _resolve_config(args)
