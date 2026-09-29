---
id: 0016
status: accepted
date: 2026-09-16
scope: web.new
artifact: assets/web/template-preview.html
rules: artifact.stale, geometry.spacing-scale, typography.display.long-title
tags: preview, render, provenance, container-queries, calibration
---

# The preview is a contact sheet, so the renderer can produce it

## Context

`template-preview.png` and `template-preview-instituto.png` were **screenshots taken by hand in a
browser**, at 2660×1498, and `artifact.stale` had been red on them since 2026-09-14. The fix the
rule prescribes — re-render the artifact — did not work, and the reason was structural rather than
cultural.

`template-preview.html` was a carousel: four frames stacked at `position: absolute; visibility:
hidden; opacity: 0`, one `.is-active` at a time. The render worker **skips invisible frames on
purpose**, and its comment is right to: a blank PNG that looks like a rendered artifact is worse
than reporting that nothing was captured. So `render template-preview.html` could only ever yield
**1 of 4** frames. A hand-taken screenshot was the only way to get the other three — and two of the
four were never captured at all.

The intent was always generation. `DESIGNER_SKILL_PLAN.md` prescribes the render command and lists
"regenerar os dois PNG" as a phase-3 task. The carousel is what made it impossible to comply.

## Decision

Every frame is mounted and visible at once. `.stage` is a grid of four `.slide` elements, each
carrying the 16:9 and pinned to the 1920 of `geometry.stage`, so a captured frame is a true
1920×1080 replica rather than a scaled approximation. The carousel script and its navigation are
gone; `is-active` became `is-settled`, which is what the class actually meant to the renderer —
entrance animations have landed.

The four PNGs are generated, one per `data-kunumi-frame`:

```bash
kunumi_critic.py render assets/web/template-preview.html --canvas 2048x1200 --scale 2 --reduced-motion
```

**Trade-off, stated plainly:** the click-through is gone. For the job this file does here — the
linter's calibration set and the visual reference — a contact sheet is better, and a reader
scrolls. If presenting matters later, the answer is a separate `template-viewer.html`, entirely
`data-kunumi-exempt`, with no committed render.

`test_every_frame_has_a_committed_render` is what keeps the practice: one PNG per frame and no PNG
without a frame. A screenshot has no frame to belong to, so it appears as an extra file and fails.

## Consequence

Three things came out of this that were not in the plan.

**Viewport units were only ever proportional by accident.** Type inside a frame was sized in `vw`,
which looked right because the old stage width was itself derived from the viewport. A contact sheet
breaks that coupling, and the cover title immediately started breaking mid-word. All 27 slide-scoped
`vw` values are now `cqw` against `container-type: inline-size` on the frame — which is what the
original comment about "display type scales with the stage" intended all along.

**The mid-word break was already committed.** The replaced screenshot shows `INTELIGÊNCI / A PARA
O`. `design-loop.md` names this exact defect as its reason for existing — *"whether a display
headline broke mid-word — and that last one is a real defect found in this repository's own
preview"* — and it had been sitting in the versioned PNG ever since. Nobody could see it, because
nobody could re-render the file to compare.

**Annotating the text surfaced three real violations.** The file carried `data-kunumi-frame` and
`data-kunumi-role="logo"` and nothing else, so the measurement pass returned 10 elements and zero
titles: **every measured type rule passed in silence on the repo's own calibration set.** It now
returns 26. With titles visible, `typography.display.long-title` fires on three of the four frames,
at 4, 3 and 3 rendered lines.

Those three violations are **left open on purpose**. They are covers and statement slides, and
`Abertura/Título` is 180px on a 1920 stage — a long statement at that size wraps past two lines by
design. That is evidence against the threshold ADR 0012 chose, and the argument there was built on
the assumption that covers wrap to two. Resolving it is a design call, not a lint call: either
ADR 0012 gains a scope for opening statements, or these covers change. Recorded here so the next
reader does not mistake three open violations for neglect.

Two advisories stand, both predating this change: `geometry.spacing-scale` on the slide interiors,
for the reason ADR 0014 gives, and one `background-image` colour literal.
