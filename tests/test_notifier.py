"""Tests for crontab_viz.notifier."""
from datetime import datetime
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.notifier import DueAlert, check_due, format_alerts


def _make_entry(schedule: str, command: str = "cmd", valid: bool = True) -> CronEntry:
    entry = CronEntry(schedule=schedule, command=command, comment="")
    object.__setattr__(entry, "is_valid", valid)
    return entry


FIXED_NOW = datetime(2024, 1, 15, 12, 0, 0)  # Monday 12:00:00


def test_check_due_returns_empty_when_no_entries():
    result = check_due([], threshold_seconds=300, now=FIXED_NOW)
    assert result == []


def test_check_due_skips_invalid_entries():
    entry = _make_entry("* * * * *", "bad", valid=False)
    result = check_due([entry], threshold_seconds=300, now=FIXED_NOW)
    assert result == []


def test_check_due_detects_imminent_job():
    # Every minute — next run is at most 60 s away
    entry = _make_entry("* * * * *", "every-minute")
    result = check_due([entry], threshold_seconds=300, now=FIXED_NOW)
    assert len(result) == 1
    assert result[0].entry.command == "every-minute"
    assert result[0].seconds_until_due <= 60


def test_check_due_excludes_far_future_job():
    # Runs once a year — definitely not within 5 minutes
    entry = _make_entry("0 0 1 1 *", "yearly")
    result = check_due([entry], threshold_seconds=300, now=FIXED_NOW)
    assert result == []


def test_check_due_sorted_soonest_first():
    entry_every_min = _make_entry("* * * * *", "every-minute")
    entry_top_of_hour = _make_entry("0 * * * *", "hourly")
    # Both may be within threshold depending on FIXED_NOW; use a very large threshold
    result = check_due(
        [entry_top_of_hour, entry_every_min],
        threshold_seconds=3700,
        now=FIXED_NOW,
    )
    for i in range(len(result) - 1):
        assert result[i].seconds_until_due <= result[i + 1].seconds_until_due


def test_due_alert_str_format():
    entry = _make_entry("* * * * *", "my-job")
    alert = DueAlert(entry=entry, next_run_time=datetime(2024, 1, 15, 12, 1, 0), seconds_until_due=60)
    text = str(alert)
    assert "my-job" in text
    assert "ALERT" in text
    assert "1m" in text


def test_format_alerts_no_alerts():
    result = format_alerts([])
    assert "No jobs" in result


def test_format_alerts_with_alerts():
    entry = _make_entry("* * * * *", "demo")
    alert = DueAlert(entry=entry, next_run_time=datetime(2024, 1, 15, 12, 1, 0), seconds_until_due=45)
    result = format_alerts([alert])
    assert "demo" in result
    assert "ALERT" in result


def test_check_due_uses_current_time_by_default():
    entry = _make_entry("* * * * *", "tick")
    # Should not raise; uses datetime.now() internally
    result = check_due([entry], threshold_seconds=300)
    assert isinstance(result, list)
