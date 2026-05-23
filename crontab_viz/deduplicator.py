"""Deduplication utilities for crontab entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from crontab_viz.parser import CronEntry


def _entry_key(entry: CronEntry) -> Tuple[str, str]:
    """Return a (schedule, command) key for deduplication."""
    schedule = " ".join(entry.fields) if entry.fields else entry.raw.split("#")[0].strip()
    command = entry.command.strip() if entry.command else ""
    return (schedule, command)


@dataclass
class DeduplicationResult:
    """Result of a deduplication pass over a list of crontab entries."""

    unique: List[CronEntry] = field(default_factory=list)
    duplicates: List[List[CronEntry]] = field(default_factory=list)

    @property
    def duplicate_count(self) -> int:
        """Total number of duplicate entries removed."""
        return sum(len(group) - 1 for group in self.duplicates)

    @property
    def total_removed(self) -> int:
        """Alias for duplicate_count."""
        return self.duplicate_count


def deduplicate(entries: List[CronEntry]) -> DeduplicationResult:
    """Remove duplicate crontab entries, keeping the first occurrence.

    Two entries are considered duplicates when they share the same
    schedule expression and command string.

    Args:
        entries: List of CronEntry objects to process.

    Returns:
        DeduplicationResult with unique entries and grouped duplicates.
    """
    seen: dict[Tuple[str, str], CronEntry] = {}
    groups: dict[Tuple[str, str], List[CronEntry]] = {}

    for entry in entries:
        key = _entry_key(entry)
        if key not in seen:
            seen[key] = entry
            groups[key] = [entry]
        else:
            groups[key].append(entry)

    unique = [seen[k] for k in seen]
    duplicates = [g for g in groups.values() if len(g) > 1]

    return DeduplicationResult(unique=unique, duplicates=duplicates)


def find_duplicates(entries: List[CronEntry]) -> List[List[CronEntry]]:
    """Return only the groups of duplicate entries (groups with 2+ members).

    Args:
        entries: List of CronEntry objects to inspect.

    Returns:
        List of groups; each group contains entries sharing schedule+command.
    """
    result = deduplicate(entries)
    return result.duplicates
