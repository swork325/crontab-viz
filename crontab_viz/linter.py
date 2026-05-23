"""Lint crontab entries and report potential issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import CronEntry


@dataclass
class LintIssue:
    entry: CronEntry
    severity: str  # 'error' | 'warning' | 'info'
    message: str

    def __str__(self) -> str:
        cmd = self.entry.command or "<no command>"
        return f"[{self.severity.upper()}] {cmd!r}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        return (
            f"{len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s), "
            f"{len(self.issues)} total issue(s)"
        )


def _check_entry(entry: CronEntry) -> List[LintIssue]:
    issues: List[LintIssue] = []

    if not entry.is_valid:
        issues.append(LintIssue(entry, "error", "Invalid cron expression"))
        return issues

    cmd = (entry.command or "").strip()
    if not cmd:
        issues.append(LintIssue(entry, "error", "Missing command"))

    if cmd and not any(c in cmd for c in ("/", ".", " ")):
        # Bare word command — might be missing a path
        issues.append(
            LintIssue(entry, "warning", "Command appears to lack an absolute path")
        )

    # Warn about very frequent schedules (every minute)
    if not entry.special:
        parts = (entry.minute, entry.hour, entry.dom, entry.month, entry.dow)
        if all(p == "*" for p in parts):
            issues.append(
                LintIssue(entry, "warning", "Job runs every minute — is that intentional?")
            )
        if entry.minute == "*" and entry.hour != "*":
            issues.append(
                LintIssue(entry, "info", "Job runs every minute within the specified hour(s)")
            )

    return issues


def lint_entries(entries: List[CronEntry]) -> LintResult:
    """Run all lint checks over a list of CronEntry objects."""
    result = LintResult()
    for entry in entries:
        result.issues.extend(_check_entry(entry))
    return result


def render_lint_report(result: LintResult) -> str:
    """Return a human-readable lint report string."""
    if not result.has_issues:
        return "No issues found."
    lines = [result.summary(), ""]
    for issue in result.issues:
        lines.append(str(issue))
    return "\n".join(lines)
