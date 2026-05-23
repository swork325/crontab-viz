"""Generate crontab entries from common schedule templates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from crontab_viz.parser import CronEntry, parse_crontab_line


@dataclass
class CronTemplate:
    name: str
    description: str
    schedule: str  # cron expression or @special
    example_command: str = "/bin/true"

    def render(self, command: str, comment: str = "") -> Optional[CronEntry]:
        """Render the template with a concrete command."""
        comment_part = f"  # {comment}" if comment else ""
        line = f"{self.schedule} {command}{comment_part}"
        return parse_crontab_line(line)


# Built-in templates
_TEMPLATES: Dict[str, CronTemplate] = {
    "every_minute": CronTemplate(
        name="every_minute",
        description="Run every minute",
        schedule="* * * * *",
        example_command="/usr/bin/check.sh",
    ),
    "hourly": CronTemplate(
        name="hourly",
        description="Run once per hour at :00",
        schedule="0 * * * *",
        example_command="/usr/bin/hourly.sh",
    ),
    "daily_midnight": CronTemplate(
        name="daily_midnight",
        description="Run daily at midnight",
        schedule="0 0 * * *",
        example_command="/usr/bin/daily.sh",
    ),
    "weekly_sunday": CronTemplate(
        name="weekly_sunday",
        description="Run every Sunday at midnight",
        schedule="0 0 * * 0",
        example_command="/usr/bin/weekly.sh",
    ),
    "monthly_first": CronTemplate(
        name="monthly_first",
        description="Run on the 1st of each month at midnight",
        schedule="0 0 1 * *",
        example_command="/usr/bin/monthly.sh",
    ),
    "at_reboot": CronTemplate(
        name="at_reboot",
        description="Run once at system boot",
        schedule="@reboot",
        example_command="/usr/bin/startup.sh",
    ),
    "workdays_9am": CronTemplate(
        name="workdays_9am",
        description="Run on weekdays (Mon-Fri) at 09:00",
        schedule="0 9 * * 1-5",
        example_command="/usr/bin/workday.sh",
    ),
}


def list_templates() -> List[CronTemplate]:
    """Return all available templates."""
    return list(_TEMPLATES.values())


def get_template(name: str) -> Optional[CronTemplate]:
    """Retrieve a template by name, or None if not found."""
    return _TEMPLATES.get(name)


def render_template(name: str, command: str, comment: str = "") -> Optional[CronEntry]:
    """Render a named template with the given command."""
    tmpl = get_template(name)
    if tmpl is None:
        return None
    return tmpl.render(command, comment)
