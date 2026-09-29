#!/usr/bin/env python3
"""The finding and report shapes shared by every artifact check.

`validate-skills.py` reports with pre-formatted `list[str]`, which is fine for a binary
pre-merge gate but cannot carry severity, provenance, or machine-readable locations. Artifact
review needs all three: a designer has to know whether a finding blocks delivery, and has to be
able to read the brandbook passage a disputed finding came from instead of deleting the check.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal


Severity = Literal["blocker", "violation", "advisory", "note"]

SEVERITY_ORDER: tuple[Severity, ...] = ("note", "advisory", "violation", "blocker")
"""Ascending severity. Index position is the comparison key for `--severity-min`."""

REPORT_SCHEMA = "kunumi.design-report/v1"
REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class Finding:
    """One machine-decidable defect in a produced artifact.

    Attributes:
        rule: Dotted, stable rule id such as `logo.no-effects`. Greppable and citable.
        severity: Tier that decides whether delivery is blocked.
        scope: Rule scope the artifact was evaluated under, such as `web.instituto`.
        locus: Where in the artifact, in the artifact's own vocabulary — a CSS selector, a
            frame name, or a text-node description.
        path: Absolute or repo-relative path to the file the finding sits in.
        line: 1-based line number, or None for whole-file and render-derived findings.
        message: One sentence stating the defect.
        fix: The concrete correction, phrased as an instruction.
        observed: The offending value, when there is a single one worth quoting.
        expected: The value the rule requires, when it is expressible.
        authority: Source file and anchor the rule derives from, such as
            `logo-governance.md#minimum-size`. This is the trust mechanism: it makes a
            contested finding arguable against the brandbook rather than deletable.
    """

    rule: str
    severity: Severity
    scope: str
    locus: str
    path: str
    line: int | None
    message: str
    fix: str
    observed: str | None = None
    expected: str | None = None
    authority: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Render the finding as a JSON-ready mapping.

        Returns:
            The finding's fields, with None entries dropped so the JSON stays readable.
        """
        return {key: value for key, value in asdict(self).items() if value is not None}

    @property
    def blocks_delivery(self) -> bool:
        """Whether this finding must be cleared before the artifact ships."""
        return self.severity in ("blocker", "violation")


def severity_at_least(severity: Severity, minimum: Severity) -> bool:
    """Test a severity against an inclusive floor.

    Args:
        severity: The finding's severity.
        minimum: The lowest severity to keep.

    Returns:
        True when `severity` is at or above `minimum`.
    """
    return SEVERITY_ORDER.index(severity) >= SEVERITY_ORDER.index(minimum)


@dataclass(frozen=True, slots=True)
class Report:
    """The result of reviewing one artifact.

    Attributes:
        artifact: Path to the reviewed artifact.
        scope: Rule scope that was applied.
        scope_reason: Why that scope was chosen, so the decision is auditable.
        findings: Every finding, in the order the checks produced them.
        rules_evaluated: How many rules actually ran.
        rules_skipped: Ids of rules that did not run, and therefore could not pass.
            Load-bearing: it makes silence auditable, so a scope cannot quietly mute a rule.
        renders: Paths of any PNG renders that accompanied the review.
    """

    artifact: str
    scope: str
    scope_reason: str
    findings: tuple[Finding, ...]
    rules_evaluated: int
    rules_skipped: tuple[str, ...] = ()
    renders: tuple[str, ...] = ()

    @property
    def counts(self) -> dict[str, int]:
        """Count findings per severity, including zeros.

        Returns:
            A mapping from severity name to occurrence count, in descending severity.
        """
        return {
            severity: sum(1 for found in self.findings if found.severity == severity)
            for severity in reversed(SEVERITY_ORDER)
        }

    @property
    def exit_code(self) -> int:
        """Map the worst finding onto a shell exit code.

        Returns:
            2 when a blocker is present, 1 when a violation is present, 0 otherwise.
            Advisories and notes never fail a run — that is what keeps them usable.
        """
        if any(found.severity == "blocker" for found in self.findings):
            return 2
        if any(found.severity == "violation" for found in self.findings):
            return 1
        return 0

    def filtered(self, minimum: Severity) -> Report:
        """Drop findings below a severity floor.

        Args:
            minimum: The lowest severity to keep.

        Returns:
            A new report carrying only the findings at or above `minimum`.
        """
        kept = tuple(f for f in self.findings if severity_at_least(f.severity, minimum))
        return Report(
            artifact=self.artifact,
            scope=self.scope,
            scope_reason=self.scope_reason,
            findings=kept,
            rules_evaluated=self.rules_evaluated,
            rules_skipped=self.rules_skipped,
            renders=self.renders,
        )

    def to_dict(self) -> dict[str, Any]:
        """Render the report against the `kunumi.design-report/v1` contract.

        Returns:
            A camelCase mapping matching the repository's other JSON files.
        """
        return {
            "schema": REPORT_SCHEMA,
            "schemaVersion": REPORT_SCHEMA_VERSION,
            "artifact": self.artifact,
            "scope": self.scope,
            "scopeReason": self.scope_reason,
            "counts": self.counts,
            "rulesEvaluated": self.rules_evaluated,
            "rulesSkipped": list(self.rules_skipped),
            "renders": list(self.renders),
            "findings": [found.to_dict() for found in self.findings],
        }

    def tally(self) -> str:
        """Render the greppable summary line.

        Mirrors the `matches=N shown=M` convention already used by `kunumi_lookup.py`, so shell
        pipelines can read a result without parsing JSON.

        Returns:
            A single line of `key=value` pairs.
        """
        counts = self.counts
        return (
            f"blockers={counts['blocker']} violations={counts['violation']} "
            f"advisories={counts['advisory']} notes={counts['note']} "
            f"scope={self.scope} renders={len(self.renders)} "
            f"evaluated={self.rules_evaluated} skipped={len(self.rules_skipped)}"
        )


