"""Tests for crontab_viz.dependency."""
from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.dependency import (
    DependencyLink,
    DependencyReport,
    _share_command_token,
    detect_dependencies,
)


def _make_entry(schedule: str, command: str, valid: bool = True) -> CronEntry:
    entry = CronEntry(
        raw=f"{schedule} {command}",
        schedule=schedule,
        command=command,
        comment="",
    )
    object.__setattr__(entry, "_valid", valid)
    return entry


def _std(minute="0", hour="*", dom="*", month="*", dow="*", command="/bin/true"):
    schedule = f"{minute} {hour} {dom} {month} {dow}"
    e = CronEntry(raw=f"{schedule} {command}", schedule=schedule, command=command, comment="")
    return e


# ---------------------------------------------------------------------------
# DependencyLink
# ---------------------------------------------------------------------------

def test_dependency_link_str_contains_commands():
    a = _std(command="/usr/bin/backup")
    b = _std(command="/usr/bin/sync")
    link = DependencyLink(predecessor=a, successor=b, gap_seconds=60, reason="test")
    text = str(link)
    assert "backup" in text
    assert "sync" in text


def test_dependency_link_str_contains_gap():
    a = _std()
    b = _std()
    link = DependencyLink(predecessor=a, successor=b, gap_seconds=120, reason="r")
    assert "120" in str(link)


# ---------------------------------------------------------------------------
# DependencyReport
# ---------------------------------------------------------------------------

def test_dependency_report_count_empty():
    report = DependencyReport()
    assert report.count == 0


def test_dependency_report_as_dict_has_link_count():
    report = DependencyReport()
    d = report.as_dict()
    assert "link_count" in d
    assert d["link_count"] == 0


def test_dependency_report_as_dict_links_list():
    a = _std(command="/usr/bin/a")
    b = _std(command="/usr/bin/b")
    link = DependencyLink(predecessor=a, successor=b, gap_seconds=10, reason="x")
    report = DependencyReport(links=[link])
    d = report.as_dict()
    assert len(d["links"]) == 1
    assert d["links"][0]["predecessor"] == "/usr/bin/a"


# ---------------------------------------------------------------------------
# _share_command_token
# ---------------------------------------------------------------------------

def test_share_command_token_common_script():
    a = _std(command="/usr/local/bin/deploy.sh --env prod")
    b = _std(command="/usr/local/bin/deploy.sh --env staging")
    token = _share_command_token(a, b)
    assert token is not None
    assert "deploy" in token or token == "/usr/local/bin/deploy.sh"


def test_share_command_token_no_common():
    a = _std(command="/usr/bin/backup")
    b = _std(command="/usr/bin/cleanup")
    token = _share_command_token(a, b)
    assert token is None


def test_share_command_token_empty_command():
    a = _std(command="")
    b = _std(command="/usr/bin/something")
    assert _share_command_token(a, b) is None


# ---------------------------------------------------------------------------
# detect_dependencies
# ---------------------------------------------------------------------------

def test_detect_dependencies_empty_list():
    report = detect_dependencies([])
    assert report.count == 0


def test_detect_dependencies_skips_invalid():
    invalid = _make_entry("bad schedule", "/bin/true", valid=False)
    report = detect_dependencies([invalid, invalid])
    assert report.count == 0


def test_detect_dependencies_detects_shared_token():
    now = datetime.datetime(2024, 1, 15, 10, 0, 0)
    # Same script name, runs at different times so gap is large
    a = _std(minute="0", hour="2", command="/usr/local/bin/report.sh --send")
    b = _std(minute="0", hour="4", command="/usr/local/bin/report.sh --archive")
    report = detect_dependencies([a, b], reference=now)
    assert report.count >= 1
    assert any("report" in lnk.reason or "report.sh" in lnk.reason for lnk in report.links)


def test_detect_dependencies_detects_close_next_run():
    now = datetime.datetime(2024, 1, 15, 10, 0, 0)
    # Both run at 10:01 and 10:02 — gap = 60 s, within default 300 s threshold
    a = _std(minute="1", hour="10", command="/bin/alpha")
    b = _std(minute="2", hour="10", command="/bin/beta")
    report = detect_dependencies([a, b], gap_threshold_seconds=300, reference=now)
    assert report.count >= 1


def test_detect_dependencies_excludes_far_apart():
    now = datetime.datetime(2024, 1, 15, 10, 0, 0)
    a = _std(minute="0", hour="1", command="/bin/alpha")
    b = _std(minute="0", hour="23", command="/bin/beta")
    report = detect_dependencies([a, b], gap_threshold_seconds=300, reference=now)
    # No shared token, gap >> 300 s
    assert report.count == 0
