"""Diff two lists of cron entries and report additions, removals, and changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from crontab_viz.parser import CronEntry


@dataclass
class CrontabDiff:
    """Result of comparing two sets of cron entries."""

    added: List[CronEntry] = field(default_factory=list)
    removed: List[CronEntry] = field(default_factory=list)
    changed: List[Tuple[CronEntry, CronEntry]] = field(default_factory=list)
    unchanged: List[CronEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No changes detected."
        return ", ".join(parts)


def _entry_key(entry: CronEntry) -> str:
    """Stable key that identifies an entry by its command."""
    return entry.command.strip()


def _schedule_str(entry: CronEntry) -> str:
    """Return a normalised schedule string for comparison."""
    if entry.special:
        return entry.special
    return " ".join([
        entry.minute or "*",
        entry.hour or "*",
        entry.dom or "*",
        entry.month or "*",
        entry.dow or "*",
    ])


def diff_entries(
    old: List[CronEntry],
    new: List[CronEntry],
) -> CrontabDiff:
    """Compare *old* and *new* entry lists and return a :class:`CrontabDiff`.

    Entries are matched by command string.  If the same command appears in
    both lists but with a different schedule it is reported as *changed*.
    """
    old_map: Dict[str, CronEntry] = {_entry_key(e): e for e in old}
    new_map: Dict[str, CronEntry] = {_entry_key(e): e for e in new}

    added: List[CronEntry] = []
    removed: List[CronEntry] = []
    changed: List[Tuple[CronEntry, CronEntry]] = []
    unchanged: List[CronEntry] = []

    for key, new_entry in new_map.items():
        if key not in old_map:
            added.append(new_entry)
        else:
            old_entry = old_map[key]
            if _schedule_str(old_entry) != _schedule_str(new_entry):
                changed.append((old_entry, new_entry))
            else:
                unchanged.append(new_entry)

    for key, old_entry in old_map.items():
        if key not in new_map:
            removed.append(old_entry)

    return CrontabDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )
