"""Terminal dashboard for visualizing crontab schedules."""

import time
import sys
from datetime import datetime
from typing import Optional

from crontab_viz.loader import load_from_file, load_from_text, load_user_crontab
from crontab_viz.formatter import format_entries, render_table
from crontab_viz.scheduler import countdown


def _clear_screen() -> None:
    """Clear the terminal screen."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _render_header(source: str) -> str:
    """Render dashboard header with current timestamp."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = "  crontab-viz  "
    border = "=" * max(len(title), len(source) + 4, 50)
    return (
        f"\033[1;36m{border}\033[0m\n"
        f"\033[1;37m{title.center(len(border))}\033[0m\n"
        f"  Source : {source}\n"
        f"  Updated: {now}\n"
        f"\033[1;36m{border}\033[0m\n"
    )


def run_dashboard(
    source: Optional[str] = None,
    text: Optional[str] = None,
    refresh_interval: int = 30,
    once: bool = False,
) -> None:
    """Run the live terminal dashboard.

    Args:
        source: Path to a crontab file. If None, loads the user crontab.
        text:   Raw crontab text to parse directly (overrides source).
        refresh_interval: Seconds between screen refreshes.
        once:   If True, render once and return (useful for testing/CI).
    """
    if text is not None:
        entries = load_from_text(text)
        label = "<inline text>"
    elif source is not None:
        entries = load_from_file(source)
        label = source
    else:
        entries = load_user_crontab()
        label = "user crontab"

    while True:
        rows = format_entries(entries)
        table = render_table(rows)
        header = _render_header(label)

        _clear_screen()
        print(header)
        print(table)
        print(f"\n  \033[90mRefreshing every {refresh_interval}s — Ctrl+C to quit\033[0m")

        if once:
            return

        try:
            time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            return
