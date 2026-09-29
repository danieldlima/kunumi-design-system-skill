"""Render tests, skipped when no engine is reachable.

The skip is the point: the skill must stay usable with no browser at all, so the suite has to
pass on a machine that cannot render.
"""

from __future__ import annotations

import pytest


def _capability():
    from kunumi_design import render

    return render.probe()


needs_engine = pytest.mark.skipif(
    not _capability().available or not _capability().measures,
    reason="no measuring render engine available",
)


def test_probe_always_answers():
    capability = _capability()
    assert capability.engine
    assert capability.reason
    assert capability.how_to_install


def test_lint_never_fails_when_rendering_is_unavailable(fixtures_dir, registry, lint):
    """A missing engine must degrade to a skipped rule, never to a crash or a false pass."""
    report, _ = lint(fixtures_dir / "compliant-card.html", registry)
    assert "logo.min-height" in report.rules_skipped


@needs_engine
def test_render_produces_a_png_and_measurements(fixtures_dir, tmp_path):
    from kunumi_design import render

    result = render.render_html(
        fixtures_dir / "compliant-card.html",
        out_dir=tmp_path,
        canvas=(800, 600),
        scale=1.0,
        reduced_motion=True,
    )
    assert result.renders
    assert result.renders[0].exists()
    assert result.meta_path.exists()


@needs_engine
def test_measurements_round_trip_through_json(fixtures_dir, tmp_path):
    from kunumi_design import render

    result = render.render_html(
        fixtures_dir / "noncompliant-logo.html",
        out_dir=tmp_path,
        canvas=(800, 600),
        scale=1.0,
    )
    reloaded = render.load_measurements(result.meta_path)
    assert len(reloaded) == len(result.measurements)


@needs_engine
def test_undersized_mark_is_caught_only_with_measurements(fixtures_dir, registry, tmp_path):
    """The 28px minimum is unknowable statically once clamp() is involved."""
    from kunumi_design import render
    from kunumi_design.checks import review

    fixture = fixtures_dir / "undersized-logo.html"
    fixture.write_text(
        """<!doctype html><html><head><meta charset="utf-8"><style>
             .mark { height: 16px; width: 56px; }
           </style></head>
           <body><img class="mark" data-kunumi-role="logo" src="m.png" alt="Kunumi"></body>
           </html>""",
        encoding="utf-8",
    )
    try:
        static = review([fixture], registry)[0]
        assert "logo.min-height" in static.rules_skipped

        result = render.render_html(fixture, out_dir=tmp_path, canvas=(400, 300), scale=1.0)
        measured = review(
            [fixture], registry,
            capabilities=frozenset({"render"}),
            measurements=result.measurements,
        )[0]
        assert "logo.min-height" in {f.rule for f in measured.findings}
    finally:
        fixture.unlink(missing_ok=True)


@needs_engine
def test_long_title_must_leave_the_display_face(fixtures_dir, registry, tmp_path):
    """A title past two rendered lines is a violation, and the Figtree version is not.

    Line count is the whole rule, and it is only knowable from the rendered box — the same reason
    `logo.min-height` needs the render pass. Both titles in the fixture carry identical wording, so
    the only difference the check can be reacting to is the face.
    """
    from kunumi_design import render
    from kunumi_design.checks import review

    fixture = fixtures_dir / "long-title.html"

    static = review([fixture], registry)[0]
    assert "typography.display.long-title" in static.rules_skipped

    result = render.render_html(
        fixture, out_dir=tmp_path, canvas=(900, 700), scale=1.0, reduced_motion=True
    )
    lines = {item.element_id: item.line_boxes for item in result.measurements if item.element_id}
    assert lines["too-long"] > 2 and lines["corrected"] > 2, "both titles must actually wrap"

    measured = review(
        [fixture], registry,
        capabilities=frozenset({"render"}),
        measurements=result.measurements,
    )[0]
    flagged = [f for f in measured.findings if f.rule == "typography.display.long-title"]
    assert [f.locus for f in flagged] == ["too-long"]


