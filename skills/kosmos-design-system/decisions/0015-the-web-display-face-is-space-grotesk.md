---
id: 0015
status: accepted
date: 2026-09-16
scope: web.new
artifact: assets/web/kunumi-tokens.css
rules: typography.display.no-unservable-face, typography.display.no-arial
tags: typography, display, licensing, space-grotesk, reproducibility
---

# The web display face is Space Grotesk, and PP Neue Machina is out of the stack

## Context

`--kunumi-font-display` named four families: `"PP Neue Machina"`, `"PP Neue Machina Inktrap"`,
`"Space Grotesk"`, `"Figtree"`. Two defects came out of rebuilding the Konstrukt diagrams.

**The order was wrong.** `tokens.json#typography.display.preferredStyle` is `Inktrap`, and
`fallbackOrder` put Inktrap first — but the CSS put the bare family name ahead of it, so on a
machine with the full family installed the **Plain** cut won. Measured on the render:
`"KONSTRUKT"` at 100px sets 637.41px in the stack as written and 637.41px in PP Neue Machina Plain,
against 632.58px in Inktrap. Every title this skill has produced on a licensed machine came out in
the wrong cut.

**The bigger defect is that the face was named at all.** `AGENTS.md` already forbids adding PP Neue
Machina to the repository, because it is commercial software from Pangram Pangram. A face that
cannot be bundled cannot be served. So the entry never described what a browser would receive — it
described what *the rendering machine happened to have*. Space Grotesk sets the same string at
584.91px: **52px narrower**. The two are not metrically compatible, so the same HTML wrapped
differently depending on whose laptop rendered it, and a locally approved layout was not the
delivered layout.

## Decision

For web, `--kunumi-font-display` is **`"Space Grotesk", "Figtree", sans-serif`**. PP Neue Machina
is removed, not reordered.

Space Grotesk is not a downgrade being tolerated: it is the alternate the brandbook itself names,
in the same sentence that names Inktrap, and it is bundled under the SIL OFL.

**This is scoped to web, and the brandbook is not overruled.** Inktrap remains the first choice for
print and for a desktop deck, where the licensed file travels with the document and the renderer is
the same machine that holds the licence. `tokens.json` keeps `family`, `preferredStyle` and
`licensed` untouched, because those are brandbook facts; what changed is `fallbackOrder`, which was
always this skill's resolution policy rather than a printed list.

## Consequence

Enforced by `typography.display.no-unservable-face`, a `violation`. It reuses the existing
`family_stack_forbids` check, so no new check code was needed — only params.

The rule is deliberately about the **stack**, not about the machine. It cannot detect whether a
licensed copy is installed, and it does not need to: the defect is naming an unservable face, and
that is visible statically.

Both test fixtures carried the old stack and now carry the new one. Two tests hold the line: one
that a stack naming the face is flagged, and one that the shipped token sheet is clean — the sheet
being the file every artifact links, where a regression would propagate silently.

Every artifact that references `var(--kunumi-font-display)` picks this up on its next render with
no edit. `konstrukt-fluxo-temas` and `konstrukt-arquitetura` were re-rendered under it.

Prose that contradicted the CSS was corrected in the same pass: `typography.md`'s resolution list,
and a line in `README.md` that promised the stack "picks it up automatically" — which had become
exactly the wrong promise.
