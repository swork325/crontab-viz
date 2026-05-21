"""Tests for the terminal dashboard module."""

import pytest
from unittest.mock import patch, MagicMock

from crontab_viz.dashboard import _render_header, _clear_screen, run_dashboard


SAMPLE_CRONTAB = """
# Daily backup
0 2 * * * /usr/bin/backup.sh
# Hourly cleanup
@hourly /usr/bin/cleanup.sh
"""


def test_render_header_contains_title():
    header = _render_header("test_source")
    assert "crontab-viz" in header


def test_render_header_contains_source():
    header = _render_header("/etc/crontab")
    assert "/etc/crontab" in header


def test_render_header_contains_timestamp():
    header = _render_header("source")
    # Should contain a date-like string
    import re
    assert re.search(r"\d{4}-\d{2}-\d{2}", header)


def test_clear_screen_writes_escape(capsys):
    _clear_screen()
    # Just ensure it doesn't raise; escape codes go to stdout directly


def test_run_dashboard_once_with_text(capsys):
    """Dashboard should render once without error when once=True."""
    run_dashboard(text=SAMPLE_CRONTAB, once=True)
    captured = capsys.readouterr()
    assert "crontab-viz" in captured.out


def test_run_dashboard_once_with_file(tmp_path, capsys):
    """Dashboard should load from file and render once."""
    cron_file = tmp_path / "crontab"
    cron_file.write_text(SAMPLE_CRONTAB)
    run_dashboard(source=str(cron_file), once=True)
    captured = capsys.readouterr()
    assert "crontab-viz" in captured.out


def test_run_dashboard_label_inline_text(capsys):
    run_dashboard(text="* * * * * echo hi", once=True)
    captured = capsys.readouterr()
    assert "<inline text>" in captured.out


def test_run_dashboard_label_file_source(tmp_path, capsys):
    cron_file = tmp_path / "my_crontab"
    cron_file.write_text("*/5 * * * * echo hello")
    run_dashboard(source=str(cron_file), once=True)
    captured = capsys.readouterr()
    assert str(cron_file) in captured.out


def test_run_dashboard_keyboard_interrupt(capsys):
    """Dashboard should exit gracefully on KeyboardInterrupt."""
    with patch("time.sleep", side_effect=KeyboardInterrupt):
        run_dashboard(text="* * * * * echo test", once=False)
    captured = capsys.readouterr()
    assert "Goodbye" in captured.out
