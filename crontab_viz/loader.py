"""Load and parse crontab files or raw crontab text."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from crontab_viz.parser import CronEntry, parse_crontab_line


def load_from_file(path: str | Path) -> List[CronEntry]:
    """Parse all cron entries from a crontab *file*.

    Blank lines and comment-only lines are silently skipped.
    Invalid schedule lines are included with ``is_valid=False``.
    """
    text = Path(path).read_text(encoding="utf-8")
    return load_from_text(text)


def load_from_text(text: str) -> List[CronEntry]:
    """Parse cron entries from a multi-line *text* string."""
    entries: List[CronEntry] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(parse_crontab_line(stripped))
    return entries


def load_user_crontab(user: Optional[str] = None) -> List[CronEntry]:
    """Load the crontab for *user* (or the current user) via ``crontab -l``.

    Returns an empty list when no crontab is installed or the command fails.
    """
    cmd = ["crontab", "-l"]
    if user:
        cmd += ["-u", user]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        # crontab -l exits non-zero when no crontab is installed
        return []

    return load_from_text(result.stdout)


def load_system_crontab(path: str | Path = "/etc/crontab") -> List[CronEntry]:
    """Load the system-wide crontab from *path*.

    Returns an empty list if the file does not exist or is unreadable.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        return load_from_file(p)
    except OSError:
        return []
