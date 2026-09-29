---
id: 0032
status: accepted
date: 2026-09-29
scope: web.new
artifact: assets/web/kunumi-tokens.css
rules: none
tags: button, contrast, urucum, component, tension
---

# A solid Urucum control carries a Chumbo label, and hovers lighter

## Context

The Kosmos Figma Button, in its urucum tint, sets a Gelo label on an Urucum fill: 3.13:1, which
fails 4.5:1 at the 12–16px label sizes. The CSS carried `--kunumi-on-accent: var(--kunumi-gelo)`.
Decision 0022 had already noted that Urucum at small sizes works as a fill carrying Chumbo text.

## Decision

`--kunumi-on-accent` is Chumbo: 4.53:1 on Urucum. Because the label is now dark, the fill
lightens on interaction — `--kunumi-accent-fill-hover` is urucum-400 (5.08:1) and
`--kunumi-accent-fill-press` urucum-300 (6.2:1). Darkening to Figma's urucum-600 would drop the
label to 3.65:1. The general `--kunumi-accent-hover` and `-press` roles keep Figma's darker steps
for accent text and rules.

The brandbook's highlight, Gelo type on an Urucum band, is untouched: it is a brandbook rule for
emphasis inside a sentence, not a control.

## Consequence

Primary buttons read darker-on-bright rather than light-on-bright. The Figma library's urucum
Tint mode (`btn/fg`, `btn/solid-hover`) needs the same change to mirror the repository.
