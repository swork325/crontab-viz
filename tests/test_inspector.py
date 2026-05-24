"""Tests for crontab_viz.inspector."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from crontab_viz.parser import CronEntry
from crontab_viz.inspector import (
    inspect_entry,
    inspect_entries,
    FieldInspection,
    EntryInspection,
)


def _make_entry(
    schedule: str = "0 * * * *",
    command: str = "/usr/bin/backup",
    comment: str = "",
    valid: bool = True,
) -> CronEntry:
    entry = MagicMock(spec=CronEntry)
    entry.schedule = schedule
    entry.command = command
    entry.comment = comment
    entry.is_valid = valid
    parts = schedule.split()
    if len(parts) == 5 and valid:
        entry.minute, entry.hour, entry.dom, entry.month, entry.dow = parts
    else:
        entry.minute = entry.hour = entry.dom = entry.month = entry.dow = None
    return entry


def test_inspect_entry_returns_entry_inspection():
    entry = _make_entry()
    result = inspect_entry(entry)
    assert isinstance(result, EntryInspection)


def test_inspect_entry_valid_standard_has_five_fields():
    entry = _make_entry(schedule="0 6 * * 1")
    result = inspect_entry(entry)
    assert len(result.fields) == 5


def test_inspect_entry_invalid_has_warning():
    entry = _make_entry(schedule="bad schedule", valid=False)
    result = inspect_entry(entry)
    assert result.has_warnings
    assert any("parse" in w.lower() for w in result.warnings)


def test_inspect_entry_invalid_has_no_fields():
    entry = _make_entry(schedule="?? bad", valid=False)
    result = inspect_entry(entry)
    assert result.fields == []


def test_inspect_entry_special_at_daily():
    entry = _make_entry(schedule="@daily")
    entry.is_valid = True
    result = inspect_entry(entry)
    assert result.is_special is True
    assert result.special_meaning == "Run once a day (0 0 * * *)"


def test_inspect_entry_special_has_no_fields():
    entry = _make_entry(schedule="@hourly")
    entry.is_valid = True
    result = inspect_entry(entry)
    assert result.fields == []


def test_inspect_entry_wildcard_schedule_warns():
    entry = _make_entry(schedule="* * * * *")
    result = inspect_entry(entry)
    assert result.has_warnings
    assert any("every minute" in w.lower() for w in result.warnings)


def test_inspect_entry_step_field_note():
    entry = _make_entry(schedule="*/15 * * * *")
    result = inspect_entry(entry)
    minute_field = result.fields[0]
    assert minute_field.has_step is True
    assert minute_field.note is not None
    assert "15" in minute_field.note


def test_inspect_entry_range_field_note():
    entry = _make_entry(schedule="0 9-17 * * *")
    result = inspect_entry(entry)
    hour_field = result.fields[1]
    assert hour_field.has_range is True
    assert hour_field.note is not None
    assert "9" in hour_field.note and "17" in hour_field.note


def test_inspect_entry_list_field():
    entry = _make_entry(schedule="0 0 1,15 * *")
    result = inspect_entry(entry)
    dom_field = result.fields[2]
    assert dom_field.has_list is True
    assert "1" in dom_field.values
    assert "15" in dom_field.values


def test_inspect_entry_wildcard_field_note():
    entry = _make_entry(schedule="0 6 * * 1")
    result = inspect_entry(entry)
    dom_field = result.fields[2]
    assert dom_field.is_wildcard is True
    assert dom_field.note is not None


def test_inspect_entries_returns_list():
    entries = [_make_entry(), _make_entry(schedule="@weekly")]
    entries[1].is_valid = True
    results = inspect_entries(entries)
    assert len(results) == 2
    assert all(isinstance(r, EntryInspection) for r in results)


def test_inspect_entries_empty_list():
    assert inspect_entries([]) == []


def test_inspect_entry_unknown_special_no_meaning():
    entry = _make_entry(schedule="@unknown")
    entry.is_valid = True
    result = inspect_entry(entry)
    assert result.is_special is True
    assert result.special_meaning is None
