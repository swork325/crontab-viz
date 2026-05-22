"""Tests for crontab_viz.reporter."""
from __future__ import annotations

import datetime
import json
import pathlib
import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.reporter import build_text_report, build_json_report, write_report


def _make_entry(
    schedule: str = "* * * * *",
    command: str = "echo hi",
    comment: str = "",
    is_valid: bool = True,
) -> CronEntry:
    entry = CronEntry(schedule=schedule, command=command, comment=comment)
    object.__setattr__(entry, "is_valid", is_valid)
    return entry


FIXED_NOW = datetime.datetime(2024, 6, 1, 12, 0, 0)


def test_text_report_contains_header():
    report = build_text_report([], now=FIXED_NOW)
    assert "Crontab Visualizer Report" in report


def test_text_report_contains_source():
    report = build_text_report([], source="/etc/crontab", now=FIXED_NOW)
    assert "/etc/crontab" in report


def test_text_report_contains_timestamp():
    report = build_text_report([], now=FIXED_NOW)
    assert "2024-06-01" in report


def test_text_report_contains_summary_section():
    entries = [_make_entry()]
    report = build_text_report(entries, now=FIXED_NOW)
    assert "Summary" in report


def test_text_report_contains_entry_command():
    entries = [_make_entry(command="backup.sh")]
    report = build_text_report(entries, now=FIXED_NOW)
    assert "backup.sh" in report


def test_json_report_is_valid_json():
    entries = [_make_entry()]
    raw = build_json_report(entries, now=FIXED_NOW)
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_json_report_top_level_keys():
    raw = build_json_report([], now=FIXED_NOW)
    data = json.loads(raw)
    for key in ("generated", "source", "summary", "entries"):
        assert key in data


def test_json_report_summary_total():
    entries = [_make_entry(), _make_entry()]
    raw = build_json_report(entries, now=FIXED_NOW)
    data = json.loads(raw)
    assert data["summary"]["total"] == 2


def test_json_report_entries_list():
    entries = [_make_entry(command="ls")]
    raw = build_json_report(entries, now=FIXED_NOW)
    data = json.loads(raw)
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) == 1


def test_json_report_source_preserved():
    raw = build_json_report([], source="myfile", now=FIXED_NOW)
    data = json.loads(raw)
    assert data["source"] == "myfile"


def test_write_report_text(tmp_path):
    out = tmp_path / "report.txt"
    write_report([_make_entry()], path=str(out), fmt="text", now=FIXED_NOW)
    assert out.exists()
    assert "Summary" in out.read_text()


def test_write_report_json(tmp_path):
    out = tmp_path / "report.json"
    write_report([_make_entry()], path=str(out), fmt="json", now=FIXED_NOW)
    assert out.exists()
    data = json.loads(out.read_text())
    assert "summary" in data
