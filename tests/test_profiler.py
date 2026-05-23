"""Tests for crontab_viz.profiler."""
import datetime
import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.profiler import (
    FrequencyProfile,
    _busiest_hour,
    profile_entry,
    profile_entries,
)


def _make_entry(raw: str, command: str = "cmd", valid: bool = True) -> CronEntry:
    entry = CronEntry.__new__(CronEntry)
    object.__setattr__(entry, "raw", raw)
    object.__setattr__(entry, "command", command)
    object.__setattr__(entry, "comment", "")
    object.__setattr__(entry, "is_valid", valid)
    if valid and not raw.startswith("@"):
        parts = raw.split()
        object.__setattr__(entry, "minute", parts[0])
        object.__setattr__(entry, "hour", parts[1])
        object.__setattr__(entry, "dom", parts[2])
        object.__setattr__(entry, "month", parts[3])
        object.__setattr__(entry, "dow", parts[4])
    else:
        object.__setattr__(entry, "minute", "*")
        object.__setattr__(entry, "hour", "*")
        object.__setattr__(entry, "dom", "*")
        object.__setattr__(entry, "month", "*")
        object.__setattr__(entry, "dow", "*")
    return entry


REF = datetime.datetime(2024, 6, 1, 12, 0, 0)


def test_profile_entry_invalid_returns_none():
    entry = _make_entry("bad entry", valid=False)
    assert profile_entry(entry, reference=REF) is None


def test_profile_entry_returns_frequency_profile():
    entry = _make_entry("* * * * *", command="/bin/true")
    result = profile_entry(entry, sample_size=48, reference=REF)
    assert isinstance(result, FrequencyProfile)


def test_profile_entry_every_minute_high_runs_per_day():
    entry = _make_entry("* * * * *", command="/bin/true")
    result = profile_entry(entry, sample_size=48, reference=REF)
    assert result is not None
    assert result.runs_per_day > 100  # ~1440 per day


def test_profile_entry_hourly_runs_per_day_approx_24():
    entry = _make_entry("0 * * * *", command="/bin/hourly")
    result = profile_entry(entry, sample_size=48, reference=REF)
    assert result is not None
    assert 20 <= result.runs_per_day <= 28


def test_profile_entry_sample_next_runs_at_most_five():
    entry = _make_entry("* * * * *", command="/bin/true")
    result = profile_entry(entry, sample_size=48, reference=REF)
    assert result is not None
    assert len(result.sample_next_runs) <= 5


def test_profile_entry_busiest_hour_is_valid_hour():
    entry = _make_entry("0 3 * * *", command="/bin/nightly")
    result = profile_entry(entry, sample_size=10, reference=REF)
    assert result is not None
    assert result.busiest_hour == 3


def test_busiest_hour_empty_returns_minus_one():
    assert _busiest_hour([]) == -1


def test_busiest_hour_single_run():
    dt = datetime.datetime(2024, 1, 1, 7, 0)
    assert _busiest_hour([dt]) == 7


def test_profile_entries_skips_invalid():
    valid = _make_entry("0 * * * *", command="ok", valid=True)
    invalid = _make_entry("bad", command="bad", valid=False)
    results = profile_entries([valid, invalid], reference=REF)
    assert len(results) == 1
    assert results[0].entry.command == "ok"


def test_as_dict_contains_expected_keys():
    entry = _make_entry("0 12 * * *", command="/bin/noon")
    result = profile_entry(entry, sample_size=10, reference=REF)
    assert result is not None
    d = result.as_dict()
    for key in ("command", "schedule", "runs_per_day", "runs_per_hour",
                "busiest_hour", "sample_next_runs"):
        assert key in d


def test_as_dict_sample_next_runs_are_iso_strings():
    entry = _make_entry("0 * * * *", command="/bin/hourly")
    result = profile_entry(entry, sample_size=5, reference=REF)
    assert result is not None
    for ts in result.as_dict()["sample_next_runs"]:
        datetime.datetime.fromisoformat(ts)  # should not raise
