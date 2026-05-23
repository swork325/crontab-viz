"""Tests for crontab_viz.linter."""
from __future__ import annotations

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.linter import (
    LintIssue,
    LintResult,
    lint_entries,
    render_lint_report,
)


def _make_entry(
    minute="0",
    hour="*",
    dom="*",
    month="*",
    dow="*",
    command="/usr/bin/backup.sh",
    comment="",
    special=None,
    valid=True,
) -> CronEntry:
    e = CronEntry.__new__(CronEntry)
    object.__setattr__(e, "minute", minute)
    object.__setattr__(e, "hour", hour)
    object.__setattr__(e, "dom", dom)
    object.__setattr__(e, "month", month)
    object.__setattr__(e, "dow", dow)
    object.__setattr__(e, "command", command)
    object.__setattr__(e, "comment", comment)
    object.__setattr__(e, "special", special)
    object.__setattr__(e, "is_valid", valid)
    return e


def test_lint_empty_list_returns_no_issues():
    result = lint_entries([])
    assert not result.has_issues


def test_lint_invalid_entry_produces_error():
    entry = _make_entry(valid=False)
    result = lint_entries([entry])
    assert len(result.errors) == 1
    assert "Invalid cron expression" in result.errors[0].message


def test_lint_missing_command_produces_error():
    entry = _make_entry(command="")
    result = lint_entries([entry])
    assert any("Missing command" in i.message for i in result.errors)


def test_lint_every_minute_wildcard_produces_warning():
    entry = _make_entry(minute="*", hour="*", dom="*", month="*", dow="*",
                        command="/usr/bin/check")
    result = lint_entries([entry])
    assert any("every minute" in i.message for i in result.warnings)


def test_lint_bare_command_produces_warning():
    entry = _make_entry(command="backup")  # no slash or dot
    result = lint_entries([entry])
    assert any("absolute path" in i.message for i in result.warnings)


def test_lint_absolute_path_command_no_path_warning():
    entry = _make_entry(command="/usr/bin/backup.sh")
    result = lint_entries([entry])
    assert not any("absolute path" in i.message for i in result.warnings)


def test_lint_every_minute_within_hour_produces_info():
    entry = _make_entry(minute="*", hour="3", command="/bin/run.sh")
    result = lint_entries([entry])
    assert any(i.severity == "info" for i in result.issues)


def test_lint_result_summary_format():
    entry = _make_entry(valid=False)
    result = lint_entries([entry])
    summary = result.summary()
    assert "error" in summary
    assert "warning" in summary


def test_render_lint_report_no_issues():
    result = LintResult()
    report = render_lint_report(result)
    assert "No issues found" in report


def test_render_lint_report_with_issues():
    entry = _make_entry(valid=False)
    result = lint_entries([entry])
    report = render_lint_report(result)
    assert "ERROR" in report
    assert "Invalid cron expression" in report


def test_lint_issue_str_contains_command():
    entry = _make_entry(command="/usr/bin/test.sh")
    issue = LintIssue(entry, "warning", "some warning")
    assert "/usr/bin/test.sh" in str(issue)
    assert "WARNING" in str(issue)
