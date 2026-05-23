"""Archive and restore crontab snapshots for historical comparison."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from crontab_viz.parser import CronEntry, parse_crontab_line


@dataclass
class CrontabSnapshot:
    """A point-in-time snapshot of crontab entries."""
    source: str
    captured_at: str
    entries: List[dict]

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "entry_count": self.entry_count,
            "entries": self.entries,
        }


def _entry_to_dict(entry: CronEntry) -> dict:
    return {
        "schedule": entry.schedule,
        "command": entry.command,
        "comment": entry.comment,
        "raw": entry.raw,
        "is_valid": entry.is_valid(),
    }


def create_snapshot(entries: List[CronEntry], source: str) -> CrontabSnapshot:
    """Create a snapshot from a list of CronEntry objects."""
    captured_at = datetime.now(timezone.utc).isoformat()
    return CrontabSnapshot(
        source=source,
        captured_at=captured_at,
        entries=[_entry_to_dict(e) for e in entries],
    )


def save_snapshot(snapshot: CrontabSnapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.as_dict(), fh, indent=2)


def load_snapshot(path: str) -> CrontabSnapshot:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return CrontabSnapshot(
        source=data["source"],
        captured_at=data["captured_at"],
        entries=data["entries"],
    )


def restore_entries(snapshot: CrontabSnapshot) -> List[CronEntry]:
    """Reconstruct CronEntry objects from a snapshot."""
    entries: List[CronEntry] = []
    for item in snapshot.entries:
        raw = item.get("raw", "")
        entry = parse_crontab_line(raw)
        if entry is not None:
            entries.append(entry)
    return entries


def list_snapshots(directory: str) -> List[str]:
    """Return sorted list of snapshot file paths in a directory."""
    if not os.path.isdir(directory):
        return []
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json")
    ]
    return sorted(files)
