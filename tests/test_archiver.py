"""Tests for crontab_viz.archiver."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from crontab_viz.archiver import (
    CrontabSnapshot,
    create_snapshot,
    list_snapshots,
    load_snapshot,
    restore_entries,
    save_snapshot,
)
from crontab_viz.parser import CronEntry


def _make_entry(schedule: str = "* * * * *", command: str = "echo hi") -> CronEntry:
    raw = f"{schedule} {command}"
    return CronEntry(schedule=schedule, command=command, comment="", raw=raw)


# --- create_snapshot ---

def test_create_snapshot_sets_source():
    entries = [_make_entry()]
    snap = create_snapshot(entries, source="/etc/crontab")
    assert snap.source == "/etc/crontab"


def test_create_snapshot_entry_count():
    entries = [_make_entry(), _make_entry(command="backup.sh")]
    snap = create_snapshot(entries, source="test")
    assert snap.entry_count == 2


def test_create_snapshot_captured_at_is_iso():
    snap = create_snapshot([], source="test")
    # Should parse without error
    from datetime import datetime
    dt = datetime.fromisoformat(snap.captured_at)
    assert dt is not None


def test_create_snapshot_entries_have_expected_keys():
    entry = _make_entry(schedule="0 * * * *", command="/usr/bin/run")
    snap = create_snapshot([entry], source="test")
    keys = snap.entries[0].keys()
    assert "schedule" in keys
    assert "command" in keys
    assert "is_valid" in keys


# --- save_snapshot / load_snapshot ---

def test_save_and_load_snapshot_roundtrip():
    entries = [_make_entry(schedule="5 4 * * *", command="cleanup")]
    snap = create_snapshot(entries, source="user")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "snap.json")
        save_snapshot(snap, path)
        loaded = load_snapshot(path)
    assert loaded.source == snap.source
    assert loaded.entry_count == snap.entry_count
    assert loaded.entries[0]["command"] == "cleanup"


def test_save_snapshot_creates_valid_json():
    snap = create_snapshot([], source="empty")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "snap.json")
        save_snapshot(snap, path)
        with open(path) as fh:
            data = json.load(fh)
    assert data["source"] == "empty"
    assert "captured_at" in data


def test_load_snapshot_raises_on_missing_file():
    """load_snapshot should raise FileNotFoundError for a non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_snapshot("/nonexistent/path/snap.json")


# --- restore_entries ---

def test_restore_entries_returns_cron_entries():
    entries = [_make_entry(schedule="0 0 * * *", command="nightly")]
    snap = create_snapshot(entries, source="test")
    restored = restore_entries(snap)
    assert len(restored) == 1
    assert restored[0].command == "nightly"


def test_restore_entries_empty_snapshot():
    snap = CrontabSnapshot(source="x", captured_at="2024-01-01T00:00:00+00:00", entries=[])
    assert restore_entries(snap) == []


# --- list_snapshots ---

def test_list_snapshots_returns_sorted_paths():
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ["c.json", "a.json", "b.json"]:
