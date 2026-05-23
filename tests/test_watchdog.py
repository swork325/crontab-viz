"""Tests for crontab_viz.watchdog."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.watchdog import WatchEvent, _file_hash, watch_file
from crontab_viz.parser import CronEntry


CRONTAB_CONTENT = b"* * * * * /usr/bin/true  # health\n"
_HASH = hashlib.md5(CRONTAB_CONTENT).hexdigest()


def _make_entry(schedule: str = "* * * * *", command: str = "/bin/true") -> CronEntry:
    return CronEntry(schedule=schedule, command=command, comment="")


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

def test_file_hash_returns_md5_for_existing_file(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)
    assert _file_hash(str(f)) == _HASH


def test_file_hash_returns_none_for_missing_file() -> None:
    assert _file_hash("/nonexistent/path/crontab") is None


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_stores_fields() -> None:
    entry = _make_entry()
    ev = WatchEvent(path="/etc/crontab", previous_hash=None, current_hash=_HASH, entries=[entry])
    assert ev.path == "/etc/crontab"
    assert ev.previous_hash is None
    assert ev.current_hash == _HASH
    assert ev.entries == [entry]


def test_watch_event_str_contains_path() -> None:
    ev = WatchEvent(path="/etc/crontab", previous_hash=None, current_hash=_HASH, entries=[])
    assert "/etc/crontab" in str(ev)


# ---------------------------------------------------------------------------
# watch_file
# ---------------------------------------------------------------------------

def test_watch_file_calls_callback_on_first_detection(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)
    events: List[WatchEvent] = []

    with patch("crontab_viz.watchdog.load_from_file", return_value=[_make_entry()]):
        watch_file(str(f), events.append, interval=0, max_iterations=1)

    assert len(events) == 1
    assert events[0].path == str(f)
    assert events[0].previous_hash is None


def test_watch_file_does_not_callback_when_unchanged(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)
    events: List[WatchEvent] = []

    with patch("crontab_viz.watchdog.load_from_file", return_value=[_make_entry()]):
        # Two iterations with no file change; callback fires only once.
        watch_file(str(f), events.append, interval=0, max_iterations=2)

    assert len(events) == 1


def test_watch_file_detects_second_change(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)
    events: List[WatchEvent] = []
    iteration = [0]

    original_hash = _file_hash(str(f))

    def fake_hash(path: str):
        iteration[0] += 1
        if iteration[0] == 1:
            return original_hash
        return hashlib.md5(b"changed content\n").hexdigest()

    with patch("crontab_viz.watchdog._file_hash", side_effect=fake_hash), \
         patch("crontab_viz.watchdog.load_from_file", return_value=[_make_entry()]):
        watch_file(str(f), events.append, interval=0, max_iterations=2)

    assert len(events) == 2


def test_watch_file_skips_unreadable_file() -> None:
    events: List[WatchEvent] = []
    with patch("crontab_viz.watchdog._file_hash", return_value=None):
        watch_file("/nonexistent", events.append, interval=0, max_iterations=2)
    assert events == []
