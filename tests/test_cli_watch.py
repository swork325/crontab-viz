"""Tests for crontab_viz.cli_watch."""
from __future__ import annotations

import argparse
import hashlib
from io import StringIO
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

import pytest

from crontab_viz.cli_watch import add_watch_subparser, _on_change, _run_watch, main
from crontab_viz.watchdog import WatchEvent
from crontab_viz.parser import CronEntry


CRONTAB_CONTENT = b"* * * * * /usr/bin/true\n"
_HASH = hashlib.md5(CRONTAB_CONTENT).hexdigest()


def _make_entry(schedule: str = "* * * * *", command: str = "/bin/true") -> CronEntry:
    return CronEntry(schedule=schedule, command=command, comment="")


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(file="/etc/crontab", interval=5.0, max_iterations=1, func=_run_watch)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _on_change
# ---------------------------------------------------------------------------

def test_on_change_prints_timestamp_and_path(capsys) -> None:
    ev = WatchEvent(path="/etc/crontab", previous_hash=None, current_hash=_HASH, entries=[])
    _on_change(ev)
    out = capsys.readouterr().out
    assert "/etc/crontab" in out
    assert "Change detected" in out


def test_on_change_prints_entry_count(capsys) -> None:
    entry = _make_entry()
    ev = WatchEvent(path="/etc/crontab", previous_hash=None, current_hash=_HASH, entries=[entry])
    _on_change(ev)
    out = capsys.readouterr().out
    assert "Entries loaded: 1" in out


def test_on_change_shows_none_for_first_detection(capsys) -> None:
    ev = WatchEvent(path="/etc/crontab", previous_hash=None, current_hash=_HASH, entries=[])
    _on_change(ev)
    out = capsys.readouterr().out
    assert "(none)" in out


# ---------------------------------------------------------------------------
# _run_watch
# ---------------------------------------------------------------------------

def test_run_watch_returns_zero(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)
    args = _make_args(file=str(f), max_iterations=1)

    with patch("crontab_viz.cli_watch.watch_file") as mock_watch:
        mock_watch.return_value = None
        result = _run_watch(args)

    assert result == 0


def test_run_watch_passes_interval_to_watch_file(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)
    args = _make_args(file=str(f), interval=2.5, max_iterations=1)

    with patch("crontab_viz.cli_watch.watch_file") as mock_watch:
        _run_watch(args)
        _, kwargs = mock_watch.call_args
        assert kwargs["interval"] == 2.5


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_no_subcommand_returns_one() -> None:
    result = main([])
    assert result == 1


def test_main_watch_subcommand_invokes_run(tmp_path: Path) -> None:
    f = tmp_path / "crontab"
    f.write_bytes(CRONTAB_CONTENT)

    with patch("crontab_viz.cli_watch.watch_file") as mock_watch:
        mock_watch.return_value = None
        result = main(["watch", str(f), "--max-iterations", "1"])

    assert result == 0
    assert mock_watch.called
