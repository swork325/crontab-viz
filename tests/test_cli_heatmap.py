"""Tests for crontab_viz.cli_heatmap."""
from __future__ import annotations

import argparse
from unittest.mock import patch, MagicMock

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.cli_heatmap import add_heatmap_subparser, _load_entries, _run_heatmap, main


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "text": None, "func": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_entry(schedule: str = "* * * * *", command: str = "cmd") -> CronEntry:
    from crontab_viz.parser import parse_crontab_line
    entry = parse_crontab_line(f"{schedule} {command}")
    assert entry is not None
    return entry


class TestLoadEntries:
    def test_load_entries_from_text(self):
        args = _make_args(text="* * * * * echo hi")
        entries = _load_entries(args)
        assert len(entries) == 1

    def test_load_entries_from_file(self, tmp_path):
        f = tmp_path / "crontab"
        f.write_text("0 2 * * * backup\n")
        args = _make_args(file=str(f))
        entries = _load_entries(args)
        assert len(entries) == 1

    def test_load_entries_falls_back_to_user_crontab(self):
        args = _make_args()
        with patch("crontab_viz.cli_heatmap.load_user_crontab", return_value=[]) as mock:
            entries = _load_entries(args)
            mock.assert_called_once()
        assert entries == []


class TestRunHeatmap:
    def test_run_heatmap_returns_zero(self, capsys):
        args = _make_args(text="* * * * * echo hi")
        result = _run_heatmap(args)
        assert result == 0

    def test_run_heatmap_prints_output(self, capsys):
        args = _make_args(text="0 3 * * * backup")
        _run_heatmap(args)
        captured = capsys.readouterr()
        assert "Mon" in captured.out or "Sun" in captured.out

    def test_run_heatmap_empty_crontab(self, capsys):
        args = _make_args(text="")
        result = _run_heatmap(args)
        assert result == 0


class TestAddHeatmapSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        add_heatmap_subparser(subs)
        args = parser.parse_args(["heatmap", "--text", "* * * * * cmd"])
        assert args.text == "* * * * * cmd"

    def test_subparser_file_flag(self, tmp_path):
        f = tmp_path / "ct"
        f.write_text("* * * * * cmd\n")
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        add_heatmap_subparser(subs)
        args = parser.parse_args(["heatmap", "--file", str(f)])
        assert args.file == str(f)


class TestMain:
    def test_main_returns_zero_with_text(self, capsys):
        result = main(["heatmap", "--text", "* * * * * echo"])
        assert result == 0
