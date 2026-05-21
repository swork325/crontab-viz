"""Simple CLI entry-point for crontab-viz.

Usage examples::

    python -m crontab_viz.cli --text '0 9 * * * /bin/backup' --export json
    python -m crontab_viz.cli --file /etc/crontab --export csv --out schedule.csv
    python -m crontab_viz.cli --user  # live dashboard from current user crontab
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from crontab_viz.dashboard import run_dashboard
from crontab_viz.exporter import export_csv, export_json, export_to_file
from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crontab-viz",
        description="Visualize and export crontab schedules.",
    )
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", metavar="CRONTAB", help="Inline crontab text.")
    source.add_argument("--file", metavar="PATH", help="Path to a crontab file.")
    source.add_argument("--user", action="store_true", help="Load the current user's crontab.")

    p.add_argument(
        "--export",
        choices=["json", "csv"],
        default=None,
        help="Export format instead of running the live dashboard.",
    )
    p.add_argument("--out", metavar="PATH", default=None, help="Output file for --export (default: stdout).")
    p.add_argument("--once", action="store_true", help="Render the dashboard once and exit (no loop).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # --- load entries ---
    if args.text:
        entries = load_from_text(args.text)
        source_label = "<inline>"
    elif args.file:
        entries = load_from_file(args.file)
        source_label = args.file
    else:
        entries = load_user_crontab()
        source_label = "user crontab"

    # --- export mode ---
    if args.export:
        now = datetime.now()
        if args.out:
            export_to_file(args.out, entries, fmt=args.export, now=now)
            print(f"Exported {len(entries)} entries to {args.out} ({args.export}).")
        else:
            if args.export == "json":
                print(export_json(entries, now=now))
            else:
                print(export_csv(entries, now=now), end="")
        return 0

    # --- dashboard mode ---
    run_dashboard(entries, source=source_label, once=args.once)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
