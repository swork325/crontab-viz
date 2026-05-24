"""Suggests cron schedule improvements based on entry analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from crontab_viz.parser import CronEntry


@dataclass
class Recommendation:
    entry: CronEntry
    message: str
    suggestion: str
    severity: str  # 'info' | 'warning' | 'improvement'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.message} -> {self.suggestion}"


def _is_every_minute(entry: CronEntry) -> bool:
    return all(f == "*" for f in entry.fields)


def _is_every_second_minute(entry: CronEntry) -> bool:
    if len(entry.fields) < 1:
        return False
    return entry.fields[0] == "*/1"


def _has_no_comment(entry: CronEntry) -> bool:
    return not entry.comment or entry.comment.strip() == ""


def _is_missing_absolute_path(entry: CronEntry) -> bool:
    cmd = entry.command.strip()
    return bool(cmd) and not cmd.startswith("/") and not cmd.startswith("~")


def _runs_too_frequently(entry: CronEntry) -> bool:
    """Heuristic: runs more often than every 5 minutes."""
    if not entry.fields or entry.fields[0] == "*":
        return True
    first = entry.fields[0]
    if first.startswith("*/"):
        try:
            step = int(first[2:])
            return step < 5
        except ValueError:
            return False
    return False


def recommend(entry: CronEntry) -> List[Recommendation]:
    """Return a list of recommendations for a single cron entry."""
    recs: List[Recommendation] = []

    if not entry.is_valid:
        recs.append(Recommendation(
            entry=entry,
            message="Entry is invalid and will not run",
            suggestion="Fix the schedule fields or command",
            severity="warning",
        ))
        return recs

    if _is_every_minute(entry) or _is_every_second_minute(entry):
        recs.append(Recommendation(
            entry=entry,
            message="Job runs every minute which may overload the system",
            suggestion="Use */5 or a specific time range instead",
            severity="warning",
        ))
    elif _runs_too_frequently(entry):
        recs.append(Recommendation(
            entry=entry,
            message="Job runs more frequently than every 5 minutes",
            suggestion="Consider spacing runs further apart",
            severity="info",
        ))

    if _has_no_comment(entry):
        recs.append(Recommendation(
            entry=entry,
            message="Entry has no descriptive comment",
            suggestion="Add an inline comment to document the job's purpose",
            severity="info",
        ))

    if _is_missing_absolute_path(entry):
        recs.append(Recommendation(
            entry=entry,
            message="Command does not use an absolute path",
            suggestion="Use the full path (e.g. /usr/bin/python3) for reliability",
            severity="improvement",
        ))

    return recs


def recommend_all(entries: List[CronEntry]) -> List[Recommendation]:
    """Return recommendations for all entries."""
    results: List[Recommendation] = []
    for entry in entries:
        results.extend(recommend(entry))
    return results
