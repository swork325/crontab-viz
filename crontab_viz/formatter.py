"""Format cron entries and their schedules for terminal display."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import countdown, format_countdown, next_run

# Column widths
_W_SCHEDULE = 20
_W_COMMAND = 36
_W_NEXT = 17
_W_COUNTDOWN = 12

_HEADER_COLOUR = "\033[1;34m"  # bold blue
_RESET = "\033[0m"
_BORDER = "\033[90m"           # dark grey


@dataclass
class FormattedRow:
    schedule: str
    command: str
    next_run_str: str
    countdown_str: str
    is_valid: bool


def _schedule_str(entry: CronEntry) -> str:
    """Return a compact schedule string for display."""
    if entry.is_reboot:
        return "@reboot"
    if not entry.is_valid():
        return "<invalid>"
    return entry.schedule


def format_entry(
    entry: CronEntry,
    reference: Optional[datetime] = None,
) -> FormattedRow:
    """Build a :class:`FormattedRow` for *entry*."""
    ref = reference or datetime.now()

    if entry.is_reboot:
        return FormattedRow(
            schedule="@reboot",
            command=entry.command,
            next_run_str="N/A (on reboot)",
            countdown_str="—",
            is_valid=True,
        )

    if not entry.is_valid():
        return FormattedRow(
            schedule=entry.schedule,
            command=entry.command,
            next_run_str="invalid",
            countdown_str="—",
            is_valid=False,
        )

    nxt = next_run(entry, after=ref)
    delta = countdown(entry, after=ref)

    next_str = nxt.strftime("%Y-%m-%d %H:%M") if nxt else "N/A"
    cd_str = format_countdown(delta)

    return FormattedRow(
        schedule=_schedule_str(entry),
        command=entry.command,
        next_run_str=next_str,
        countdown_str=cd_str,
        is_valid=True,
    )


def render_table(rows: List[FormattedRow], *, colour: bool = True) -> str:
    """Render a list of :class:`FormattedRow` as a fixed-width terminal table."""
    col_widths = {"schedule": _W_SCHEDULE, "command": _W_COMMAND, "next_run": _W_NEXT, "countdown": _W_COUNTDOWN}
    sep = f"{_BORDER}{'─' * (sum(col_widths.values()) + 13)}{_RESET}\n" if colour else ""

    header = (
        f"{_HEADER_COLOUR if colour else ''}"
        f"{'SCHEDULE':<{col_widths['schedule']}}  "
        f"{'COMMAND':<{col_widths['command']}}  "
        f"{'NEXT RUN':<{col_widths['next_run']}}  "
        f"{'COUNTDOWN':<{col_widths['countdown']}}"
        f"{_RESET if colour else ''}\n"
    )
    lines = [sep, header, sep]

    for row in rows:
        sched_col = row.schedule
        cmd_col = row.command[: col_widths["command"]]
        line = (
            f"{sched_col:<{col_widths['schedule']}}  "
            f"{cmd_col:<{col_widths['command']}}  "
            f"{row.next_run_str:<{col_widths['next_run']}}  "
            f"{row.countdown_str:<{col_widths['countdown']}}\n"
        )
        lines.append(line)

    lines.append(sep)
    return "".join(lines)


def format_entries(entries: List[CronEntry], *, colour: bool = True, reference: Optional[datetime] = None) -> str:
    """Format a list of CronEntry objects into a rendered table string."""
    rows = [format_entry(e, reference=reference) for e in entries]
    return render_table(rows, colour=colour)
