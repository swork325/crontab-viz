"""Tests for crontab_viz.validator."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from crontab_viz.parser import CronEntry
from crontab_viz.validator import (
    ValidationIssue,
    ValidationReport,
    validate_entries,
)


def _make_entry(schedule: str, command: str, valid: bool = True) -> CronEntry:
    entry = CronEntry.__new__(CronEntry)
    entry.schedule = schedule
    entry.command = command
    entry.comment = ""
    entry.is_valid = valid
    entry.fields = {}
    return entry


def test_validate_empty_list_returns_clean_report():
    report = validate_entries([])
    assert report.is_clean
    assert report.issues == []


def test_validate_invalid_entry_produces_error():
    entry = _make_entry("bad", "cmd", valid=False)
    report = validate_entries([entry])
    assert not report.is_clean
    assert any(i.severity == "error" for i in report.issues)


def test_validate_every_minute_produces_warning():
    entry = _make_entry("* * * * *", "/usr/bin/cmd")
    report = validate_entries([entry])
    assert any(i.severity == "warning" for i in report.issues)
    assert report.is_clean  # warning is not an error


def test_validate_empty_command_produces_error():
    entry = _make_entry("0 * * * *", "")
    report = validate_entries([entry])
    assert not report.is_clean
    assert any("empty" in i.message.lower() for i in report.issues)


def test_validate_unknown_special_schedule_produces_error():
    entry = _make_entry("@unknown", "/usr/bin/cmd")
    report = validate_entries([entry])
    assert not report.is_clean
    assert any("Unknown special" in i.message for i in report.issues)


def test_validate_known_special_schedule_ok():
    entry = _make_entry("@daily", "/usr/bin/backup")
    report = validate_entries([entry])
    assert report.is_clean


def test_validate_relative_command_produces_info():
    entry = _make_entry("0 1 * * *", "myscript.sh")
    report = validate_entries([entry])
    assert any(i.severity == "info" for i in report.issues)


def test_validation_report_as_dict_structure():
    entry = _make_entry("* * * * *", "/usr/bin/cmd")
    report = validate_entries([entry])
    d = report.as_dict()
    assert "total" in d
    assert "errors" in d
    assert "warnings" in d
    assert "issues" in d
    assert isinstance(d["issues"], list)


def test_validation_issue_str_contains_severity():
    entry = _make_entry("bad", "cmd", valid=False)
    issue = ValidationIssue(entry, "error", "some problem")
    assert "ERROR" in str(issue)
    assert "some problem" in str(issue)


def test_validate_multiple_entries_aggregates_issues():
    entries = [
        _make_entry("0 * * * *", "/usr/bin/a"),
        _make_entry("* * * * *", "/usr/bin/b"),
        _make_entry("bad", "c", valid=False),
    ]
    report = validate_entries(entries)
    assert len(report.issues) >= 2  # at least warning + error
    assert not report.is_clean
