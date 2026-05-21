"""Command-line interface for crontab-viz."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from crontab_viz.dashboard import run_dashboard
from crontab_viz.exporter import export_to_file
from crontab_viz.filter import FilterCriteria, filter_entries, search_entries
from crontab_viz.formatter import format_entries, render_table
from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-viz",
        description="Visualize and inspect crontab schedules.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Load crontab from a file.")
    source.add_argument(
        "--text", metavar="TEXT", help="Load crontab from an inline string."
    )
    source.add_argument(
        "--user",
        action="store_true",
        default=True,
        help="Load the current user's crontab (default).",
    )

    parser.add_argument(
        "--search", metavar="QUERY", help="Filter entries by command or comment."
    )
    parser.add_argument(
        "--tag",
        metavar="TAG",
        action="append",
        dest="tags",
        help="Filter entries whose comment contains TAG (repeatable).",
    )
    parser.add_argument(
        "--valid-only",
        action="store_true",
        help="Show only syntactically valid entries.",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Export filtered entries to a JSON or CSV file.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run as a live dashboard (refreshes every 5 seconds).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        metavar="SECS",
        help="Refresh interval for --watch mode (default: 5).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --- load entries ---
    if args.file:
        entries = load_from_file(args.file)
        source_label = args.file
    elif args.text:
        entries = load_from_text(args.text)
        source_label = "<inline>"
    else:
        entries = load_user_crontab()
        source_label = "user crontab"

    # --- filter ---
    if args.search:
        entries = search_entries(entries, args.search)

    criteria = FilterCriteria(
        only_valid=args.valid_only,
        tags=args.tags or [],
    )
    entries = filter_entries(entries, criteria)

    # --- export ---
    if args.export:
        export_to_file(entries, args.export)
        print(f"Exported {len(entries)} entries to {args.export}")
        return 0

    # --- watch / static ---
    if args.watch:
        run_dashboard(entries, source=source_label, interval=args.interval)
    else:
        rows = format_entries(entries)
        print(render_table(rows))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
