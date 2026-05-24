"""Inspect individual cron entries for detailed field-level analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from crontab_viz.parser import CronEntry

_SPECIAL_MEANINGS = {
    "@reboot": "Run once at startup",
    "@yearly": "Run once a year (0 0 1 1 *)",
    "@annually": "Run once a year (0 0 1 1 *)",
    "@monthly": "Run once a month (0 0 1 * *)",
    "@weekly": "Run once a week (0 0 * * 0)",
    "@daily": "Run once a day (0 0 * * *)",
    "@midnight": "Run once a day at midnight (0 0 * * *)",
    "@hourly": "Run once an hour (0 * * * *)",
}

_FIELD_NAMES = ["minute", "hour", "day-of-month", "month", "day-of-week"]
_FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


@dataclass
class FieldInspection:
    name: str
    raw: str
    is_wildcard: bool
    has_step: bool
    has_range: bool
    has_list: bool
    values: List[str]
    note: Optional[str] = None


@dataclass
class EntryInspection:
    entry: CronEntry
    is_special: bool
    special_meaning: Optional[str]
    fields: List[FieldInspection] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def _inspect_field(name: str, raw: str, valid_range: tuple) -> FieldInspection:
    is_wildcard = raw == "*"
    has_step = "/" in raw
    has_range = "-" in raw.lstrip("-")
    has_list = "," in raw
    values = [v.strip() for v in raw.split(",")]

    note: Optional[str] = None
    if has_step:
        parts = raw.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            step = int(parts[1])
            note = f"every {step} {name}(s)"
    elif has_range:
        bounds = raw.split("-")
        if len(bounds) == 2 and all(b.isdigit() for b in bounds):
            note = f"{name} from {bounds[0]} to {bounds[1]}"
    elif has_list:
        note = f"{name} in [{raw}]"
    elif is_wildcard:
        note = f"every {name}"

    return FieldInspection(
        name=name,
        raw=raw,
        is_wildcard=is_wildcard,
        has_step=has_step,
        has_range=has_range,
        has_list=has_list,
        values=values,
        note=note,
    )


def inspect_entry(entry: CronEntry) -> EntryInspection:
    """Produce a detailed field-level inspection of a single CronEntry."""
    raw_schedule = (entry.schedule or "").strip()
    is_special = raw_schedule.startswith("@")
    special_meaning = _SPECIAL_MEANINGS.get(raw_schedule) if is_special else None

    inspection = EntryInspection(
        entry=entry,
        is_special=is_special,
        special_meaning=special_meaning,
    )

    if not entry.is_valid:
        inspection.warnings.append("Entry failed to parse; field analysis unavailable.")
        return inspection

    if is_special:
        return inspection

    raw_fields = [entry.minute, entry.hour, entry.dom, entry.month, entry.dow]
    for name, raw, rng in zip(_FIELD_NAMES, raw_fields, _FIELD_RANGES):
        fi = _inspect_field(name, raw or "*", rng)
        inspection.fields.append(fi)

    if all(f.is_wildcard for f in inspection.fields):
        inspection.warnings.append("All fields are wildcards: job runs every minute.")

    return inspection


def inspect_entries(entries: List[CronEntry]) -> List[EntryInspection]:
    """Inspect a list of CronEntry objects."""
    return [inspect_entry(e) for e in entries]
