"""Tests for crontab_viz.formatter."""

from datetime import datetime

import pytest

from crontab_viz.formatter import format_entries, format_entry, render_table, FormattedRow
from crontab_viz.parser import CronEntry, parse_crontab_line


REFERENCE = datetime(2024, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------------------
# format_entry
# ---------------------------------------------------------------------------

def test_format_entry_valid():
    entry = parse_crontab_line("* * * * * echo hello")
    row = format_entry(entry, reference=REFERENCE)
    assert row.is_valid is True
    assert row.command == "echo hello"
    assert row.countdown_str == "1m"
    assert row.next_run_str == "2024-01-01 00:01"


def test_format_entry_invalid():
    entry = CronEntry(raw="bad", command="", fields=(), is_valid=False)
    row = format_entry(entry, reference=REFERENCE)
    assert row.is_valid is False
    assert row.schedule == "<invalid>"
    assert row.next_run_str == "N/A"
    assert row.countdown_str == "N/A"


def test_format_entry_specific_schedule():
    entry = parse_crontab_line("0 6 * * * morning-job")
    row = format_entry(entry, reference=REFERENCE)
    assert row.next_run_str == "2024-01-01 06:00"
    assert "h" in row.countdown_str  # several hours away


# ---------------------------------------------------------------------------
# render_table
# ---------------------------------------------------------------------------

def test_render_table_contains_header():
    rows = []
    table = render_table(rows)
    assert "SCHEDULE" in table
    assert "NEXT RUN" in table
    assert "IN" in table
    assert "COMMAND" in table


def test_render_table_contains_row_data():
    row = FormattedRow(
        schedule="* * * * *",
        command="echo test",
        next_run_str="2024-01-01 00:01",
        countdown_str="1m",
        is_valid=True,
    )
    table = render_table([row])
    assert "echo test" in table
    assert "2024-01-01 00:01" in table


def test_render_table_invalid_row_prefixed():
    row = FormattedRow(
        schedule="<invalid>",
        command="bad-cmd",
        next_run_str="N/A",
        countdown_str="N/A",
        is_valid=False,
    )
    table = render_table([row])
    assert "! " in table


# ---------------------------------------------------------------------------
# format_entries convenience wrapper
# ---------------------------------------------------------------------------

def test_format_entries_multiple():
    lines = [
        "* * * * * job-one",
        "0 12 * * * job-two",
    ]
    entries = [parse_crontab_line(l) for l in lines]
    table = format_entries(entries, reference=REFERENCE)
    assert "job-one" in table
    assert "job-two" in table
