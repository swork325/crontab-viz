"""Integration tests for heatmap building from realistic crontab snippets."""
from __future__ import annotations

import pytest

from crontab_viz.loader import load_from_text
from crontab_viz.heatmap import build_heatmap, render_heatmap

_SAMPLE_CRONTAB = """
# Daily backup at 2am
0 2 * * * /usr/bin/backup.sh
# Hourly health check
0 * * * * /usr/bin/healthcheck.sh
# Every weekday at noon
0 12 * * 1-5 /usr/bin/report.sh
# Invalid line
not_a_valid_cron_entry
"""


def test_integration_builds_without_error():
    entries = load_from_text(_SAMPLE_CRONTAB)
    hm = build_heatmap(entries)
    assert hm is not None


def test_integration_backup_at_hour_2():
    entries = load_from_text(_SAMPLE_CRONTAB)
    hm = build_heatmap(entries)
    # All days should have at least 1 hit at hour 2 (backup + hourly)
    assert all(hm.grid[d][2] >= 1 for d in range(7))


def test_integration_hourly_check_all_hours():
    entries = load_from_text(_SAMPLE_CRONTAB)
    hm = build_heatmap(entries)
    # Hourly check fires every hour, every day
    assert all(hm.grid[d][h] >= 1 for d in range(7) for h in range(24))


def test_integration_weekday_report_only_on_weekdays():
    entries = load_from_text("0 12 * * 1-5 /usr/bin/report.sh")
    hm = build_heatmap(entries)
    # dow 1-5 = Mon-Fri; Sun(0) and Sat(6) should be 0 at hour 12
    assert hm.grid[0][12] == 0  # Sunday
    assert hm.grid[6][12] == 0  # Saturday
    assert hm.grid[1][12] >= 1  # Monday


def test_integration_render_is_string():
    entries = load_from_text(_SAMPLE_CRONTAB)
    hm = build_heatmap(entries)
    output = render_heatmap(hm)
    assert isinstance(output, str)
    assert len(output) > 0


def test_integration_render_contains_all_days():
    entries = load_from_text(_SAMPLE_CRONTAB)
    hm = build_heatmap(entries)
    output = render_heatmap(hm)
    for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
        assert day in output


def test_integration_invalid_lines_ignored():
    entries = load_from_text("not_valid\n* * * * * echo hi")
    hm = build_heatmap(entries)
    # Only the valid entry contributes; grid should not be all-zero
    assert hm.max_value() >= 1
