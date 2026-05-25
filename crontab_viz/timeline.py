"""Timeline: build a chronological view of upcoming cron job runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_n_runs


@dataclass
class TimelineEvent:
    """A single scheduled event on the timeline."""
    run_at: datetime
    command: str
    comment: str
    schedule: str

    def __str__(self) -> str:
        ts = self.run_at.strftime("%Y-%m-%d %H:%M")
        label = f"[{self.comment}]" if self.comment else ""
        return f"{ts}  {self.schedule:<20}  {self.command}  {label}".rstrip()


@dataclass
class Timeline:
    """Ordered collection of upcoming TimelineEvents."""
    events: List[TimelineEvent] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    def earliest(self) -> Optional[TimelineEvent]:
        return self.events[0] if self.events else None

    def latest(self) -> Optional[TimelineEvent]:
        return self.events[-1] if self.events else None


def build_timeline(
    entries: List[CronEntry],
    *,
    n: int = 5,
    now: Optional[datetime] = None,
) -> Timeline:
    """Return a Timeline of the next *n* runs per valid entry, sorted by time."""
    if now is None:
        now = datetime.now()

    events: List[TimelineEvent] = []
    for entry in entries:
        if not entry.is_valid:
            continue
        schedule = (
            entry.special
            if entry.special
            else " ".join([
                entry.minute, entry.hour,
                entry.dom, entry.month, entry.dow,
            ])
        )
        for run_at in next_n_runs(entry, n=n, now=now):
            events.append(
                TimelineEvent(
                    run_at=run_at,
                    command=entry.command,
                    comment=entry.comment or "",
                    schedule=schedule,
                )
            )

    events.sort(key=lambda e: e.run_at)
    return Timeline(events=events)


def render_timeline(timeline: Timeline) -> str:
    """Render a Timeline as a plain-text string."""
    if not timeline.events:
        return "No upcoming runs found."
    header = f"{'TIME':<17}  {'SCHEDULE':<20}  COMMAND"
    separator = "-" * 60
    lines = [header, separator]
    for event in timeline.events:
        lines.append(str(event))
    return "\n".join(lines)
