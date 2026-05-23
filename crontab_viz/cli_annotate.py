"""CLI sub-command: annotate — print human-readable descriptions for cron entries."""
from __future__ import annotations

import argparse
import sys
from typing import List

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.parser import CronEntry
from crontab_viz.annotator import annotate_entries, AnnotatedEntry


def add_annotate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "annotate",
        help="Print human-readable descriptions for each cron entry.",
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Path to a crontab file.")
    source.add_argument("--text", metavar="TEXT", help="Crontab text supplied inline.")
    source.add_argument(
        "--user", action="store_true", help="Load the current user's crontab."
    )
    p.add_argument(
        "--invalid", action="store_true", help="Include invalid entries in output."
    )
    p.set_defaults(func=_run_annotate)


def _load_entries(
    args: argparse.Namespace,
) -> List[CronEntry]:
    if args.file:
        return load_from_file(args.file)
    if args.text:
        return load_from_text(args.text)
    return load_user_crontab()


def _render(annotated: List[AnnotatedEntry], include_invalid: bool) -> str:
    lines: List[str] = []
    for ann in annotated:
        if not ann.entry.is_valid and not include_invalid:
            continue
        validity = "[valid]" if ann.entry.is_valid else "[invalid]"
        note_str = "  (" + "; ".join(ann.notes) + ")" if ann.notes else ""
        lines.append(f"{validity} {ann.entry.command}")
        lines.append(f"  Schedule : {ann.entry.raw_schedule}")
        lines.append(f"  Meaning  : {ann.description}{note_str}")
        lines.append("")
    return "\n".join(lines)


def _run_annotate(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    annotated = annotate_entries(entries)
    output = _render(annotated, include_invalid=args.invalid)
    if not output.strip():
        print("No entries to display.", file=sys.stderr)
        return 1
    print(output)
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crontab-annotate",
        description="Show human-readable descriptions for cron schedules.",
    )
    sub = parser.add_subparsers(dest="command")
    add_annotate_subparser(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
