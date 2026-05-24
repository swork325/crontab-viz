"""Timezone conversion utilities for cron entries."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # Python 3.9+
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # type: ignore

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run


@dataclass
class TimezoneResult:
    entry: CronEntry
    utc_next_run: Optional[datetime]
    local_next_run: Optional[datetime]
    timezone: str
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.error is None and self.local_next_run is not None

    def formatted(self) -> str:
        if not self.is_valid:
            return f"[{self.timezone}] error: {self.error}"
        assert self.local_next_run is not None
        return self.local_next_run.strftime("%Y-%m-%d %H:%M:%S %Z")


def resolve_timezone(tz_name: str) -> Optional[ZoneInfo]:
    """Return a ZoneInfo for *tz_name*, or None if unknown."""
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        return None


def convert_next_run(
    entry: CronEntry,
    tz_name: str,
    now: Optional[datetime] = None,
) -> TimezoneResult:
    """Compute the next run for *entry* expressed in *tz_name*.

    The base reference time *now* is assumed UTC when no tzinfo is attached.
    """
    zone = resolve_timezone(tz_name)
    if zone is None:
        return TimezoneResult(
            entry=entry,
            utc_next_run=None,
            local_next_run=None,
            timezone=tz_name,
            error=f"Unknown timezone: {tz_name!r}",
        )

    base = now or datetime.utcnow()
    utc_next = next_run(entry, base)

    if utc_next is None:
        return TimezoneResult(
            entry=entry,
            utc_next_run=None,
            local_next_run=None,
            timezone=tz_name,
            error="Could not compute next run (invalid entry?)",
        )

    utc_aware = utc_next.replace(tzinfo=ZoneInfo("UTC"))
    local_dt = utc_aware.astimezone(zone)

    return TimezoneResult(
        entry=entry,
        utc_next_run=utc_next,
        local_next_run=local_dt,
        timezone=tz_name,
    )


def convert_entries(
    entries: list[CronEntry],
    tz_name: str,
    now: Optional[datetime] = None,
) -> list[TimezoneResult]:
    """Batch-convert *entries* to *tz_name*."""
    return [convert_next_run(e, tz_name, now) for e in entries]
