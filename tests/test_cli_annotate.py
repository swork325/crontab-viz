"""Tests for crontab_viz.cli_annotate."""
from __future__ import annotations

import argparse
from unittest.mock import patch, MagicMock

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.cli_annotate import add_annotate_subparser, _render, _run_annotate, main
from crontab_viz.annotator import annotate_entries


def _make_entry(line: str) -> CronEntry:
    return CronEntry(raw_line=line)


# --- _render ---

def test_render_includes_valid_entry():
    entries = [_make_entry("0 0 * * * /usr/bin/backup")]
    annotated = annotate_entries(entries)
    output = _render(annotated, include_invalid=False)
    assert "/usr/bin/backup" in output


def test_render_excludes_invalid_by_default():
    entries = [_make_entry("not valid")]
    annotated = annotate_entries(entries)
    output = _render(annotated, include_invalid=False)
    assert output.strip() == ""


def test_render_includes_invalid_when_flag_set():
    entries = [_make_entry("not valid")]
    annotated = annotate_entries(entries)
    output = _render(annotated, include_invalid=True)
    assert "[invalid]" in output


def test_render_shows_schedule_meaning():
    entries = [_make_entry("@daily /usr/bin/backup")]
    annotated = annotate_entries(entries)
    output = _render(annotated, include_invalid=False)
    assert "midnight" in output.lower() or "daily" in output.lower()


def test_render_shows_notes_when_present():
    entries = [_make_entry("0 0 * * * /usr/bin/backup # nightly")]
    annotated = annotate_entries(entries)
    output = _render(annotated, include_invalid=False)
    assert "nightly" in output


# --- _run_annotate ---

def _make_args(**kwargs):
    defaults = {"file": None, "text": None, "user": False, "invalid": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_annotate_with_text_returns_zero(capsys):
    args = _make_args(text="0 0 * * * /usr/bin/backup")
    result = _run_annotate(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "/usr/bin/backup" in captured.out


def test_run_annotate_empty_text_returns_one(capsys):
    args = _make_args(text="")
    result = _run_annotate(args)
    assert result == 1


def test_run_annotate_from_file(tmp_path, capsys):
    f = tmp_path / "crontab.txt"
    f.write_text("*/5 * * * * /usr/bin/check\n")
    args = _make_args(file=str(f))
    result = _run_annotate(args)
    assert result == 0
    assert "/usr/bin/check" in capsys.readouterr().out


def test_run_annotate_user_crontab(capsys):
    mock_entries = [_make_entry("0 1 * * * /usr/bin/task")]
    with patch("crontab_viz.cli_annotate.load_user_crontab", return_value=mock_entries):
        args = _make_args(user=True)
        result = _run_annotate(args)
    assert result == 0


# --- main ---

def test_main_no_subcommand_returns_one():
    result = main([])
    assert result == 1


def test_main_annotate_subcommand(capsys):
    result = main(["annotate", "--text", "@hourly /usr/bin/cleanup"])
    assert result == 0
    assert "/usr/bin/cleanup" in capsys.readouterr().out
