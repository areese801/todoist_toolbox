"""Tests for todoist.config module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from todoist.config import get_config


class TestGetConfig:
    """Tests for get_config()."""

    def test_loads_config_from_file(self, tmp_path):
        """get_config should load and return the JSON config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "work_label": "TestLabel",
            "project_color": "red",
            "no_robots_label": "_skip",
            "timezone": "UTC",
            "friday_cutoff_hour": 17,
        }))

        with patch("todoist.config.CONFIG_PATH", config_file):
            cfg = get_config()

        assert cfg["work_label"] == "TestLabel"
        assert cfg["project_color"] == "red"
        assert cfg["no_robots_label"] == "_skip"
        assert cfg["timezone"] == "UTC"
        assert cfg["friday_cutoff_hour"] == 17

    def test_missing_file_raises(self):
        """get_config should raise FileNotFoundError if config.json is missing."""
        with (
            patch("todoist.config.CONFIG_PATH", Path("/nonexistent/config.json")),
            pytest.raises(FileNotFoundError),
        ):
            get_config()

    def test_missing_key_raises(self, tmp_path):
        """get_config should raise KeyError if a required key is missing."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"work_label": "Work"}))

        with (
            patch("todoist.config.CONFIG_PATH", config_file),
            pytest.raises(KeyError),
        ):
            get_config()
