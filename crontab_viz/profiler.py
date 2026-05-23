"""Profiler module: analyse crontab entries for execution frequency patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_n_runs

import datetime


@dataclass
class FrequencyProfile:
    """Frequency analysis for a single crontab entry."""
    entry: CronEntry
    runs_per_day: float
    runs_per_hour: float
    busiest_hour: int  # 0-23, or -1 if unknown
    sample_next_runs: List[datetime.datetime] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return {
            "command": self.entry.command,
            "schedule": self.entry.raw,
            "runs_per_day": round(self.runs_per_day, 4),
            "runs_per_hour": round(self.runs_per_hour, 4),
            "busiest_hour": self.busiest_hour,
            "sample_next_runs": [
                r.isoformat() for r in self.sample_next_runs
            ],
        }


def _busiest_hour(runs: List[datetime.datetime]) -> int:
    """Return the hour (0-23) that appears most in *runs*, or -1 if empty."""
    if not runs:
        return -1
    counts: Dict[int, int] = {}
    for r in runs:
        counts[r.hour] = counts.get(r.hour, 0) + 1
    return max(counts, key=lambda h: counts[h])


def profile_entry(
    entry: CronEntry,
    sample_size: int = 48,
    reference: datetime.datetime | None = None,
) -> FrequencyProfile | None:
    """Return a FrequencyProfile for *entry*, or None if the entry is invalid."""
    if not entry.is_valid:
        return None

    ref = reference or datetime.datetime.now()
    runs = next_n_runs(entry, sample_size, ref)
    if not runs:
        return None

    # Estimate daily/hourly rate from the sample window
    window_hours = (
        (runs[-1] - runs[0]).total_seconds() / 3600.0 if len(runs) > 1 else 24.0
    )
    window_days = window_hours / 24.0 or 1.0
    runs_per_day = len(runs) / window_days
    runs_per_hour = runs_per_day / 24.0

    return FrequencyProfile(
        entry=entry,
        runs_per_day=runs_per_day,
        runs_per_hour=runs_per_hour,
        busiest_hour=_busiest_hour(runs),
        sample_next_runs=runs[:5],
    )


def profile_entries(
    entries: List[CronEntry],
    sample_size: int = 48,
    reference: datetime.datetime | None = None,
) -> List[FrequencyProfile]:
    """Return FrequencyProfile objects for all valid entries."""
    results = []
    for entry in entries:
        prof = profile_entry(entry, sample_size=sample_size, reference=reference)
        if prof is not None:
            results.append(prof)
    return results
