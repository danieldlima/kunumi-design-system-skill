---
id: 0035
status: proposed
date: 2026-09-29
scope: web.new
artifact: references/web-specs.md
rules: artifact.social-meta, logo.min-height
tags: favicon, icon, logo, digital, proposed
---

# Favicons and app icons are resampled from the approved symbol

## Context

A published page needs a favicon (32, 48), an Apple touch icon (180) and manifest icons (192,
512). The brandbook prints the 28px minimum for the positive RGB lockup only, no minimum for the
symbol alone, and no guidance on polarity in a browser tab. Decision 0028 established that
resampling an approved mark is not a redraw.

## Decision

Produce every icon size by resampling the approved symbol in `assets/local/brand-marks/shared/`,
at the sizes in `tokens.json#digital.appIcons`, never by redrawing or simplifying it. Check it at
32px on light and dark tabs. Keep the whole block `status: proposed` until the brand confirms that
the symbol is legible at 32px and which polarity a tab gets.

## Consequence

Icons can ship now as resamples. If the brand sets a symbol minimum above 32px, the favicon needs
an approved simplified mark, which only the brand can supply.
