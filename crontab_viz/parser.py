"""Crontab entry parser module."""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class CronEntry:
    """Represents a single parsed crontab entry."""

    raw: str
    schedule: str
    command: str
    comment: Optional[str] = None
    fields: dict = field(default_factory=dict)

    def __post_init__(self):
        self.fields = self._parse_fields()

    def _parse_fields(self) -> dict:
        parts = self.schedule.split()
        if len(parts) != 5:
            return {}
        keys = ["minute", "hour", "day_of_month", "month", "day_of_week"]
        return dict(zip(keys, parts))

    def is_valid(self) -> bool:
        return len(self.fields) == 5


SPECIAL_SCHEDULES = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


def parse_crontab_line(line: str) -> Optional[CronEntry]:
    """Parse a single crontab line into a CronEntry."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    comment = None
    if " #" in line:
        line, comment = line.split(" #", 1)
        comment = comment.strip()
        line = line.strip()

    for alias, expansion in SPECIAL_SCHEDULES.items():
        if line.startswith(alias):
            command = line[len(alias):].strip()
            return CronEntry(raw=line, schedule=expansion, command=command, comment=comment)

    parts = line.split(None, 5)
    if len(parts) < 6:
        return None

    schedule = " ".join(parts[:5])
    command = parts[5]
    return CronEntry(raw=line, schedule=schedule, command=command, comment=comment)


def parse_crontab(text: str) -> list[CronEntry]:
    """Parse a full crontab file text and return valid entries."""
    entries = []
    for line in text.splitlines():
        entry = parse_crontab_line(line)
        if entry and entry.is_valid():
            entries.append(entry)
    return entries
