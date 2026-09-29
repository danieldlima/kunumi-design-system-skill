---
id: 0030
status: accepted
date: 2026-09-29
scope: web.new
artifact: assets/web/kunumi-tokens.css
rules: color.prefer-semantic-token
tags: theme, dark, tokens, semantic, web
---

# Dark mode is opt-in, and follows the system only when an artifact asks

## Context

`.kunumi-theme-dark` re-pointed four roles and left `--kunumi-border` and every accent state on
their light values; decision 0007 recorded that only roles survive the flip and left the rest
open. Nothing honoured `prefers-color-scheme`, and `:root` declares `color-scheme: light`.

Making `:root` follow the system would silently turn every existing artifact dark on a dark-mode
machine, including slide replicas and social assets that are single-ground by design.

## Decision

Keep light as the default. Offer dark two ways: `.kunumi-theme-dark` forces it, and
`.kunumi-theme-auto` follows `prefers-color-scheme`. Both carry the same role block, generated
from `tokens.json#color.semantic.roles`, which mirrors the Kosmos Figma Semantic collection:
border, subtle border, hairline, raised surface, accent states, accent text, focus ring and
disabled surface now flip. Urucum as `--kunumi-accent` does not. The dark raised surface is
neutral-800 `#262B31` from the library, replacing the earlier `color-mix` approximation.
`validate-skills.py` fails when either block drifts from the token table or re-points a raw
palette token.

## Consequence

An artifact is dark only when it says so. A page that wants to follow the reader's system adds
one class. The designer loop renders a dark pass for any page that offers it.
