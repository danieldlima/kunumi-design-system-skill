---
id: 0012
status: accepted
date: 2026-09-16
scope: web.new
artifact: references/typography.md
rules: typography.display.long-title, typography.display.case, typography.display.tracking
tags: typography, display, figtree, long-title, render
---

# A title past two lines leaves the display face for Figtree

## Context

`typography.md` states the rule without a length qualifier: titles are PP Neue Machina Inktrap or
Space Grotesk, **always uppercase**, tracked **+3%**. Nothing in the brandbook bounds how long a
title may be, and the rule reads as unconditional.

It stops working at length. The display face earns its place through exactly those two traits, and
both turn against a long title: uppercase removes the word shapes a reader scans by, and positive
tracking widens lines that are already long. A three-line uppercase Inktrap title is the one place
where the brandbook's own title recipe reads worse than body type set large.

The team already solved this. Their slide template sets "Nome longo do capítulo 2" in Figtree
sentence case at title size — measured in `references/slide-template-measured.md`.

## Decision

Past **two rendered lines**, a title is set in **Figtree SemiBold, sentence case, tracking 0**. Up
to two lines the brandbook rule stands unchanged.

**The threshold is two and not one** because `Abertura/Título` is 180px on a 1920px stage: nearly
every real cover wraps to two lines, so a one-line limit would retire the display face from the
covers it was chosen for. Two lines is the smallest limit that leaves the face its job.

**The fallback drops uppercase**, which is the part of this entry that departs from a printed rule
rather than filling a gap in one. Keeping uppercase and changing only the family was considered and
rejected: it would preserve the letter of "titles are always uppercase" while leaving the actual
defect in place, since caps are what break multi-line reading, not the Inktrap. The team's own
template is the precedent, and it is sentence case.

This is **not** the availability fallback. `fallbackOrder` answers whether the face is licensed and
present; this answers whether the title is too long for it. A licensed PP Neue Machina still yields
to Figtree at three lines.

It is also **not the first move**. Cutting the title to two lines is preferred. Figtree is correct
when the words are all load-bearing, not when the title is merely unedited — which is why the
finding's fix names both remedies.

## Consequence

Enforced as `typography.display.long-title`, `requires: ["render"]`. Line count is only knowable
from the rendered box, exactly as ADR 0006 argued about the title ratio — and this is the first rule
to act on that argument rather than record it.

Two pieces of machinery were needed, both worth knowing about:

**The render pass now counts line boxes.** Deriving lines from `height / lineHeight` fails where it
matters most: `line-height: normal` computes to the string `"normal"`, which is precisely the case
of an unstyled title. `_render_worker.py` walks a `Range` over the element's contents and counts
distinct rect tops instead, so `Measurement.line_boxes` is measured rather than inferred.

**`.kunumi-title-long` had to be carved out of the display checks.** The token contains
`kunumi-title`, so `classify_role` classified it as display and both `typography.display.case` and
`typography.display.tracking` fired on a title this very decision asked to be sentence case at
tracking 0. `_display_tokens` now excludes long-title selectors. They stay classified as display
for everything else, so the display **leading** range still governs them — the exception is about
case and tracking, not about rhythm.

A false violation against a system-prescribed value is worse than a missing rule, because it
teaches the reader to ignore the linter.
