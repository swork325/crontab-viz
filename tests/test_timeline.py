"""Unit tests for crontab_viz.timeline."""
from __future__ import annotations

from datetime import datetime

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.timeline import (
    TimelineEvent,
    Timeline,
    build_timeline,
    render_timeline,
)


NOW = datetime(2024, 1, 15, 12, 0, 0)


def _std(minute="0", hour="*", dom="*", month="*", dow="*", command="cmd", comment=""):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, comment=comment,
    )


def _make_entry(**kwargs):
    return _std(**kwargs)


# --- TimelineEvent ---

def test_timeline_event_str_contains_command():
    ev = TimelineEvent(run_at=NOW, command="/bin/backup", comment="", schedule="0 * * * *")
    assert "/bin/backup" in str(ev)


def test_timeline_event_str_contains_timestamp():
    ev = TimelineEvent(run_at=NOW, command="cmd", comment="", schedule="* * * * *")
    assert "2024-01-15 12:00" in str(ev)


def test_timeline_event_str_contains_comment():
    ev = TimelineEvent(run_at=NOW, command="cmd", comment="backup", schedule="0 2 * * *")
    assert "backup" in str(ev)


# --- Timeline ---

def test_timeline_count_empty():
    tl = Timeline()
    assert tl.count == 0


def test_timeline_earliest_none_when_empty():
    tl = Timeline()
    assert tl.earliest() is None


def test_timeline_latest_none_when_empty():
    tl = Timeline()
    assert tl.latest() is None


# --- build_timeline ---

def test_build_timeline_empty_entries_returns_empty():
    tl = build_timeline([], n=3, now=NOW)
    assert tl.count == 0


def test_build_timeline_skips_invalid_entries():
    bad = CronEntry(minute="", hour="", dom="", month="", dow="", command="bad")
    tl = build_timeline([bad], n=3, now=NOW)
    assert tl.count == 0


def test_build_timeline_returns_sorted_events():
    e1 = _std(minute="0", hour="14", command="afternoon")
    e2 = _std(minute="0", hour="2", command="early")
    tl = build_timeline([e1, e2], n=1, now=NOW)
    times = [ev.run_at for ev in tl.events]
    assert times == sorted(times)


def test_build_timeline_n_runs_per_entry():
    entry = _std(minute="0", hour="*", command="hourly")
    tl = build_timeline([entry], n=3, now=NOW)
    assert tl.count == 3


def test_build_timeline_earliest_is_soonest():
    e1 = _std(minute="0", hour="14", command="late")
    e2 = _std(minute="0", hour="13", command="soon")
    tl = build_timeline([e1, e2], n=1, now=NOW)
    assert tl.earliest() is not None
    assert tl.earliest().command == "soon"  # type: ignore[union-attr]


def test_build_timeline_event_command_matches_entry():
    entry = _std(minute="30", hour="*", command="/usr/bin/task")
    tl = build_timeline([entry], n=2, now=NOW)
    for ev in tl.events:
        assert ev.command == "/usr/bin/task"


# --- render_timeline ---

def test_render_timeline_empty_shows_message():
    tl = Timeline()
    out = render_timeline(tl)
    assert "No upcoming" in out


def test_render_timeline_contains_header():
    entry = _std(minute="0", hour="*", command="check")
    tl = build_timeline([entry], n=1, now=NOW)
    out = render_timeline(tl)
    assert "TIME" in out
    assert "COMMAND" in out


def test_render_timeline_contains_command():
    entry = _std(minute="0", hour="*", command="/bin/myapp")
    tl = build_timeline([entry], n=1, now=NOW)
    out = render_timeline(tl)
    assert "/bin/myapp" in out
