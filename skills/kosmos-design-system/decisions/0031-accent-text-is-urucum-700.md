---
id: 0031
status: proposed
date: 2026-09-29
scope: web.new
artifact: references/tokens.json
rules: color.prefer-semantic-token
tags: tokens, contrast, urucum, accent, proposed
---

# `--kunumi-accent-text` is urucum-700, and resolves 0022 once approved

## Context

Decision 0022 found that `--kunumi-accent-text` was named by 0019 and did not exist, so small
accented text had to fall back to Grafite. Urucum on Gelo is 3.13:1 and fails 4.5:1 for text
below 24px. The Kosmos Figma `text/accent` role is full Urucum in Light, so it has the same
defect.

## Decision

Define `--kunumi-accent-text` as urucum-700 `#BC392F` in light (4.89:1 on Gelo) and urucum-400
`#F26058` in dark (5.08:1 on Chumbo), both tonal steps from the Figma primitives. The role ships
with `status: proposed` in `tokens.json` because a darkened Urucum is a new shade of the brand's
accent and needs brand approval. `.kunumi-kicker` keeps `--kunumi-accent` until then.

## Consequence

Once approved: point `.kunumi-kicker` at `--kunumi-accent-text`, mark this entry accepted, update
the Figma `text/accent` role, and 0022's Grafite fallback retires. In dark, small accent text stays
off the raised surface, where urucum-400 measures 4.48:1.
