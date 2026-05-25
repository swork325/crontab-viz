"""Optimizer: suggests more efficient cron schedule expressions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from crontab_viz.parser import CronEntry


@dataclass
class OptimizationSuggestion:
    entry: CronEntry
    original_schedule: str
    suggested_schedule: str
    reason: str

    def __str__(self) -> str:
        cmd = self.entry.command or "<no command>"
        return (
            f"[{cmd}] {self.original_schedule!r} -> {self.suggested_schedule!r}: "
            f"{self.reason}"
        )


def _schedule_str(entry: CronEntry) -> str:
    if entry.special:
        return entry.special
    return " ".join([
        entry.minute or "*",
        entry.hour or "*",
        entry.dom or "*",
        entry.month or "*",
        entry.dow or "*",
    ])


def _check_redundant_wildcards(entry: CronEntry) -> Optional[OptimizationSuggestion]:
    """Suggest @daily/@hourly when fields collapse to a known special."""
    if entry.special:
        return None
    m, h, dom, mon, dow = (
        entry.minute, entry.hour, entry.dom, entry.month, entry.dow
    )
    original = _schedule_str(entry)
    if m == "0" and h == "0" and dom == "*" and mon == "*" and dow == "*":
        return OptimizationSuggestion(entry, original, "@daily",
                                      "Equivalent to @daily; use special form for clarity")
    if m == "0" and h == "*" and dom == "*" and mon == "*" and dow == "*":
        return OptimizationSuggestion(entry, original, "@hourly",
                                      "Equivalent to @hourly; use special form for clarity")
    if m == "0" and h == "0" and dom == "1" and mon == "*" and dow == "*":
        return OptimizationSuggestion(entry, original, "@monthly",
                                      "Equivalent to @monthly; use special form for clarity")
    if m == "0" and h == "0" and dom == "*" and mon == "*" and dow == "0":
        return OptimizationSuggestion(entry, original, "@weekly",
                                      "Equivalent to @weekly; use special form for clarity")
    return None


def _check_duplicate_wildcards(entry: CronEntry) -> Optional[OptimizationSuggestion]:
    """Detect patterns like */1 which are equivalent to *."""
    if entry.special:
        return None
    fields = [entry.minute, entry.hour, entry.dom, entry.month, entry.dow]
    names = ["minute", "hour", "dom", "month", "dow"]
    for f, name in zip(fields, names):
        if f and f.endswith("/1") and f.startswith("*"):
            original = _schedule_str(entry)
            return OptimizationSuggestion(
                entry, original, original.replace(f, "*"),
                f"Field '{name}': '{f}' is equivalent to '*'; simplify to '*'"
            )
    return None


def optimize_entry(entry: CronEntry) -> List[OptimizationSuggestion]:
    """Return all optimization suggestions for a single entry."""
    if not entry.is_valid:
        return []
    suggestions: List[OptimizationSuggestion] = []
    for check in (_check_redundant_wildcards, _check_duplicate_wildcards):
        result = check(entry)
        if result:
            suggestions.append(result)
    return suggestions


def optimize_entries(entries: List[CronEntry]) -> List[OptimizationSuggestion]:
    """Return all optimization suggestions across a list of entries."""
    suggestions: List[OptimizationSuggestion] = []
    for entry in entries:
        suggestions.extend(optimize_entry(entry))
    return suggestions
