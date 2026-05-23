"""CLI subcommand: archive — save and inspect crontab snapshots."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from crontab_viz.archiver import (
    create_snapshot,
    list_snapshots,
    load_snapshot,
    restore_entries,
    save_snapshot,
)
from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.formatter import format_entries


def add_archive_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("archive", help="Save or inspect crontab snapshots")
    p.add_argument("action", choices=["save", "list", "show"], help="Action to perform")
    p.add_argument("--file", "-f", help="Crontab file to snapshot (default: user crontab)")
    p.add_argument("--text", help="Inline crontab text to snapshot")
    p.add_argument("--dir", default=".crontab_snapshots", help="Snapshot directory")
    p.add_argument("--snapshot", help="Snapshot file path (for 'show' action)")
    p.add_argument("--source", default="", help="Label for the snapshot source")
    p.set_defaults(func=_run_archive)


def _load_entries(args: argparse.Namespace):
    if getattr(args, "text", None):
        return load_from_text(args.text)
    if getattr(args, "file", None):
        return load_from_file(args.file)
    return load_user_crontab()


def _run_archive(args: argparse.Namespace) -> int:
    action = args.action

    if action == "save":
        entries = _load_entries(args)
        source = args.source or getattr(args, "file", "") or "user"
        snapshot = create_snapshot(entries, source=source)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{ts}.json"
        path = os.path.join(args.dir, filename)
        save_snapshot(snapshot, path)
        print(f"Snapshot saved: {path} ({snapshot.entry_count} entries)")
        return 0

    if action == "list":
        paths = list_snapshots(args.dir)
        if not paths:
            print(f"No snapshots found in {args.dir}")
            return 0
        print(f"Snapshots in {args.dir}:")
        for p in paths:
            snap = load_snapshot(p)
            print(f"  {os.path.basename(p)}  source={snap.source}  "
                  f"entries={snap.entry_count}  at={snap.captured_at}")
        return 0

    if action == "show":
        if not args.snapshot:
            print("Error: --snapshot is required for 'show' action", file=sys.stderr)
            return 1
        snap = load_snapshot(args.snapshot)
        entries = restore_entries(snap)
        print(f"Snapshot: {args.snapshot}")
        print(f"Source:   {snap.source}")
        print(f"Captured: {snap.captured_at}")
        print()
        table = format_entries(entries)
        print(table)
        return 0

    print(f"Unknown action: {action}", file=sys.stderr)
    return 1


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="crontab-archive")
    subs = parser.add_subparsers()
    add_archive_subparser(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
