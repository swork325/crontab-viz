"""Compute next-run times for cron entries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from crontab_viz.parser import CronEntry

# Maximum minutes to scan forward when searching for the next run time
_MAX_SCAN_MINUTES = 366 * 24 * 60  # one year


def _field_matches(value: int, field: str) -> bool:
    """Return True if *value* satisfies the cron *field* expression."""
    if field == "*":
        return True
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = 0 if base == "*" else int(base)
            if value >= start and (value - start) % int(step) == 0:
                return True
        elif "-" in part:
            lo, hi = part.split("-", 1)
            if int(lo) <= value <= int(hi):
                return True
        else:
            if value == int(part):
                return True
    return False


def next_run(entry: CronEntry, after: Optional[datetime] = None) -> Optional[datetime]:
    """Return the next datetime at which *entry* would fire.

    Scans minute-by-minute starting one minute after *after* (defaults to
    ``datetime.now()``).
    Returns ``None`` if no match is found within one year or if the entry
    is a ``@reboot`` entry (which only runs once at boot time).
    """
    if entry.is_reboot:
        return None
    if not entry.is_valid:
        return None

    start = (after or datetime.now()).replace(second=0, microsecond=0)
    candidate = start + timedelta(minutes=1)

    minute_f = entry.fields.get("minute", "*")
    hour_f = entry.fields.get("hour", "*")
    dom_f = entry.fields.get("day_of_month", "*")
    month_f = entry.fields.get("month", "*")
    dow_f = entry.fields.get("day_of_week", "*")

    for _ in range(_MAX_SCAN_MINUTES):
        if (
            _field_matches(candidate.minute, minute_f)
            and _field_matches(candidate.hour, hour_f)
            and _field_matches(candidate.day, dom_f)
            and _field_matches(candidate.month, month_f)
            and _field_matches(candidate.weekday(), dow_f)
        ):
            return candidate
        candidate += timedelta(minutes=1)

    return None


def next_n_runs(
    entry: CronEntry,
    n: int,
    after: Optional[datetime] = None,
) -> list[datetime]:
    """Return the next *n* datetimes at which *entry* would fire.

    Each subsequent run is computed starting from the previous result, so the
    returned list is always in ascending chronological order.  If fewer than
    *n* matches are found within the one-year scan window the list will be
    shorter than requested.
    """
    results: list[datetime] = []
    reference = after
    for _ in range(n):
        nxt = next_run(entry, after=reference)
        if nxt is None:
            break
        results.append(nxt)
        reference = nxt
    return results


def countdown(entry: CronEntry, after: Optional[datetime] = None) -> Optional[timedelta]:
    """Return the timedelta until *entry* next fires, or ``None``."""
    reference = after or datetime.now()
    nxt = next_run(entry, after=reference)
    if nxt is None:
        return None
    return nxt - reference.replace(second=0, microsecond=0)


def format_countdown(delta: Optional[timedelta]) -> str:
    """Human-readable countdown string, e.g. '2h 05m' or 'N/A'."""
    if delta is None:
        return "N/A"
    total_minutes = int(delta.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"
