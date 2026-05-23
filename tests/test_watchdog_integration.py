"""Integration tests for the watchdog module using real temp files."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import List

import pytest

from crontab_viz.watchdog import WatchEvent, watch_file


LINE_A = b"* * * * * /bin/true  # job-a\n"
LINE_B = b"0 * * * * /bin/backup  # job-b\n"


def test_integration_detects_initial_file(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(LINE_A)
    events: List[WatchEvent] = []
    watch_file(str(f), events.append, interval=0, max_iterations=1)
    assert len(events) == 1
    assert events[0].previous_hash is None
    assert events[0].current_hash == hashlib.md5(LINE_A).hexdigest()


def test_integration_entries_loaded_from_real_file(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(LINE_A)
    events: List[WatchEvent] = []
    watch_file(str(f), events.append, interval=0, max_iterations=1)
    assert len(events[0].entries) >= 1
    assert any(e.command == "/bin/true" for e in events[0].entries)


def test_integration_no_event_for_unchanged_file(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(LINE_A)
    events: List[WatchEvent] = []
    # First iteration fires; second should not because file is unchanged.
    watch_file(str(f), events.append, interval=0, max_iterations=2)
    assert len(events) == 1


def test_integration_detects_content_change(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(LINE_A)
    events: List[WatchEvent] = []
    call_count = [0]

    def callback(ev: WatchEvent) -> None:
        events.append(ev)
        # After first event, overwrite the file to simulate a change.
        if call_count[0] == 0:
            f.write_bytes(LINE_B)
        call_count[0] += 1

    watch_file(str(f), callback, interval=0, max_iterations=2)
    assert len(events) == 2
    assert events[1].previous_hash == hashlib.md5(LINE_A).hexdigest()
    assert events[1].current_hash == hashlib.md5(LINE_B).hexdigest()


def test_integration_missing_file_produces_no_events() -> None:
    events: List[WatchEvent] = []
    watch_file("/nonexistent/path/crontab", events.append, interval=0, max_iterations=3)
    assert events == []
