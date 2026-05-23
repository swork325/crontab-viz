"""Tests for crontab_viz.templater and cli_template."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from crontab_viz.templater import (
    list_templates,
    get_template,
    render_template,
    CronTemplate,
)
from crontab_viz.cli_template import _run_list, _run_render, main
import argparse


# ---------------------------------------------------------------------------
# templater unit tests
# ---------------------------------------------------------------------------

def test_list_templates_returns_nonempty():
    templates = list_templates()
    assert len(templates) > 0


def test_list_templates_are_cron_template_instances():
    for tmpl in list_templates():
        assert isinstance(tmpl, CronTemplate)


def test_get_template_known_name():
    tmpl = get_template("hourly")
    assert tmpl is not None
    assert tmpl.name == "hourly"


def test_get_template_unknown_returns_none():
    assert get_template("nonexistent_template") is None


def test_render_template_returns_valid_entry():
    entry = render_template("daily_midnight", "/usr/bin/backup.sh")
    assert entry is not None
    assert entry.is_valid
    assert entry.command == "/usr/bin/backup.sh"


def test_render_template_with_comment():
    entry = render_template("hourly", "/usr/bin/sync.sh", comment="sync data")
    assert entry is not None
    assert entry.comment == "sync data"


def test_render_template_unknown_name_returns_none():
    result = render_template("does_not_exist", "/bin/true")
    assert result is None


def test_template_render_method_directly():
    tmpl = get_template("weekly_sunday")
    assert tmpl is not None
    entry = tmpl.render("/usr/bin/weekly.sh", "weekly job")
    assert entry is not None
    assert entry.is_valid


def test_at_reboot_template_is_special():
    entry = render_template("at_reboot", "/usr/bin/startup.sh")
    assert entry is not None
    assert entry.is_valid
    assert entry.schedule.startswith("@")


def test_workdays_schedule_correct():
    tmpl = get_template("workdays_9am")
    assert tmpl is not None
    assert "1-5" in tmpl.schedule


# ---------------------------------------------------------------------------
# cli_template tests
# ---------------------------------------------------------------------------

def test_run_list_exits_zero(capsys):
    rc = _run_list()
    assert rc == 0
    captured = capsys.readouterr()
    assert "NAME" in captured.out
    assert "hourly" in captured.out


def test_run_render_valid_template(capsys):
    args = argparse.Namespace(name="daily_midnight", command="/bin/backup.sh", comment="")
    rc = _run_render(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "/bin/backup.sh" in captured.out


def test_run_render_unknown_template_returns_one(capsys):
    args = argparse.Namespace(name="no_such", command="/bin/true", comment="")
    rc = _run_render(args)
    assert rc == 1


def test_main_list_subcommand(capsys):
    rc = main(["template", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "monthly_first" in out


def test_main_render_subcommand(capsys):
    rc = main(["template", "render", "hourly", "/usr/bin/myjob.sh"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "/usr/bin/myjob.sh" in out
