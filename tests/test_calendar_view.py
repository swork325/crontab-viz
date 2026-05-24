"""Unit tests for crontab_viz.calendar_view."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.calendar_view import CalendarMatrix, render_calendar, DAYS, HOURS


def _make_entry(schedule: str, command: str = "echo test", valid: bool = True) -> CronEntry:
    entry = CronEntry(raw=f"{schedule} {command}", schedule=schedule, command=command)
    if not valid:
        object.__setattr__(entry, "is_valid", False)
    return entry


def _std(minute="*", hour="*", dom="*", month="*", dow="*", cmd="echo hi") -> CronEntry:
    schedule = f"{minute} {hour} {dom} {month} {dow}"
    return CronEntry(
        raw=f"{schedule} {cmd}",
        schedule=schedule,
        command=cmd,
        fields=(minute, hour, dom, month, dow),
    )


def test_matrix_all_wildcards_fills_all_slots():
    entry = _std()
    m = CalendarMatrix([entry])
    for d in range(7):
        for h in HOURS:
            assert m.matrix[d][h] == 1


def test_matrix_specific_hour_fills_only_that_hour():
    entry = _std(hour="3")
    m = CalendarMatrix([entry])
    for d in range(7):
        assert m.matrix[d][3] == 1
        assert m.matrix[d][4] == 0


def test_matrix_specific_dow_fills_only_that_day():
    entry = _std(dow="1")  # Monday
    m = CalendarMatrix([entry])
    assert m.matrix[1][0] == 1
    assert m.matrix[0][0] == 0  # Sunday


def test_matrix_invalid_entry_ignored():
    entry = CronEntry(raw="bad line", schedule="bad", command="", is_valid=False)
    m = CalendarMatrix([entry])
    for d in range(7):
        for h in HOURS:
            assert m.matrix[d][h] == 0


def test_matrix_multiple_entries_accumulate():
    e1 = _std(hour="6")
    e2 = _std(hour="6")
    m = CalendarMatrix([e1, e2])
    for d in range(7):
        assert m.matrix[d][6] == 2


def test_busiest_hour_returns_int():
    entry = _std(hour="10")
    m = CalendarMatrix([entry])
    assert m.busiest_hour() == 10


def test_busiest_day_returns_day_name():
    entry = _std(dow="5")  # Friday
    m = CalendarMatrix([entry])
    assert m.busiest_day() == "Fri"


def test_render_calendar_contains_day_labels():
    m = CalendarMatrix([])
    output = render_calendar(m)
    for day in DAYS:
        assert day in output


def test_render_calendar_contains_hour_zero():
    m = CalendarMatrix([])
    output = render_calendar(m)
    assert "0" in output


def test_render_calendar_shows_count_digit():
    entry = _std(hour="2")
    m = CalendarMatrix([entry])
    output = render_calendar(m)
    assert "1" in output
