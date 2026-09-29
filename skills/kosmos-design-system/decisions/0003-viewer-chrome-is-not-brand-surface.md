---
id: 0003
status: accepted
date: 2026-09-14
scope: exempt
artifact: assets/web/template-preview.html
rules: color.palette.unapproved, color.prefer-semantic-token, geometry.radius
tags: chrome, scope, exemption, preview
---

# The preview's viewer chrome is exempt, and its near-Chumbo backdrop stays

## Context

`template-preview.html` is two things in one file: four brand artifact slides, and the carousel
that displays them. The carousel's own surfaces — `body { background: #11151a }`, the `.stage`
drop shadow, its 4px corner — are not Kunumi artifacts, but they share the stylesheet, so a
file-level scope cannot separate them.

`#11151a` is a deliberate near-Chumbo: darker than `#1C2127` so the Gelo stage reads as lifted off
the page. It is a viewer affordance, not a brand color.

## Decision

Exemption belongs at the element level, not the file level. The carousel wrappers carry
`data-kunumi-exempt="viewer-chrome"`, and the four slides carry `data-kunumi-frame`, so the linter
evaluates the artifact and ignores the apparatus around it.

`#11151a` stays. It never touches a brand surface.

## Consequence

Element-level exemption is now a required feature of the scope mechanism, not an optimisation —
any artifact that ships inside a viewer needs it. The risk is that `data-kunumi-exempt` becomes a
convenient way to silence findings, so exemption is reported in every run: a reader can always see
what was not evaluated.
