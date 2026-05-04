"""
Centralized configuration for the todoist toolbox.

Loads non-sensitive settings from config.json (committed to version control).
Sensitive values (API tokens) remain in .env files.
"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

_REQUIRED_KEYS = [
    "work_label",
    "project_color",
    "no_robots_label",
    "no_due_date_label",
    "timezone",
    "friday_cutoff_hour",
]


def get_config() -> dict:
    """
    Load and validate the config from config.json.

    Returns:
        Dict with all config values.
    Raises:
        FileNotFoundError: If config.json does not exist.
        KeyError: If any required key is missing.
    """
    config = json.loads(CONFIG_PATH.read_text())

    missing = [k for k in _REQUIRED_KEYS if k not in config]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")

    return config
