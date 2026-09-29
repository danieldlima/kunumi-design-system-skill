---
id: 0010
status: accepted
date: 2026-09-16
scope: web.new
artifact: references/slide-template-measured.md
rules: none
tags: typography, scale, layout, measurement, rule-gap
supersedes: 0006
---

# The title ratio is per slide role, and surplus vertical space is the template's norm

## Context

ADR 0006 read `tokens.json#typography.scaleRatios.title` — `"5x - 7.5x"` — as title-size over
body-size, found a 68px title on 20px body (3.4x) to be under the floor, and raised the title to
100px. It recorded the ratio as an unchecked checklist question.

The team's slide template contradicts the premise. Measured across the export:

| Slide role | Title | Body | Ratio |
|---|---|---|---|
| Phase display | 64 | 21 | 3.05x |
| Content slide | 43 | 17 | 2.53x |
| Keyword slide | 53 | 27 | 1.96x |
| Resource slide | 27 | 16 | 1.69x |
| Column slide | 31 | 19 | 1.63x |

**Nothing reaches 5x.** The brandbook's own variables do not either, in either direction:
`Abertura/Título` at 180 over `Miolo/Texto` at 20 is 9x, and `Miolo/Título` at 22 over the same body
is 1.1x. Three sources, three answers — which means `5x - 7.5x` is not a title-over-body ratio at
all. `scaleRatios` carries `gridUnit: "y"` and `titleGridHeight: "2y"`, so the printed range is
most likely stated against the grid unit, and 0006 read it against the wrong denominator.

## Decision

Title scale is **per slide role**, in the measured band **1.6x – 3.1x** for content, chapter and
keyword slides. It is not a single global ratio and must not be linted as one.

`5x - 7.5x` is left in `tokens.json` untouched and unenforced. It is not contradicted for the one
case this export cannot show — a cover slide, absent from pages 44–72 — where the brandbook's own
9x sits in the same order of magnitude.

The ratio numbers are also **historical**, in the sense set out in
`references/slide-template-measured.md`: they were measured on sentence-case Figtree titles, and
uppercase Neue Machina Inktrap at +3% tracking carries different optical mass at the same px. Treat
the band as a sanity range, not a target.

## Consequence

The checklist question 5a proposed by 0006 — "does the title measure 5x to 7.5x the body?" — must
not be added. The question to ask instead is whether the title is inside 1.6x–3.1x of body **for
that slide's role**.

**The vertical-hole diagnosis in 0006 was wrong.** 0006 attributed a 200px gap between copy and
flow band to a title lacking mass, and fixed it by tripling the title. The template shows that a
single content band floating in a mostly empty canvas is a first-class layout: its timeline page
puts content in y 397..603, **19% of the canvas height**, with 397px empty above and 443px below,
and the band sits near the vertical centre rather than filling from the top.

So the correct response to surplus vertical space is to **centre the band and leave the air**, not
to inflate type until the gap closes. The 100px title shipped on `konstrukt-fluxo` is above every
measured precedent and should be revisited against this file rather than treated as settled.

This does not disturb ADR 0008's finding that stretching *boxes* to absorb surplus height is worse
than air between them — the template confirms it, holding node width constant at 148px regardless
of the space available.
