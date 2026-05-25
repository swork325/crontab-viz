"""Heatmap renderer: shows job frequency across hours and days of week."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from crontab_viz.parser import CronEntry
from crontab_viz.calendar_view import CalendarMatrix

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
HOURS = list(range(24))

_SHADES = [" ", "░", "▒", "▓", "█"]


@dataclass
class Heatmap:
    """Aggregated hit-count grid: rows=days(0-6), cols=hours(0-23)."""
    grid: List[List[int]] = field(default_factory=lambda: [[0] * 24 for _ in range(7)])

    def add(self, matrix: CalendarMatrix) -> None:
        """Accumulate a CalendarMatrix into the heatmap grid."""
        for dow in range(7):
            for hour in range(24):
                self.grid[dow][hour] += matrix.cells[dow][hour]

    def max_value(self) -> int:
        return max(v for row in self.grid for v in row) or 1


def build_heatmap(entries: List[CronEntry]) -> Heatmap:
    """Build a Heatmap from a list of CronEntry objects."""
    hm = Heatmap()
    for entry in entries:
        if not entry.is_valid:
            continue
        matrix = CalendarMatrix(entry)
        hm.add(matrix)
    return hm


def render_heatmap(hm: Heatmap) -> str:
    """Render the heatmap as a plain-text grid string."""
    max_val = hm.max_value()
    lines: List[str] = []

    # Header: hour labels (every 3 hours)
    header = "     " + "".join(
        f"{h:02d} " if h % 3 == 0 else "   " for h in HOURS
    )
    lines.append(header)
    lines.append("     " + "-" * (24 * 3))

    for dow, day_name in enumerate(DAYS):
        row_chars = []
        for hour in range(24):
            val = hm.grid[dow][hour]
            shade_idx = min(int(val / max_val * (len(_SHADES) - 1)), len(_SHADES) - 1)
            row_chars.append(_SHADES[shade_idx] * 2 + " ")
        lines.append(f"{day_name}  " + "".join(row_chars))

    lines.append("")
    lines.append(f"Legend: {' '.join(_SHADES)}  (0 → {max_val} jobs)")
    return "\n".join(lines)
