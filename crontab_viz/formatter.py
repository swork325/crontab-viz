"""Format cron entries and their schedules for terminal display."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import countdown, format_countdown, next_run

# Column widths
_W_SCHEDULE = 20
_W_NEXT = 16
_W_COUNTDOWN = 10


@dataclass
class FormattedRow:
    schedule: str
    command: str
    next_run_str: str
    countdown_str: str
    is_valid: bool


def _schedule_str(entry: CronEntry) -> str:
    """Return a compact schedule string for display."""
    if not entry.is_valid:
        return "<invalid>"
    return " ".join(entry.fields)


def format_entry(
    entry: CronEntry,
    reference: Optional[datetime] = None,
) -> FormattedRow:
    """Build a :class:`FormattedRow` for *entry*."""
    ref = reference or datetime.now()
    nxt = next_run(entry, after=ref)
    delta = countdown(entry, after=ref)

    next_str = nxt.strftime("%Y-%m-%d %H:%M") if nxt else "N/A"
    cd_str = format_countdown(delta)

    return FormattedRow(
        schedule=_schedule_str(entry),
        command=entry.command,
        next_run_str=next_str,
        countdown_str=cd_str,
        is_valid=entry.is_valid,
    )


def render_table(rows: List[FormattedRow]) -> str:
    """Render a list of :class:`FormattedRow` as a plain-text table."""
    header = (
        f"{'SCHEDULE':<{_W_SCHEDULE}}"
        f"{'NEXT RUN':<{_W_NEXT}}"
        f"{'IN':<{_W_COUNTDOWN}}"
        f"COMMAND"
    )
    separator = "-" * (len(header) + 20)
    lines = [header, separator]
    for row in rows:
        prefix = "" if row.is_valid else "! "
        lines.append(
            f"{prefix}{row.schedule:<{_W_SCHEDULE}}"
            f"{row.next_run_str:<{_W_NEXT}}"
            f"{row.countdown_str:<{_W_COUNTDOWN}}"
            f"{row.command}"
        )
    return "\n".join(lines)


def format_entries(
    entries: List[CronEntry],
    reference: Optional[datetime] = None,
) -> str:
    """Convenience wrapper: format a list of entries into a table string."""
    rows = [format_entry(e, reference=reference) for e in entries]
    return render_table(rows)
