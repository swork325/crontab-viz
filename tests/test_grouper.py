"""Tests for crontab_viz.grouper."""

from __future__ import annotations

import pytest

from crontab_viz.grouper import GroupBy, group_entries
from crontab_viz.parser import CronEntry


def _make_entry(
    schedule: str = "* * * * *",
    command: str = "echo hi",
    comment: str = "",
    is_valid: bool = True,
) -> CronEntry:
    entry = object.__new__(CronEntry)
    entry.schedule = schedule
    entry.command = command
    entry.comment = comment
    entry.is_valid = is_valid
    return entry


# ---------------------------------------------------------------------------
# GroupBy.VALIDITY
# ---------------------------------------------------------------------------

def test_group_validity_separates_valid_and_invalid():
    entries = [
        _make_entry(is_valid=True),
        _make_entry(is_valid=False),
        _make_entry(is_valid=True),
    ]
    groups = group_entries(entries, by=GroupBy.VALIDITY)
    assert "valid" in groups
    assert "invalid" in groups
    assert groups["valid"].count == 2
    assert groups["invalid"].count == 1


def test_group_validity_all_valid():
    entries = [_make_entry(is_valid=True) for _ in range(3)]
    groups = group_entries(entries, by=GroupBy.VALIDITY)
    assert "invalid" not in groups
    assert groups["valid"].count == 3


# ---------------------------------------------------------------------------
# GroupBy.SCHEDULE_TYPE
# ---------------------------------------------------------------------------

def test_group_schedule_type_standard():
    entries = [_make_entry(schedule="0 6 * * *")]
    groups = group_entries(entries, by=GroupBy.SCHEDULE_TYPE)
    assert "standard" in groups


def test_group_schedule_type_special():
    entries = [_make_entry(schedule="@daily")]
    groups = group_entries(entries, by=GroupBy.SCHEDULE_TYPE)
    assert "special" in groups


def test_group_schedule_type_mixed():
    entries = [
        _make_entry(schedule="@hourly"),
        _make_entry(schedule="30 4 * * *"),
        _make_entry(schedule="bad", is_valid=False),
    ]
    groups = group_entries(entries, by=GroupBy.SCHEDULE_TYPE)
    assert groups["special"].count == 1
    assert groups["standard"].count == 1
    assert groups["invalid"].count == 1


# ---------------------------------------------------------------------------
# GroupBy.COMMENT
# ---------------------------------------------------------------------------

def test_group_comment_uses_comment_text():
    entries = [
        _make_entry(comment="backup"),
        _make_entry(comment="backup"),
        _make_entry(comment="cleanup"),
    ]
    groups = group_entries(entries, by=GroupBy.COMMENT)
    assert groups["backup"].count == 2
    assert groups["cleanup"].count == 1


def test_group_comment_empty_falls_back():
    entries = [_make_entry(comment=""), _make_entry(comment=None)]
    groups = group_entries(entries, by=GroupBy.COMMENT)
    assert "<no comment>" in groups
    assert groups["<no comment>"].count == 2


# ---------------------------------------------------------------------------
# GroupBy.HOUR
# ---------------------------------------------------------------------------

def test_group_hour_extracts_hour_field():
    entries = [
        _make_entry(schedule="0 6 * * *"),
        _make_entry(schedule="0 6 1 * *"),
        _make_entry(schedule="0 12 * * *"),
    ]
    groups = group_entries(entries, by=GroupBy.HOUR)
    assert groups["hour:6"].count == 2
    assert groups["hour:12"].count == 1


def test_group_empty_entries_returns_empty_dict():
    groups = group_entries([], by=GroupBy.VALIDITY)
    assert groups == {}
