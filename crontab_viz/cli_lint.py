"""CLI sub-command: lint — check crontab entries for issues."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .parser import CronEntry
from .loader import load_from_file, load_from_text, load_user_crontab
from .linter import lint_entries, render_lint_report


def add_lint_subparser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("lint", help="Lint crontab entries for common issues")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--file", "-f", metavar="PATH", help="Path to a crontab file")
    src.add_argument("--text", "-t", metavar="TEXT", help="Raw crontab text")
    src.add_argument(
        "--user", "-u", action="store_true", help="Use the current user crontab"
    )
    p.add_argument(
        "--errors-only",
        action="store_true",
        help="Only report errors, suppress warnings and info",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with non-zero status if errors are found",
    )
    p.set_defaults(func=_run_lint)


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if args.file:
        return load_from_file(args.file)
    if args.text:
        return load_from_text(args.text)
    if args.user:
        return load_user_crontab()
    return []


def _run_lint(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    if not entries:
        print("No crontab entries to lint.", file=sys.stderr)
        return 0

    result = lint_entries(entries)

    if getattr(args, "errors_only", False):
        from .linter import LintResult, LintIssue
        filtered = LintResult(issues=[i for i in result.issues if i.severity == "error"])
        report = render_lint_report(filtered)
    else:
        report = render_lint_report(result)

    print(report)

    if getattr(args, "exit_code", False) and result.errors:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="crontab-lint",
        description="Lint crontab entries for common issues",
    )
    subs = parser.add_subparsers(dest="command")
    add_lint_subparser(subs)
    # Allow running without sub-command name for convenience
    parser.add_argument("--file", "-f", metavar="PATH")
    parser.add_argument("--text", "-t", metavar="TEXT")
    parser.add_argument("--user", "-u", action="store_true")
    parser.add_argument("--errors-only", action="store_true")
    parser.add_argument("--exit-code", action="store_true")
    args = parser.parse_args()
    sys.exit(_run_lint(args))


if __name__ == "__main__":  # pragma: no cover
    main()
