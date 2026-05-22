"""Group cron entries by various criteria for summary views."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from crontab_viz.parser import CronEntry


class GroupBy(str, Enum):
    HOUR = "hour"
    COMMENT = "comment"
    VALIDITY = "validity"
    SCHEDULE_TYPE = "schedule_type"


@dataclass
class EntryGroup:
    key: str
    entries: List[CronEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)


def _hour_key(entry: CronEntry) -> str:
    """Return the hour field as a grouping key, or 'invalid' for bad entries."""
    if not entry.is_valid:
        return "invalid"
    fields = entry.schedule.split()
    if len(fields) >= 2:
        return f"hour:{fields[1]}"
    # special @-syntax — extract keyword
    return entry.schedule.split()[0] if fields else "unknown"


def _comment_key(entry: CronEntry) -> str:
    """Group by comment text, falling back to '<no comment>'."""
    return entry.comment.strip() if entry.comment and entry.comment.strip() else "<no comment>"


def _validity_key(entry: CronEntry) -> str:
    return "valid" if entry.is_valid else "invalid"


def _schedule_type_key(entry: CronEntry) -> str:
    """Distinguish @special entries from standard 5-field entries."""
    if not entry.is_valid:
        return "invalid"
    if entry.schedule.startswith("@"):
        return "special"
    return "standard"


_KEY_FN = {
    GroupBy.HOUR: _hour_key,
    GroupBy.COMMENT: _comment_key,
    GroupBy.VALIDITY: _validity_key,
    GroupBy.SCHEDULE_TYPE: _schedule_type_key,
}


def group_entries(
    entries: List[CronEntry],
    by: GroupBy = GroupBy.VALIDITY,
) -> Dict[str, EntryGroup]:
    """Partition *entries* into named groups according to *by*.

    Returns an ordered dict mapping group key -> EntryGroup.
    """
    key_fn = _KEY_FN[by]
    groups: Dict[str, EntryGroup] = {}
    for entry in entries:
        k = key_fn(entry)
        if k not in groups:
            groups[k] = EntryGroup(key=k)
        groups[k].entries.append(entry)
    return groups
