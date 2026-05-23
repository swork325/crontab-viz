"""Integration tests: parse real crontab text then validate."""
from __future__ import annotations

from crontab_viz.loader import load_from_text
from crontab_viz.validator import validate_entries

SAMPLE_CRONTAB = """
# Daily backup
0 2 * * * /usr/bin/backup.sh

# Every minute — suspicious
* * * * * /usr/bin/poll

# Bad line
not-a-valid-cron-line

# Missing command
0 1 * * *

@daily /usr/bin/cleanup
@reboot /usr/bin/init-service
@unknown /usr/bin/oops
"""


def test_integration_detects_every_minute_warning():
    entries = load_from_text(SAMPLE_CRONTAB)
    report = validate_entries(entries)
    warnings = [i for i in report.warnings if "every minute" in i.message.lower()]
    assert len(warnings) >= 1


def test_integration_detects_invalid_parse_error():
    entries = load_from_text(SAMPLE_CRONTAB)
    report = validate_entries(entries)
    assert not report.is_clean


def test_integration_known_specials_do_not_error():
    text = "@daily /usr/bin/cleanup\n@reboot /usr/bin/init\n@hourly /usr/bin/poll"
    entries = load_from_text(text)
    report = validate_entries(entries)
    special_errors = [
        i for i in report.errors if "Unknown special" in i.message
    ]
    assert special_errors == []


def test_integration_unknown_special_produces_error():
    text = "@unknown /usr/bin/oops"
    entries = load_from_text(text)
    report = validate_entries(entries)
    assert any("Unknown special" in i.message for i in report.errors)


def test_integration_absolute_path_no_info():
    text = "0 3 * * * /usr/bin/backup"
    entries = load_from_text(text)
    report = validate_entries(entries)
    info_issues = [i for i in report.issues if i.severity == "info"]
    assert info_issues == []


def test_integration_report_as_dict_counts_match():
    entries = load_from_text(SAMPLE_CRONTAB)
    report = validate_entries(entries)
    d = report.as_dict()
    assert d["errors"] == len(report.errors)
    assert d["warnings"] == len(report.warnings)
    assert d["total"] == len(report.issues)
