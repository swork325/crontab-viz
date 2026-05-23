"""CLI sub-command: watch a crontab file and print changes to stdout."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from crontab_viz.watchdog import WatchEvent, watch_file
from crontab_viz.formatter import format_entries


def add_watch_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("watch", help="Watch a crontab file for changes")
    p.add_argument("file", help="Path to the crontab file to watch")
    p.add_argument(
        "--interval",
        type=float,
        default=5.0,
        metavar="SECS",
        help="Polling interval in seconds (default: 5)",
    )
    p.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N poll iterations (for testing)",
    )
    p.set_defaults(func=_run_watch)


def _on_change(event: WatchEvent) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] Change detected in {event.path!r}")
    print(f"  Hash: {event.previous_hash or '(none)'} -> {event.current_hash}")
    print(f"  Entries loaded: {len(event.entries)}")
    if event.entries:
        table = format_entries(event.entries)
        print(table)
    sys.stdout.flush()


def _run_watch(args: argparse.Namespace) -> int:
    print(f"Watching {args.file!r} every {args.interval}s … (Ctrl-C to stop)")
    sys.stdout.flush()
    try:
        watch_file(
            path=args.file,
            callback=_on_change,
            interval=args.interval,
            max_iterations=args.max_iterations,
        )
    except KeyboardInterrupt:  # pragma: no cover
        print("\nStopped.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crontab-watch",
        description="Watch a crontab file for changes",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_watch_subparser(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)
