"""Integration tests: annotator works end-to-end with real parsed entries."""
from __future__ import annotations

from crontab_viz.loader import load_from_text
from crontab_viz.annotator import annotate_entries, describe_schedule


SAMPLE_CRONTAB = """
# System maintenance
@daily /usr/bin/logrotate
@reboot /usr/bin/start-services
*/15 * * * * /usr/bin/monitor
0 9-17 * * 1-5 /usr/bin/workday-task
30 6 1 * * /usr/bin/monthly-report
# invalid line here
not_a_cron_entry
"""


def test_annotate_all_entries_have_description():
    entries = load_from_text(SAMPLE_CRONTAB)
    annotated = annotate_entries(entries)
    for ann in annotated:
        assert ann.description, f"Empty description for: {ann.entry.raw_line}"


def test_annotate_valid_entries_count():
    entries = load_from_text(SAMPLE_CRONTAB)
    valid = [e for e in entries if e.is_valid]
    annotated = annotate_entries(valid)
    assert len(annotated) == len(valid)


def test_annotate_at_daily_description():
    entries = load_from_text("@daily /usr/bin/logrotate")
    annotated = annotate_entries(entries)
    assert len(annotated) == 1
    assert "midnight" in annotated[0].description.lower() or "daily" in annotated[0].description.lower()


def test_annotate_step_schedule_description():
    entries = load_from_text("*/15 * * * * /usr/bin/monitor")
    annotated = annotate_entries(entries)
    assert "15" in annotated[0].description


def test_annotate_range_schedule_description():
    entries = load_from_text("0 9-17 * * 1-5 /usr/bin/workday-task")
    annotated = annotate_entries(entries)
    desc = annotated[0].description
    assert "9" in desc and "17" in desc


def test_annotate_invalid_entry_description():
    entries = load_from_text("not_a_cron_entry")
    annotated = annotate_entries(entries)
    invalid = [a for a in annotated if not a.entry.is_valid]
    assert all(a.description == "Invalid schedule" for a in invalid)


def test_annotate_comment_in_notes():
    entries = load_from_text("@daily /usr/bin/logrotate # rotate logs")
    annotated = annotate_entries(entries)
    notes_text = " ".join(annotated[0].notes)
    assert "rotate logs" in notes_text
