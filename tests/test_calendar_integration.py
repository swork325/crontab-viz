"""Integration tests for calendar_view using realistic crontab text."""
from __future__ import annotations

from crontab_viz.loader import load_from_text
from crontab_viz.calendar_view import CalendarMatrix, render_calendar, HOURS

SAMPLE = """
# Daily backup at 2am every day
0 2 * * * /usr/bin/backup.sh
# Weekday report at 9am Mon-Fri
0 9 * * 1-5 /usr/bin/report.sh
# Every hour on Sunday
0 * * * 0 /usr/bin/ping.sh
# Invalid entry
not_valid_cron
"""


def test_integration_matrix_built_without_error():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    assert matrix.matrix is not None


def test_integration_backup_appears_at_hour_2():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    # backup runs every day at 2am
    for d in range(7):
        assert matrix.matrix[d][2] >= 1


def test_integration_report_only_on_weekdays():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    # Mon-Fri = days 1-5, not Sun(0) or Sat(6)
    for d in range(1, 6):
        assert matrix.matrix[d][9] >= 1
    assert matrix.matrix[0][9] == 0  # Sunday
    assert matrix.matrix[6][9] == 0  # Saturday


def test_integration_sunday_ping_all_hours():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    for h in HOURS:
        assert matrix.matrix[0][h] >= 1  # Sunday every hour


def test_integration_render_is_string():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    output = render_calendar(matrix)
    assert isinstance(output, str)
    assert len(output) > 0


def test_integration_busiest_day_is_string():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    bd = matrix.busiest_day()
    assert isinstance(bd, str)
    assert bd in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def test_integration_busiest_hour_in_range():
    entries = load_from_text(SAMPLE)
    matrix = CalendarMatrix(entries)
    bh = matrix.busiest_hour()
    assert 0 <= bh <= 23
