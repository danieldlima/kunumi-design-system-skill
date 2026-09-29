---
id: 0033
status: proposed
date: 2026-09-29
scope: web.new
artifact: assets/web/kunumi-tokens.css
rules: interaction.focus-visible, interaction.focus-outline-removed, logo.no-effects
tags: focus, accessibility, states, logo, proposed
---

# The focus ring is 2px, offset 2px, drawn on the control and never on the mark

## Context

The Kosmos Figma Button has Default, Hover and Disabled states and no focus state. The brandbook
has no interaction states at all. Removing the browser's outline is the most common way a styled
page becomes unusable from a keyboard, and a linked logo is exactly where a ring would otherwise
land on the mark.

## Decision

Every interactive element gets a 2px `--kunumi-focus-ring` outline offset 2px on `:focus-visible`,
set once in `kunumi-tokens.css` inside `:where()` so any component can restyle it. The ring is
Urucum on light (3.13:1, above the 3:1 non-text floor) and urucum-400 on dark (5.08:1). When the
focused element is a linked mark, the ring goes on the link box, never as an effect on the mark
image. Removing an outline on `:focus` without a replacement is a violation; a page with
interactive elements and no focus style at all is an advisory, since the browser still draws one.
Width and offset are proposed until the brand approves them.

## Consequence

Keyboard focus looks the same on every Kunumi surface. Artifacts that drop the ring for pointer
users must use `:focus:not(:focus-visible)`, which the rule accepts.
