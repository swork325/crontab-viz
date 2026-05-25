"""CLI sub-command: detect potential scheduling dependencies."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .parser import CronEntry
from .loader import load_from_file, load_from_text, load_user_crontab
from .dependency import detect_dependencies


def add_dependency_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "dependency",
        help="Detect potential scheduling dependencies between cron entries.",
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Path to crontab file.")
    source.add_argument("--text", metavar="TEXT", help="Inline crontab text.")
    p.add_argument(
        "--gap",
        type=int,
        default=300,
        metavar="SECONDS",
        help="Max next-run gap (seconds) to consider entries dependent (default: 300).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output as JSON.",
    )
    p.set_defaults(func=_run_dependency)


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if args.file:
        return load_from_file(args.file)
    if args.text:
        return load_from_text(args.text)
    return load_user_crontab()


def _run_dependency(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    report = detect_dependencies(entries, gap_threshold_seconds=args.gap)

    if args.as_json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(f"Dependency scan — gap threshold: {args.gap}s")
    print(f"Entries analysed : {len([e for e in entries if e.is_valid])}")
    print(f"Links detected   : {report.count}")

    if report.count == 0:
        print("No potential dependencies found.")
        return 0

    print()
    for lnk in report.links:
        print(f"  {lnk}")

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="crontab-viz dependency",
        description="Detect potential scheduling dependencies.",
    )
    add_dependency_subparser(parser.add_subparsers(dest="cmd"))
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
