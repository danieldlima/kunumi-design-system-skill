---
id: 0007
status: accepted
date: 2026-09-14
scope: web.new
artifact: konstrukt-fluxo-temas
rules: color.prefer-semantic-token
tags: dark-mode, tokens, theme, gap
---

# An artifact that must work in both themes may only use semantic role tokens

## Context

The light flow slide used `--kunumi-grafite` for supporting copy and `--kunumi-concreto` for
structure. Both are raw palette tokens, and `.kunumi-theme-dark` does not touch them: it
re-points only `--kunumi-ground`, `--kunumi-ink`, `--kunumi-ink-muted` and
`--kunumi-surface-raised`.

Flipping the class would therefore have left Grafite `#5E5E5E` text sitting on Chumbo `#1C2127` —
a contrast ratio near 1.5:1, effectively invisible. The lint pass would have said nothing, because
both values are approved brand colors and the rule set has no opinion about which ground they land
on.

## Decision

Any artifact intended to theme must draw every color from the semantic roles —
`--kunumi-ground`, `--kunumi-ink`, `--kunumi-ink-muted`, `--kunumi-border`, `--kunumi-accent`,
`--kunumi-on-accent`, `--kunumi-surface-raised` — and never from the raw palette.

The existing `color.prefer-semantic-token` advisory already points this way, but it only fires on
*literal hexes*. A raw token reference passes it. The advisory's message should be widened from
"prefer a token" to "prefer a *semantic* token", because `var(--kunumi-grafite)` is exactly as
theme-blind as `#5E5E5E`.

## Consequence

The flow slide was refactored to semantic roles, and light and dark then became the same file with
one class toggled — which is the evidence the decision rests on.

**Open question for the token layer, not for this loop:** `--kunumi-border` does not flip either,
so it stays Concreto `#B4ADA4` on Chumbo. That happens to read as a correct light hairline on dark,
so nothing broke. But it is luck, not design. Either the dark theme should re-point `--kunumi-border`
deliberately, or `tokens.json` should record why it is theme-invariant.
