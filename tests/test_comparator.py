"""Tests for crontab_viz.comparator."""
import pytest
from crontab_viz.parser import CronEntry
from crontab_viz.comparator import compare_entries, ComparisonReport


def _make_entry(schedule: str, command: str, valid: bool = True) -> CronEntry:
    entry = CronEntry(
        raw_line=f"{schedule} {command}",
        schedule_str=schedule,
        command=command,
        comment="",
    )
    object.__setattr__(entry, "is_valid", valid)
    return entry


def _std(schedule: str, command: str) -> CronEntry:
    """Create a valid standard CronEntry."""
    return _make_entry(schedule, command, valid=True)


# ---------------------------------------------------------------------------
# compare_entries returns ComparisonReport
# ---------------------------------------------------------------------------

def test_compare_empty_lists_returns_empty_report():
    report = compare_entries([], [])
    assert isinstance(report, ComparisonReport)
    assert report.rows == []


def test_compare_identical_entries_marked_same():
    a = [_std("0 * * * *", "/bin/foo")]
    b = [_std("0 * * * *", "/bin/foo")]
    report = compare_entries(a, b)
    assert len(report.same) == 1
    assert report.same[0].status == "same"


def test_compare_detects_schedule_change():
    a = [_std("0 * * * *", "/bin/foo")]
    b = [_std("30 * * * *", "/bin/foo")]
    report = compare_entries(a, b)
    assert len(report.changed) == 1
    row = report.changed[0]
    assert row.schedule_a == "0 * * * *"
    assert row.schedule_b == "30 * * * *"
    assert row.status == "changed"


def test_compare_detects_entry_only_in_a():
    a = [_std("0 * * * *", "/bin/foo")]
    b: list = []
    report = compare_entries(a, b)
    assert len(report.only_in_a) == 1
    assert report.only_in_a[0].schedule_b == "—"
    assert report.only_in_a[0].next_run_b == "—"


def test_compare_detects_entry_only_in_b():
    a: list = []
    b = [_std("0 * * * *", "/bin/bar")]
    report = compare_entries(a, b)
    assert len(report.only_in_b) == 1
    assert report.only_in_b[0].schedule_a == "—"
    assert report.only_in_b[0].next_run_a == "—"


def test_compare_mixed_entries():
    a = [
        _std("0 * * * *", "/bin/foo"),
        _std("5 * * * *", "/bin/baz"),
    ]
    b = [
        _std("0 * * * *", "/bin/foo"),
        _std("10 * * * *", "/bin/baz"),
        _std("@daily", "/bin/new"),
    ]
    report = compare_entries(a, b)
    assert len(report.same) == 1
    assert len(report.changed) == 1
    assert len(report.only_in_b) == 1
    assert len(report.only_in_a) == 0


def test_summary_string_format():
    a = [_std("0 * * * *", "/bin/foo")]
    b = [_std("5 * * * *", "/bin/foo")]
    report = compare_entries(a, b)
    summary = report.summary()
    assert "same=0" in summary
    assert "changed=1" in summary
    assert "only_a=0" in summary
    assert "only_b=0" in summary


def test_invalid_entry_next_run_label_is_invalid():
    a = [_make_entry("not-valid", "/bin/bad", valid=False)]
    b: list = []
    report = compare_entries(a, b)
    assert report.only_in_a[0].next_run_a == "invalid"


def test_command_used_as_identity_key():
    """Two entries with different schedules but same command → treated as one pair."""
    a = [_std("0 1 * * *", "/usr/bin/backup")]
    b = [_std("0 2 * * *", "/usr/bin/backup")]
    report = compare_entries(a, b)
    assert len(report.rows) == 1
    assert report.rows[0].status == "changed"
