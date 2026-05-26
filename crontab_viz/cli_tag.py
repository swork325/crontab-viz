"""CLI sub-command: tag — list crontab entries with their auto-generated tags."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.tagger import TaggedEntry, filter_by_tag, tag_entries


def add_tag_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *tag* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "tag",
        help="Display crontab entries with auto-generated tags",
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Read crontab from file")
    source.add_argument("--text", metavar="TEXT", help="Parse inline crontab text")
    p.add_argument(
        "--filter",
        metavar="TAG",
        dest="tag_filter",
        help="Only show entries that carry this tag",
    )
    p.add_argument(
        "--no-auto",
        action="store_true",
        default=False,
        help="Disable automatic tag generation",
    )


def _load_entries(args: argparse.Namespace):
    if args.file:
        return load_from_file(args.file)
    if args.text:
        return load_from_text(args.text)
    return load_user_crontab()


def _render(tagged: List[TaggedEntry]) -> str:
    lines: List[str] = []
    col_w = 50
    header = f"{'SCHEDULE + COMMAND':<{col_w}}  TAGS"
    lines.append(header)
    lines.append("-" * (col_w + 20))
    for te in tagged:
        label = f"{te.entry.schedule}  {te.entry.command}"
        if len(label) > col_w:
            label = label[: col_w - 1] + "\u2026"
        tag_str = ", ".join(te.tags) if te.tags else "(none)"
        lines.append(f"{label:<{col_w}}  {tag_str}")
    return "\n".join(lines)


def _run_tag(args: argparse.Namespace, out=sys.stdout) -> int:
    try:
        entries = _load_entries(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading crontab: {exc}", file=sys.stderr)
        return 1

    auto = not args.no_auto
    tagged = tag_entries(entries, auto=auto)

    if args.tag_filter:
        tagged = filter_by_tag(tagged, args.tag_filter)
        if not tagged:
            print(f"No entries found with tag '{args.tag_filter}'.", file=out)
            return 0

    print(_render(tagged), file=out)
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for the standalone ``crontab-tag`` command.

    Parses *argv* (defaults to ``sys.argv[1:]``) and runs the tag sub-command.
    Exits with a non-zero status code on failure.
    """
    parser = argparse.ArgumentParser(
        prog="crontab-tag",
        description="Show crontab entries with auto-generated tags",
    )
    add_tag_subparser(parser.add_subparsers(dest="command"))
    # Allow running without sub-command for convenience
    parser.add_argument("--file", metavar="PATH")
    parser.add_argument("--text", metavar="TEXT")
    parser.add_argument("--filter", metavar="TAG", dest="tag_filter", default=None)
    parser.add_argument("--no-auto", action="store_true", default=False)
    args = parser.parse_args(argv)
    sys.exit(_run_tag(args))
