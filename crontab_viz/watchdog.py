"""Watchdog module: monitors a crontab file for changes and triggers callbacks."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from crontab_viz.loader import load_from_file
from crontab_viz.parser import CronEntry


@dataclass
class WatchEvent:
    """Represents a detected change in a watched crontab file."""

    path: str
    previous_hash: Optional[str]
    current_hash: str
    entries: List[CronEntry]

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"WatchEvent(path={self.path!r}, "
            f"changed={self.previous_hash != self.current_hash}, "
            f"entries={len(self.entries)})"
        )


def _file_hash(path: str) -> Optional[str]:
    """Return MD5 hex-digest of file contents, or None if unreadable."""
    try:
        data = Path(path).read_bytes()
        return hashlib.md5(data).hexdigest()
    except OSError:
        return None


def watch_file(
    path: str,
    callback: Callable[[WatchEvent], None],
    interval: float = 5.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds; invoke *callback* on change.

    Parameters
    ----------
    path:
        Absolute or relative path to the crontab file to watch.
    callback:
        Callable invoked with a :class:`WatchEvent` whenever the file changes.
    interval:
        Polling interval in seconds.
    max_iterations:
        Stop after this many iterations (useful for testing).  ``None`` means
        run indefinitely.
    """
    previous_hash: Optional[str] = None
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        current_hash = _file_hash(path)
        if current_hash is not None and current_hash != previous_hash:
            entries = load_from_file(path)
            event = WatchEvent(
                path=path,
                previous_hash=previous_hash,
                current_hash=current_hash,
                entries=entries,
            )
            callback(event)
            previous_hash = current_hash
        iterations += 1
        if max_iterations is None or iterations < max_iterations:  # pragma: no cover
            time.sleep(interval)
