---
id: 0009
status: accepted
date: 2026-09-16
scope: web.new
artifact: references/slide-template-measured.md
rules: typography.line-height.display
tags: typography, leading, tokens, measurement
supersedes: 0002
---

# Display leading is 137%, and `Miolo/Título`'s 34px is the transcription error

## Context

ADR 0002 recorded a tension it could not resolve: `typography.lineHeightRanges.display` prints
`110% - 140%`, while `typography.variables` carries `Miolo/Título` at size 22 with
`lineHeight: "34px"` — 1.545, outside the brandbook's own range. 0002 named two candidate
resolutions and left them for a human reading of the brandbook.

The design team's own slide template settles it by measurement. From
`references/slide-template-measured.md`:

| Size | Baseline pitch | Ratio |
|---|---|---|
| 64px | 88px | **137.5%** |
| 27px | 37px | **137.0%** |

Two independent sizes, five baselines apart on the chapter page, land on the same value. The
deck's large text is set at 137% — inside `110% - 140%`, and 21 points below 1.545.

## Decision

`lineHeightRanges.display` stands as written. `Miolo/Título`'s `34px` is a transcription error, not
a competing convention.

The arithmetic supports it: 22px × 1.375 is 30.25px, and 30px at 22px is 136% — the measured
value. `34` for `30` is a plausible single-digit slip, and no slide anywhere in the export is set
near 154%.

The second candidate resolution in 0002 — that `Miolo/Título` is "a title at body scale needing its
own range" — is rejected. The closest comparable size in the real deck, 27px lead copy, runs at
137%, so there is no looser regime for titles at body scale.

## Consequence

`.kunumi-title` should be corrected from `line-height: 1.55` to **1.375**, which is both inside the
range and the deck's measured practice. This is the one place where 0002's instruction is reversed:
0002 said explicitly "do not fix the CSS to 1.40", on the grounds that the CSS faithfully
implemented the type variable. The variable is now known to be wrong, so fidelity to it is no
longer a reason.

`typography.variables[Miolo/Título].lineHeight` needs a human to confirm 30px against the printed
brandbook before `tokens.json` is edited — a measured deck is strong evidence about practice but is
not the brandbook itself. Until then the rule fires correctly and the CSS, once corrected, passes.

Small dense text is a separate matter: 16–17px copy in the deck sits at ~118%, which is Figtree's
natural single spacing rather than a chosen value. It is not display text and the display range
does not reach it.
