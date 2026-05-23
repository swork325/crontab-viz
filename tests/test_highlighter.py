"""Tests for crontab_viz.highlighter."""
import pytest
from crontab_viz.highlighter import (
    highlight_schedule,
    highlight_command,
    highlight_comment,
    HighlightedSchedule,
    _RESET,
    _CYAN,
    _BOLD,
    _DIM,
    _GREEN,
)


def test_highlight_schedule_returns_highlighted_schedule():
    result = highlight_schedule("* * * * *")
    assert isinstance(result, HighlightedSchedule)


def test_highlight_schedule_raw_preserved():
    schedule = "0 12 * * 1"
    result = highlight_schedule(schedule)
    assert result.raw == schedule


def test_highlight_schedule_five_field_labels():
    result = highlight_schedule("30 6 * * 1-5")
    assert len(result.field_labels) == 5
    assert result.field_labels[0] == ("minute", "30")
    assert result.field_labels[1] == ("hour", "6")
    assert result.field_labels[4] == ("day-of-week", "1-5")


def test_highlight_schedule_coloured_contains_reset():
    result = highlight_schedule("0 0 * * *")
    assert _RESET in result.coloured


def test_highlight_schedule_special_at_daily():
    result = highlight_schedule("@daily")
    assert result.field_labels == [("special", "@daily")]
    assert _CYAN in result.coloured
    assert _BOLD in result.coloured


def test_highlight_schedule_special_at_reboot():
    result = highlight_schedule("@reboot")
    assert result.raw == "@reboot"
    assert len(result.field_labels) == 1


def test_highlight_schedule_invalid_field_count():
    result = highlight_schedule("* * *")
    assert result.coloured == "* * *"
    assert result.field_labels == []


def test_highlight_schedule_field_labels_contain_all_field_names():
    """All five standard field names should appear in the labels for a full schedule."""
    result = highlight_schedule("0 12 1 6 3")
    field_names = [label[0] for label in result.field_labels]
    assert field_names == ["minute", "hour", "day-of-month", "month", "day-of-week"]


def test_highlight_command_short_unchanged():
    cmd = "/usr/bin/backup.sh"
    result = highlight_command(cmd)
    assert cmd in result
    assert _DIM in result


def test_highlight_command_truncated():
    long_cmd = "a" * 80
    result = highlight_command(long_cmd, max_len=20)
    # Stripped ANSI: original 80 chars should be truncated
    assert "\u2026" in result


def test_highlight_command_exact_max_len_not_truncated():
    cmd = "a" * 60
    result = highlight_command(cmd, max_len=60)
    assert "\u2026" not in result


def test_highlight_comment_non_empty():
    result = highlight_comment("# backup job")
    assert "# backup job" in result
    assert _GREEN in result
    assert _DIM in result


def test_highlight_comment_empty_returns_empty_string():
    assert highlight_comment("") == ""
