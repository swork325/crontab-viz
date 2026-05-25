"""Detect potential scheduling dependencies between cron entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import CronEntry
from .scheduler import next_run


@dataclass
class DependencyLink:
    """A potential dependency relationship between two cron entries."""
    predecessor: CronEntry
    successor: CronEntry
    gap_seconds: int
    reason: str

    def __str__(self) -> str:
        pred = self.predecessor.command or "<unknown>"
        succ = self.successor.command or "<unknown>"
        return f"{pred!r} -> {succ!r} (gap={self.gap_seconds}s, reason={self.reason})"


@dataclass
class DependencyReport:
    """Collection of detected dependency links."""
    links: List[DependencyLink] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.links)

    def as_dict(self) -> dict:
        return {
            "link_count": self.count,
            "links": [
                {
                    "predecessor": lnk.predecessor.command,
                    "successor": lnk.successor.command,
                    "gap_seconds": lnk.gap_seconds,
                    "reason": lnk.reason,
                }
                for lnk in self.links
            ],
        }


def _share_command_token(a: CronEntry, b: CronEntry) -> Optional[str]:
    """Return a shared meaningful token between two commands, or None."""
    if not a.command or not b.command:
        return None
    tokens_a = set(a.command.split())
    tokens_b = set(b.command.split())
    shared = tokens_a & tokens_b - {"/bin/bash", "sh", "-c", "&&", "||"}
    return next(iter(shared), None)


def detect_dependencies(
    entries: List[CronEntry],
    gap_threshold_seconds: int = 300,
    reference: Optional[object] = None,
) -> DependencyReport:
    """Detect entries that may depend on each other.

    Two entries are considered potentially dependent when:
    - They share a meaningful command token, OR
    - Their next-run times are within *gap_threshold_seconds* of each other.
    """
    import datetime

    now = reference or datetime.datetime.now()
    valid = [e for e in entries if e.is_valid]
    report = DependencyReport()

    for i, a in enumerate(valid):
        nr_a = next_run(a, now)
        for b in valid[i + 1 :]:
            nr_b = next_run(b, now)
            reasons = []
            token = _share_command_token(a, b)
            if token:
                reasons.append(f"shared token '{token}'")
            if nr_a and nr_b:
                gap = int(abs((nr_b - nr_a).total_seconds()))
                if gap <= gap_threshold_seconds:
                    reasons.append(f"next-run gap {gap}s")
                if reasons:
                    pred, succ = (a, b) if (nr_a <= nr_b) else (b, a)
                    report.links.append(
                        DependencyLink(
                            predecessor=pred,
                            successor=succ,
                            gap_seconds=gap,
                            reason="; ".join(reasons),
                        )
                    )
    return report
