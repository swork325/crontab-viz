"""CLI sub-command helpers for generating crontab reports."""
from __future__ import annotations

import argparse
import sys
from typing import List

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.reporter import build_text_report, build_json_report, write_report


def add_report_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *report* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "report",
        help="Generate a summary report of crontab entries",
    )
    source_group = p.add_mutually_exclusive_group()
    source_group.add_argument(
        "--file", "-f", metavar="PATH",
        help="Path to a crontab file",
    )
    source_group.add_argument(
        "--text", "-t", metavar="TEXT",
        help="Inline crontab text (newlines as \\n)",
    )
    source_group.add_argument(
        "--user", "-u", action="store_true",
        help="Use the current user's crontab",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--output", "-o", metavar="PATH",
        help="Write report to file instead of stdout",
    )
    p.set_defaults(func=_run_report)


def _load_entries(args: argparse.Namespace):
    if args.file:
        return load_from_file(args.file), args.file
    if args.text:
        raw = args.text.replace("\\n", "\n")
        return load_from_text(raw), "<inline>"
    if args.user:
        return load_user_crontab(), "<user crontab>"
    return [], ""


def _run_report(args: argparse.Namespace) -> int:
    entries, source = _load_entries(args)

    if args.output:
        write_report(entries, path=args.output, fmt=args.fmt, source=source)
        print(f"Report written to {args.output}")
    else:
        if args.fmt == "json":
            print(build_json_report(entries, source=source))
        else:
            print(build_text_report(entries, source=source))
    return 0


def main(argv: List[str] | None = None) -> int:
    """Standalone entry-point for the report sub-command."""
    parser = argparse.ArgumentParser(
        prog="crontab-report",
        description="Generate a crontab summary report",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_report_subparser(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
