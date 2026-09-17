"""Scope tests: the documented tensions, asserted.

Each case here corresponds to a real conflict between reference files. If any of these starts
failing, the linter has begun contradicting the brandbook it is supposed to enforce.
"""

from __future__ import annotations


def test_chart_scope_permits_the_chart_palette(fixtures_dir, registry, lint):
    """Inside a chart, the data palette is the correct choice, not a misuse."""
    _, default_scope = lint(fixtures_dir / "noncompliant-chart.html", registry)
    _, chart_scope = lint(fixtures_dir / "noncompliant-chart.html", registry, scope="web.chart")
    assert "color.chart.data-only" in default_scope
    assert "color.chart.data-only" not in chart_scope


def test_instituto_scope_permits_the_gradient_terminus(fixtures_dir, registry, lint):
    """tokens.json sanctions #000000 as the Instituto gradient terminus and nowhere else."""
    _, default_scope = lint(fixtures_dir / "noncompliant-card.html", registry)
    _, instituto = lint(fixtures_dir / "noncompliant-card.html", registry, scope="web.instituto")
    assert "color.prohibition.black" in default_scope
    assert "color.prohibition.black" not in instituto


def test_profile_photo_scope_permits_the_exact_triplets(fixtures_dir, registry, lint):
    """profile-photo-system.md prints twelve exact combinations using pure black and white."""
    _, scoped = lint(fixtures_dir / "noncompliant-card.html", registry, scope="web.profile-photo")
    assert "color.prohibition.black" not in scoped
    assert "color.prohibition.white" not in scoped


def test_deck_derived_scope_demotes_rather_than_mutes(fixtures_dir, registry, lint):
    """Deck work preserves inherited Figtree type, so the case rule becomes a note, not silence.

    Demotion is the point: the observation survives and only the alarm is dropped.
    """
    report, _ = lint(fixtures_dir / "noncompliant-card.html", registry, scope="web.deck-derived")
    by_rule = {found.rule: found.severity for found in report.findings}
    assert by_rule.get("typography.display.case") == "note"
    assert "typography.display.case" not in registry.resolved_scope("web.deck-derived").relax


def test_exempt_scope_evaluates_nothing(registry):
    active, skipped = registry.effective_rules("exempt")
    assert active == ()
    assert len(skipped) == len(registry.rules)


def test_every_relaxing_scope_states_its_authority(registry):
    """A scope may not relax or demote a rule without citing why.

    This is the guard against scope becoming a mute button.
    """
    for name in registry.scopes:
        scope = registry.resolved_scope(name)
        if scope.relax or scope.demote:
            assert scope.why, f"scope {name} relaxes rules without a stated authority"


def test_skipped_rules_are_always_reported(fixtures_dir, registry, lint):
    """Silence must be auditable: a rule that did not run has to say so."""
    report, _ = lint(fixtures_dir / "compliant-card.html", registry)
    assert "logo.min-height" in report.rules_skipped


def test_unknown_scope_fails_loudly(registry):
    import pytest

    with pytest.raises(SystemExit):
        registry.effective_rules("web.invented")
