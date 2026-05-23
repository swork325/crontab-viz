"""Score crontab entries by complexity and risk for prioritised review."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import CronEntry


@dataclass
class EntryScore:
    entry: CronEntry
    complexity: int = 0
    risk: int = 0
    notes: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.complexity + self.risk

    def as_dict(self) -> dict:
        return {
            "command": self.entry.command,
            "schedule": self.entry.raw_schedule,
            "complexity": self.complexity,
            "risk": self.risk,
            "total": self.total,
            "notes": self.notes,
        }


def _complexity_score(entry: CronEntry) -> tuple[int, list[str]]:
    """Return a complexity score and explanatory notes for the schedule."""
    score = 0
    notes: list[str] = []

    if not entry.is_valid:
        return 0, []

    if entry.raw_schedule.startswith("@"):
        return 1, ["special schedule macro"]

    fields = [entry.minute, entry.hour, entry.day_of_month, entry.month, entry.day_of_week]
    labels = ["minute", "hour", "dom", "month", "dow"]

    for value, label in zip(fields, labels):
        if value == "*":
            continue
        score += 1
        if "," in value:
            score += 1
            notes.append(f"{label} uses list")
        if "-" in value:
            score += 1
            notes.append(f"{label} uses range")
        if "/" in value:
            score += 1
            notes.append(f"{label} uses step")

    return score, notes


def _risk_score(entry: CronEntry) -> tuple[int, list[str]]:
    """Return a risk score based on command characteristics."""
    score = 0
    notes: list[str] = []
    cmd = entry.command.lower()

    risky_patterns = [
        ("rm ", "uses rm"),
        ("sudo", "uses sudo"),
        ("curl", "downloads via curl"),
        ("wget", "downloads via wget"),
        ("> /dev/", "redirects to device"),
        ("dd ", "uses dd"),
        ("|sh", "pipes to shell"),
        ("|bash", "pipes to bash"),
    ]

    for pattern, note in risky_patterns:
        if pattern in cmd:
            score += 2
            notes.append(note)

    if not cmd.strip():
        score += 3
        notes.append("empty command")

    if entry.minute == "*" and entry.hour == "*":
        score += 2
        notes.append("runs every minute")

    return score, notes


def score_entry(entry: CronEntry) -> EntryScore:
    """Compute a full score for a single crontab entry."""
    es = EntryScore(entry=entry)
    if not entry.is_valid:
        es.risk = 1
        es.notes.append("invalid entry")
        return es

    c, c_notes = _complexity_score(entry)
    r, r_notes = _risk_score(entry)
    es.complexity = c
    es.risk = r
    es.notes = c_notes + r_notes
    return es


def score_entries(entries: List[CronEntry]) -> List[EntryScore]:
    """Score all entries, sorted by total score descending."""
    scored = [score_entry(e) for e in entries]
    return sorted(scored, key=lambda s: s.total, reverse=True)
