"""Compare two sets of crontab entries and produce a human-readable comparison report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import next_run, format_countdown


def _entry_key(entry: CronEntry) -> str:
    """Stable key based on schedule fields and command."""
    return f"{entry.schedule_str}|{entry.command.strip()}"


@dataclass
class ComparisonRow:
    command: str
    schedule_a: str
    schedule_b: str
    next_run_a: str
    next_run_b: str
    status: str  # 'same', 'changed', 'only_a', 'only_b'


@dataclass
class ComparisonReport:
    rows: List[ComparisonRow] = field(default_factory=list)

    @property
    def only_in_a(self) -> List[ComparisonRow]:
        return [r for r in self.rows if r.status == "only_a"]

    @property
    def only_in_b(self) -> List[ComparisonRow]:
        return [r for r in self.rows if r.status == "only_b"]

    @property
    def changed(self) -> List[ComparisonRow]:
        return [r for r in self.rows if r.status == "changed"]

    @property
    def same(self) -> List[ComparisonRow]:
        return [r for r in self.rows if r.status == "same"]

    def summary(self) -> str:
        return (
            f"same={len(self.same)}, changed={len(self.changed)}, "
            f"only_a={len(self.only_in_a)}, only_b={len(self.only_in_b)}"
        )


def _next_run_label(entry: CronEntry) -> str:
    if not entry.is_valid:
        return "invalid"
    dt = next_run(entry)
    if dt is None:
        return "unknown"
    return format_countdown(dt)


def compare_entries(
    entries_a: Sequence[CronEntry],
    entries_b: Sequence[CronEntry],
) -> ComparisonReport:
    """Compare two lists of CronEntry objects and return a ComparisonReport."""
    map_a: dict[str, CronEntry] = {}
    for e in entries_a:
        key = e.command.strip()
        map_a[key] = e

    map_b: dict[str, CronEntry] = {}
    for e in entries_b:
        key = e.command.strip()
        map_b[key] = e

    rows: List[ComparisonRow] = []
    all_commands = sorted(set(map_a) | set(map_b))

    for cmd in all_commands:
        in_a = cmd in map_a
        in_b = cmd in map_b

        if in_a and in_b:
            ea, eb = map_a[cmd], map_b[cmd]
            status = "same" if ea.schedule_str == eb.schedule_str else "changed"
            rows.append(ComparisonRow(
                command=cmd,
                schedule_a=ea.schedule_str,
                schedule_b=eb.schedule_str,
                next_run_a=_next_run_label(ea),
                next_run_b=_next_run_label(eb),
                status=status,
            ))
        elif in_a:
            ea = map_a[cmd]
            rows.append(ComparisonRow(
                command=cmd,
                schedule_a=ea.schedule_str,
                schedule_b="—",
                next_run_a=_next_run_label(ea),
                next_run_b="—",
                status="only_a",
            ))
        else:
            eb = map_b[cmd]
            rows.append(ComparisonRow(
                command=cmd,
                schedule_a="—",
                schedule_b=eb.schedule_str,
                next_run_a="—",
                next_run_b=_next_run_label(eb),
                status="only_b",
            ))

    return ComparisonReport(rows=rows)