@needs_engine
def test_the_long_title_class_is_not_judged_for_case_or_tracking(fixtures_dir, registry, lint):
    """The exception must not collide with the rules it deliberately departs from.

    `.kunumi-title-long` contains `kunumi-title`, so without the carve-out in `_display_tokens`
    both `typography.display.case` and `typography.display.tracking` would fire on a title the
    system itself asked to be set sentence case at tracking 0.
    """
    report, triggered = lint(fixtures_dir / "long-title.html", registry)
    assert "typography.display.case" not in triggered
    assert "typography.display.tracking" not in triggered

    offenders = [f.locus for f in report.findings]
    assert not any("title-long" in locus for locus in offenders)


@needs_engine
def test_line_count_survives_the_json_round_trip(fixtures_dir, tmp_path):
    """A reloaded render must carry line counts, or the long-title rule silently stops working.

    `to_dict` lists measurement fields by hand, so a new field is dropped unless it is added
    there too — and the failure is invisible: the rule runs, finds 0 lines everywhere, and
    reports a clean pass.
    """
    from kunumi_design import render

    result = render.render_html(
        fixtures_dir / "long-title.html",
        out_dir=tmp_path, canvas=(900, 700), scale=1.0, reduced_motion=True,
    )
    live = {item.element_id: item.line_boxes for item in result.measurements if item.element_id}
    reloaded = {
        item.element_id: item.line_boxes
        for item in render.load_measurements(result.meta_path) if item.element_id
    }
    assert live == reloaded
    assert reloaded["too-long"] > 2


@needs_engine
def test_opening_statement_is_exempt_but_still_judged_for_case(fixtures_dir, registry, tmp_path):
    """The statement exemption is narrow: it drops the line limit and nothing else.

    `long_title_face` keys on the measured role, so `statement` steps out of it. Case and tracking
    key on the selector cascade instead, so a statement is still required to be uppercase at +3%
    — which is the whole reason the exemption is safe to grant. See ADR 0018.
    """
    from kunumi_design import render
    from kunumi_design.checks import review

    fixture = fixtures_dir / "opening-statement.html"
    fixture.write_text(
        """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
             :root {
               --kunumi-font-display: "Space Grotesk", "Figtree", sans-serif;
               --kunumi-track-display: 0.03em;
             }
             .slot { width: 420px; }
             .kunumi-display {
               font-family: var(--kunumi-font-display);
               font-size: 44px;
               text-transform: uppercase;
               letter-spacing: var(--kunumi-track-display);
               line-height: 1.375;
             }
           </style></head><body>
             <div class="slot">
               <h1 class="kunumi-display" data-kunumi-role="statement"
                   id="opener">Inteligência para o que ainda não tem nome</h1>
             </div>
             <div class="slot">
               <h2 class="kunumi-display" data-kunumi-role="title"
                   id="plain">Inteligência para o que ainda não tem nome</h2>
             </div>
           </body></html>""",
        encoding="utf-8",
    )
    try:
        result = render.render_html(
            fixture, out_dir=tmp_path, canvas=(900, 700), scale=1.0, reduced_motion=True
        )
        lines = {m.element_id: m.line_boxes for m in result.measurements if m.element_id}
        assert lines["opener"] > 2 and lines["plain"] > 2, "identical copy must wrap identically"

        measured = review(
            [fixture], registry,
            capabilities=frozenset({"render"}),
            measurements=result.measurements,
        )[0]
        flagged = [f for f in measured.findings if f.rule == "typography.display.long-title"]
        assert [f.locus for f in flagged] == ["plain"], "only the plain title is judged"

        # The narrowness of the exemption: case and tracking still apply to both.
        assert "typography.display.case" not in {f.rule for f in measured.findings}
        assert "typography.display.tracking" not in {f.rule for f in measured.findings}
    finally:
        fixture.unlink(missing_ok=True)
