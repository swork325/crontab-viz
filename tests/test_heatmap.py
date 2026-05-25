"""Tests for crontab_viz.heatmap."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.heatmap import Heatmap, build_heatmap, render_heatmap


def _make_entry(schedule: str, command: str = "cmd") -> CronEntry:
    line = f"{schedule} {command}"
    from crontab_viz.parser import parse_crontab_line
    entry = parse_crontab_line(line)
    assert entry is not None
    return entry


def _std(minute="*", hour="*", dom="*", month="*", dow="*", cmd="cmd") -> CronEntry:
    return _make_entry(f"{minute} {hour} {dom} {month} {dow}", cmd)


class TestHeatmapDataclass:
    def test_initial_grid_all_zeros(self):
        hm = Heatmap()
        assert all(v == 0 for row in hm.grid for v in row)

    def test_grid_dimensions(self):
        hm = Heatmap()
        assert len(hm.grid) == 7
        assert all(len(row) == 24 for row in hm.grid)

    def test_max_value_empty_returns_one(self):
        hm = Heatmap()
        assert hm.max_value() == 1

    def test_max_value_after_increment(self):
        hm = Heatmap()
        hm.grid[0][0] = 5
        assert hm.max_value() == 5


class TestBuildHeatmap:
    def test_build_heatmap_skips_invalid(self):
        from crontab_viz.parser import CronEntry
        bad = CronEntry(raw="bad line", schedule="bad", command="", comment="", is_valid=False, fields=[])
        hm = build_heatmap([bad])
        assert hm.max_value() == 1  # still all zeros → max clamps to 1

    def test_build_heatmap_all_wildcards_nonzero(self):
        entry = _std()  # * * * * * — every minute
        hm = build_heatmap([entry])
        # Every cell should be > 0
        assert all(hm.grid[d][h] > 0 for d in range(7) for h in range(24))

    def test_build_heatmap_specific_hour(self):
        entry = _std(hour="3")  # runs only at hour 3
        hm = build_heatmap([entry])
        assert all(hm.grid[d][3] > 0 for d in range(7))
        assert all(hm.grid[d][4] == 0 for d in range(7))

    def test_build_heatmap_specific_dow(self):
        entry = _std(dow="1")  # Monday only
        hm = build_heatmap([entry])
        assert all(hm.grid[1][h] > 0 for h in range(24))
        assert all(hm.grid[0][h] == 0 for h in range(24))

    def test_build_heatmap_accumulates_multiple_entries(self):
        e1 = _std(hour="2")
        e2 = _std(hour="2")
        hm = build_heatmap([e1, e2])
        assert hm.grid[0][2] == 2


class TestRenderHeatmap:
    def test_render_returns_string(self):
        hm = build_heatmap([_std()])
        result = render_heatmap(hm)
        assert isinstance(result, str)

    def test_render_contains_day_labels(self):
        hm = build_heatmap([_std()])
        result = render_heatmap(hm)
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            assert day in result

    def test_render_contains_legend(self):
        hm = build_heatmap([_std()])
        result = render_heatmap(hm)
        assert "Legend" in result

    def test_render_has_seven_day_rows(self):
        hm = build_heatmap([_std()])
        lines = render_heatmap(hm).splitlines()
        day_lines = [l for l in lines if any(d in l for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])]
        assert len(day_lines) == 7
