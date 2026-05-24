"""CLI sub-command: alias — show human-readable aliases for cron entries."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from crontab_viz.loader import load_from_file, load_from_text
from crontab_viz.parser import CronEntry
from crontab_viz.aliaser import alias_entries, AliasedEntry


def add_alias_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "alias",
        help="Display human-readable aliases for recognised cron schedules.",
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", metavar="PATH", help="Path to a crontab file.")
    source.add_argument("--text", metavar="CRON", help="Inline crontab text.")
    p.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON.",
    )
    p.add_argument(
        "--unaliased",
        action="store_true",
        help="Also list entries with no alias.",
    )


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if getattr(args, "file", None):
        return load_from_file(args.file)
    if getattr(args, "text", None):
        return load_from_text(args.text)
    return []


def _render_text(
    aliased: List[AliasedEntry],
    all_entries: List[CronEntry],
    show_unaliased: bool,
) -> None:
    aliased_set = {id(a.entry) for a in aliased}
    print(f"{'SCHEDULE':<25} {'ALIAS':<30} COMMAND")
    print("-" * 75)
    for ae in aliased:
        sched = ae.entry.special or (
            f"{ae.entry.minute} {ae.entry.hour} "
            f"{ae.entry.day} {ae.entry.month} {ae.entry.weekday}"
        )
        tag = " [custom]" if ae.custom else ""
        print(f"{sched:<25} {ae.alias + tag:<30} {ae.entry.command}")
    if show_unaliased:
        for entry in all_entries:
            if not entry.is_valid or id(entry) in aliased_set:
                continue
            sched = entry.special or (
                f"{entry.minute} {entry.hour} "
                f"{entry.day} {entry.month} {entry.weekday}"
            )
            print(f"{sched:<25} {'(no alias)':<30} {entry.command}")


def _render_json(aliased: List[AliasedEntry]) -> None:
    out = [
        {
            "alias": ae.alias,
            "custom": ae.custom,
            "command": ae.entry.command,
            "schedule": ae.entry.special or (
                f"{ae.entry.minute} {ae.entry.hour} "
                f"{ae.entry.day} {ae.entry.month} {ae.entry.weekday}"
            ),
        }
        for ae in aliased
    ]
    print(json.dumps(out, indent=2))


def _run_alias(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    aliased = alias_entries(entries)
    if getattr(args, "json", False):
        _render_json(aliased)
    else:
        _render_text(aliased, entries, getattr(args, "unaliased", False))
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="crontab-viz alias")
    subs = parser.add_subparsers(dest="command")
    add_alias_subparser(subs)
    args = parser.parse_args(argv)
    sys.exit(_run_alias(args))


if __name__ == "__main__":  # pragma: no cover
    main()
