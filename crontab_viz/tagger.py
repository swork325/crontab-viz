"""Tag crontab entries with user-defined or auto-generated labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from crontab_viz.parser import CronEntry


@dataclass
class TaggedEntry:
    """A CronEntry decorated with a set of tags."""

    entry: CronEntry
    tags: List[str] = field(default_factory=list)

    def has_tag(self, tag: str) -> bool:
        """Return True if *tag* is present (case-insensitive)."""
        return tag.lower() in (t.lower() for t in self.tags)

    def add_tag(self, tag: str) -> None:
        """Add *tag* if it is not already present (case-insensitive)."""
        if not self.has_tag(tag):
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> bool:
        """Remove *tag* (case-insensitive). Return True if it was present."""
        lower = tag.lower()
        before = len(self.tags)
        self.tags = [t for t in self.tags if t.lower() != lower]
        return len(self.tags) < before


# ---------------------------------------------------------------------------
# Auto-tagging rules
# ---------------------------------------------------------------------------

_KEYWORD_TAGS: Dict[str, str] = {
    "backup": "backup",
    "log": "logging",
    "clean": "maintenance",
    "purge": "maintenance",
    "report": "reporting",
    "sync": "sync",
    "deploy": "deploy",
    "restart": "ops",
    "reload": "ops",
    "monitor": "monitoring",
    "alert": "monitoring",
}


def _auto_tags(entry: CronEntry) -> List[str]:
    """Derive tags from the command and comment text."""
    combined = f"{entry.command} {entry.comment or ''}".lower()
    found: List[str] = []
    for keyword, tag in _KEYWORD_TAGS.items():
        if keyword in combined and tag not in found:
            found.append(tag)
    if not entry.is_valid:
        found.append("invalid")
    elif entry.schedule.startswith("@"):
        found.append("special")
    else:
        found.append("standard")
    return found


def tag_entry(
    entry: CronEntry,
    extra_tags: Optional[List[str]] = None,
    auto: bool = True,
) -> TaggedEntry:
    """Wrap *entry* in a :class:`TaggedEntry`, optionally auto-tagging it."""
    tags: List[str] = list(extra_tags or [])
    if auto:
        for t in _auto_tags(entry):
            if t not in tags:
                tags.append(t)
    return TaggedEntry(entry=entry, tags=tags)


def tag_entries(
    entries: List[CronEntry],
    extra_tags: Optional[List[str]] = None,
    auto: bool = True,
) -> List[TaggedEntry]:
    """Bulk-tag a list of entries."""
    return [tag_entry(e, extra_tags=extra_tags, auto=auto) for e in entries]


def filter_by_tag(tagged: List[TaggedEntry], tag: str) -> List[TaggedEntry]:
    """Return only entries that carry *tag*."""
    return [te for te in tagged if te.has_tag(tag)]
