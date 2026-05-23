"""Annotator module: attach human-readable descriptions to cron entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from crontab_viz.parser import CronEntry


_SPECIAL_DESCRIPTIONS: dict[str, str] = {
    "@reboot": "Run once at startup",
    "@yearly": "Run once a year (Jan 1 00:00)",
    "@annually": "Run once a year (Jan 1 00:00)",
    "@monthly": "Run once a month (1st 00:00)",
    "@weekly": "Run once a week (Sun 00:00)",
    "@daily": "Run once a day at midnight",
    "@midnight": "Run once a day at midnight",
    "@hourly": "Run once an hour at :00",
}


@dataclass
class AnnotatedEntry:
    entry: CronEntry
    description: str
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        base = f"{self.entry.command}: {self.description}"
        if self.notes:
            return base + " (" + "; ".join(self.notes) + ")"
        return base


def _describe_field(value: str, unit: str) -> str:
    if value == "*":
        return f"every {unit}"
    if "," in value:
        return f"{unit}s {value}"
    if "-" in value:
        lo, hi = value.split("-", 1)
        return f"{unit}s {lo}–{hi}"
    if value.startswith("*/"):
        step = value[2:]
        return f"every {step} {unit}(s)"
    return f"{unit} {value}"


def describe_schedule(entry: CronEntry) -> str:
    """Return a human-readable description of the schedule."""
    if not entry.is_valid:
        return "Invalid schedule"
    raw = entry.raw_schedule.strip()
    if raw in _SPECIAL_DESCRIPTIONS:
        return _SPECIAL_DESCRIPTIONS[raw]
    minute, hour, dom, month, dow = (
        entry.minute, entry.hour, entry.dom, entry.month, entry.dow
    )
    parts = [
        _describe_field(minute, "minute"),
        _describe_field(hour, "hour"),
        _describe_field(dom, "day-of-month"),
        _describe_field(month, "month"),
        _describe_field(dow, "weekday"),
    ]
    return ", ".join(parts)


def _build_notes(entry: CronEntry) -> List[str]:
    notes: List[str] = []
    if entry.comment:
        notes.append(f"comment: {entry.comment}")
    if entry.is_valid and entry.raw_schedule.startswith("@"):
        notes.append("special macro")
    return notes


def annotate_entry(entry: CronEntry) -> AnnotatedEntry:
    """Annotate a single CronEntry with a description and notes."""
    return AnnotatedEntry(
        entry=entry,
        description=describe_schedule(entry),
        notes=_build_notes(entry),
    )


def annotate_entries(entries: List[CronEntry]) -> List[AnnotatedEntry]:
    """Annotate a list of CronEntry objects."""
    return [annotate_entry(e) for e in entries]
