"""Tests for crontab_viz.cli_calendar."""
from __future__ import annotations

import argparse
import io
from unittest.mock import patch, MagicMock

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.cli_calendar import _load_entries, _run_calendar, add_calendar_subparser


SAMPLE_TEXT = "0 6 * * 1 echo weekly\n*/5 * * * * echo frequent"


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "text": None, "stats": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_load_entries_from_text():
    args = _make_args(text=SAMPLE_TEXT)
    entries = _load_entries(args)
    assert len(entries) == 2


def test_load_entries_from_file(tmp_path):
    p = tmp_path / "cron.txt"
    p.write_text(SAMPLE_TEXT)
    args = _make_args(file=str(p))
    entries = _load_entries(args)
    assert len(entries) == 2


def test_load_entries_falls_back_to_user_crontab():
    args = _make_args()
    with patch("crontab_viz.cli_calendar.load_user_crontab", return_value=[]) as mock:
        entries = _load_entries(args)
    mock.assert_called_once()
    assert entries == []


def test_run_calendar_returns_zero():
    args = _make_args(text=SAMPLE_TEXT)
    out = io.StringIO()
    result = _run_calendar(args, out=out)
    assert result == 0


def test_run_calendar_output_contains_day_labels():
    args = _make_args(text=SAMPLE_TEXT)
    out = io.StringIO()
    _run_calendar(args, out=out)
    output = out.getvalue()
    assert "Mon" in output
    assert "Fri" in output


def test_run_calendar_stats_flag_prints_busiest():
    args = _make_args(text=SAMPLE_TEXT, stats=True)
    out = io.StringIO()
    _run_calendar(args, out=out)
    output = out.getvalue()
    assert "Busiest hour" in output
    assert "Busiest day" in output


def test_run_calendar_no_stats_flag_omits_busiest():
    args = _make_args(text=SAMPLE_TEXT, stats=False)
    out = io.StringIO()
    _run_calendar(args, out=out)
    output = out.getvalue()
    assert "Busiest hour" not in output


def test_add_calendar_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_calendar_subparser(subs)
    args = parser.parse_args(["calendar", "--text", "* * * * * echo hi"])
    assert args.command == "calendar"
    assert args.text == "* * * * * echo hi"
