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
            open(os.path.join(tmpdir, name), "w").close()
        result = list_snapshots(tmpdir)
    basenames = [os.path.basename(p) for p in result]
    assert basenames == ["a.json", "b.json", "c.json"]


def test_list_snapshots_missing_directory_returns_empty():
    assert list_snapshots("/nonexistent/path/xyz") == []


def test_list_snapshots_ignores_non_json_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "snap.json"), "w").close()
        open(os.path.join(tmpdir, "notes.txt"), "w").close()
        result = list_snapshots(tmpdir)
    assert all(p.endswith(".json") for p in result)
    assert len(result) == 1
