"""Tests for crontab_viz.aliaser."""
from __future__ import annotations

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.aliaser import (
    AliasedEntry,
    _schedule_key,
    resolve_alias,
    alias_entries,
)


def _make_entry(
    minute="*",
    hour="*",
    day="*",
    month="*",
    weekday="*",
    command="/usr/bin/job",
    special=None,
    comment="",
) -> CronEntry:
    raw = f"{minute} {hour} {day} {month} {weekday} {command}"
    if special:
        raw = f"{special} {command}"
    return CronEntry(raw=raw)


# --- _schedule_key ---

def test_schedule_key_standard_fields():
    entry = _make_entry(minute="0", hour="*", day="*", month="*", weekday="*")
    assert _schedule_key(entry) == "0 * * * *"


def test_schedule_key_special_at_daily():
    entry = _make_entry(special="@daily")
    assert _schedule_key(entry) == "@daily"


def test_schedule_key_special_case_insensitive():
    entry = _make_entry(special="@Daily")
    assert _schedule_key(entry) == "@daily"


# --- resolve_alias ---

def test_resolve_alias_known_builtin():
    entry = _make_entry(special="@daily")
    assert resolve_alias(entry) == "Daily job"


def test_resolve_alias_unknown_returns_none():
    entry = _make_entry(minute="7", hour="3", day="*", month="*", weekday="*")
    assert resolve_alias(entry) is None


def test_resolve_alias_custom_overrides_builtin():
    entry = _make_entry(special="@daily")
    custom = {"@daily": "My custom daily"}
    assert resolve_alias(entry, custom_aliases=custom) == "My custom daily"


def test_resolve_alias_custom_only_key():
    entry = _make_entry(minute="7", hour="3", day="*", month="*", weekday="*")
    custom = {"7 3 * * *": "My special job"}
    assert resolve_alias(entry, custom_aliases=custom) == "My special job"


# --- alias_entries ---

def test_alias_entries_returns_only_matched():
    e1 = _make_entry(special="@hourly")
    e2 = _make_entry(minute="7", hour="3", day="*", month="*", weekday="*")
    result = alias_entries([e1, e2])
    assert len(result) == 1
    assert result[0].alias == "Hourly job"


def test_alias_entries_skips_invalid():
    invalid = CronEntry(raw="not a valid cron line at all")
    result = alias_entries([invalid])
    assert result == []


def test_alias_entries_custom_flag_true_for_custom():
    entry = _make_entry(minute="*/5", hour="*", day="*", month="*", weekday="*")
    custom = {"*/5 * * * *": "Frequent task"}
    result = alias_entries([entry], custom_aliases=custom)
    assert len(result) == 1
    assert result[0].custom is True


def test_alias_entries_custom_flag_false_for_builtin():
    entry = _make_entry(special="@reboot")
    result = alias_entries([entry])
    assert len(result) == 1
    assert result[0].custom is False


def test_aliased_entry_str_contains_alias_and_command():
    entry = _make_entry(special="@daily", command="/bin/backup")
    ae = AliasedEntry(entry=entry, alias="Daily job", custom=False)
    s = str(ae)
    assert "Daily job" in s
    assert "/bin/backup" in s
    assert "[builtin]" in s


def test_aliased_entry_str_custom_tag():
    entry = _make_entry(minute="0", hour="12", day="*", month="*", weekday="*")
    ae = AliasedEntry(entry=entry, alias="Noon run", custom=True)
    assert "[custom]" in str(ae)
