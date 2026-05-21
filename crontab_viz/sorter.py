"""Sorting utilities for cron entries based on various criteria."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run


class SortKey(str, Enum):
    NEXT_RUN = "next_run"
    COMMAND = "command"
    COMMENT = "comment"
    SCHEDULE = "schedule"


@dataclass
class SortCriteria:
    key: SortKey = SortKey.NEXT_RUN
    reverse: bool = False


def _sort_key_next_run(entry: CronEntry, now: Optional[object] = None):
    """Return a sortable value for next run time; invalid entries sort last."""
    if not entry.is_valid():
        # Push invalid entries to the end regardless of direction
        return (1, 0)
    try:
        import datetime
        reference = now or datetime.datetime.now()
        nxt = next_run(entry, reference)
        return (0, nxt.timestamp())
    except Exception:
        return (1, 0)


def sort_entries(
    entries: List[CronEntry],
    criteria: Optional[SortCriteria] = None,
    now: Optional[object] = None,
) -> List[CronEntry]:
    """Return a new list of entries sorted according to *criteria*.

    Parameters
    ----------
    entries:
        Source list of :class:`CronEntry` objects.
    criteria:
        Sorting parameters.  Defaults to ascending next-run order.
    now:
        Reference datetime used when sorting by next-run time.  Defaults to
        ``datetime.datetime.now()``.
    """
    if criteria is None:
        criteria = SortCriteria()

    key = criteria.key

    if key == SortKey.NEXT_RUN:
        sorted_entries = sorted(
            entries,
            key=lambda e: _sort_key_next_run(e, now),
        )
    elif key == SortKey.COMMAND:
        sorted_entries = sorted(
            entries,
            key=lambda e: (e.command or "").lower(),
        )
    elif key == SortKey.COMMENT:
        sorted_entries = sorted(
            entries,
            key=lambda e: (e.comment or "").lower(),
        )
    elif key == SortKey.SCHEDULE:
        sorted_entries = sorted(
            entries,
            key=lambda e: e.raw_schedule,
        )
    else:
        sorted_entries = list(entries)

    if criteria.reverse:
        sorted_entries = list(reversed(sorted_entries))

    return sorted_entries
