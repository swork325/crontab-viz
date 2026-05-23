"""Compute statistical metrics over a list of CronEntry objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run

from datetime import datetime, timezone


@dataclass
class CrontabStatistics:
    total: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    special_count: int = 0
    standard_count: int = 0
    unique_commands: int = 0
    most_common_commands: List[tuple] = field(default_factory=list)
    busiest_hour: int | None = None
    busiest_hour_count: int = 0
    avg_runs_per_day: float = 0.0
    next_due_command: str = ""
    next_due_in_seconds: float | None = None

    def as_dict(self) -> Dict:
        return {
            "total": self.total,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "special_count": self.special_count,
            "standard_count": self.standard_count,
            "unique_commands": self.unique_commands,
            "most_common_commands": self.most_common_commands,
            "busiest_hour": self.busiest_hour,
            "busiest_hour_count": self.busiest_hour_count,
            "avg_runs_per_day": round(self.avg_runs_per_day, 4),
            "next_due_command": self.next_due_command,
            "next_due_in_seconds": self.next_due_in_seconds,
        }


def _estimate_daily_runs(entry: CronEntry) -> float:
    """Rough estimate of how many times a standard cron entry fires per day."""
    if not entry.is_valid:
        return 0.0
    if entry.special:
        mapping = {
            "@yearly": 1 / 365,
            "@annually": 1 / 365,
            "@monthly": 1 / 30,
            "@weekly": 1 / 7,
            "@daily": 1.0,
            "@midnight": 1.0,
            "@hourly": 24.0,
            "@reboot": 0.0,
        }
        return mapping.get(entry.special.lower(), 0.0)
    try:
        minute_vals = entry.fields["minute"]
        hour_vals = entry.fields["hour"]
        minutes_per_day = len(minute_vals) * len(hour_vals)
        return float(minutes_per_day) / 60.0
    except Exception:
        return 0.0


def compute_statistics(entries: List[CronEntry], top_n: int = 3) -> CrontabStatistics:
    """Compute aggregate statistics for a list of CronEntry objects."""
    now = datetime.now(tz=timezone.utc)
    stats = CrontabStatistics()
    stats.total = len(entries)

    command_counter: Counter = Counter()
    hour_counter: Counter = Counter()
    daily_runs_total = 0.0
    soonest_delta: float | None = None
    soonest_command = ""

    for entry in entries:
        if entry.is_valid:
            stats.valid_count += 1
            if entry.special:
                stats.special_count += 1
            else:
                stats.standard_count += 1
                try:
                    for h in entry.fields.get("hour", []):
                        hour_counter[h] += 1
                except Exception:
                    pass
            command_counter[entry.command.strip()] += 1
            daily_runs_total += _estimate_daily_runs(entry)
            try:
                nxt = next_run(entry, now)
                delta = (nxt - now).total_seconds()
                if soonest_delta is None or delta < soonest_delta:
                    soonest_delta = delta
                    soonest_command = entry.command.strip()
            except Exception:
                pass
        else:
            stats.invalid_count += 1

    stats.unique_commands = len(command_counter)
    stats.most_common_commands = command_counter.most_common(top_n)
    if hour_counter:
        busiest = hour_counter.most_common(1)[0]
        stats.busiest_hour = busiest[0]
        stats.busiest_hour_count = busiest[1]
    stats.avg_runs_per_day = daily_runs_total / max(stats.valid_count, 1)
    stats.next_due_command = soonest_command
    stats.next_due_in_seconds = soonest_delta
    return stats
