"""Notifier module: alert when a cron job is due within a threshold."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run, countdown


@dataclass
class DueAlert:
    """Represents a cron entry that is due within the alert threshold."""
    entry: CronEntry
    next_run_time: datetime
    seconds_until_due: float

    def __str__(self) -> str:
        mins = int(self.seconds_until_due // 60)
        secs = int(self.seconds_until_due % 60)
        return (
            f"[ALERT] '{self.entry.command}' due in "
            f"{mins}m {secs}s (at {self.next_run_time.strftime('%H:%M:%S')})"
        )


def check_due(
    entries: List[CronEntry],
    threshold_seconds: float = 300.0,
    now: Optional[datetime] = None,
) -> List[DueAlert]:
    """Return DueAlert objects for entries whose next run is within threshold.

    Args:
        entries: List of CronEntry objects to check.
        threshold_seconds: Seconds window to consider "due soon" (default 5 min).
        now: Reference datetime; defaults to datetime.now().

    Returns:
        Sorted list of DueAlert (soonest first).
    """
    if now is None:
        now = datetime.now()

    alerts: List[DueAlert] = []
    for entry in entries:
        if not entry.is_valid:
            continue
        try:
            run_time = next_run(entry, now=now)
            secs = countdown(entry, now=now)
        except Exception:
            continue
        if 0 <= secs <= threshold_seconds:
            alerts.append(DueAlert(entry=entry, next_run_time=run_time, seconds_until_due=secs))

    alerts.sort(key=lambda a: a.seconds_until_due)
    return alerts


def format_alerts(alerts: List[DueAlert]) -> str:
    """Format a list of DueAlert objects into a human-readable string."""
    if not alerts:
        return "No jobs due within threshold."
    lines = [str(alert) for alert in alerts]
    return "\n".join(lines)
