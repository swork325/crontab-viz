"""Tests for crontab_viz.tagger."""
from __future__ import annotations

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.tagger import (
    TaggedEntry,
    filter_by_tag,
    tag_entries,
    tag_entry,
)


def _make_entry(
    schedule: str = "* * * * *",
    command: str = "echo hello",
    comment: str = "",
) -> CronEntry:
    return CronEntry(schedule=schedule, command=command, comment=comment)


# ---------------------------------------------------------------------------
# TaggedEntry
# ---------------------------------------------------------------------------

def test_tagged_entry_has_tag_case_insensitive():
    entry = _make_entry()
    te = TaggedEntry(entry=entry, tags=["Backup", "OPS"])
    assert te.has_tag("backup")
    assert te.has_tag("ops")
    assert not te.has_tag("deploy")


# ---------------------------------------------------------------------------
# tag_entry – auto-tagging
# ---------------------------------------------------------------------------

def test_tag_entry_standard_schedule_gets_standard_tag():
    te = tag_entry(_make_entry(schedule="0 * * * *", command="echo hi"))
    assert te.has_tag("standard")


def test_tag_entry_special_schedule_gets_special_tag():
    te = tag_entry(_make_entry(schedule="@daily", command="echo hi"))
    assert te.has_tag("special")


def test_tag_entry_invalid_entry_gets_invalid_tag():
    te = tag_entry(_make_entry(schedule="bad schedule", command="echo hi"))
    assert te.has_tag("invalid")


def test_tag_entry_keyword_in_command():
    te = tag_entry(_make_entry(command="/usr/bin/backup.sh"))
    assert te.has_tag("backup")


def test_tag_entry_keyword_in_comment():
    te = tag_entry(_make_entry(command="run.sh", comment="sync files"))
    assert te.has_tag("sync")


def test_tag_entry_extra_tags_included():
    te = tag_entry(_make_entry(), extra_tags=["production", "critical"])
    assert te.has_tag("production")
    assert te.has_tag("critical")


def test_tag_entry_no_auto_skips_auto_tags():
    te = tag_entry(_make_entry(command="backup.sh"), auto=False)
    assert not te.has_tag("backup")
    assert not te.has_tag("standard")


def test_tag_entry_no_duplicate_tags():
    te = tag_entry(
        _make_entry(command="backup.sh"),
        extra_tags=["backup"],
        auto=True,
    )
    assert te.tags.count("backup") == 1


# ---------------------------------------------------------------------------
# tag_entries
# ---------------------------------------------------------------------------

def test_tag_entries_returns_correct_count():
    entries = [_make_entry() for _ in range(5)]
    result = tag_entries(entries)
    assert len(result) == 5


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

def test_filter_by_tag_returns_matching_entries():
    entries = [
        _make_entry(command="backup.sh"),
        _make_entry(command="echo hello"),
        _make_entry(command="run_backup.py"),
    ]
    tagged = tag_entries(entries)
    result = filter_by_tag(tagged, "backup")
    assert len(result) == 2


def test_filter_by_tag_empty_when_none_match():
    entries = [_make_entry(command="echo hello")]
    tagged = tag_entries(entries)
    result = filter_by_tag(tagged, "deploy")
    assert result == []
