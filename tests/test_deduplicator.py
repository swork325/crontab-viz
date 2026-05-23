"""Tests for crontab_viz.deduplicator."""
from __future__ import annotations

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.deduplicator import (
    DeduplicationResult,
    deduplicate,
    find_duplicates,
    _entry_key,
)


def _make_entry(raw: str, command: str = "", comment: str = "") -> CronEntry:
    entry = CronEntry(raw=raw, command=command, comment=comment)
    return entry


def _make_standard(schedule: str, command: str) -> CronEntry:
    """Build a valid-looking entry from a 5-field schedule string."""
    raw = f"{schedule} {command}"
    entry = CronEntry(raw=raw, command=command, comment="")
    # Manually set fields so _entry_key works without full parsing
    object.__setattr__(entry, "fields", schedule.split())
    return entry


# ---------------------------------------------------------------------------
# _entry_key
# ---------------------------------------------------------------------------

def test_entry_key_uses_fields_and_command():
    entry = _make_standard("0 5 * * *", "/usr/bin/backup")
    key = _entry_key(entry)
    assert key == ("0 5 * * *", "/usr/bin/backup")


def test_entry_key_strips_command_whitespace():
    entry = _make_standard("*/15 * * * *", "  /bin/check  ")
    key = _entry_key(entry)
    assert key[1] == "/bin/check"


# ---------------------------------------------------------------------------
# deduplicate
# ---------------------------------------------------------------------------

def test_deduplicate_empty_list():
    result = deduplicate([])
    assert result.unique == []
    assert result.duplicates == []
    assert result.duplicate_count == 0


def test_deduplicate_no_duplicates():
    a = _make_standard("0 1 * * *", "/bin/a")
    b = _make_standard("0 2 * * *", "/bin/b")
    result = deduplicate([a, b])
    assert len(result.unique) == 2
    assert result.duplicates == []


def test_deduplicate_keeps_first_occurrence():
    a = _make_standard("0 1 * * *", "/bin/a")
    b = _make_standard("0 1 * * *", "/bin/a")
    result = deduplicate([a, b])
    assert result.unique == [a]


def test_deduplicate_reports_duplicate_group():
    a = _make_standard("0 1 * * *", "/bin/a")
    b = _make_standard("0 1 * * *", "/bin/a")
    result = deduplicate([a, b])
    assert len(result.duplicates) == 1
    assert set(result.duplicates[0]) == {a, b}


def test_deduplicate_count():
    a = _make_standard("0 1 * * *", "/bin/a")
    b = _make_standard("0 1 * * *", "/bin/a")
    c = _make_standard("0 1 * * *", "/bin/a")
    result = deduplicate([a, b, c])
    assert result.duplicate_count == 2
    assert result.total_removed == 2


def test_deduplicate_mixed_entries():
    a = _make_standard("0 1 * * *", "/bin/a")
    b = _make_standard("0 1 * * *", "/bin/a")  # dup of a
    c = _make_standard("0 2 * * *", "/bin/c")  # unique
    result = deduplicate([a, b, c])
    assert len(result.unique) == 2
    assert result.duplicate_count == 1


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_find_duplicates_returns_only_dup_groups():
    a = _make_standard("0 1 * * *", "/bin/a")
    b = _make_standard("0 1 * * *", "/bin/a")
    c = _make_standard("0 2 * * *", "/bin/c")
    groups = find_duplicates([a, b, c])
    assert len(groups) == 1
    assert b in groups[0]


def test_find_duplicates_empty_when_no_dups():
    a = _make_standard("0 1 * * *", "/bin/a")
    groups = find_duplicates([a])
    assert groups == []
