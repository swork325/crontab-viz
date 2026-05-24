"""CLI sub-command: crontab-viz snapshot — periodic crontab snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import List

from crontab_viz.loader import load_from_file, load_from_text
from crontab_viz.parser import CronEntry
from crontab_viz.snapshotter import SnapshotSession, run_snapshots


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snapshot", help="Capture periodic crontab snapshots")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--file", metavar="PATH", help="Crontab file to read")
    group.add_argument("--text", metavar="TEXT", help="Inline crontab text")
    p.add_argument(
        "--interval",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Seconds between snapshots (default: 60)",
    )
    p.add_argument(
        "--count",
        type=int,
        default=3,
        metavar="N",
        help="Number of snapshots to capture (default: 3)",
    )
    p.add_argument("--output", metavar="PATH", help="Write JSON session to file")
    p.set_defaults(func=_run_snapshot)


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if args.file:
        return load_from_file(args.file)
    if args.text:
        return load_from_text(args.text)
    return []


def _on_snapshot_print(snap) -> None:  # type: ignore[no-untyped-def]
    ts = snap.captured_at
    print(f"[{ts}] Captured snapshot: {snap.entry_count} entries")


def _run_snapshot(args: argparse.Namespace) -> int:
    session = run_snapshots(
        load_entries=lambda: _load_entries(args),
        source=args.file or "<text>",
        interval_seconds=args.interval,
        max_snapshots=args.count,
        on_snapshot=_on_snapshot_print,
    )
    data = session.as_dict()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        print(f"Session written to {args.output}")
    else:
        print(json.dumps(data, indent=2))
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="crontab-viz snapshot")
    subs = parser.add_subparsers()
    add_snapshot_subparser(subs)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
