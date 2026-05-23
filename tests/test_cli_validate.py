"""Tests for crontab_viz.cli_validate."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.cli_validate import _run_validate, add_validate_subparser
from crontab_viz.parser import CronEntry
from crontab_viz.validator import ValidationReport, ValidationIssue


def _make_entry(schedule: str, command: str, valid: bool = True) -> CronEntry:
    e = CronEntry.__new__(CronEntry)
    e.schedule = schedule
    e.command = command
    e.comment = ""
    e.is_valid = valid
    e.fields = {}
    return e


def _make_args(**kwargs):
    args = MagicMock()
    args.file = kwargs.get("file", None)
    args.text = kwargs.get("text", None)
    args.user = kwargs.get("user", False)
    args.fmt = kwargs.get("fmt", "text")
    args.strict = kwargs.get("strict", False)
    return args


def test_run_validate_clean_returns_zero(capsys):
    entry = _make_entry("0 1 * * *", "/usr/bin/backup")
    args = _make_args(text="0 1 * * * /usr/bin/backup")
    with patch("crontab_viz.cli_validate._load_entries", return_value=[entry]):
        code = _run_validate(args)
    assert code == 0


def test_run_validate_with_error_returns_one(capsys):
    entry = _make_entry("bad", "cmd", valid=False)
    args = _make_args()
    with patch("crontab_viz.cli_validate._load_entries", return_value=[entry]):
        code = _run_validate(args)
    assert code == 1


def test_run_validate_strict_warning_returns_one(capsys):
    entry = _make_entry("* * * * *", "/usr/bin/cmd")
    args = _make_args(strict=True)
    with patch("crontab_viz.cli_validate._load_entries", return_value=[entry]):
        code = _run_validate(args)
    assert code == 1


def test_run_validate_json_output_is_valid_json(capsys):
    entry = _make_entry("0 * * * *", "/usr/bin/cmd")
    args = _make_args(fmt="json")
    with patch("crontab_viz.cli_validate._load_entries", return_value=[entry]):
        _run_validate(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "errors" in data
    assert "warnings" in data


def test_run_validate_text_output_contains_summary(capsys):
    entry = _make_entry("0 * * * *", "/usr/bin/cmd")
    args = _make_args(fmt="text")
    with patch("crontab_viz.cli_validate._load_entries", return_value=[entry]):
        _run_validate(args)
    out = capsys.readouterr().out
    assert "error" in out.lower()


def test_add_validate_subparser_registers_command():
    import argparse
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_validate_subparser(subs)
    args = parser.parse_args(["validate", "--user"])
    assert args.user is True
