"""Export crontab schedule data to various formats (JSON, CSV)."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import List

from crontab_viz.formatter import FormattedRow, format_entries
from crontab_viz.parser import CronEntry


def export_json(entries: List[CronEntry], now: datetime | None = None) -> str:
    """Serialize cron entries to a JSON string."""
    if now is None:
        now = datetime.now()

    rows: List[FormattedRow] = format_entries(entries, now)
    records = [
        {
            "command": row.command,
            "schedule": row.schedule,
            "next_run": row.next_run,
            "countdown": row.countdown,
            "valid": row.valid,
        }
        for row in rows
    ]
    return json.dumps(records, indent=2)


def export_csv(entries: List[CronEntry], now: datetime | None = None) -> str:
    """Serialize cron entries to a CSV string."""
    if now is None:
        now = datetime.now()

    rows: List[FormattedRow] = format_entries(entries, now)
    output = io.StringIO()
    fieldnames = ["command", "schedule", "next_run", "countdown", "valid"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "command": row.command,
                "schedule": row.schedule,
                "next_run": row.next_run,
                "countdown": row.countdown,
                "valid": row.valid,
            }
        )
    return output.getvalue()


def export_to_file(path: str, entries: List[CronEntry], fmt: str = "json", now: datetime | None = None) -> None:
    """Write exported data to *path*. *fmt* is either ``'json'`` or ``'csv'``."""
    if fmt == "json":
        content = export_json(entries, now)
    elif fmt == "csv":
        content = export_csv(entries, now)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
