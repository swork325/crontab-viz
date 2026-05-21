"""Filter and search utilities for cron entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from crontab_viz.parser import CronEntry


@dataclass
class FilterCriteria:
    """Criteria used to filter a list of CronEntry objects."""

    command_pattern: Optional[str] = None  # substring or regex
    comment_pattern: Optional[str] = None
    only_valid: bool = False
    tags: List[str] = field(default_factory=list)  # match any tag in comment


def _matches_pattern(text: str, pattern: str) -> bool:
    """Return True if *pattern* appears in *text* (case-insensitive substring or regex)."""
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return pattern.lower() in text.lower()


def filter_entries(entries: List[CronEntry], criteria: FilterCriteria) -> List[CronEntry]:
    """Return the subset of *entries* that satisfy all conditions in *criteria*."""
    result: List[CronEntry] = []

    for entry in entries:
        if criteria.only_valid and not entry.is_valid:
            continue

        if criteria.command_pattern and not _matches_pattern(
            entry.command, criteria.command_pattern
        ):
            continue

        if criteria.comment_pattern and not _matches_pattern(
            entry.comment or "", criteria.comment_pattern
        ):
            continue

        if criteria.tags:
            comment_lower = (entry.comment or "").lower()
            if not any(tag.lower() in comment_lower for tag in criteria.tags):
                continue

        result.append(entry)

    return result


def search_entries(entries: List[CronEntry], query: str) -> List[CronEntry]:
    """Convenience wrapper: search *entries* by command or comment containing *query*."""
    criteria = FilterCriteria(command_pattern=query)
    by_command = filter_entries(entries, criteria)

    criteria_comment = FilterCriteria(comment_pattern=query)
    by_comment = filter_entries(entries, criteria_comment)

    seen: set = set()
    combined: List[CronEntry] = []
    for e in by_command + by_comment:
        key = id(e)
        if key not in seen:
            seen.add(key)
            combined.append(e)
    return combined
