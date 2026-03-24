"""
Persistent JSON-file-backed cache for recurrence interval lookups.

Cache location follows XDG convention: ~/.cache/todoist-toolbox/interval_cache.json

Values are integers representing the recurrence interval in days for a given
recurrence pattern (e.g. "every day" -> 1, "every week" -> 7), or null if the
probe failed. Intervals are stable properties of a due string and do not expire.
"""

import json
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "interval_cache.json"

MISS = object()  # sentinel to distinguish "not cached" from "cached as None"


def load_cache() -> dict[str, int | None]:
    """
    Read the interval cache from disk.

    Returns an empty dict if the file is missing or contains invalid JSON.
    """
    try:
        return json.loads(CACHE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict[str, int | None]) -> None:
    """
    Write the interval cache to disk, creating parent directories as needed.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2) + "\n")


def get_cached_interval(cache: dict[str, int | None], due_string: str) -> int | None:
    """
    Look up a due_string in the cache.

    Returns the cached interval in days (or None for failed probes), or MISS
    if the key is absent.
    """
    value = cache.get(due_string, MISS)
    return value
