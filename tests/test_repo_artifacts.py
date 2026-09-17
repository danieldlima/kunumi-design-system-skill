"""Ratchet tests against the repository's own artifacts.

These began as proof that the engine finds real defects: the display stack carried Arial, the
Instituto cover recoloured an approved mark with a CSS filter, and both committed previews were
JPEGs wearing a `.png` extension while being older than the sources they depicted.

All four are now fixed, so the tests are inverted: they assert the defects stay gone. That
inversion is the ratchet. Each one tightens once, never loosens.
"""

from __future__ import annotations

import pathlib

import pytest


@pytest.fixture(scope="module")
def web_dir(skill_dir):
    return skill_dir / "assets" / "web"


def test_display_stack_no_longer_carries_arial(web_dir, registry, lint):
    """typography.md:35 - Arial is a body fallback only. Never use Arial for display."""
    _, triggered = lint(web_dir / "kunumi-tokens.css", registry)
    assert "typography.display.no-arial" not in triggered


def test_preview_no_longer_recolors_an_approved_mark(web_dir, registry, lint):
    """logo-governance.md prohibition 4 - no effects or other colors on the mark.

    The Instituto cover already sourced the negative lockup, so the `brightness(0) invert(1)`
    filter was both a prohibition breach and redundant.
    """
    _, triggered = lint(web_dir / "template-preview.html", registry)
    assert "logo.no-effects" not in triggered


PREVIEW_FRAMES = [
    "template-preview-kunumi-capa.png",
    "template-preview-kunumi-dados.png",
    "template-preview-instituto-gradiente.png",
    "template-preview-instituto-pixels.png",
]


@pytest.mark.parametrize("name", PREVIEW_FRAMES)
def test_committed_previews_are_real_and_current(name, web_dir, registry, lint):
    _, triggered = lint(web_dir / name, registry)
    assert triggered == set()


def test_every_frame_has_a_committed_render(web_dir):
    """One PNG per frame, no PNG without a frame, and every PNG claimed by the render record.

    Frame-to-file matching alone only proves a name is plausible. The render.json is what proves
    the file came out of a render at all, which is the half `artifact.stale` cannot see: a
    screenshot is younger than its sources and passes every age check.
    """
    import json
    import re

    html = (web_dir / "template-preview.html").read_text(encoding="utf-8")
    frames = set(re.findall(r'data-kunumi-frame="([^"]+)"', html))
    committed = {path.name for path in web_dir.glob("template-preview-*.png")}
    assert committed == {f"template-preview-{name}.png" for name in frames}

    record = json.loads((web_dir / "template-preview.render.json").read_text(encoding="utf-8"))
    assert record["schema"] == "kunumi.render/v1"
    # Names, not paths: `renders` stores absolute paths belonging to the machine that rendered.
    produced = {pathlib.Path(item).name for item in record["renders"]}
    assert committed == produced


def test_unprovenanced_raster_is_flagged(web_dir, registry, lint):
    """An orphan PNG beside the HTML is a violation, even when it is brand-new.

    This is the rule that a screenshot cannot pass. `artifact.stale` would clear it, because a
    file taken seconds ago is newer than every source it depicts.
    """
    stray = web_dir / "template-preview-handmade.png"
    stray.write_bytes((web_dir / "template-preview-kunumi-capa.png").read_bytes())
    try:
        _, triggered = lint(stray, registry)
        assert "artifact.unprovenanced" in triggered
        assert "artifact.stale" not in triggered, "a fresh screenshot passes the age check"
    finally:
        stray.unlink(missing_ok=True)


def test_supplied_assets_are_not_judged_for_provenance(skill_dir, registry, lint):
    """A brand mark is not a render and must never be asked for a render.json.

    The rule keys on a sibling `.html`, which is what separates "this directory delivers rendered
    artifacts" from "this directory holds supplied files".
    """
    mark = skill_dir / "assets/local/brand-marks/core/kunumi_logotipo_positivo_rgb.png"
    _, triggered = lint(mark, registry)
    assert "artifact.unprovenanced" not in triggered


def test_repo_web_artifacts_have_no_blockers(web_dir, registry, lint):
    """The ratchet threshold enforced in CI."""
    for path in sorted(web_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in (".html", ".css", ".png", ".svg"):
            continue
        report, _ = lint(path, registry)
        blockers = [f.rule for f in report.findings if f.severity == "blocker"]
        assert blockers == [], f"{path.name}: {blockers}"


def test_token_sheet_is_clean_and_the_leading_tension_is_resolved(web_dir, registry, lint):
    """No violation survives on the token sheet, and the history says why.

    `.kunumi-title` used to set 1.55 leading — outside lineHeightRanges.display, but a faithful
    implementation of the `Miolo/Título` variable (34px at 22px = 1.545). Decision 0002 recorded
    that tension rather than silencing the rule. Decision 0009 resolved it: the team's own slide
    template measures 137.5% on display text, so 34px is a transcription error and the CSS is now
    1.375.

    Both entries must stay reachable through the rule's join key, or the correction loses its
    reasoning the moment someone wonders why the value is 1.375.
    """
    from kunumi_design import decisions

    _, triggered = lint(web_dir / "kunumi-tokens.css", registry)
    assert triggered == set()

    recorded = decisions.select(decisions.load_all(), rule="typography.line-height.display")
    assert [item.id for item in recorded][0] == "0009"


def test_preview_frames_are_annotated(web_dir):
    """Frames and roles must stay annotated, or render and lint both lose their footing."""
    text = (web_dir / "template-preview.html").read_text(encoding="utf-8")
    assert text.count("data-kunumi-frame=") == 4
    assert 'data-kunumi-exempt="viewer-chrome"' in text
    assert 'data-kunumi-role="logo"' in text
