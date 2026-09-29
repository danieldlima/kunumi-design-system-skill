---
id: 0029
status: accepted
date: 2026-09-29
scope: web.new
artifact: references/web-specs.md
rules: layout.breakpoint-scale
tags: layout, breakpoints, grid, product, web
---

# Web layout is a product layer at 768 and 1440, not a brandbook rule

## Context

The brandbook was drawn for graphic and print material. It prints the dois-por-dois composition
principle and the 1920x1080 stage, and no breakpoint, column count, gutter or page margin. Pages
built from the skill each chose their own, and the only breakpoints in the repository were 720
and 480, in `template-preview.html`, a slide replica.

The Kosmos Figma library carries three grid styles (375 / 768 / 1440 with 4 / 8 / 12 columns),
and labels its own breakpoints as invented.

## Decision

Adopt the library's grids as the web layout, mobile-first: 4 columns, 16px gutter and 24px margin
below 768px; 8 columns, 24px gutter and 48px margin from 768px; 12 columns, 24px gutter and 96px
margin from 1440px. The content container is 1248px (1440 − 2 × 96). The values live in
`tokens.json#layout` under a product-layer authority, and `layout.breakpoint-scale` flags any
other media-query width as an advisory.

A slide replica keeps its stage's breakpoints. `web.deck-derived` demotes the rule to a note, and
the 720 and 480 in `template-preview.html` stand as the known advisory on an undeclared replica.

## Consequence

Every new page has the same two breakpoints, and a third needs a decision entry. The brandbook's
dois por dois is read onto the grid (6 + 6, 4 + 4, stacked) rather than replaced by it. If the
brand later prints screen breakpoints, they supersede these.
