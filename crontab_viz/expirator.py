"""Expirator: detect cron entries that may have outlived their usefulness.

An entry is considered 'stale' if its comment contains a date-like token
(e.g. 2023-01-15) that is in the past, or if the command references a
path that looks like a temporary/one-off artefact.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

from crontab_viz.parser import CronEntry

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_TEMP_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\btmp\b",
        r"\btemp\b",
        r"\btest\b",
        r"\bone.?off\b",
        r"/tmp/",
    ]
]


@dataclass
class ExpirationWarning:
    entry: CronEntry
    reason: str
    date_found: Optional[date] = None

    def __str__(self) -> str:
        cmd = self.entry.command or "<no command>"
        if self.date_found:
            return f"[STALE {self.date_found}] {cmd}: {self.reason}"
        return f"[STALE] {cmd}: {self.reason}"


def _extract_date(text: str) -> Optional[date]:
    """Return the first ISO date found in *text*, or None."""
    m = _DATE_RE.search(text)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _is_temp_command(command: str) -> bool:
    return any(p.search(command) for p in _TEMP_PATTERNS)


def check_expiration(
    entries: List[CronEntry],
    reference: Optional[date] = None,
) -> List[ExpirationWarning]:
    """Return expiration warnings for *entries*.

    Args:
        entries: Parsed cron entries to inspect.
        reference: The date to compare against; defaults to today.

    Returns:
        A list of :class:`ExpirationWarning` objects (may be empty).
    """
    today = reference or datetime.utcnow().date()
    warnings: List[ExpirationWarning] = []

    for entry in entries:
        if not entry.is_valid:
            continue

        comment = entry.comment or ""
        command = entry.command or ""

        found_date = _extract_date(comment) or _extract_date(command)
        if found_date and found_date < today:
            warnings.append(
                ExpirationWarning(
                    entry=entry,
                    reason="contains a past date",
                    date_found=found_date,
                )
            )
            continue

        if _is_temp_command(command):
            warnings.append(
                ExpirationWarning(
                    entry=entry,
                    reason="command looks like a temporary/one-off job",
                )
            )

    return warnings
