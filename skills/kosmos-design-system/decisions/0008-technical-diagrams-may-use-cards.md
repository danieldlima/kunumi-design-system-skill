---
id: 0008
status: accepted
date: 2026-09-14
scope: web.new
artifact: konstrukt-arquitetura
rules: geometry.radius
tags: diagram, cards, hairlines, density
---

# A technical diagram is the case where a card is warranted

## Context

`visual-behavior.md` says hairline rules and edge alignment are the dominant language and that
"rounded-card UI is not the default". `geometry.radius` sanctions a 10px card radius "when a card
is warranted" without saying when that is.

A system diagram needs closed regions: the reader has to see that `konstrukt-server` and
`run_selection` are inside the same runtime and that the model is outside it. Hairlines separate;
they do not enclose. The flow slide, which only had to show a sequence, needed no boxes at all and
got none.

## Decision

A card is warranted when the diagram's meaning depends on containment. Then: 10px radius via
`--kunumi-radius-card`, a 1px `--kunumi-border` hairline, and `--kunumi-surface-raised` as the
fill — which is also the correct use of the white exception documented in
`color.prohibition.observedException`, an elevated surface on Gelo.

Sequence, hierarchy and comparison do not depend on containment, and there the hairline language
stands.

## Consequence

Two findings came out of building it, both worth keeping:

**Stretching boxes to fill a slide is worse than air between them.** Cycle 2 set the tiers row to
`1fr` so the cards would absorb the surplus height; the emptiness simply moved inside the cards,
which reads far worse than a margin. A technical diagram answers surplus space with information —
a fourth real item per tier — not with height.

**A drawn connection is not optional.** The generated-artifact bridge was first stated only in a
label, with a text arrow. In a diagram whose subject is connections, an edge that is named but not
rendered reads as an afterthought. It now has vertical stubs leaving Browser and entering Servidor.
