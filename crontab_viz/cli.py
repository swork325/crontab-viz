"""CLI entry point for crontab-viz."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab, load_system_crontab
from crontab_viz.formatter import format_entries, render_table
from crontab_viz.exporter import export_to_file
from crontab_viz.filter import FilterCriteria, filter_entries
from crontab_viz.sorter import SortCriteria, SortKey, sort_entries
from crontab_viz.dashboard import run_dashboard
from crontab_viz.notifier import check_due, format_alerts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-viz",
        description="Visualize and manage crontab schedules.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Load crontab from a file.")
    source.add_argument("--text", metavar="TEXT", help="Parse crontab from a string.")
    source.add_argument("--user", action="store_true", help="Load the current user's crontab.")
    source.add_argument("--system", action="store_true", help="Load system-wide crontab.")

    parser.add_argument("--dashboard", action="store_true", help="Run live dashboard.")
    parser.add_argument("--interval", type=float, default=5.0, help="Dashboard refresh interval (seconds).")
    parser.add_argument("--export", metavar="PATH", help="Export results to JSON or CSV file.")
    parser.add_argument("--filter-command", metavar="PATTERN", help="Filter by command pattern.")
    parser.add_argument("--only-valid", action="store_true", help="Show only valid entries.")
    parser.add_argument(
        "--sort",
        choices=[k.value for k in SortKey],
        default=SortKey.NEXT_RUN.value,
        help="Sort entries by field.",
    )
    parser.add_argument("--alerts", action="store_true", help="Show jobs due within threshold.")
    parser.add_argument("--alert-threshold", type=float, default=300.0,
                        help="Alert threshold in seconds (default 300).")
    return parser


def main(argv: Optional[list] = None) -> None:  # pragma: no cover — integration entry
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --- Load entries ---
    if args.file:
        entries = load_from_file(args.file)
    elif args.text:
        entries = load_from_text(args.text)
    elif args.user:
        entries = load_user_crontab()
    elif args.system:
        entries = load_system_crontab()
    else:
        parser.print_help()
        sys.exit(0)

    # --- Filter ---
    criteria = FilterCriteria(
        only_valid=args.only_valid,
        command_pattern=args.filter_command,
    )
    entries = filter_entries(entries, criteria)

    # --- Sort ---
    sort_criteria = SortCriteria(key=SortKey(args.sort))
    entries = sort_entries(entries, sort_criteria)

    # --- Alerts mode ---
    if args.alerts:
        alerts = check_due(entries, threshold_seconds=args.alert_threshold)
        print(format_alerts(alerts))
        return

    # --- Dashboard mode ---
    if args.dashboard:
        run_dashboard(entries, interval=args.interval)
        return

    # --- Export ---
    if args.export:
        export_to_file(entries, args.export)
        print(f"Exported {len(entries)} entries to {args.export}")
        return

    # --- Default: print table ---
    rows = format_entries(entries)
    print(render_table(rows))


if __name__ == "__main__":
    main()
