"""Tests for crontab_viz.differ."""

from __future__ import annotations

import pytest

from crontab_viz.differ import CrontabDiff, diff_entries
from crontab_viz.parser import CronEntry


def _make_entry(
    command: str = "/usr/bin/true",
    minute: str = "0",
    hour: str = "*",
    dom: str = "*",
    month: str = "*",
    dow: str = "*",
    special: str | None = None,
    valid: bool = True,
) -> CronEntry:
    return CronEntry(
        raw=f"{minute} {hour} {dom} {month} {dow} {command}",
        command=command,
        comment="",
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        special=special,
        valid=valid,
    )


def test_diff_all_same_returns_unchanged():
    entries = [_make_entry("/bin/a"), _make_entry("/bin/b")]
    result = diff_entries(entries, entries)
    assert result.unchanged == entries
    assert result.added == []
    assert result.removed == []
    assert result.changed == []


def test_diff_detects_added_entry():
    old = [_make_entry("/bin/a")]
    new = [_make_entry("/bin/a"), _make_entry("/bin/b")]
    result = diff_entries(old, new)
    assert len(result.added) == 1
    assert result.added[0].command == "/bin/b"
    assert result.removed == []


def test_diff_detects_removed_entry():
    old = [_make_entry("/bin/a"), _make_entry("/bin/b")]
    new = [_make_entry("/bin/a")]
    result = diff_entries(old, new)
    assert len(result.removed) == 1
    assert result.removed[0].command == "/bin/b"
    assert result.added == []


def test_diff_detects_schedule_change():
    old = [_make_entry("/bin/a", minute="0", hour="1")]
    new = [_make_entry("/bin/a", minute="30", hour="2")]
    result = diff_entries(old, new)
    assert len(result.changed) == 1
    old_e, new_e = result.changed[0]
    assert old_e.hour == "1"
    assert new_e.hour == "2"


def test_diff_special_schedule_change():
    old_entry = _make_entry("/bin/a", special="@daily")
    new_entry = _make_entry("/bin/a", special="@hourly")
    result = diff_entries([old_entry], [new_entry])
    assert len(result.changed) == 1


def test_diff_no_changes_has_changes_false():
    entries = [_make_entry("/bin/a")]
    result = diff_entries(entries, entries)
    assert result.has_changes is False


def test_diff_with_addition_has_changes_true():
    old = [_make_entry("/bin/a")]
    new = [_make_entry("/bin/a"), _make_entry("/bin/b")]
    result = diff_entries(old, new)
    assert result.has_changes is True


def test_summary_no_changes():
    entries = [_make_entry("/bin/a")]
    result = diff_entries(entries, entries)
    assert result.summary() == "No changes detected."


def test_summary_with_changes():
    old = [_make_entry("/bin/a"), _make_entry("/bin/b")]
    new = [
        _make_entry("/bin/a", minute="5"),
        _make_entry("/bin/c"),
    ]
    result = diff_entries(old, new)
    summary = result.summary()
    assert "+" in summary or "-" in summary or "~" in summary


def test_diff_empty_lists():
    result = diff_entries([], [])
    assert result.added == []
    assert result.removed == []
    assert result.changed == []
    assert result.unchanged == []
