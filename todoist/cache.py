"""
Persistent JSON-file-backed cache for recurrence interval lookups.

Cache location follows XDG convention: ~/.cache/todoist-toolbox/interval_cache.json

Values are integers representing the recurrence interval in days for a given
recurrence pattern (e.g. "every day" -> 1, "every week" -> 7). Null values
from failed probes are treated as cache misses and retried on the next run.
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

    Returns the cached interval in days, or MISS if the key is absent or
    the cached value is None (a previously failed probe that should be retried).
    """
    value = cache.get(due_string, MISS)
    if value is None:
        return MISS
    return value
