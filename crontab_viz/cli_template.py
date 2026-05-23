"""CLI sub-command: list and render crontab templates."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from crontab_viz.templater import list_templates, render_template, get_template


def add_template_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "template",
        help="List or render common crontab schedule templates",
    )
    sub = parser.add_subparsers(dest="template_cmd", required=True)

    # list sub-command
    sub.add_parser("list", help="List all available templates")

    # render sub-command
    render_p = sub.add_parser("render", help="Render a template with a command")
    render_p.add_argument("name", help="Template name (see 'list')")
    render_p.add_argument("command", help="Command to embed in the cron entry")
    render_p.add_argument("--comment", default="", help="Optional inline comment")

    parser.set_defaults(func=_run_template)


def _run_list() -> int:
    templates = list_templates()
    header = f"{'NAME':<20} {'SCHEDULE':<15} DESCRIPTION"
    print(header)
    print("-" * len(header))
    for tmpl in templates:
        print(f"{tmpl.name:<20} {tmpl.schedule:<15} {tmpl.description}")
    return 0


def _run_render(args: argparse.Namespace) -> int:
    tmpl = get_template(args.name)
    if tmpl is None:
        print(f"Error: unknown template '{args.name}'. Run 'template list' to see options.",
              file=sys.stderr)
        return 1

    entry = render_template(args.name, args.command, args.comment)
    if entry is None or not entry.is_valid:
        print("Error: rendered entry is invalid.", file=sys.stderr)
        return 1

    print(f"# {tmpl.description}")
    schedule = entry.schedule
    print(f"{schedule} {entry.command}")
    return 0


def _run_template(args: argparse.Namespace) -> int:
    if args.template_cmd == "list":
        return _run_list()
    if args.template_cmd == "render":
        return _run_render(args)
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="crontab-viz-template")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    add_template_subparser(subparsers)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
