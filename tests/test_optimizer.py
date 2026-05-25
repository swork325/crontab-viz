"""Tests for crontab_viz.optimizer."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from crontab_viz.optimizer import (
    OptimizationSuggestion,
    optimize_entries,
    optimize_entry,
)
from crontab_viz.parser import CronEntry


def _make_entry(
    minute="*", hour="*", dom="*", month="*", dow="*",
    command="/bin/cmd", comment="", special=None, valid=True,
) -> CronEntry:
    entry = CronEntry.__new__(CronEntry)
    object.__setattr__(entry, "minute", minute)
    object.__setattr__(entry, "hour", hour)
    object.__setattr__(entry, "dom", dom)
    object.__setattr__(entry, "month", month)
    object.__setattr__(entry, "dow", dow)
    object.__setattr__(entry, "command", command)
    object.__setattr__(entry, "comment", comment)
    object.__setattr__(entry, "special", special)
    object.__setattr__(entry, "is_valid", valid)
    return entry


def _std(**kwargs) -> CronEntry:
    defaults = dict(minute="*", hour="*", dom="*", month="*", dow="*",
                    command="/bin/cmd", comment="", special=None, valid=True)
    defaults.update(kwargs)
    return _make_entry(**defaults)


class TestOptimizeEntry:
    def test_invalid_entry_returns_no_suggestions(self):
        entry = _std(valid=False)
        assert optimize_entry(entry) == []

    def test_daily_pattern_suggests_at_daily(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        assert len(suggestions) == 1
        assert suggestions[0].suggested_schedule == "@daily"

    def test_hourly_pattern_suggests_at_hourly(self):
        entry = _std(minute="0", hour="*", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        assert any(s.suggested_schedule == "@hourly" for s in suggestions)

    def test_monthly_pattern_suggests_at_monthly(self):
        entry = _std(minute="0", hour="0", dom="1", month="*", dow="*")
        suggestions = optimize_entry(entry)
        assert any(s.suggested_schedule == "@monthly" for s in suggestions)

    def test_weekly_pattern_suggests_at_weekly(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="0")
        suggestions = optimize_entry(entry)
        assert any(s.suggested_schedule == "@weekly" for s in suggestions)

    def test_wildcard_step_one_suggests_simplification(self):
        entry = _std(minute="*/1")
        suggestions = optimize_entry(entry)
        assert len(suggestions) == 1
        assert "*/1" in suggestions[0].original_schedule
        assert "*/1" not in suggestions[0].suggested_schedule

    def test_special_entry_skips_redundant_wildcard_check(self):
        entry = _make_entry(special="@daily", valid=True)
        suggestions = optimize_entry(entry)
        assert suggestions == []

    def test_suggestion_str_contains_command(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*",
                     command="/usr/bin/backup")
        s = optimize_entry(entry)[0]
        assert "/usr/bin/backup" in str(s)

    def test_suggestion_str_contains_reason(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*")
        s = optimize_entry(entry)[0]
        assert s.reason in str(s)


class TestOptimizeEntries:
    def test_empty_list_returns_empty(self):
        assert optimize_entries([]) == []

    def test_aggregates_suggestions_from_multiple_entries(self):
        entries = [
            _std(minute="0", hour="0", dom="*", month="*", dow="*"),
            _std(minute="0", hour="*", dom="*", month="*", dow="*"),
        ]
        suggestions = optimize_entries(entries)
        assert len(suggestions) == 2

    def test_no_suggestions_for_non_optimizable_entries(self):
        entries = [_std(minute="5", hour="3", dom="*", month="*", dow="*")]
        assert optimize_entries(entries) == []
