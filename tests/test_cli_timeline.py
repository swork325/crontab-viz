"""Unit tests for crontab_viz.cli_timeline."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.cli_timeline import _load_entries, _run_timeline, add_timeline_subparser


SAMPLE_TEXT = "0 * * * * /bin/check  # hourly\n@daily /bin/backup  # daily backup"


def _make_args(**kwargs):
    defaults = {"file": None, "text": None, "runs": 5, "limit": 0}
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    return ns


# --- _load_entries ---

def test_load_entries_from_text():
    args = _make_args(text=SAMPLE_TEXT)
    entries = _load_entries(args)
    assert len(entries) >= 1


def test_load_entries_from_file(tmp_path):
    f = tmp_path / "crontab.txt"
    f.write_text(SAMPLE_TEXT)
    args = _make_args(file=str(f))
    entries = _load_entries(args)
    assert len(entries) >= 1


def test_load_entries_falls_back_to_user_crontab():
    args = _make_args()
    with patch("crontab_viz.cli_timeline.load_user_crontab", return_value=[]) as mock_load:
        entries = _load_entries(args)
    mock_load.assert_called_once()
    assert entries == []


# --- _run_timeline ---

def test_run_timeline_returns_zero(capsys):
    args = _make_args(text=SAMPLE_TEXT)
    rc = _run_timeline(args)
    assert rc == 0


def test_run_timeline_prints_output(capsys):
    args = _make_args(text=SAMPLE_TEXT)
    _run_timeline(args)
    out = capsys.readouterr().out
    assert len(out) > 0


def test_run_timeline_limit_caps_events(capsys):
    text = "\n".join(f"0 {h} * * * /bin/job{h}" for h in range(10))
    args = _make_args(text=text, runs=3, limit=4)
    _run_timeline(args)
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if "/bin/job" in l]
    assert len(lines) <= 4


def test_run_timeline_no_limit_shows_all(capsys):
    text = "\n".join(f"0 {h} * * * /bin/job{h}" for h in range(3))
    args = _make_args(text=text, runs=2, limit=0)
    _run_timeline(args)
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if "/bin/job" in l]
    assert len(lines) == 6  # 3 entries × 2 runs each


# --- add_timeline_subparser ---

def test_add_timeline_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_timeline_subparser(subs)
    args = parser.parse_args(["timeline", "--runs", "3"])
    assert args.command == "timeline"
    assert args.runs == 3


def test_add_timeline_subparser_default_runs():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_timeline_subparser(subs)
    args = parser.parse_args(["timeline"])
    assert args.runs == 5


def test_add_timeline_subparser_default_limit():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_timeline_subparser(subs)
    args = parser.parse_args(["timeline"])
    assert args.limit == 0
