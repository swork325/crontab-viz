"""Summarize a collection of crontab entries into human-readable statistics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run

import datetime


@dataclass
class CrontabSummary:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    special: int = 0
    standard: int = 0
    unique_commands: int = 0
    next_due: str = ""
    busiest_hour: str = ""
    hour_distribution: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "special": self.special,
            "standard": self.standard,
            "unique_commands": self.unique_commands,
            "next_due": self.next_due,
            "busiest_hour": self.busiest_hour,
            "hour_distribution": self.hour_distribution,
        }


def _hour_label(hour_field: str) -> str:
    """Return a display label for a cron hour field."""
    if hour_field == "*":
        return "every hour"
    return f"{hour_field}:00"


def summarize(entries: List[CronEntry], now: datetime.datetime | None = None) -> CrontabSummary:
    """Build a :class:`CrontabSummary` from *entries*."""
    if now is None:
        now = datetime.datetime.now()

    summary = CrontabSummary()
    summary.total = len(entries)

    commands = set()
    hour_counts: Dict[str, int] = {}
    earliest_dt: datetime.datetime | None = None
    earliest_label = ""

    for entry in entries:
        if not entry.is_valid:
            summary.invalid += 1
            continue

        summary.valid += 1
        commands.add(entry.command)

        if entry.schedule.startswith("@"):
            summary.special += 1
        else:
            summary.standard += 1
            hour_key = _hour_label(entry.fields[1]) if entry.fields else "unknown"
            hour_counts[hour_key] = hour_counts.get(hour_key, 0) + 1

        nxt = next_run(entry, now)
        if nxt is not None and (earliest_dt is None or nxt < earliest_dt):
            earliest_dt = nxt
            earliest_label = nxt.strftime("%Y-%m-%d %H:%M:%S")

    summary.unique_commands = len(commands)
    summary.next_due = earliest_label
    summary.hour_distribution = hour_counts

    if hour_counts:
        summary.busiest_hour = max(hour_counts, key=lambda k: hour_counts[k])

    return summary


def render_summary(summary: CrontabSummary) -> str:
    """Return a multi-line human-readable string for *summary*."""
    lines = [
        "=== Crontab Summary ===",
        f"  Total entries   : {summary.total}",
        f"  Valid           : {summary.valid}",
        f"  Invalid         : {summary.invalid}",
        f"  Standard        : {summary.standard}",
        f"  Special (@)     : {summary.special}",
        f"  Unique commands : {summary.unique_commands}",
        f"  Next due        : {summary.next_due or 'n/a'}",
        f"  Busiest hour    : {summary.busiest_hour or 'n/a'}",
    ]
    return "\n".join(lines)
