"""Tests for crontab_viz.filter module."""
from __future__ import annotations

import pytest

from crontab_viz.filter import FilterCriteria, filter_entries, search_entries
from crontab_viz.parser import CronEntry


def _make_entry(
    command: str = "echo hello",
    comment: str = "",
    is_valid: bool = True,
    raw: str = "* * * * * echo hello",
) -> CronEntry:
    entry = CronEntry.__new__(CronEntry)
    object.__setattr__(entry, "raw", raw)
    object.__setattr__(entry, "minute", "*")
    object.__setattr__(entry, "hour", "*")
    object.__setattr__(entry, "dom", "*")
    object.__setattr__(entry, "month", "*")
    object.__setattr__(entry, "dow", "*")
    object.__setattr__(entry, "command", command)
    object.__setattr__(entry, "comment", comment)
    object.__setattr__(entry, "is_valid", is_valid)
    return entry


def test_filter_only_valid_removes_invalid():
    entries = [_make_entry(is_valid=True), _make_entry(is_valid=False)]
    result = filter_entries(entries, FilterCriteria(only_valid=True))
    assert len(result) == 1
    assert result[0].is_valid is True


def test_filter_command_pattern_substring():
    entries = [
        _make_entry(command="/usr/bin/backup.sh"),
        _make_entry(command="echo hello"),
    ]
    result = filter_entries(entries, FilterCriteria(command_pattern="backup"))
    assert len(result) == 1
    assert "backup" in result[0].command


def test_filter_command_pattern_regex():
    entries = [
        _make_entry(command="run_job_1"),
        _make_entry(command="run_job_2"),
        _make_entry(command="cleanup"),
    ]
    result = filter_entries(entries, FilterCriteria(command_pattern=r"run_job_\d"))
    assert len(result) == 2


def test_filter_comment_pattern():
    entries = [
        _make_entry(comment="# daily backup"),
        _make_entry(comment="# health check"),
    ]
    result = filter_entries(entries, FilterCriteria(comment_pattern="backup"))
    assert len(result) == 1


def test_filter_tags_match_any():
    entries = [
        _make_entry(comment="# tag:critical maintenance"),
        _make_entry(comment="# routine check"),
        _make_entry(comment="# tag:critical backup"),
    ]
    result = filter_entries(entries, FilterCriteria(tags=["critical"]))
    assert len(result) == 2


def test_filter_no_criteria_returns_all():
    entries = [_make_entry() for _ in range(5)]
    result = filter_entries(entries, FilterCriteria())
    assert len(result) == 5


def test_filter_combined_criteria():
    entries = [
        _make_entry(command="backup.sh", is_valid=True),
        _make_entry(command="backup.sh", is_valid=False),
        _make_entry(command="echo hi", is_valid=True),
    ]
    result = filter_entries(
        entries, FilterCriteria(command_pattern="backup", only_valid=True)
    )
    assert len(result) == 1
    assert result[0].is_valid is True


def test_search_entries_by_command():
    entries = [
        _make_entry(command="/opt/scripts/deploy.sh"),
        _make_entry(command="echo hello"),
    ]
    result = search_entries(entries, "deploy")
    assert len(result) == 1


def test_search_entries_no_duplicates():
    """An entry matching both command and comment should appear only once."""
    entry = _make_entry(command="backup.sh", comment="# backup job")
    result = search_entries([entry], "backup")
    assert len(result) == 1


def test_search_entries_empty_query_returns_all():
    entries = [_make_entry() for _ in range(3)]
    result = search_entries(entries, "")
    assert len(result) == 3
