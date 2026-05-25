"""Tests for crontab_viz.expirator."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from crontab_viz.expirator import (
    ExpirationWarning,
    _extract_date,
    _is_temp_command,
    check_expiration,
)
from crontab_viz.parser import CronEntry


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_entry(
    command: str = "/usr/bin/backup.sh",
    comment: str = "",
    valid: bool = True,
) -> CronEntry:
    if valid:
        return CronEntry(
            raw=f"0 2 * * * {command} # {comment}",
            minute="0",
            hour="2",
            day="*",
            month="*",
            weekday="*",
            command=command,
            comment=comment,
        )
    return CronEntry(
        raw="not a cron line",
        minute=None,
        hour=None,
        day=None,
        month=None,
        weekday=None,
        command=None,
        comment=None,
    )


# ---------------------------------------------------------------------------
# _extract_date
# ---------------------------------------------------------------------------

def test_extract_date_finds_iso_date():
    assert _extract_date("cleanup 2022-06-01") == date(2022, 6, 1)


def test_extract_date_returns_none_when_absent():
    assert _extract_date("no date here") is None


def test_extract_date_ignores_invalid_date():
    assert _extract_date("bad 2022-99-99") is None


# ---------------------------------------------------------------------------
# _is_temp_command
# ---------------------------------------------------------------------------

def test_is_temp_command_detects_tmp_path():
    assert _is_temp_command("/tmp/run.sh")


def test_is_temp_command_detects_temp_keyword():
    assert _is_temp_command("/usr/local/bin/temp_cleanup.sh")


def test_is_temp_command_detects_test_keyword():
    assert _is_temp_command("/home/user/test_job.sh")


def test_is_temp_command_clean_command_returns_false():
    assert not _is_temp_command("/usr/bin/backup.sh")


# ---------------------------------------------------------------------------
# check_expiration
# ---------------------------------------------------------------------------

def test_check_expiration_empty_list_returns_empty():
    assert check_expiration([]) == []


def test_check_expiration_skips_invalid_entries():
    invalid = _make_entry(valid=False)
    result = check_expiration([invalid], reference=date(2024, 1, 1))
    assert result == []


def test_check_expiration_detects_past_date_in_comment():
    entry = _make_entry(comment="one-off migration 2021-03-15")
    result = check_expiration([entry], reference=date(2024, 1, 1))
    assert len(result) == 1
    assert result[0].date_found == date(2021, 3, 15)
    assert "past date" in result[0].reason


def test_check_expiration_ignores_future_date_in_comment():
    entry = _make_entry(comment="scheduled for 2099-12-31")
    result = check_expiration([entry], reference=date(2024, 1, 1))
    assert result == []


def test_check_expiration_detects_temp_command():
    entry = _make_entry(command="/tmp/one_off_fix.sh")
    result = check_expiration([entry], reference=date(2024, 1, 1))
    assert len(result) == 1
    assert result[0].date_found is None
    assert "temporary" in result[0].reason


def test_check_expiration_past_date_takes_priority_over_temp():
    entry = _make_entry(command="/tmp/fix.sh", comment="2020-01-01 temp fix")
    result = check_expiration([entry], reference=date(2024, 1, 1))
    # past date is found first; only one warning per entry
    assert len(result) == 1
    assert result[0].date_found == date(2020, 1, 1)


def test_expiration_warning_str_with_date():
    entry = _make_entry(command="/usr/bin/old.sh")
    w = ExpirationWarning(entry=entry, reason="contains a past date", date_found=date(2021, 5, 10))
    text = str(w)
    assert "2021-05-10" in text
    assert "old.sh" in text


def test_expiration_warning_str_without_date():
    entry = _make_entry(command="/tmp/temp.sh")
    w = ExpirationWarning(entry=entry, reason="temporary job")
    text = str(w)
    assert "STALE" in text
    assert "temp.sh" in text
