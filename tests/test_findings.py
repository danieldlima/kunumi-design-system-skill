"""Contract tests for the finding and report shapes."""

from __future__ import annotations

import json


def _finding(**overrides):
    from kunumi_design.findings import Finding

    base = dict(
        rule="color.prohibition.black",
        severity="blocker",
        scope="web.new",
        locus="body",
        path="/tmp/a.html",
        line=12,
        message="m",
        fix="f",
        authority="tokens.json#color.prohibition",
    )
    base.update(overrides)
    return Finding(**base)


def _report(findings):
    from kunumi_design.findings import Report

    return Report(
        artifact="/tmp/a.html",
        scope="web.new",
        scope_reason="default",
        findings=tuple(findings),
        rules_evaluated=19,
        rules_skipped=("logo.min-height",),
    )


def test_exit_code_ranks_blocker_above_violation():
    assert _report([_finding()]).exit_code == 2
    assert _report([_finding(severity="violation")]).exit_code == 1
    assert _report([_finding(severity="advisory")]).exit_code == 0
    assert _report([_finding(severity="note")]).exit_code == 0
    assert _report([]).exit_code == 0


def test_counts_sum_to_the_finding_total():
    report = _report([_finding(), _finding(severity="advisory"), _finding(severity="note")])
    assert sum(report.counts.values()) == len(report.findings)


def test_json_contract_is_camel_case_and_versioned():
    payload = json.loads(json.dumps(_report([_finding()]).to_dict()))
    assert payload["schema"] == "kunumi.design-report/v1"
    assert payload["schemaVersion"] == 1
    assert payload["scopeReason"] == "default"
    assert payload["rulesEvaluated"] == 19
    assert payload["rulesSkipped"] == ["logo.min-height"]


def test_severity_floor_is_inclusive():
    report = _report([_finding(severity="advisory"), _finding(severity="violation")])
    assert {f.severity for f in report.filtered("violation").findings} == {"violation"}
    assert len(report.filtered("advisory").findings) == 2


def test_tally_is_greppable():
    tally = _report([_finding()]).tally()
    assert "blockers=1" in tally
    assert "scope=web.new" in tally


def test_none_fields_are_dropped_from_json():
    payload = _finding(observed=None, expected=None).to_dict()
    assert "observed" not in payload
    assert "line" in payload


def test_sort_puts_blockers_first():
    from kunumi_design.findings import sort_findings

    ordered = sort_findings([_finding(severity="note"), _finding(severity="blocker")])
    assert [f.severity for f in ordered] == ["blocker", "note"]
