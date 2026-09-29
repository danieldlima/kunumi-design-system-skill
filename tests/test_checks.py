"""Fixture-driven check tests.

Every fixture is paired with the exact set of rule ids it must trigger, asserted as set
equality. `assert findings` would pass while a check silently stopped working, and a linter suite
that cannot fail is how a linter rots.
"""

from __future__ import annotations

import pathlib

import pytest


NONCOMPLIANT_CARD = {
    "typography.display.no-arial",
    "color.prohibition.black",
    "typography.negative-tracking",
    "color.prohibition.white",
    "typography.display.case",
    "typography.display.tracking",
    "typography.line-height.body",
    "geometry.radius",
    "geometry.spacing-scale",
}

NONCOMPLIANT_CHART = {
    "color.chart.data-only",
    "color.superseded",
    "color.prefer-semantic-token",
    # Its call-to-action button has no focus style and the page does not link the token sheet.
    "interaction.focus-visible",
}

NONCOMPLIANT_LOGO = {
    "logo.no-effects",
    "logo.no-distortion",
}


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("noncompliant-card.html", NONCOMPLIANT_CARD),
        ("noncompliant-chart.html", NONCOMPLIANT_CHART),
        ("noncompliant-logo.html", NONCOMPLIANT_LOGO),
        ("responsive-offscale.html", {"layout.breakpoint-scale"}),
        ("responsive-onscale.html", set()),
        ("interactive-no-focus.html", {"interaction.focus-visible"}),
        ("interactive-linked.html", set()),
        ("focus-removed.html", {"interaction.focus-outline-removed"}),
        ("focus-replaced.html", set()),
        ("published-no-og.html", {"artifact.social-meta"}),
        ("published-complete.html", set()),
    ],
)
def test_noncompliant_fixture_triggers_exactly(fixture, expected, fixtures_dir, registry, lint):
    _, triggered = lint(fixtures_dir / fixture, registry)
    assert triggered == expected


def test_compliant_card_is_clean(fixtures_dir, registry, lint):
    """The single most important test: a correct artifact must produce nothing that blocks it."""
    report, _ = lint(fixtures_dir / "compliant-card.html", registry)
    blocking = [found for found in report.findings if found.blocks_delivery]
    assert blocking == [], [f"{f.rule}: {f.observed}" for f in blocking]


def test_exemption_covers_chrome_but_a_frame_re_enters_brand_scope(fixtures_dir, registry, lint):
    """Exemption must flow down a subtree and stop at a frame.

    Viewer chrome and brand artifact share a stylesheet in practice, so the chrome's near-Chumbo
    backdrop and its 3px corner must be suppressed. But the frame inside that chrome is the
    deliverable, so it stays under review — its literal Gelo hex is still an advisory. Both
    directions matter: without the flow-down the linter cries wolf, and without the reset it
    goes blind to the actual artifact.
    """
    report, triggered = lint(fixtures_dir / "exempt-chrome.html", registry)

    # Chrome: suppressed. #11151a is not an approved color and 3px is not a sanctioned radius.
    assert "color.palette.unapproved" not in triggered
    assert "geometry.radius" not in triggered

    # Frame: still reviewed.
    frame_findings = [f for f in report.findings if ".frame" in f.locus]
    assert {f.rule for f in frame_findings} == {"color.prefer-semantic-token"}


def test_logo_checks_ignore_non_logo_selectors(fixtures_dir, registry, lint):
    """A mark rule must not fire on an ordinary element."""
    report, _ = lint(fixtures_dir / "noncompliant-card.html", registry)
    assert all(not found.rule.startswith("logo.") for found in report.findings)


def test_findings_carry_authority(fixtures_dir, registry, lint):
    """Every finding must cite where its rule comes from, or it cannot be argued with."""
    report, _ = lint(fixtures_dir / "noncompliant-card.html", registry)
    missing = [found.rule for found in report.findings if not found.authority]
    assert missing == []


def test_unservable_display_face_is_flagged(fixtures_dir, registry, lint):
    """A commercial face in a web display stack is a violation, not a nicety.

    It cannot be bundled, so it cannot be served; naming it makes the rendered title depend on
    whether the machine doing the rendering happens to have a licensed copy. The two faces are
    not metrically compatible, so that is a layout difference, not just a texture one.
    """
    fixture = fixtures_dir / "unservable-face.html"
    fixture.write_text(
        """<!doctype html><html><head><meta charset="utf-8"><style>
             :root {
               --kunumi-font-display: "PP Neue Machina", "Space Grotesk", sans-serif;
             }
             .kunumi-title {
               font-family: var(--kunumi-font-display);
               text-transform: uppercase;
               letter-spacing: 0.03em;
               line-height: 1.375;
             }
           </style></head><body><h1 class="kunumi-title">Konstrukt</h1></body></html>""",
        encoding="utf-8",
    )
    try:
        _, triggered = lint(fixture, registry)
        assert "typography.display.no-unservable-face" in triggered
    finally:
        fixture.unlink(missing_ok=True)


def test_the_shipped_token_sheet_has_no_unservable_face(registry, lint):
    """The token sheet is the thing every artifact links, so it must be clean itself."""
    sheet = (
        pathlib.Path(__file__).resolve().parents[1]
        / "skills/kosmos-design-system/assets/web/kunumi-tokens.css"
    )
    _, triggered = lint(sheet, registry)
    assert "typography.display.no-unservable-face" not in triggered


def test_published_page_reports_missing_meta_and_a_wrong_image_size(fixtures_dir, registry, lint):
    """Both halves of the rule fire: what is missing, and a declared size off digital.og."""
    report, _ = lint(fixtures_dir / "published-no-og.html", registry)
    observed = sorted(f.observed for f in report.findings if f.rule == "artifact.social-meta")
    assert observed == ["missing og:image, <link rel=\"icon\">", "og:image declared 1080x1080"]


def test_social_meta_is_opt_in(fixtures_dir, registry, lint):
    """A mock-up is not a published page: under web.new the rule is not even evaluated."""
    report, triggered = lint(fixtures_dir / "published-no-og.html", registry, scope="web.new")
    assert "artifact.social-meta" not in triggered
    assert "artifact.social-meta" in report.rules_skipped


def test_breakpoints_are_demoted_on_a_slide_replica(fixtures_dir, registry, lint):
    """A deck replica keeps its stage breakpoints; the observation stays, the alarm drops."""
    report, _ = lint(fixtures_dir / "responsive-offscale.html", registry, scope="web.deck-derived")
    found = [f for f in report.findings if f.rule == "layout.breakpoint-scale"]
    assert [f.severity for f in found] == ["note"]


def test_breakpoint_finding_is_aggregated(fixtures_dir, registry, lint):
    """Two invented breakpoints are one decision about the layout, not two defects."""
    report, _ = lint(fixtures_dir / "responsive-offscale.html", registry)
    found = [f for f in report.findings if f.rule == "layout.breakpoint-scale"]
    assert len(found) == 1
    assert found[0].locus == "2 media queries"
