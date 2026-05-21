"""Tests for crontab_viz.exporter."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from datetime import datetime

import pytest

from crontab_viz.exporter import export_csv, export_json, export_to_file
from crontab_viz.parser import CronEntry

FIXED_NOW = datetime(2024, 6, 1, 12, 0, 0)


def _make_entry(minute="0", hour="9", command="/usr/bin/backup"):
    return CronEntry(
        minute=minute,
        hour=hour,
        day_of_month="*",
        month="*",
        day_of_week="*",
        command=command,
        raw=f"{minute} {hour} * * * {command}",
    )


def test_export_json_returns_list():
    entries = [_make_entry()]
    result = json.loads(export_json(entries, now=FIXED_NOW))
    assert isinstance(result, list)
    assert len(result) == 1


def test_export_json_fields_present():
    entries = [_make_entry()]
    record = json.loads(export_json(entries, now=FIXED_NOW))[0]
    for field in ("command", "schedule", "next_run", "countdown", "valid"):
        assert field in record


def test_export_json_command_value():
    entries = [_make_entry(command="/bin/echo hello")]
    record = json.loads(export_json(entries, now=FIXED_NOW))[0]
    assert record["command"] == "/bin/echo hello"


def test_export_json_multiple_entries():
    entries = [_make_entry(command=f"/cmd{i}") for i in range(3)]
    records = json.loads(export_json(entries, now=FIXED_NOW))
    assert len(records) == 3


def test_export_csv_has_header():
    entries = [_make_entry()]
    result = export_csv(entries, now=FIXED_NOW)
    reader = csv.DictReader(io.StringIO(result))
    assert set(reader.fieldnames or []) >= {"command", "schedule", "next_run", "countdown", "valid"}


def test_export_csv_row_count():
    entries = [_make_entry(command=f"/job{i}") for i in range(4)]
    result = export_csv(entries, now=FIXED_NOW)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 4


def test_export_to_file_json(tmp_path):
    entries = [_make_entry()]
    out = tmp_path / "out.json"
    export_to_file(str(out), entries, fmt="json", now=FIXED_NOW)
    assert out.exists()
    data = json.loads(out.read_text())
    assert isinstance(data, list)


def test_export_to_file_csv(tmp_path):
    entries = [_make_entry()]
    out = tmp_path / "out.csv"
    export_to_file(str(out), entries, fmt="csv", now=FIXED_NOW)
    assert out.exists()
    assert "command" in out.read_text()


def test_export_to_file_invalid_format():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_to_file("/tmp/x.txt", [], fmt="xml")
