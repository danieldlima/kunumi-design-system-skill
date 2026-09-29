---
id: 0011
status: accepted
date: 2026-09-16
scope: web.new
artifact: references/slide-template-measured.md
rules: geometry.radius
tags: diagram, slides, radius, concreto, measurement
---

# Slide diagram nodes are square Concreto fills, not 10px cards

## Context

ADR 0008 decided that a technical diagram is the case where a card is warranted — 10px radius via
`--kunumi-radius-card`, a 1px hairline border, `--kunumi-surface-raised` as the fill — because
containment needs closed regions and hairlines separate rather than enclose. That reasoning was
sound and the sources supported it: `geometry.radius.card` is a brandbook value.

The team's slide template encloses too, and does it differently. Measured:

- node box corner radius is **0** — the bezier control points in the PDF are degenerate, so the
  squareness is exact rather than apparent
- fill is **CONCRETO `#B4ADA4`**, flat, with **no stroke** at all
- label sits centred in Gelo, not in Chumbo on a light surface
- the marked node is solid **URUCUM**
- connectors are **2px Chumbo** with a solid triangular arrowhead **9×7px**

## Decision

Scope 0008 to the medium. On **slides**, diagram nodes are square Concreto fills with no border.
On **web**, 0008 stands unchanged: 10px radius, hairline border, raised surface.

The two are not in conflict once the denominator is named. A web card is an elevated surface on
Gelo and reads as one. A slide node is structure, and `color.chart`-adjacent restraint aside,
Concreto's stated role in `tokens.json` is exactly "rules, grids, inactive structure" — the
template extends it from line to filled region, which is a consistent reading, with Urucum marking
the one active node.

## Consequence

The diagram dialect invented in the 2026-09-14 session is replaced by measured values. Of what was
invented, three things were **wrong** and are corrected: the 10px radius on slide nodes, the
hairline border, and the raised-surface fill.

Two were **right** and now have precedent behind them rather than instinct:

- **Vertical stubs.** The template runs 2px stubs from a label down to the timeline axis, Concreto
  for ordinary labels and Urucum for the marked one. 0008's "a drawn connection is not optional"
  holds, with measurements.
- **Constant node width.** Nodes are 148px regardless of surplus space, confirming that boxes are
  not stretched to fill a slide.

One value in the template is deliberately **not** adopted: its timeline label boxes are filled
`#000000`, which the brandbook prohibits — Chumbo replaces black. Use Chumbo. This is listed among
the three historical defects in `references/slide-template-measured.md` and is not precedent.

The thinnest line in the deck is the **0.8px** timeline axis, well under the 1px hairline the web
rules assume. Slides are projected at a fixed size and can carry it; screens at arbitrary DPR
cannot. Do not port 0.8px to web.