def merge(reports: Sequence[Report]) -> Report:
    """Combine per-artifact reports into one.

    Args:
        reports: Reports to merge; must not be empty.

    Returns:
        A report spanning every input, keeping the highest severity and the union of skipped
        rules. `artifact` becomes a count when more than one artifact was reviewed.

    Raises:
        ValueError: When `reports` is empty.
    """
    if not reports:
        raise ValueError("merge() needs at least one report")
    if len(reports) == 1:
        return reports[0]

    skipped: list[str] = []
    for report in reports:
        for rule in report.rules_skipped:
            if rule not in skipped:
                skipped.append(rule)

    scopes = sorted({report.scope for report in reports})
    return Report(
        artifact=f"{len(reports)} artifacts",
        scope=",".join(scopes),
        scope_reason="merged across artifacts",
        findings=tuple(found for report in reports for found in report.findings),
        rules_evaluated=max(report.rules_evaluated for report in reports),
        rules_skipped=tuple(skipped),
        renders=tuple(path for report in reports for path in report.renders),
    )


def format_text(report: Report, *, relative_to: str | None = None) -> str:
    """Render a report for a terminal.

    Findings are grouped worst-first so the reader meets the blocking problems before the
    advisory noise.

    Args:
        report: The report to render.
        relative_to: Optional path prefix to strip from finding paths, for shorter output.

    Returns:
        The full text block, ending in the greppable tally line.
    """
    lines: list[str] = []
    for severity in reversed(SEVERITY_ORDER):
        group = [found for found in report.findings if found.severity == severity]
        if not group:
            continue
        for found in group:
            path = found.path
            if relative_to and path.startswith(relative_to):
                path = path[len(relative_to) :].lstrip("/")
            where = f"{path}:{found.line}" if found.line else path
            lines.append(f"{severity:<9} {found.rule}")
            lines.append(f"  {where}  ({found.locus})")
            lines.append(f"  {found.message}")
            if found.observed is not None or found.expected is not None:
                lines.append(f"  observed: {found.observed}  expected: {found.expected}")
            if found.fix:
                lines.append(f"  fix: {found.fix}")
            if found.authority:
                lines.append(f"  authority: {found.authority}")
            lines.append("")

    if report.rules_skipped:
        lines.append(f"not evaluated: {', '.join(report.rules_skipped)}")
        lines.append("")

    lines.append(report.tally())
    return "\n".join(lines)


def format_json(report: Report) -> str:
    """Render a report as JSON.

    Args:
        report: The report to serialize.

    Returns:
        Pretty-printed JSON matching the repository's formatting conventions.
    """
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def sort_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Order findings worst-first, then by file position.

    Args:
        findings: The findings to order.

    Returns:
        A tuple sorted by descending severity, then path, then line, then rule id.
    """
    return tuple(
        sorted(
            findings,
            key=lambda f: (
                -SEVERITY_ORDER.index(f.severity),
                f.path,
                f.line if f.line is not None else -1,
                f.rule,
            ),
        )
    )
