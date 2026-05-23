"""CLI sub-command: validate — semantic validation of crontab entries."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .loader import load_from_file, load_from_text, load_user_crontab
from .parser import CronEntry
from .validator import ValidationReport, validate_entries


def add_validate_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("validate", help="Semantically validate crontab entries")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--file", "-f", metavar="PATH", help="Path to crontab file")
    src.add_argument("--text", "-t", metavar="TEXT", help="Inline crontab text")
    src.add_argument("--user", "-u", action="store_true", help="Load current user crontab")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    p.add_argument("--strict", action="store_true", help="Exit non-zero on warnings too")
    p.set_defaults(func=_run_validate)


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if args.file:
        return load_from_file(args.file)
    if args.text:
        return load_from_text(args.text)
    return load_user_crontab()


def _run_validate(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    report = validate_entries(entries)

    if args.fmt == "json":
        print(json.dumps(report.as_dict(), indent=2))
    else:
        if not report.issues:
            print("No issues found. Crontab looks clean.")
        for issue in report.issues:
            print(str(issue))
        print(f"\nSummary: {len(report.errors)} error(s), {len(report.warnings)} warning(s).")

    if not report.is_clean:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="crontab-validate")
    subs = parser.add_subparsers()
    add_validate_subparser(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
