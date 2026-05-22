"""Tests for crontab_viz.summarizer."""
from __future__ import annotations

import datetime
import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.summarizer import summarize, render_summary, CrontabSummary


def _make_entry(
    schedule: str = "* * * * *",
    command: str = "echo hi",
    comment: str = "",
    is_valid: bool = True,
) -> CronEntry:
    entry = CronEntry(schedule=schedule, command=command, comment=comment)
    object.__setattr__(entry, "is_valid", is_valid)
    return entry


FIXED_NOW = datetime.datetime(2024, 6, 1, 12, 0, 0)


def test_summarize_empty_list():
    s = summarize([], now=FIXED_NOW)
    assert s.total == 0
    assert s.valid == 0
    assert s.invalid == 0


def test_summarize_counts_total():
    entries = [_make_entry(), _make_entry(), _make_entry(is_valid=False)]
    s = summarize(entries, now=FIXED_NOW)
    assert s.total == 3


def test_summarize_valid_and_invalid_counts():
    entries = [
        _make_entry(is_valid=True),
        _make_entry(is_valid=False),
        _make_entry(is_valid=False),
    ]
    s = summarize(entries, now=FIXED_NOW)
    assert s.valid == 1
    assert s.invalid == 2


def test_summarize_special_vs_standard():
    entries = [
        _make_entry(schedule="@daily"),
        _make_entry(schedule="@hourly"),
        _make_entry(schedule="0 9 * * 1"),
    ]
    s = summarize(entries, now=FIXED_NOW)
    assert s.special == 2
    assert s.standard == 1


def test_summarize_unique_commands():
    entries = [
        _make_entry(command="echo a"),
        _make_entry(command="echo a"),
        _make_entry(command="echo b"),
    ]
    s = summarize(entries, now=FIXED_NOW)
    assert s.unique_commands == 2


def test_summarize_next_due_populated_for_valid_entries():
    entries = [_make_entry(schedule="* * * * *")]
    s = summarize(entries, now=FIXED_NOW)
    assert s.next_due != ""


def test_summarize_hour_distribution_standard_entry():
    entries = [_make_entry(schedule="0 3 * * *")]
    s = summarize(entries, now=FIXED_NOW)
    assert "3:00" in s.hour_distribution
    assert s.hour_distribution["3:00"] == 1


def test_summarize_busiest_hour():
    entries = [
        _make_entry(schedule="0 3 * * *"),
        _make_entry(schedule="30 3 * * *"),
        _make_entry(schedule="0 5 * * *"),
    ]
    s = summarize(entries, now=FIXED_NOW)
    assert s.busiest_hour == "3:00"


def test_render_summary_contains_totals():
    s = CrontabSummary(total=10, valid=8, invalid=2)
    output = render_summary(s)
    assert "10" in output
    assert "8" in output
    assert "2" in output


def test_render_summary_contains_header():
    s = CrontabSummary()
    output = render_summary(s)
    assert "Summary" in output


def test_as_dict_keys():
    s = CrontabSummary(total=5)
    d = s.as_dict()
    for key in ("total", "valid", "invalid", "special", "standard",
                "unique_commands", "next_due", "busiest_hour", "hour_distribution"):
        assert key in d
