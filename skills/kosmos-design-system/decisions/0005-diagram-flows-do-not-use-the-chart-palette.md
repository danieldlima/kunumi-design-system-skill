---
id: 0005
status: accepted
date: 2026-09-14
scope: web.new
artifact: konstrukt-fluxo
rules: color.chart.data-only
tags: diagram, chart-palette, slides, flow
---

# A process diagram is not data, so it does not get the chart palette

## Context

A five-stage flow diagram wants five distinguishable colors, and `color.chart` offers exactly five.
The temptation is obvious and wrong: `tokens.json#color.chart.rule` says the palette "foi
desenvolvida exclusivamente para a representação de dados e utilização em gráficos e deve ser
utilizada apenas nesse contexto".

A flow diagram encodes sequence, not quantity. Nothing in it is a measurement.

## Decision

Diagram stages are built from the institutional palette alone — Chumbo for names, Grafite for
supporting copy, Concreto for structure — with Urucum marking the one stage that carries the
narrative point. Differentiation comes from hairline rules and edge alignment, which
`visual-behavior.md` names as the dominant language, not from hue.

If a diagram genuinely needs five hues to be legible, it has too many stages.

## Consequence

`color.chart.data-only` stays at `blocker` for diagram work, and the `web.chart` scope is not the
right escape hatch for a diagram — that scope exists for actual charts. A slide that needs the
chart palette must say what it is plotting.

Five columns separated by 2px Concreto ticks read as a sequence without any color coding at all,
which is the evidence this decision rests on.
