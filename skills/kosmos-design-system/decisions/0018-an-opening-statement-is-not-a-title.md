---
id: 0018
status: accepted
date: 2026-09-17
scope: web.new
artifact: assets/web/template-preview.html
rules: typography.display.long-title, typography.display.case, typography.display.tracking
tags: typography, display, statement, scope-relaxation, brand-voice
---

# An opening statement is not a title, so the two-line limit does not reach it

## Context

ADR 0012 sent any title past two rendered lines to Figtree sentence case. Its threshold rested on
one assumption, stated there in as many words: *"`Abertura/Título` is 180px on a 1920px stage:
nearly every real cover wraps to two lines."*

Annotating the repo's own reference slides — the first time measured type rules ran on them at all
(ADR 0016) — showed the assumption was wrong. Three of four display lines run past two:

| Surface | Line | Rendered lines |
| --- | --- | --- |
| Kunumi cover | "Inteligência para o que ainda não tem nome." | **4** |
| Instituto gradient | "O futuro informa o presente." | **3** |
| Instituto pixels | "Conhecimento que se move em rede." | **3** |
| Kunumi data | "Duas medidas. Uma conclusão." | 2 |

A statement at 180px wraps past two lines *by design*. The threshold is right for titles and wrong
for statements, and raising it to fit statements would have retired the rule for the titles it was
written to catch.

## Decision

`data-kunumi-role="statement"` is exempt from `typography.display.long-title`. It keeps the display
face at any length.

**The test is what the line does, not how long it is:**

> A **statement** asserts something about the brand, on a surface whose job is to open — a cover,
> a section divider. A **title** describes what is on the surface.

That is why "Duas medidas. Uma conclusão." keeps `role="title"` while the other three become
statements: it describes the two metrics printed beneath it. The distinction holds independently of
line count, which is the property that matters — a rule whose exemption is defined by what is
currently failing is not a rule.

The exemption lives in `design-rules.json` as `params.exemptRoles`, not in the check body, so a
reviewer reading the rule sees the relaxation without reading Python.

## Consequence

**The exemption is narrow, and that is what makes it safe to grant.** It removes the line limit and
nothing else. `typography.display.case` and `typography.display.tracking` key on the selector
cascade rather than on the measured role, so a statement is still required to be uppercase at +3%.
`test_opening_statement_is_exempt_but_still_judged_for_case` asserts both halves against identical
copy marked two different ways: only the `title` is flagged for length, and neither is flagged for
case or tracking.

**The abuse vector is named rather than engineered away.** Marking a content title `statement` to
clear the rule is the one way this goes wrong, and no measurement can catch it — the judgment is
about what the copy asserts, which is a reading task. So it is a checklist question, 6b, and one
statement per surface. Two guards that could have been built were considered and rejected as
false precision: an absolute size floor (the preview's own statements render at 88px, not the
brandbook's 180px, so any floor would either reject them or admit everything) and a
statement-to-body ratio (the render pass cannot group a text node with the body copy of its own
frame, because only the frame element carries `data-kunumi-frame`).

ADR 0012 is **not** superseded. Its decision stands for titles, including its preference for
cutting a title to two lines before reaching for Figtree. What changed is that statements were
never in its scope, and now the rule knows it.

With the three statements annotated, `review` on the preview reports **0 violations across 23
rules with none skipped** — the first time the repo's calibration set has been clean under the
measured type rules, because until ADR 0016 it was never measured.
