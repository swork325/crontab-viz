"""Tests for crontab_viz.timezonifier."""
from datetime import datetime
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.timezonifier import (
    TimezoneResult,
    convert_entries,
    convert_next_run,
    resolve_timezone,
)


def _make_entry(schedule: str = "0 9 * * *", command: str = "/bin/job") -> CronEntry:
    return CronEntry(raw=f"{schedule} {command}", schedule=schedule, command=command)


# ---------------------------------------------------------------------------
# resolve_timezone
# ---------------------------------------------------------------------------

def test_resolve_timezone_known_returns_zone_info():
    zone = resolve_timezone("Europe/London")
    assert zone is not None


def test_resolve_timezone_unknown_returns_none():
    zone = resolve_timezone("Not/AReal_Zone")
    assert zone is None


# ---------------------------------------------------------------------------
# convert_next_run
# ---------------------------------------------------------------------------

def test_convert_next_run_unknown_tz_returns_error():
    entry = _make_entry()
    result = convert_next_run(entry, "Bad/Zone")
    assert result.error is not None
    assert "Unknown timezone" in result.error
    assert not result.is_valid


def test_convert_next_run_valid_entry_returns_local_datetime():
    entry = _make_entry("0 9 * * *")
    now = datetime(2024, 1, 15, 8, 0, 0)  # UTC 08:00 → next run UTC 09:00
    result = convert_next_run(entry, "Europe/Paris", now=now)
    assert result.is_valid
    assert result.local_next_run is not None
    assert result.local_next_run.tzinfo is not None
    assert result.utc_next_run is not None


def test_convert_next_run_local_time_differs_from_utc():
    entry = _make_entry("0 9 * * *")
    now = datetime(2024, 6, 15, 8, 0, 0)  # UTC; Paris is UTC+2 in summer
    result = convert_next_run(entry, "Europe/Paris", now=now)
    assert result.is_valid
    assert result.local_next_run is not None
    # 09:00 UTC == 11:00 Paris (CEST, UTC+2)
    assert result.local_next_run.hour == 11


def test_convert_next_run_invalid_entry_returns_error():
    entry = CronEntry(
        raw="bad line",
        schedule="bad",
        command="",
        is_valid=False,
    )
    result = convert_next_run(entry, "UTC")
    assert not result.is_valid
    assert result.error is not None


def test_convert_next_run_stores_timezone_name():
    entry = _make_entry()
    result = convert_next_run(entry, "America/New_York")
    assert result.timezone == "America/New_York"


def test_convert_next_run_formatted_contains_timezone_abbr():
    entry = _make_entry("0 12 * * *")
    now = datetime(2024, 1, 15, 11, 0, 0)
    result = convert_next_run(entry, "UTC", now=now)
    assert result.is_valid
    formatted = result.formatted()
    assert "UTC" in formatted


def test_convert_next_run_formatted_error_contains_tz():
    entry = _make_entry()
    result = convert_next_run(entry, "Fake/Zone")
    assert "Fake/Zone" in result.formatted()


# ---------------------------------------------------------------------------
# convert_entries
# ---------------------------------------------------------------------------

def test_convert_entries_returns_one_result_per_entry():
    entries = [_make_entry("0 6 * * *"), _make_entry("30 18 * * *")]
    now = datetime(2024, 3, 10, 5, 0, 0)
    results = convert_entries(entries, "Asia/Tokyo", now=now)
    assert len(results) == 2


def test_convert_entries_all_valid_for_good_tz():
    entries = [_make_entry("0 8 * * *"), _make_entry("@daily")]
    now = datetime(2024, 3, 10, 7, 0, 0)
    results = convert_entries(entries, "America/Chicago", now=now)
    assert all(r.is_valid for r in results)


def test_convert_entries_empty_list_returns_empty():
    results = convert_entries([], "UTC")
    assert results == []
