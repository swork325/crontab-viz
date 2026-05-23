"""Semantic validation of cron entries beyond basic parsing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import CronEntry


@dataclass
class ValidationIssue:
    entry: CronEntry
    severity: str  # 'error' | 'warning' | 'info'
    message: str

    def __str__(self) -> str:
        cmd = self.entry.command or "<no command>"
        return f"[{self.severity.upper()}] {cmd!r}: {self.message}"


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0

    def as_dict(self) -> dict:
        return {
            "total": len(self.issues),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "issues": [
                {"severity": i.severity, "command": i.entry.command, "message": i.message}
                for i in self.issues
            ],
        }


def _check_entry(entry: CronEntry) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if not entry.is_valid:
        issues.append(ValidationIssue(entry, "error", "Entry failed to parse"))
        return issues

    if not entry.command or not entry.command.strip():
        issues.append(ValidationIssue(entry, "error", "Command is empty"))

    schedule = entry.schedule
    if schedule == "* * * * *":
        issues.append(ValidationIssue(entry, "warning", "Runs every minute — intentional?"))

    if schedule.startswith("@"):
        known = {"@reboot", "@yearly", "@annually", "@monthly", "@weekly", "@daily", "@midnight", "@hourly"}
        if schedule.split()[0] not in known:
            issues.append(ValidationIssue(entry, "error", f"Unknown special schedule: {schedule!r}"))

    cmd = entry.command or ""
    if cmd.strip().startswith("/") is False and cmd.strip() and not any(
        cmd.strip().startswith(p) for p in ("bash", "python", "sh", "env", "sudo", "/")
    ):
        issues.append(ValidationIssue(entry, "info", "Command does not use an absolute path"))

    return issues


def validate_entries(entries: List[CronEntry]) -> ValidationReport:
    """Run semantic validation on all entries and return a consolidated report."""
    report = ValidationReport()
    for entry in entries:
        report.issues.extend(_check_entry(entry))
    return report
