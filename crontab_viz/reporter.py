"""Generate a full text or JSON report combining summary + entry table."""
from __future__ import annotations

import datetime
import json
from typing import List, Optional

from crontab_viz.parser import CronEntry
from crontab_viz.summarizer import summarize, render_summary
from crontab_viz.formatter import format_entries
from crontab_viz.exporter import export_json


def build_text_report(
    entries: List[CronEntry],
    source: str = "",
    now: Optional[datetime.datetime] = None,
) -> str:
    """Return a complete plain-text report for *entries*."""
    if now is None:
        now = datetime.datetime.now()

    header_parts = ["Crontab Visualizer Report"]
    if source:
        header_parts.append(f"Source : {source}")
    header_parts.append(f"Generated : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    header = "\n".join(header_parts)

    summary = summarize(entries, now=now)
    summary_text = render_summary(summary)

    table = format_entries(entries, now=now)

    return "\n\n".join([header, summary_text, table])


def build_json_report(
    entries: List[CronEntry],
    source: str = "",
    now: Optional[datetime.datetime] = None,
) -> str:
    """Return a JSON string containing summary stats and per-entry data."""
    if now is None:
        now = datetime.datetime.now()

    summary = summarize(entries, now=now)
    rows = export_json(entries, now=now)

    payload = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "summary": summary.as_dict(),
        "entries": rows,
    }
    return json.dumps(payload, indent=2)


def write_report(
    entries: List[CronEntry],
    path: str,
    fmt: str = "text",
    source: str = "",
    now: Optional[datetime.datetime] = None,
) -> None:
    """Write a report to *path* in *fmt* format ('text' or 'json')."""
    if fmt == "json":
        content = build_json_report(entries, source=source, now=now)
    else:
        content = build_text_report(entries, source=source, now=now)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
