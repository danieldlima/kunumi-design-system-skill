---
id: 0014
status: accepted
date: 2026-09-16
scope: web.new
artifact: konstrukt-fluxo-temas, konstrukt-arquitetura
rules: geometry.spacing-scale
tags: geometry, spacing, advisory, measurement
---

# Measured slide geometry outranks the 4px product spacing scale

## Context

`geometry.spacing-scale` fires an advisory on both Konstrukt diagrams: 9px column gutters, a 92px
row height, a 112px arrow offset and a few others sit off the 4px product scale.

Every one of those numbers is measured from the team's slide template rather than chosen:

- **9px** — the gutter between stacked bars and between columns in the template's table page
- **92px** — the row height that makes hairlines align across three columns of two-line text
- **172px** — arrow gutters, from the 89.6px time-grid pitch, doubled to hold their own labels
- **58 / 36 / 43 / 57 / 146 / 1619** — chrome and content datums, measured to the pixel

Rounding 9px to 8px or 92px to 92px-on-the-scale would put the artifact *further* from the template
it is meant to match, to satisfy a scale whose own `authority` field reads "product layer, not
brandbook. The brandbook prints no screen spacing scale."

## Decision

The advisory is accepted for slide-shaped artifacts built against
`references/slide-template-measured.md`. Measured brand geometry outranks the product spacing
scale where the two disagree.

The precedent already exists in `tokens.json`: `geometry.cardPaddingNote` says the brandbook's 30px
card padding "deliberately sits off the 4px product spacing scale. Do not round it to 32px." This
is the same argument applied to a larger set of measured values.

## Consequence

The rule is not relaxed and its scope is not changed — it stays an advisory, and it stays useful,
because on a genuine web surface with no measured template behind it the 4px scale is still the
right default. What this entry supplies is the justification the loop demands for accepting it,
so the next person does not "fix" 9px to 8px and quietly break the alignment.

This is the **first** occurrence of accepting this advisory for measured slide geometry. On the
third, `design-rules.json` should gain a scope that exempts artifacts declaring themselves against
the measured template, rather than a fourth entry being written.
