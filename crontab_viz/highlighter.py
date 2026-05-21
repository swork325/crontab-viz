"""Syntax highlighting utilities for cron schedule fields."""
from dataclasses import dataclass
from typing import List, Tuple

# ANSI colour codes
_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_DIM = "\033[2m"

# One colour per cron field position
_FIELD_COLOURS = [_CYAN, _GREEN, _YELLOW, _MAGENTA, _RED]
_FIELD_NAMES = ["minute", "hour", "day-of-month", "month", "day-of-week"]


@dataclass
class HighlightedSchedule:
    """Colourised representation of a cron schedule string."""
    raw: str
    coloured: str
    field_labels: List[Tuple[str, str]]  # [(field_name, value), ...]


def highlight_schedule(schedule: str) -> HighlightedSchedule:
    """Return a HighlightedSchedule with ANSI-coloured fields.

    Handles standard 5-field expressions and @special shortcuts.
    """
    if schedule.startswith("@"):
        coloured = f"{_BOLD}{_CYAN}{schedule}{_RESET}"
        return HighlightedSchedule(
            raw=schedule,
            coloured=coloured,
            field_labels=[("special", schedule)],
        )

    parts = schedule.split()
    if len(parts) != 5:
        # Fall back to plain display for unrecognised formats
        return HighlightedSchedule(raw=schedule, coloured=schedule, field_labels=[])

    coloured_parts: List[str] = []
    field_labels: List[Tuple[str, str]] = []
    for i, (part, colour, name) in enumerate(zip(parts, _FIELD_COLOURS, _FIELD_NAMES)):
        coloured_parts.append(f"{colour}{part}{_RESET}")
        field_labels.append((name, part))

    return HighlightedSchedule(
        raw=schedule,
        coloured=" ".join(coloured_parts),
        field_labels=field_labels,
    )


def highlight_command(command: str, max_len: int = 60) -> str:
    """Return a dimmed, optionally truncated command string."""
    truncated = command if len(command) <= max_len else command[:max_len - 1] + "…"
    return f"{_DIM}{truncated}{_RESET}"


def highlight_comment(comment: str) -> str:
    """Return a dimmed green comment string."""
    return f"{_DIM}{_GREEN}{comment}{_RESET}" if comment else ""
