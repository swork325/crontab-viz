"""Tests for the crontab parser module."""

import pytest
from crontab_viz.parser import parse_crontab_line, parse_crontab, CronEntry


def test_parse_simple_entry():
    line = "0 * * * * /usr/bin/backup.sh"
    entry = parse_crontab_line(line)
    assert entry is not None
    assert entry.schedule == "0 * * * *"
    assert entry.command == "/usr/bin/backup.sh"
    assert entry.is_valid()


def test_parse_entry_with_comment():
    line = "30 6 * * 1 /scripts/weekly.sh #weekly job"
    entry = parse_crontab_line(line)
    assert entry is not None
    assert entry.comment == "weekly job"
    assert entry.command == "/scripts/weekly.sh"


def test_parse_special_at_daily():
    entry = parse_crontab_line("@daily /usr/bin/cleanup")
    assert entry is not None
    assert entry.schedule == "0 0 * * *"
    assert entry.command == "/usr/bin/cleanup"
    assert entry.is_valid()


def test_parse_special_at_hourly():
    entry = parse_crontab_line("@hourly /usr/bin/check")
    assert entry is not None
    assert entry.schedule == "0 * * * *"


def test_skip_comment_lines():
    assert parse_crontab_line("# this is a comment") is None


def test_skip_empty_lines():
    assert parse_crontab_line("") is None
    assert parse_crontab_line("   ") is None


def test_parse_fields():
    entry = parse_crontab_line("5 4 * * 2 /bin/cmd")
    assert entry.fields["minute"] == "5"
    assert entry.fields["hour"] == "4"
    assert entry.fields["day_of_week"] == "2"


def test_parse_crontab_multiline():
    text = """
# System crontab
0 * * * * /usr/bin/job1
@daily /usr/bin/job2
# another comment
30 2 * * 0 /usr/bin/job3
"""
    entries = parse_crontab(text)
    assert len(entries) == 3
    assert entries[0].command == "/usr/bin/job1"
    assert entries[1].command == "/usr/bin/job2"
    assert entries[2].command == "/usr/bin/job3"


def test_invalid_schedule_returns_none():
    entry = parse_crontab_line("not a valid crontab line")
    assert entry is None or not entry.is_valid()
