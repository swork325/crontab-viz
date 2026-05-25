"""CLI sub-command: heatmap — visualise job density across hours and days."""
from __future__ import annotations

import argparse
import sys
from typing import List

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.parser import CronEntry
from crontab_viz.heatmap import build_heatmap, render_heatmap


def add_heatmap_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("heatmap", help="Show a job-frequency heatmap")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--file", "-f", metavar="PATH", help="Crontab file to read")
    source.add_argument("--text", "-t", metavar="TEXT", help="Inline crontab text")
    p.set_defaults(func=_run_heatmap)


def _load_entries(args: argparse.Namespace) -> List[CronEntry]:
    if getattr(args, "file", None):
        return load_from_file(args.file)
    if getattr(args, "text", None):
        return load_from_text(args.text)
    return load_user_crontab()


def _run_heatmap(args: argparse.Namespace) -> int:
    entries = _load_entries(args)
    hm = build_heatmap(entries)
    print(render_heatmap(hm))
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crontab-heatmap")
    subs = parser.add_subparsers()
    add_heatmap_subparser(subs)
    args = parser.parse_args(argv or ["heatmap"])
    if hasattr(args, "func"):
        return args.func(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
