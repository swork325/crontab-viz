"""Periodic snapshot scheduler: captures crontab state at intervals."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

from crontab_viz.archiver import CrontabSnapshot, create_snapshot
from crontab_viz.parser import CronEntry


@dataclass
class SnapshotSession:
    """Holds all snapshots captured during a session."""

    source: str
    snapshots: List[CrontabSnapshot] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.snapshots)

    @property
    def latest(self) -> Optional[CrontabSnapshot]:
        return self.snapshots[-1] if self.snapshots else None

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "snapshot_count": self.count,
            "snapshots": [s.as_dict() for s in self.snapshots],
        }


def take_snapshot(
    entries: List[CronEntry],
    source: str,
    label: Optional[str] = None,
) -> CrontabSnapshot:
    """Capture a single snapshot of the given entries."""
    snap = create_snapshot(entries, source)
    if label:
        snap.metadata["label"] = label  # type: ignore[attr-defined]
    return snap


def run_snapshots(
    load_entries: Callable[[], List[CronEntry]],
    source: str,
    interval_seconds: float,
    max_snapshots: int,
    on_snapshot: Optional[Callable[[CrontabSnapshot], None]] = None,
) -> SnapshotSession:
    """Capture *max_snapshots* snapshots, sleeping *interval_seconds* between each.

    Args:
        load_entries: Callable that returns the current list of CronEntry objects.
        source: Human-readable source label stored in each snapshot.
        interval_seconds: Seconds to sleep between captures.
        max_snapshots: Total number of snapshots to take before returning.
        on_snapshot: Optional callback invoked immediately after each capture.

    Returns:
        A SnapshotSession containing all captured snapshots.
    """
    session = SnapshotSession(source=source)
    for i in range(max_snapshots):
        entries = load_entries()
        label = f"snapshot-{i + 1}"
        snap = take_snapshot(entries, source, label=label)
        session.snapshots.append(snap)
        if on_snapshot:
            on_snapshot(snap)
        if i < max_snapshots - 1:
            time.sleep(interval_seconds)
    return session
