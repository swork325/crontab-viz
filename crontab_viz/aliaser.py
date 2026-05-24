"""Aliaser: map cron entries to human-readable alias names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from crontab_viz.parser import CronEntry

# Built-in aliases keyed by (schedule_string, command_fragment)
_BUILTIN_ALIASES: Dict[str, str] = {
    "@daily": "Daily job",
    "@hourly": "Hourly job",
    "@reboot": "Run at reboot",
    "@weekly": "Weekly job",
    "@monthly": "Monthly job",
    "@yearly": "Yearly job",
    "@annually": "Yearly job",
    "0 * * * *": "Every hour on the hour",
    "0 0 * * *": "Daily at midnight",
    "0 12 * * *": "Daily at noon",
    "*/5 * * * *": "Every 5 minutes",
    "*/15 * * * *": "Every 15 minutes",
    "*/30 * * * *": "Every 30 minutes",
    "0 0 * * 0": "Weekly on Sunday midnight",
    "0 0 1 * *": "Monthly on the 1st at midnight",
}


@dataclass
class AliasedEntry:
    entry: CronEntry
    alias: str
    custom: bool = False

    def __str__(self) -> str:
        tag = "[custom]" if self.custom else "[builtin]"
        return f"{tag} {self.alias!r} -> {self.entry.command}"


def _schedule_key(entry: CronEntry) -> str:
    """Return a normalised schedule string for lookup."""
    if entry.special:
        return entry.special.lower()
    parts = [entry.minute, entry.hour, entry.day, entry.month, entry.weekday]
    return " ".join(p for p in parts if p is not None)


def resolve_alias(
    entry: CronEntry,
    custom_aliases: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Return an alias string for *entry*, or ``None`` if no alias matches."""
    key = _schedule_key(entry)
    if custom_aliases and key in custom_aliases:
        return custom_aliases[key]
    return _BUILTIN_ALIASES.get(key)


def alias_entries(
    entries: List[CronEntry],
    custom_aliases: Optional[Dict[str, str]] = None,
) -> List[AliasedEntry]:
    """Return an :class:`AliasedEntry` for every entry that has a known alias."""
    result: List[AliasedEntry] = []
    for entry in entries:
        if not entry.is_valid:
            continue
        alias = resolve_alias(entry, custom_aliases)
        if alias is None:
            continue
        is_custom = (
            custom_aliases is not None
            and _schedule_key(entry) in custom_aliases
        )
        result.append(AliasedEntry(entry=entry, alias=alias, custom=is_custom))
    return result
