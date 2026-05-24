"""Tests for crontab_viz.snapshotter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.snapshotter import (
    SnapshotSession,
    run_snapshots,
    take_snapshot,
)


def _make_entry(schedule: str = "* * * * *", command: str = "echo hi") -> CronEntry:
    return CronEntry(raw=f"{schedule} {command}", schedule=schedule, command=command)


# ---------------------------------------------------------------------------
# take_snapshot
# ---------------------------------------------------------------------------

def test_take_snapshot_returns_snapshot():
    entries = [_make_entry()]
    snap = take_snapshot(entries, source="test")
    assert snap is not None


def test_take_snapshot_source_stored():
    entries = [_make_entry()]
    snap = take_snapshot(entries, source="my-source")
    assert snap.source == "my-source"


def test_take_snapshot_entry_count():
    entries = [_make_entry(), _make_entry(command="echo bye")]
    snap = take_snapshot(entries, source="s")
    assert snap.entry_count == 2


def test_take_snapshot_label_stored_in_metadata():
    entries = [_make_entry()]
    snap = take_snapshot(entries, source="s", label="my-label")
    assert snap.metadata.get("label") == "my-label"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# SnapshotSession
# ---------------------------------------------------------------------------

def test_session_starts_empty():
    session = SnapshotSession(source="x")
    assert session.count == 0
    assert session.latest is None


def test_session_as_dict_has_source():
    session = SnapshotSession(source="src")
    d = session.as_dict()
    assert d["source"] == "src"


def test_session_as_dict_snapshot_count():
    session = SnapshotSession(source="src")
    snap = take_snapshot([_make_entry()], source="src")
    session.snapshots.append(snap)
    assert session.as_dict()["snapshot_count"] == 1


def test_session_latest_returns_last_snapshot():
    session = SnapshotSession(source="src")
    s1 = take_snapshot([_make_entry()], source="src", label="a")
    s2 = take_snapshot([_make_entry()], source="src", label="b")
    session.snapshots.extend([s1, s2])
    assert session.latest is s2


# ---------------------------------------------------------------------------
# run_snapshots
# ---------------------------------------------------------------------------

def test_run_snapshots_returns_session():
    with patch("crontab_viz.snapshotter.time.sleep"):
        session = run_snapshots(
            load_entries=lambda: [_make_entry()],
            source="test",
            interval_seconds=1,
            max_snapshots=2,
        )
    assert isinstance(session, SnapshotSession)


def test_run_snapshots_correct_count():
    with patch("crontab_viz.snapshotter.time.sleep"):
        session = run_snapshots(
            load_entries=lambda: [_make_entry()],
            source="test",
            interval_seconds=0,
            max_snapshots=3,
        )
    assert session.count == 3


def test_run_snapshots_callback_called():
    calls: List[object] = []
    with patch("crontab_viz.snapshotter.time.sleep"):
        run_snapshots(
            load_entries=lambda: [_make_entry()],
            source="test",
            interval_seconds=0,
            max_snapshots=2,
            on_snapshot=lambda snap: calls.append(snap),
        )
    assert len(calls) == 2


def test_run_snapshots_no_sleep_after_last():
    """sleep should be called N-1 times for N snapshots."""
    with patch("crontab_viz.snapshotter.time.sleep") as mock_sleep:
        run_snapshots(
            load_entries=lambda: [],
            source="s",
            interval_seconds=5,
            max_snapshots=4,
        )
    assert mock_sleep.call_count == 3
