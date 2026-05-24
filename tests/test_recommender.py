"""Tests for crontab_viz.recommender."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.recommender import (
    Recommendation,
    recommend,
    recommend_all,
)


def _make_entry(
    fields=None,
    command="/usr/bin/backup.sh",
    comment="backup job",
    is_valid=True,
    raw="",
) -> CronEntry:
    entry = MagicMock(spec=CronEntry)
    entry.fields = fields if fields is not None else ["0", "2", "*", "*", "*"]
    entry.command = command
    entry.comment = comment
    entry.is_valid = is_valid
    entry.raw = raw
    return entry


def test_recommend_invalid_entry_returns_warning():
    entry = _make_entry(is_valid=False)
    recs = recommend(entry)
    assert len(recs) == 1
    assert recs[0].severity == "warning"
    assert "invalid" in recs[0].message.lower()


def test_recommend_invalid_entry_returns_early():
    """Invalid entries should only get one recommendation."""
    entry = _make_entry(is_valid=False)
    recs = recommend(entry)
    assert len(recs) == 1


def test_recommend_every_minute_wildcard_warns():
    entry = _make_entry(fields=["*", "*", "*", "*", "*"], command="/bin/echo hi", comment="echo")
    recs = recommend(entry)
    severities = [r.severity for r in recs]
    assert "warning" in severities


def test_recommend_every_second_minute_step_warns():
    entry = _make_entry(fields=["*/1", "*", "*", "*", "*"], command="/bin/echo", comment="echo")
    recs = recommend(entry)
    messages = [r.message for r in recs]
    assert any("every minute" in m.lower() for m in messages)


def test_recommend_frequent_step_produces_info():
    entry = _make_entry(fields=["*/2", "*", "*", "*", "*"], command="/bin/check", comment="check")
    recs = recommend(entry)
    severities = [r.severity for r in recs]
    assert "info" in severities or "warning" in severities


def test_recommend_no_comment_produces_info():
    entry = _make_entry(comment="")
    recs = recommend(entry)
    messages = [r.message for r in recs]
    assert any("comment" in m.lower() for m in messages)


def test_recommend_missing_absolute_path_produces_improvement():
    entry = _make_entry(command="backup.sh", comment="backup")
    recs = recommend(entry)
    severities = [r.severity for r in recs]
    assert "improvement" in severities


def test_recommend_absolute_path_no_path_improvement():
    entry = _make_entry(command="/usr/bin/backup.sh", comment="backup")
    recs = recommend(entry)
    severities = [r.severity for r in recs]
    assert "improvement" not in severities


def test_recommend_clean_entry_returns_no_recs():
    entry = _make_entry(
        fields=["0", "3", "*", "*", "*"],
        command="/usr/bin/backup.sh",
        comment="nightly backup",
    )
    recs = recommend(entry)
    assert recs == []


def test_recommendation_str_contains_severity():
    entry = _make_entry(is_valid=False)
    rec = recommend(entry)[0]
    assert rec.severity.upper() in str(rec)


def test_recommend_all_aggregates_across_entries():
    e1 = _make_entry(comment="")
    e2 = _make_entry(command="script.sh", comment="")
    recs = recommend_all([e1, e2])
    assert len(recs) >= 2


def test_recommend_all_empty_list_returns_empty():
    assert recommend_all([]) == []
