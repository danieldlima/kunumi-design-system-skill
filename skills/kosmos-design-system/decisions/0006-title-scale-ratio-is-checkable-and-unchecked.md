---
id: 0006
status: superseded-by-0010
date: 2026-09-14
scope: web.new
artifact: konstrukt-fluxo
rules: none
tags: typography, scale, rule-gap, checklist
---

# The title-to-body scale ratio is a printed number that no rule checks

## Context

The first draft of the Konstrukt flow slide set its title at 68px against 20px body copy — a ratio
of 3.4x. `tokens.json#typography.scaleRatios.title` prints the brandbook range as **"5x - 7.5x"**,
so 68px was well under the floor; the range starts at 100px.

The lint pass reported the artifact clean. Nothing was wrong by any rule that exists: the title was
uppercase, correctly tracked, and inside the display leading range.

The defect surfaced in the visual pass as something that looked like a different problem — a
200px vertical hole between the copy and the flow band. The title simply lacked the mass to anchor
the composition. Raising it to 100px fixed the ratio and the hole in one move.

## Decision

Record the gap rather than paper over it. `scaleRatios` carries four concrete ratios — title
`5x - 7.5x`, subtitle `1.2x - 1.6x`, lead `1.1x`, body `x` — and they are as machine-checkable as
`lineHeightRanges`, which is already derived and enforced.

It is not added as a rule in this pass, for one reason: the check needs to know which declaration
is the body baseline, and a static pass cannot. It belongs in the render pass, against the measured
`fontSize` of nodes carrying `data-kunumi-role="title"` and `data-kunumi-role="body"`.

## Consequence

Until then, title scale is a **checklist** question, not a rule, and the checklist does not yet ask
it. Add it as question 5a: does the title measure 5x to 7.5x the body?

This is also the clearest evidence so far for the design split the engine rests on: the rule that
would have caught this needs measured geometry, which is exactly why the render pass exists and
why `requires: ["render"]` is part of the rule schema rather than an afterthought.
