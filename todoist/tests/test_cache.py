"""Tests for todoist.cache module."""

import json
import pytest
from datetime import date, timedelta

from todoist.cache import load_cache, save_cache, get_cached_due_date, MISS


class TestLoadCache:
    """Tests for load_cache()."""

    def test_returns_empty_when_no_file(self, tmp_path, monkeypatch):
        """When the cache file doesn't exist, return an empty dict."""
        monkeypatch.setattr("todoist.cache.CACHE_FILE", tmp_path / "missing.json")
        assert load_cache() == {}

    def test_handles_corrupt_json(self, tmp_path, monkeypatch):
        """When the cache file contains invalid JSON, return an empty dict."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json{{{")
        monkeypatch.setattr("todoist.cache.CACHE_FILE", bad_file)
        assert load_cache() == {}


class TestSaveCache:
    """Tests for save_cache()."""

    def test_creates_directory_and_file(self, tmp_path, monkeypatch):
        """save_cache should create parent directories if they don't exist."""
        cache_dir = tmp_path / "sub" / "dir"
        cache_file = cache_dir / "cache.json"
        monkeypatch.setattr("todoist.cache.CACHE_DIR", cache_dir)
        monkeypatch.setattr("todoist.cache.CACHE_FILE", cache_file)

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        save_cache({"every day": tomorrow})

        assert cache_file.exists()
        assert json.loads(cache_file.read_text()) == {"every day": tomorrow}


class TestRoundTrip:
    """Tests for save + load round-trip."""

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        """Data saved with save_cache should be recoverable with load_cache."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("todoist.cache.CACHE_DIR", tmp_path)
        monkeypatch.setattr("todoist.cache.CACHE_FILE", cache_file)

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        next_month = (date.today() + timedelta(days=30)).isoformat()
        data = {
            "every day": tomorrow,
            "every week": next_week,
            "every month": next_month,
        }
        save_cache(data)
        assert load_cache() == data

    def test_none_values_roundtrip(self, tmp_path, monkeypatch):
        """None values (failed probes) should survive JSON serialization."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("todoist.cache.CACHE_DIR", tmp_path)
        monkeypatch.setattr("todoist.cache.CACHE_FILE", cache_file)

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        data = {"every day": tomorrow, "weird schedule": None}
        save_cache(data)
        loaded = load_cache()
        assert loaded == data
        assert loaded["weird schedule"] is None


class TestGetCachedDueDate:
    """Tests for get_cached_due_date()."""

    def test_returns_cached_value_for_future_date(self):
        """When the cached date is in the future, return it."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        cache = {
            "every day": tomorrow,
            "every week": (date.today() + timedelta(days=7)).isoformat(),
        }
        assert get_cached_due_date(cache, "every day") == tomorrow

    def test_returns_cached_none(self):
        """When the cached value is None (failed probe), return None, not MISS."""
        cache = {"broken": None}
        result = get_cached_due_date(cache, "broken")
        assert result is None
        assert result is not MISS

    def test_returns_miss_for_absent_key(self):
        """When the due_string is not in the cache, return MISS sentinel."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        cache = {"every day": tomorrow}
        assert get_cached_due_date(cache, "every week") is MISS

    def test_returns_miss_for_stale_date(self):
        """When the cached date is in the past, return MISS (stale)."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        cache = {"every day": yesterday}
        assert get_cached_due_date(cache, "every day") is MISS

    def test_returns_value_for_today(self):
        """A cached date of today is still valid (not yet past)."""
        today = date.today().isoformat()
        cache = {"every day": today}
        # today is not < today, so it should be a hit
        assert get_cached_due_date(cache, "every day") == today

    def test_returns_miss_for_corrupt_date_string(self):
        """If the cached value is not a valid ISO date, return MISS."""
        cache = {"every day": "not-a-date"}
        assert get_cached_due_date(cache, "every day") is MISS
