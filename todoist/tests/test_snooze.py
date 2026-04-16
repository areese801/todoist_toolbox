"""Tests for the snooze engine."""

import json
from datetime import datetime, timedelta

import pytest

from todoist.tui.snooze import (
    SNOOZE_PREFIX,
    build_restore_kwargs,
    build_snooze_comment,
    is_past_wake_time,
    is_snooze_comment,
    parse_snooze_comment,
    resolve_preset_wake_time,
)


class TestResolvePresetWakeTime:
    """Tests for resolve_preset_wake_time()."""

    def test_30m_preset(self):
        """30m preset adds 30 minutes to now."""
        now = datetime(2026, 4, 16, 10, 0, 0)
        result = resolve_preset_wake_time("30m", now=now)
        assert result == datetime(2026, 4, 16, 10, 30, 0)

    def test_1h_preset(self):
        """1h preset adds 1 hour to now."""
        now = datetime(2026, 4, 16, 10, 0, 0)
        result = resolve_preset_wake_time("1h", now=now)
        assert result == datetime(2026, 4, 16, 11, 0, 0)

    def test_2h_preset(self):
        """2h preset adds 2 hours to now."""
        now = datetime(2026, 4, 16, 10, 0, 0)
        result = resolve_preset_wake_time("2h", now=now)
        assert result == datetime(2026, 4, 16, 12, 0, 0)

    def test_afternoon_preset_before_1pm(self):
        """Afternoon preset resolves to 13:00 today if before 1pm."""
        now = datetime(2026, 4, 16, 9, 0, 0)
        result = resolve_preset_wake_time("afternoon", now=now)
        assert result == datetime(2026, 4, 16, 13, 0, 0)

    def test_afternoon_preset_after_1pm(self):
        """Afternoon preset resolves to 13:00 tomorrow if after 1pm."""
        now = datetime(2026, 4, 16, 14, 0, 0)
        result = resolve_preset_wake_time("afternoon", now=now)
        assert result == datetime(2026, 4, 17, 13, 0, 0)

    def test_evening_preset_before_6pm(self):
        """Evening preset resolves to 18:00 today if before 6pm."""
        now = datetime(2026, 4, 16, 10, 0, 0)
        result = resolve_preset_wake_time("evening", now=now)
        assert result == datetime(2026, 4, 16, 18, 0, 0)

    def test_evening_preset_after_6pm(self):
        """Evening preset resolves to 18:00 tomorrow if after 6pm."""
        now = datetime(2026, 4, 16, 19, 0, 0)
        result = resolve_preset_wake_time("evening", now=now)
        assert result == datetime(2026, 4, 17, 18, 0, 0)

    def test_custom_minutes(self):
        """Custom '45m' string parses correctly."""
        now = datetime(2026, 4, 16, 10, 0, 0)
        result = resolve_preset_wake_time("45m", now=now)
        assert result == datetime(2026, 4, 16, 10, 45, 0)

    def test_custom_hours(self):
        """Custom '3h' string parses correctly."""
        now = datetime(2026, 4, 16, 10, 0, 0)
        result = resolve_preset_wake_time("3h", now=now)
        assert result == datetime(2026, 4, 16, 13, 0, 0)

    def test_invalid_preset_raises(self):
        """Unrecognized preset raises ValueError."""
        with pytest.raises(ValueError, match="Unrecognized"):
            resolve_preset_wake_time("next week")


class TestBuildSnoozeComment:
    """Tests for build_snooze_comment()."""

    def test_basic_comment(self):
        """Comment has correct prefix and parseable JSON payload."""
        wake = datetime(2026, 4, 16, 14, 0, 0)
        result = build_snooze_comment(
            original_due_date="2026-04-16",
            original_due_string="every day",
            wake_time=wake,
            is_recurring=True,
        )
        assert result.startswith(SNOOZE_PREFIX)
        payload = json.loads(result[len(SNOOZE_PREFIX):])
        assert payload["original_due_date"] == "2026-04-16"
        assert payload["original_due_string"] == "every day"
        assert payload["wake_time"] == "2026-04-16T14:00:00"
        assert payload["is_recurring"] is True

    def test_non_recurring_task(self):
        """Non-recurring task has is_recurring=False in payload."""
        wake = datetime(2026, 4, 16, 18, 0, 0)
        result = build_snooze_comment(
            original_due_date="2026-04-16",
            original_due_string=None,
            wake_time=wake,
            is_recurring=False,
        )
        payload = json.loads(result[len(SNOOZE_PREFIX):])
        assert payload["is_recurring"] is False
        assert payload["original_due_string"] is None


