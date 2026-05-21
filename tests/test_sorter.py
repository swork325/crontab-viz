"""Tests for crontab_viz.sorter."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.sorter import SortCriteria, SortKey, sort_entries


def _make_entry(schedule: str, command: str, comment: str = "") -> CronEntry:
    line = f"{schedule} {command}" if not comment else f"{schedule} {command} # {comment}"
    return CronEntry(
        raw=line,
        raw_schedule=schedule,
        command=command,
        comment=comment,
    )


FIXED_NOW = datetime.datetime(2024, 1, 15, 12, 0, 0)


def test_sort_by_command_ascending():
    entries = [
        _make_entry("* * * * *", "zzz_task"),
        _make_entry("* * * * *", "aaa_task"),
        _make_entry("* * * * *", "mmm_task"),
    ]
    result = sort_entries(entries, SortCriteria(key=SortKey.COMMAND))
    commands = [e.command for e in result]
    assert commands == ["aaa_task", "mmm_task", "zzz_task"]


def test_sort_by_command_descending():
    entries = [
        _make_entry("* * * * *", "aaa_task"),
        _make_entry("* * * * *", "zzz_task"),
    ]
    result = sort_entries(entries, SortCriteria(key=SortKey.COMMAND, reverse=True))
    assert result[0].command == "zzz_task"


def test_sort_by_comment():
    entries = [
        _make_entry("* * * * *", "cmd", "zebra job"),
        _make_entry("* * * * *", "cmd", "alpha job"),
    ]
    result = sort_entries(entries, SortCriteria(key=SortKey.COMMENT))
    assert result[0].comment == "alpha job"


def test_sort_by_schedule_lexicographic():
    entries = [
        _make_entry("5 4 * * *", "cmd"),
        _make_entry("0 * * * *", "cmd"),
        _make_entry("@daily", "cmd"),
    ]
    result = sort_entries(entries, SortCriteria(key=SortKey.SCHEDULE))
    schedules = [e.raw_schedule for e in result]
    assert schedules == sorted(["5 4 * * *", "0 * * * *", "@daily"])


def test_sort_default_criteria_returns_list():
    entries = [
        _make_entry("* * * * *", "b_cmd"),
        _make_entry("* * * * *", "a_cmd"),
    ]
    result = sort_entries(entries)
    assert isinstance(result, list)
    assert len(result) == 2


def test_invalid_entries_sorted_last_by_next_run():
    valid = _make_entry("* * * * *", "valid_cmd")
    invalid = CronEntry(raw="bad line", raw_schedule="bad", command="", comment="")
    entries = [invalid, valid]
    result = sort_entries(entries, SortCriteria(key=SortKey.NEXT_RUN), now=FIXED_NOW)
    assert result[0].command == "valid_cmd"
    assert result[-1] is invalid


def test_sort_does_not_mutate_original():
    entries = [
        _make_entry("* * * * *", "z"),
        _make_entry("* * * * *", "a"),
    ]
    original_order = [e.command for e in entries]
    sort_entries(entries, SortCriteria(key=SortKey.COMMAND))
    assert [e.command for e in entries] == original_order


def test_empty_list_returns_empty():
    assert sort_entries([]) == []
