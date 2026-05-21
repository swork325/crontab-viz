"""Formatting utilities for rendering cron entries as a terminal table."""
from dataclasses import dataclass
from typing import List

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run, format_countdown
from crontab_viz.highlighter import highlight_schedule, highlight_command, highlight_comment

_HEADER_COLOUR = "\033[1;34m"  # bold blue
_RESET = "\033[0m"
_BORDER = "\033[90m"           # dark grey


@dataclass
class FormattedRow:
    schedule: str          # plain schedule string
    command: str
    comment: str
    next_run_str: str
    countdown_str: str
    is_valid: bool


def _schedule_str(entry: CronEntry) -> str:
    """Return a compact schedule string for the entry."""
    if entry.special:
        return entry.special
    return " ".join([
        entry.minute, entry.hour, entry.day_of_month,
        entry.month, entry.day_of_week,
    ])


def format_entry(entry: CronEntry) -> FormattedRow:
    """Convert a CronEntry into a FormattedRow."""
    sched = _schedule_str(entry)
    if entry.is_valid():
        nr = next_run(entry)
        nr_str = nr.strftime("%Y-%m-%d %H:%M") if nr else "N/A"
        cd_str = format_countdown(entry)
    else:
        nr_str = "invalid"
        cd_str = "—"

    return FormattedRow(
        schedule=sched,
        command=entry.command,
        comment=entry.comment or "",
        next_run_str=nr_str,
        countdown_str=cd_str,
        is_valid=entry.is_valid(),
    )


def render_table(rows: List[FormattedRow], *, colour: bool = True) -> str:
    """Render a list of FormattedRows as a fixed-width terminal table."""
    col_widths = {"schedule": 20, "command": 36, "next_run": 17, "countdown": 12}
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
        if colour:
            sched_col = highlight_schedule(row.schedule).coloured
            cmd_col = highlight_command(row.command, max_len=col_widths["command"])
            comment_col = highlight_comment(row.comment)
        else:
            sched_col = row.schedule
            cmd_col = row.command[: col_widths["command"]]
            comment_col = row.comment

        line = (
            f"{sched_col:<{col_widths['schedule']}}  "
            f"{cmd_col:<{col_widths['command']}}  "
            f"{row.next_run_str:<{col_widths['next_run']}}  "
            f"{row.countdown_str:<{col_widths['countdown']}}\n"
        )
        lines.append(line)

    lines.append(sep)
    return "".join(lines)


def format_entries(entries: List[CronEntry], *, colour: bool = True) -> str:
    """Format a list of CronEntry objects into a rendered table string."""
    rows = [format_entry(e) for e in entries]
    return render_table(rows, colour=colour)
