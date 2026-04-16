"""
Snooze engine for Todoist tasks.

Stores snooze metadata as a JSON comment on the Todoist task (source of truth).
The comment is prefixed with a marker so it can be identified programmatically.

Comment format:
    _snooze:{"original_due_date":"2026-04-16","original_due_string":"every day",
             "wake_time":"2026-04-16T14:00:00","is_recurring":true}

On snooze: writes the comment, reschedules the task to tomorrow.
On unsnooze: restores the original due date/string, deletes the snooze comment.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional

SNOOZE_PREFIX = "_snooze:"

# Preset durations for the snooze modal
SNOOZE_PRESETS = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "afternoon": None,  # Resolved dynamically to 13:00 today or tomorrow
    "evening": None,  # Resolved dynamically to 18:00 today or tomorrow
}


def resolve_preset_wake_time(preset: str, now: Optional[datetime] = None) -> datetime:
    """
    Resolve a snooze preset name to an absolute wake_time.

    Args:
        preset: One of the keys in SNOOZE_PRESETS, or a custom duration
                string like "45m" or "3h".
        now: Current time. Defaults to datetime.now().

    Returns:
        Absolute datetime when the task should wake up.

    Raises:
        ValueError: If the preset is unrecognized.
    """
    if now is None:
        now = datetime.now()

    if preset == "afternoon":
        target = now.replace(hour=13, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    if preset == "evening":
        target = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    delta = SNOOZE_PRESETS.get(preset)
    if delta is not None:
        return now + delta

    # Try parsing custom duration strings like "45m", "3h", "90m"
    match = re.match(r"^(\d+)\s*(m|h)$", preset.strip())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == "m":
            return now + timedelta(minutes=value)
        else:
            return now + timedelta(hours=value)

    raise ValueError(f"Unrecognized snooze preset: {preset!r}")


def build_snooze_comment(
    original_due_date: str,
    original_due_string: Optional[str],
    wake_time: datetime,
    is_recurring: bool,
) -> str:
    """
    Build the snooze metadata comment string.

    Args:
        original_due_date: The task's original due date as ISO string (YYYY-MM-DD or datetime).
        original_due_string: The task's original due string (e.g. "every day").
        wake_time: When the task should unsnooze.
        is_recurring: Whether the task was recurring.

    Returns:
        Comment string with _snooze: prefix and JSON payload.
    """
    payload = {
        "original_due_date": original_due_date,
        "original_due_string": original_due_string,
        "wake_time": wake_time.isoformat(),
        "is_recurring": is_recurring,
    }
    return SNOOZE_PREFIX + json.dumps(payload)


def parse_snooze_comment(content: str) -> Optional[dict]:
    """
    Parse a snooze metadata comment.

    Args:
        content: The comment content string.

    Returns:
        Parsed snooze metadata dict with wake_time as datetime, or None
        if the comment is not a snooze comment.
    """
    if not content.startswith(SNOOZE_PREFIX):
        return None

    try:
        data = json.loads(content[len(SNOOZE_PREFIX):])
        data["wake_time"] = datetime.fromisoformat(data["wake_time"])
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def is_snooze_comment(content: str) -> bool:
    """
    Check if a comment string is a snooze metadata comment.

    Args:
        content: The comment content string.

    Returns:
        True if the comment starts with the snooze prefix.
    """
    return content.startswith(SNOOZE_PREFIX)


def is_past_wake_time(snooze_data: dict, now: Optional[datetime] = None) -> bool:
    """
    Check whether a snoozed task's wake_time has passed.

    Args:
        snooze_data: Parsed snooze metadata dict (from parse_snooze_comment).
        now: Current time. Defaults to datetime.now().

    Returns:
        True if current time >= wake_time.
    """
    if now is None:
        now = datetime.now()
    return now >= snooze_data["wake_time"]


def build_restore_kwargs(snooze_data: dict) -> dict:
    """
    Build the kwargs for api.update_task() to restore a snoozed task.

    Args:
        snooze_data: Parsed snooze metadata dict.

    Returns:
        Dict suitable for passing to api.update_task() as kwargs.
    """
    kwargs = {}
    if snooze_data.get("original_due_string"):
        kwargs["due_string"] = snooze_data["original_due_string"]
    elif snooze_data.get("original_due_date"):
        kwargs["due_date"] = snooze_data["original_due_date"]
    return kwargs


def extract_url(text: str) -> Optional[str]:
    """
    Extract the first URL from a text string.

    Looks for http:// or https:// URLs in the text.

    Args:
        text: The text to search.

    Returns:
        The first URL found, or None.
    """
    match = re.search(r"https?://[^\s)<>\]\"']+", text)
    if match:
        url = match.group(0)
        # Strip trailing punctuation that's likely not part of the URL
        url = url.rstrip(".,;:!?)")
        return url
    return None
