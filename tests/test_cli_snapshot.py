"""Tests for crontab_viz.cli_snapshot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.cli_snapshot import _load_entries, _on_snapshot_print, _run_snapshot, add_snapshot_subparser
from crontab_viz.parser import CronEntry
from crontab_viz.snapshotter import take_snapshot


def _make_entry(schedule: str = "* * * * *", command: str = "echo hi") -> CronEntry:
    return CronEntry(raw=f"{schedule} {command}", schedule=schedule, command=command)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": None,
        "text": None,
        "interval": 0.0,
        "count": 2,
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _load_entries
# ---------------------------------------------------------------------------

def test_load_entries_from_text():
    args = _make_args(text="* * * * * echo hi")
    entries = _load_entries(args)
    assert len(entries) == 1


def test_load_entries_empty_when_no_source():
    args = _make_args()
    entries = _load_entries(args)
    assert entries == []


def test_load_entries_from_file(tmp_path: Path):
    f = tmp_path / "crontab"
    f.write_text("* * * * * echo hello\n")
    args = _make_args(file=str(f))
    entries = _load_entries(args)
    assert len(entries) == 1


# ---------------------------------------------------------------------------
# _on_snapshot_print
# ---------------------------------------------------------------------------

def test_on_snapshot_print_outputs_entry_count(capsys):
    snap = take_snapshot([_make_entry()], source="src")
    _on_snapshot_print(snap)
    captured = capsys.readouterr().out
    assert "1" in captured


def test_on_snapshot_print_outputs_captured_at(capsys):
    snap = take_snapshot([_make_entry()], source="src")
    _on_snapshot_print(snap)
    captured = capsys.readouterr().out
    assert snap.captured_at in captured


# ---------------------------------------------------------------------------
# _run_snapshot
# ---------------------------------------------------------------------------

def test_run_snapshot_returns_zero():
    args = _make_args(text="* * * * * echo hi", count=1)
    with patch("crontab_viz.snapshotter.time.sleep"):
        result = _run_snapshot(args)
    assert result == 0


def test_run_snapshot_prints_json(capsys):
    args = _make_args(text="* * * * * echo hi", count=1)
    with patch("crontab_viz.snapshotter.time.sleep"):
        _run_snapshot(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "snapshots" in data


def test_run_snapshot_writes_file(tmp_path: Path, capsys):
    out_file = tmp_path / "session.json"
    args = _make_args(text="* * * * * echo hi", count=1, output=str(out_file))
    with patch("crontab_viz.snapshotter.time.sleep"):
        _run_snapshot(args)
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["snapshot_count"] == 1


# ---------------------------------------------------------------------------
# add_snapshot_subparser
# ---------------------------------------------------------------------------

def test_add_snapshot_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_snapshot_subparser(subs)
    args = parser.parse_args(["snapshot", "--count", "1", "--interval", "0"])
    assert hasattr(args, "func")
