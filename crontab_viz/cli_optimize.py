"""CLI sub-command: optimize — suggest schedule improvements."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.optimizer import optimize_entries, OptimizationSuggestion
from crontab_viz.parser import CronEntry


def add_optimize_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("optimize", help="Suggest schedule optimizations")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Read crontab from file")
    source.add_argument("--text", metavar="TEXT", help="Read crontab from inline text")
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)"
    )
    p.set_defaults(func=_run_optimize)


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if getattr(args, "file", None):
        return load_from_file(args.file)
    if getattr(args, "text", None):
        return load_from_text(args.text)
    return load_user_crontab()


def _run_optimize(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    suggestions = optimize_entries(entries)

    if args.format == "json":
        output = [
            {
                "command": s.entry.command,
                "original": s.original_schedule,
                "suggested": s.suggested_schedule,
                "reason": s.reason,
            }
            for s in suggestions
        ]
        print(json.dumps(output, indent=2))
    else:
        if not suggestions:
            print("No optimizations suggested.")
        else:
            print(f"Found {len(suggestions)} suggestion(s):\n")
            for s in suggestions:
                print(f"  {s}")

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="crontab-optimize")
    subs = parser.add_subparsers()
    add_optimize_subparser(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