class TestParseSnoozeComment:
    """Tests for parse_snooze_comment()."""

    def test_valid_comment(self):
        """Valid snooze comment is parsed correctly."""
        wake = datetime(2026, 4, 16, 14, 0, 0)
        comment = build_snooze_comment(
            original_due_date="2026-04-16",
            original_due_string="every day",
            wake_time=wake,
            is_recurring=True,
        )
        result = parse_snooze_comment(comment)
        assert result is not None
        assert result["original_due_date"] == "2026-04-16"
        assert result["wake_time"] == wake

    def test_non_snooze_comment(self):
        """Regular comment returns None."""
        assert parse_snooze_comment("Just a note") is None

    def test_malformed_json(self):
        """Malformed JSON after prefix returns None."""
        assert parse_snooze_comment("_snooze:{bad json}") is None

    def test_empty_string(self):
        """Empty string returns None."""
        assert parse_snooze_comment("") is None


class TestIsSnoozeComment:
    """Tests for is_snooze_comment()."""

    def test_snooze_comment(self):
        """String with snooze prefix returns True."""
        assert is_snooze_comment("_snooze:{}")

    def test_regular_comment(self):
        """Regular string returns False."""
        assert not is_snooze_comment("Hello world")

    def test_empty_string(self):
        """Empty string returns False."""
        assert not is_snooze_comment("")


class TestIsPastWakeTime:
    """Tests for is_past_wake_time()."""

    def test_past_wake_time(self):
        """Returns True when now is after wake_time."""
        data = {"wake_time": datetime(2026, 4, 16, 10, 0, 0)}
        now = datetime(2026, 4, 16, 11, 0, 0)
        assert is_past_wake_time(data, now=now) is True

    def test_future_wake_time(self):
        """Returns False when now is before wake_time."""
        data = {"wake_time": datetime(2026, 4, 16, 14, 0, 0)}
        now = datetime(2026, 4, 16, 10, 0, 0)
        assert is_past_wake_time(data, now=now) is False

    def test_exact_wake_time(self):
        """Returns True when now equals wake_time."""
        wake = datetime(2026, 4, 16, 10, 0, 0)
        data = {"wake_time": wake}
        assert is_past_wake_time(data, now=wake) is True


class TestBuildRestoreKwargs:
    """Tests for build_restore_kwargs()."""

    def test_recurring_task_restores_due_string(self):
        """Recurring task restores via due_string."""
        data = {
            "original_due_date": "2026-04-16",
            "original_due_string": "every day",
            "is_recurring": True,
        }
        result = build_restore_kwargs(data)
        assert result == {"due_string": "every day"}

    def test_non_recurring_task_restores_due_date(self):
        """Non-recurring task with no due_string restores via due_date."""
        data = {
            "original_due_date": "2026-04-20",
            "original_due_string": None,
            "is_recurring": False,
        }
        result = build_restore_kwargs(data)
        assert result == {"due_date": "2026-04-20"}

    def test_due_string_takes_priority(self):
        """When both due_date and due_string exist, due_string wins."""
        data = {
            "original_due_date": "2026-04-16",
            "original_due_string": "tomorrow",
            "is_recurring": False,
        }
        result = build_restore_kwargs(data)
        assert result == {"due_string": "tomorrow"}

    def test_empty_fields(self):
        """When both are empty/None, returns empty dict."""
        data = {
            "original_due_date": "",
            "original_due_string": "",
            "is_recurring": False,
        }
        result = build_restore_kwargs(data)
        assert result == {}
