"""Tests for crontab_viz.scheduler."""

from datetime import datetime, timedelta

import pytest

from crontab_viz.parser import parse_crontab_line
from crontab_viz.scheduler import (
    countdown,
    format_countdown,
    next_run,
    _field_matches,
)


# ---------------------------------------------------------------------------
# _field_matches
# ---------------------------------------------------------------------------

def test_wildcard_always_matches():
    assert _field_matches(42, "*") is True


def test_exact_value_matches():
    assert _field_matches(5, "5") is True
    assert _field_matches(6, "5") is False


def test_range_matches():
    assert _field_matches(3, "1-5") is True
    assert _field_matches(6, "1-5") is False


def test_step_matches():
    assert _field_matches(0, "*/15") is True
    assert _field_matches(15, "*/15") is True
    assert _field_matches(30, "*/15") is True
    assert _field_matches(7, "*/15") is False


def test_list_matches():
    assert _field_matches(1, "1,3,5") is True
    assert _field_matches(4, "1,3,5") is False


# ---------------------------------------------------------------------------
# next_run
# ---------------------------------------------------------------------------

def test_next_run_every_minute():
    entry = parse_crontab_line("* * * * * echo hi")
    after = datetime(2024, 1, 1, 12, 0, 0)
    nxt = next_run(entry, after=after)
    assert nxt == datetime(2024, 1, 1, 12, 1)


def test_next_run_specific_time():
    entry = parse_crontab_line("30 9 * * * backup")
    after = datetime(2024, 6, 15, 8, 0)
    nxt = next_run(entry, after=after)
    assert nxt == datetime(2024, 6, 15, 9, 30)


def test_next_run_crosses_midnight():
    entry = parse_crontab_line("0 0 * * * midnight-job")
    after = datetime(2024, 3, 10, 23, 0)
    nxt = next_run(entry, after=after)
    assert nxt == datetime(2024, 3, 11, 0, 0)


def test_next_run_invalid_entry_returns_none():
    from crontab_viz.parser import CronEntry
    entry = CronEntry(raw="bad line", command="", fields=(), is_valid=False)
    assert next_run(entry) is None


# ---------------------------------------------------------------------------
# countdown & format_countdown
# ---------------------------------------------------------------------------

def test_countdown_returns_timedelta():
    entry = parse_crontab_line("* * * * * echo")
    after = datetime(2024, 1, 1, 0, 0, 0)
    delta = countdown(entry, after=after)
    assert delta == timedelta(minutes=1)


def test_format_countdown_minutes_only():
    assert format_countdown(timedelta(minutes=45)) == "45m"


def test_format_countdown_hours_and_minutes():
    assert format_countdown(timedelta(hours=2, minutes=5)) == "2h 05m"


def test_format_countdown_none():
    assert format_countdown(None) == "N/A"
