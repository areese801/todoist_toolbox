"""
Persistent JSON-file-backed cache for recurrence due-date lookups.

Cache location follows XDG convention: ~/.cache/todoist-toolbox/interval_cache.json

Values are ISO date strings (e.g. "2026-03-20") representing the next due date
for a given recurrence pattern, or null if the probe failed. Entries whose date
is in the past are treated as stale and returned as MISS.
"""
import json
from datetime import date
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "todoist-toolbox"
CACHE_FILE = CACHE_DIR / "interval_cache.json"

MISS = object()  # sentinel to distinguish "not cached" from "cached as None"


def load_cache() -> dict[str, str | None]:
    """
    Read the due-date cache from disk.

    Returns an empty dict if the file is missing or contains invalid JSON.
    """
    try:
        return json.loads(CACHE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict[str, str | None]) -> None:
    """
    Write the due-date cache to disk, creating parent directories as needed.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2) + "\n")


def get_cached_due_date(
    cache: dict[str, str | None], due_string: str
) -> str | None:
    """
    Look up a due_string in the cache.

    Returns the cached ISO date string (or None for failed probes), or MISS
    if the key is absent or the cached date is in the past (stale).
    """
    value = cache.get(due_string, MISS)
    if value is MISS:
        return MISS

    # None means a previous probe failed — still a valid cache hit
    if value is None:
        return None

    # If the cached date is in the past, treat as stale
    try:
        cached_date = date.fromisoformat(value)
    except (ValueError, TypeError):
        return MISS

    if cached_date < date.today():
        return MISS

    return value
