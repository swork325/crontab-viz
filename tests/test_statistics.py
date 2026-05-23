"""Tests for crontab_viz.statistics module."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.statistics import compute_statistics, _estimate_daily_runs


def _make_entry(
    schedule: str = "* * * * *",
    command: str = "echo hello",
    comment: str = "",
    is_valid: bool = True,
) -> CronEntry:
    entry = CronEntry.__new__(CronEntry)
    object.__setattr__(entry, "raw", f"{schedule} {command}")
    object.__setattr__(entry, "command", command)
    object.__setattr__(entry, "comment", comment)
    object.__setattr__(entry, "is_valid", is_valid)
    if schedule.startswith("@"):
        object.__setattr__(entry, "special", schedule)
        object.__setattr__(entry, "fields", {})
    else:
        object.__setattr__(entry, "special", None)
        parts = schedule.split()
        names = ["minute", "hour", "day", "month", "weekday"]
        fields = {}
        for name, part in zip(names, parts):
            if part == "*":
                fields[name] = list(range(60 if name == "minute" else 24 if name == "hour" else 32))
            else:
                fields[name] = [int(part)]
        object.__setattr__(entry, "fields", fields)
    return entry


def test_compute_statistics_empty_list():
    stats = compute_statistics([])
    assert stats.total == 0
    assert stats.valid_count == 0
    assert stats.invalid_count == 0


def test_compute_statistics_counts_total():
    entries = [_make_entry() for _ in range(5)]
    stats = compute_statistics(entries)
    assert stats.total == 5


def test_compute_statistics_valid_and_invalid():
    entries = [
        _make_entry(is_valid=True),
        _make_entry(is_valid=True),
        _make_entry(is_valid=False),
    ]
    stats = compute_statistics(entries)
    assert stats.valid_count == 2
    assert stats.invalid_count == 1


def test_compute_statistics_special_vs_standard():
    entries = [
        _make_entry(schedule="@daily", command="backup"),
        _make_entry(schedule="0 6 * * *", command="report"),
    ]
    stats = compute_statistics(entries)
    assert stats.special_count == 1
    assert stats.standard_count == 1


def test_compute_statistics_unique_commands():
    entries = [
        _make_entry(command="cmd_a"),
        _make_entry(command="cmd_a"),
        _make_entry(command="cmd_b"),
    ]
    stats = compute_statistics(entries)
    assert stats.unique_commands == 2


def test_compute_statistics_most_common_commands():
    entries = [
        _make_entry(command="alpha"),
        _make_entry(command="alpha"),
        _make_entry(command="beta"),
    ]
    stats = compute_statistics(entries, top_n=2)
    commands = [c for c, _ in stats.most_common_commands]
    assert "alpha" in commands


def test_estimate_daily_runs_wildcard():
    entry = _make_entry(schedule="* * * * *")
    runs = _estimate_daily_runs(entry)
    assert runs > 0


def test_estimate_daily_runs_at_daily():
    entry = _make_entry(schedule="@daily")
    runs = _estimate_daily_runs(entry)
    assert runs == 1.0


def test_estimate_daily_runs_at_hourly():
    entry = _make_entry(schedule="@hourly")
    runs = _estimate_daily_runs(entry)
    assert runs == 24.0


def test_estimate_daily_runs_invalid():
    entry = _make_entry(is_valid=False)
    runs = _estimate_daily_runs(entry)
    assert runs == 0.0


def test_as_dict_keys_present():
    entries = [_make_entry()]
    stats = compute_statistics(entries)
    d = stats.as_dict()
    expected_keys = [
        "total", "valid_count", "invalid_count", "special_count",
        "standard_count", "unique_commands", "most_common_commands",
        "busiest_hour", "busiest_hour_count", "avg_runs_per_day",
        "next_due_command", "next_due_in_seconds",
    ]
    for key in expected_keys:
        assert key in d


def test_next_due_command_populated():
    entries = [_make_entry(schedule="* * * * *", command="my_job")]
    stats = compute_statistics(entries)
    assert stats.next_due_command == "my_job"
    assert stats.next_due_in_seconds is not None
    assert stats.next_due_in_seconds >= 0
