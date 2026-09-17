---
id: 0013
status: accepted
date: 2026-09-16
scope: web.new
artifact: konstrukt-fluxo-temas, konstrukt-arquitetura
rules: color.contrast, geometry.radius
tags: diagram, contrast, concreto, urucum, tension, measurement
---

# Node labels are Chumbo, because the template's own Gelo labels measure 1.95:1

## Context

`references/slide-template-measured.md` records the team's diagram language, and ADR 0011 adopted
it: square nodes, flat Concreto fill, no stroke, **label centred in Gelo**. That last part was
transcribed from the template faithfully and is not usable.

Measured contrast of the template's own pairings:

| Pair | Ratio | WCAG 1.4.3 at this size |
|---|---|---|
| Gelo `#F0F0F0` on Concreto `#B4ADA4` | **1.95:1** | fails 4.5:1 |
| Gelo on Urucum `#F04E44` | **3.14:1** | fails 4.5:1 |
| **Chumbo `#1C2127` on Concreto** | **7.29:1** | passes |
| **Chumbo on Urucum** | **4.54:1** | passes |

This is a tension between two sources, not a defect in the artifact: the measured reference is an
accurate record of what the team drew, and what the team drew does not meet contrast.

It is also not a new finding. The `kunumi/konstrukt` token rebuild reached the identical
conclusion from the other direction — its commit message records that "`primary.text.*` used
`#FFFFFF`, which the brandbook forbids as a text colour; Chumbo on Urucum reaches 4.53:1 and is
brand-legal". Two independent measurements, 0.01 apart, agreeing on the same fix.

## Decision

Diagram node labels are **Chumbo** on both Concreto and Urucum fills. Everything else in ADR 0011
stands: radius 0, flat fill, no stroke.

`slide-template-measured.md` keeps recording Gelo, because its job is to say what the template
does, not what we should do. The departure is recorded here instead, which is where the reader
looking at the rule will find it.

Bar fills follow the same logic but land on the opposite answer: a Chumbo bar carries a **Gelo**
label at 14.2:1. The rule is not "labels are always Chumbo" — it is that the label is whichever of
Chumbo or Gelo clears 4.5:1 against its own fill, and only Urucum and Concreto are ambiguous enough
to need saying.

## Consequence

Urucum surfaces now carry Chumbo labels in both themes while Chumbo/Gelo surfaces invert with the
theme. That asymmetry is correct and deliberate: Urucum is a fixed accent that does not flip, so
pinning its label is what keeps it legible on both grounds.

One thing this cost, worth knowing before it is rediscovered: **a bar filled with a literal
`var(--kunumi-chumbo)` disappears on the dark ground.** The first build of `konstrukt-arquitetura`
did exactly that and the light render looked perfect — the defect was invisible until the dark
frame was opened. `--kunumi-ink` / `--kunumi-ground` inverts with the theme and reads in both.
ADR 0007 already said only semantic tokens survive the theme flip; this is its second occurrence,
and the third triggers a `design-rules.json` edit.
