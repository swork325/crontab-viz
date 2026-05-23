"""Tests for crontab_viz.scorer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.scorer import EntryScore, score_entry, score_entries


def _make_entry(
    minute="0",
    hour="*",
    dom="*",
    month="*",
    dow="*",
    command="/usr/bin/backup.sh",
    comment="",
    valid=True,
) -> CronEntry:
    e = CronEntry.__new__(CronEntry)
    object.__setattr__(e, "minute", minute)
    object.__setattr__(e, "hour", hour)
    object.__setattr__(e, "day_of_month", dom)
    object.__setattr__(e, "month", month)
    object.__setattr__(e, "day_of_week", dow)
    object.__setattr__(e, "command", command)
    object.__setattr__(e, "comment", comment)
    object.__setattr__(e, "raw", f"{minute} {hour} {dom} {month} {dow} {command}")
    object.__setattr__(e, "raw_schedule", f"{minute} {hour} {dom} {month} {dow}")
    object.__setattr__(e, "is_valid", valid)
    return e


def test_score_entry_invalid_has_risk():
    e = _make_entry(valid=False)
    s = score_entry(e)
    assert s.risk >= 1
    assert "invalid entry" in s.notes


def test_score_entry_invalid_total_nonzero():
    e = _make_entry(valid=False)
    s = score_entry(e)
    assert s.total > 0


def test_score_entry_simple_schedule_low_complexity():
    e = _make_entry(minute="0", hour="3")
    s = score_entry(e)
    assert s.complexity <= 4


def test_score_entry_list_in_field_increases_complexity():
    e = _make_entry(minute="0,30")
    s = score_entry(e)
    assert s.complexity > score_entry(_make_entry(minute="0")).complexity
    assert any("list" in n for n in s.notes)


def test_score_entry_range_in_field_increases_complexity():
    e = _make_entry(hour="1-5")
    s = score_entry(e)
    assert any("range" in n for n in s.notes)


def test_score_entry_step_in_field_increases_complexity():
    e = _make_entry(minute="*/5")
    s = score_entry(e)
    assert any("step" in n for n in s.notes)


def test_score_entry_sudo_command_adds_risk():
    e = _make_entry(command="sudo /usr/bin/cleanup.sh")
    s = score_entry(e)
    assert s.risk >= 2
    assert any("sudo" in n for n in s.notes)


def test_score_entry_rm_command_adds_risk():
    e = _make_entry(command="rm -rf /tmp/cache")
    s = score_entry(e)
    assert s.risk >= 2
    assert any("rm" in n for n in s.notes)


def test_score_entry_every_minute_adds_risk():
    e = _make_entry(minute="*", hour="*")
    s = score_entry(e)
    assert any("every minute" in n for n in s.notes)


def test_score_entry_special_schedule_low_complexity():
    e = _make_entry()
    object.__setattr__(e, "raw_schedule", "@daily")
    s = score_entry(e)
    assert s.complexity == 1
    assert any("macro" in n for n in s.notes)


def test_score_entries_sorted_descending():
    low = _make_entry(command="/bin/true")
    high = _make_entry(minute="*", hour="*", command="sudo rm -rf /tmp")
    result = score_entries([low, high])
    assert result[0].total >= result[1].total


def test_score_entries_returns_all():
    entries = [_make_entry() for _ in range(5)]
    result = score_entries(entries)
    assert len(result) == 5


def test_entry_score_as_dict_keys():
    e = _make_entry()
    s = score_entry(e)
    d = s.as_dict()
    for key in ("command", "schedule", "complexity", "risk", "total", "notes"):
        assert key in d
