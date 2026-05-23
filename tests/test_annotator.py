"""Tests for crontab_viz.annotator."""
from __future__ import annotations

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.annotator import (
    AnnotatedEntry,
    describe_schedule,
    annotate_entry,
    annotate_entries,
)


def _make_entry(
    schedule: str = "* * * * *",
    command: str = "echo hi",
    comment: str = "",
    valid: bool = True,
) -> CronEntry:
    raw = f"{schedule} {command}"
    if comment:
        raw = f"{raw} # {comment}"
    entry = CronEntry(raw_line=raw)
    # Force validity for test isolation
    object.__setattr__(entry, "_valid", None)  # let __post_init__ handle it
    return CronEntry(raw_line=raw)


# --- describe_schedule ---

def test_describe_special_at_daily():
    entry = CronEntry(raw_line="@daily /usr/bin/backup")
    result = describe_schedule(entry)
    assert result == "Run once a day at midnight"


def test_describe_special_at_reboot():
    entry = CronEntry(raw_line="@reboot /usr/bin/init-script")
    result = describe_schedule(entry)
    assert result == "Run once at startup"


def test_describe_special_at_hourly():
    entry = CronEntry(raw_line="@hourly /usr/bin/cleanup")
    result = describe_schedule(entry)
    assert result == "Run once an hour at :00"


def test_describe_wildcard_schedule():
    entry = CronEntry(raw_line="* * * * * echo hi")
    result = describe_schedule(entry)
    assert "every minute" in result
    assert "every hour" in result


def test_describe_specific_minute_and_hour():
    entry = CronEntry(raw_line="30 6 * * * echo hi")
    result = describe_schedule(entry)
    assert "minute 30" in result
    assert "hour 6" in result


def test_describe_range_field():
    entry = CronEntry(raw_line="0 9-17 * * * echo hi")
    result = describe_schedule(entry)
    assert "9" in result and "17" in result


def test_describe_step_field():
    entry = CronEntry(raw_line="*/15 * * * * echo hi")
    result = describe_schedule(entry)
    assert "15" in result


def test_describe_invalid_entry():
    entry = CronEntry(raw_line="not a valid cron line")
    result = describe_schedule(entry)
    assert result == "Invalid schedule"


# --- annotate_entry ---

def test_annotate_entry_returns_annotated_entry():
    entry = CronEntry(raw_line="0 0 * * * /usr/bin/backup")
    result = annotate_entry(entry)
    assert isinstance(result, AnnotatedEntry)
    assert result.entry is entry


def test_annotate_entry_description_not_empty():
    entry = CronEntry(raw_line="0 0 * * * /usr/bin/backup")
    result = annotate_entry(entry)
    assert result.description


def test_annotate_entry_with_comment_adds_note():
    entry = CronEntry(raw_line="0 0 * * * /usr/bin/backup # nightly backup")
    result = annotate_entry(entry)
    assert any("nightly backup" in note for note in result.notes)


def test_annotate_entry_special_adds_macro_note():
    entry = CronEntry(raw_line="@daily /usr/bin/backup")
    result = annotate_entry(entry)
    assert any("special macro" in note for note in result.notes)


def test_annotated_entry_str_contains_command():
    entry = CronEntry(raw_line="0 0 * * * /usr/bin/backup")
    result = annotate_entry(entry)
    assert "/usr/bin/backup" in str(result)


# --- annotate_entries ---

def test_annotate_entries_returns_list():
    entries = [
        CronEntry(raw_line="0 0 * * * /usr/bin/backup"),
        CronEntry(raw_line="@hourly /usr/bin/cleanup"),
    ]
    results = annotate_entries(entries)
    assert len(results) == 2
    assert all(isinstance(r, AnnotatedEntry) for r in results)


def test_annotate_entries_empty_list():
    assert annotate_entries([]) == []
