"""Calendar-style view showing which hours/days cron jobs are scheduled to run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import _field_matches

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
HOURS = list(range(24))


@dataclass
class CalendarMatrix:
    """A 7-day x 24-hour activity matrix for a set of cron entries."""
    entries: List[CronEntry]
    # matrix[day][hour] = count of jobs active at that slot
    matrix: Dict[int, Dict[int, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.matrix = {d: {h: 0 for h in HOURS} for d in range(7)}
        for entry in self.entries:
            if entry.is_valid:
                self._fill(entry)

    def _fill(self, entry: CronEntry) -> None:
        fields = entry.fields
        if fields is None:
            return
        minute_f, hour_f, _dom, _month, dow_f = fields
        for day in range(7):
            if _field_matches(dow_f, day):
                for hour in HOURS:
                    if _field_matches(hour_f, hour):
                        self.matrix[day][hour] += 1

    def busiest_hour(self) -> int:
        """Return the hour (0-23) with the most scheduled jobs across all days."""
        totals = {h: sum(self.matrix[d][h] for d in range(7)) for h in HOURS}
        return max(totals, key=lambda h: totals[h])

    def busiest_day(self) -> str:
        """Return the day name with the most scheduled jobs."""
        totals = {d: sum(self.matrix[d][h] for h in HOURS) for d in range(7)}
        return DAYS[max(totals, key=lambda d: totals[d])]


def render_calendar(matrix: CalendarMatrix) -> str:
    """Render a compact ASCII calendar grid (days x hours)."""
    col_w = 3
    header = "     " + "".join(f"{h:>{col_w}}" for h in HOURS)
    lines = [header, "     " + "-" * (col_w * 24)]
    for d in range(7):
        row = f"{DAYS[d]:>4} |"
        for h in HOURS:
            count = matrix.matrix[d][h]
            cell = "." if count == 0 else str(min(count, 9))
            row += f"{cell:>{col_w}}"
        lines.append(row)
    return "\n".join(lines)
