"""CLI sub-command: timeline — show upcoming cron runs in chronological order."""
from __future__ import annotations

import argparse
from typing import List

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.parser import CronEntry
from crontab_viz.timeline import build_timeline, render_timeline


def add_timeline_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("timeline", help="Show upcoming job runs in chronological order")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Path to a crontab file")
    source.add_argument("--text", metavar="CRONTAB", help="Inline crontab text")
    p.add_argument(
        "--runs", type=int, default=5, metavar="N",
        help="Number of upcoming runs to show per entry (default: 5)",
    )
    p.add_argument(
        "--limit", type=int, default=0, metavar="L",
        help="Cap total events displayed (0 = unlimited)",
    )


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if getattr(args, "file", None):
        return load_from_file(args.file)
    if getattr(args, "text", None):
        return load_from_text(args.text)
    return load_user_crontab()


def _run_timeline(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    timeline = build_timeline(entries, n=args.runs)
    if args.limit > 0:
        from crontab_viz.timeline import Timeline
        timeline = Timeline(events=timeline.events[: args.limit])
    print(render_timeline(timeline))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="crontab-timeline")
    subs = parser.add_subparsers(dest="command")
    add_timeline_subparser(subs)
    args = parser.parse_args()
    if args.command == "timeline":
        raise SystemExit(_run_timeline(args))
    parser.print_help()
