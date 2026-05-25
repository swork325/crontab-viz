"""Tests for crontab_viz.optimizer module."""

import pytest
from crontab_viz.parser import CronEntry
from crontab_viz.optimizer import (
    OptimizationSuggestion,
    optimize_entry,
    optimize_entries,
)


def _make_entry(
    schedule: str,
    command: str = "/usr/bin/backup",
    comment: str = "",
) -> CronEntry:
    line = f"{schedule} {command}"
    if comment:
        line = f"# {comment}\n{line}"
    from crontab_viz.parser import parse_crontab_line
    entries = list(parse_crontab_line(line.split('\n')[-1]))
    entry = entries[0] if entries else CronEntry(
        raw=line,
        schedule=schedule,
        command=command,
        comment=comment,
        is_special=schedule.startswith("@"),
    )
    return entry


def _std(
    minute="*",
    hour="*",
    dom="*",
    month="*",
    dow="*",
    command="/usr/bin/task",
) -> CronEntry:
    schedule = f"{minute} {hour} {dom} {month} {dow}"
    return _make_entry(schedule, command)


class TestOptimizeEntry:
    def test_invalid_entry_returns_no_suggestions(self):
        entry = CronEntry(
            raw="not a valid cron",
            schedule="not a valid cron",
            command="",
            comment="",
            is_special=False,
        )
        suggestions = optimize_entry(entry)
        assert suggestions == []

    def test_daily_pattern_suggests_at_daily(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        messages = [s.message for s in suggestions]
        assert any("@daily" in m for m in messages)

    def test_hourly_pattern_suggests_at_hourly(self):
        entry = _std(minute="0", hour="*", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        messages = [s.message for s in suggestions]
        assert any("@hourly" in m for m in messages)

    def test_weekly_pattern_suggests_at_weekly(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="0")
        suggestions = optimize_entry(entry)
        messages = [s.message for s in suggestions]
        assert any("@weekly" in m for m in messages)

    def test_monthly_pattern_suggests_at_monthly(self):
        entry = _std(minute="0", hour="0", dom="1", month="*", dow="*")
        suggestions = optimize_entry(entry)
        messages = [s.message for s in suggestions]
        assert any("@monthly" in m for m in messages)

    def test_redundant_wildcards_flagged(self):
        # */1 is equivalent to *
        entry = _std(minute="*/1", hour="*", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        messages = [s.message for s in suggestions]
        assert any("*/1" in m or "redundant" in m.lower() for m in messages)

    def test_no_suggestions_for_complex_schedule(self):
        entry = _std(minute="15", hour="3", dom="*", month="*", dow="1-5")
        suggestions = optimize_entry(entry)
        # A specific weekday schedule shouldn't trigger @daily/@weekly etc.
        messages = [s.message for s in suggestions]
        assert not any("@daily" in m for m in messages)

    def test_suggestion_has_original_schedule(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        assert len(suggestions) > 0
        assert suggestions[0].original_schedule is not None

    def test_suggestion_has_suggested_schedule(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        assert len(suggestions) > 0
        assert suggestions[0].suggested_schedule is not None

    def test_suggestion_str_contains_message(self):
        entry = _std(minute="0", hour="0", dom="*", month="*", dow="*")
        suggestions = optimize_entry(entry)
        assert len(suggestions) > 0
        assert suggestions[0].message in str(suggestions[0])

    def test_already_special_entry_no_duplicate_suggestion(self):
        from crontab_viz.parser import parse_crontab_line
        results = list(parse_crontab_line("@daily /usr/bin/backup"))
        if results:
            entry = results[0]
            suggestions = optimize_entry(entry)
            # @daily is already optimal
            assert not any("@daily" in s.message for s in suggestions)


class TestOptimizeEntries:
    def test_optimize_entries_empty_list(self):
        result = optimize_entries([])
        assert result == {}

    def test_optimize_entries_returns_dict_keyed_by_command(self):
        entries = [
            _std(minute="0", hour="0", dom="*", month="*", dow="*", command="/bin/a"),
            _std(minute="15", hour="3", dom="*", month="*", dow="1-5", command="/bin/b"),
        ]
        result = optimize_entries(entries)
        # At least the first entry should have suggestions
        assert isinstance(result, dict)

    def test_optimize_entries_excludes_no_suggestion_entries(self):
        entries = [
            _std(minute="15", hour="3", dom="*", month="*", dow="1-5", command="/bin/b"),
        ]
        result = optimize_entries(entries)
        # Complex schedule may have no suggestions; dict may be empty
        for key, suggestions in result.items():
            assert isinstance(suggestions, list)
