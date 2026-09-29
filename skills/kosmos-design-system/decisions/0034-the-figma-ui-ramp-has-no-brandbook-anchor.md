---
id: 0034
status: proposed
date: 2026-09-29
scope: web.new
artifact: references/tokens.json
rules: none
tags: typography, scale, product, ui, tension
---

# The Figma UI ramp keeps no brandbook step, so 0019 does not cover it yet

## Context

Decision 0019 admits a product type ramp only when it keeps two brandbook steps at their literal
values — 22px `Miolo/Título` and 13px `Cabecalho/Menu` — and says a ramp with no literal anchor
is not covered. The Kosmos Figma `UI/*` ramp is 48 / 32 / 24 / 18 for display, 12 for overline,
18 / 16 / 14 / 12 for text and labels. It keeps neither anchor, and sets Display and Title L in
Space Grotesk Bold where the brandbook variables are SemiBold.

## Decision

Record the ramp in `tokens.json#typography.productRamp` with `status: proposed` and do not mirror
it into `kunumi-tokens.css`. Web work keeps using the brandbook classes with their fluid clamps,
and a dense view derives its ramp under 0019. This is a tension between two sources and needs a
ruling, not an artifact fix.

## Consequence

The ruling is one of two things: change the library ramp to carry 22 and 13 (Title S at 22,
Overline at 13), or accept an unanchored UI ramp and supersede that clause of 0019. Either way,
change `tokens.json` first and then mirror.
