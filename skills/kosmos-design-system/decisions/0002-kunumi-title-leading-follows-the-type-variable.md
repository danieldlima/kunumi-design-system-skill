---
id: 0002
status: superseded-by-0009
date: 2026-09-14
scope: web.new
artifact: assets/web/kunumi-tokens.css
rules: typography.line-height.display
tags: typography, leading, tokens, tension
---

# tokens.json contradicts itself on display leading, and the CSS followed the variable

## Context

`.kunumi-title` sets `line-height: 1.55`, which the linter reports as outside
`typography.lineHeightRanges.display` of `"110% - 140%"`.

The CSS is not careless. `typography.variables` carries `Miolo/Título` at `size: 22` with
`lineHeight: "34px"`, and 34 / 22 is **1.545**. `--kunumi-text-title` is `1.375rem`, which is
22px. So `1.55` is a faithful implementation of the brandbook's own named type variable — and that
variable falls outside the brandbook's own stated display range.

This is a defect in the sources, not in the artifact. Two passages of the same file disagree.

## Decision

Leave the CSS as it is for now and record the tension rather than silencing the rule. The finding
stands at `violation` because it is correctly identifying a real inconsistency; what is wrong is
upstream.

Resolving it needs a human reading of the brandbook, which is outside what this loop may decide.
The two candidate resolutions are: `lineHeightRanges.display` applies only to large display sizes
and `Miolo/Título` is a title at body scale that needs its own range; or `Miolo/Título`'s 34px is
itself a transcription error.

## Consequence

`typography.line-height.display` will keep firing on `kunumi-tokens.css` until `tokens.json` is
reconciled. Do not relax the rule and do not "fix" the CSS to 1.40, which would make the token
sheet diverge from the type variable it implements.

**This is the first of three occurrences needed to trigger a `design-rules.json` edit.** If the
same tension is hit twice more, the rule gains a scope rather than the CSS gaining a workaround.
