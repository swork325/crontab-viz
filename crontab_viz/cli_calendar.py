"""CLI sub-command: crontab-viz calendar — show hour/day activity grid."""
from __future__ import annotations

import argparse
import sys
from typing import List

from crontab_viz.parser import CronEntry
from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.calendar_view import CalendarMatrix, render_calendar, DAYS


def add_calendar_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("calendar", help="Show hour/day activity grid")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--file", metavar="PATH", help="Path to crontab file")
    src.add_argument("--text", metavar="CRON", help="Raw crontab text")
    p.add_argument("--stats", action="store_true", help="Print busiest hour/day")


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if getattr(args, "file", None):
        return load_from_file(args.file)
    if getattr(args, "text", None):
        return load_from_text(args.text)
    return load_user_crontab()


def _run_calendar(args: argparse.Namespace, out=sys.stdout) -> int:
    entries = _load_entries(args)
    matrix = CalendarMatrix(entries)
    print(render_calendar(matrix), file=out)
    if getattr(args, "stats", False):
        bh = matrix.busiest_hour()
        bd = matrix.busiest_day()
        print(f"\nBusiest hour : {bh:02d}:00", file=out)
        print(f"Busiest day  : {bd}", file=out)
    return 0


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="crontab-viz-calendar")
    subs = parser.add_subparsers(dest="command")
    add_calendar_subparser(subs)
    args = parser.parse_args(argv)
    if args.command == "calendar":
        sys.exit(_run_calendar(args))
    else:
        parser.print_help()
