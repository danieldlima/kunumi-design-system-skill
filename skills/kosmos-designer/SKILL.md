---
name: kosmos-designer
description: Produce a Kunumi web artifact and verify it before delivering. Use when asked to design, generate, build, mock up, lay out, or revise a Kunumi page, section, hero, card, component, chart, or social asset for the web, or to review an existing artifact for brand fidelity. Runs a closed loop: propose, render, lint, look at the render, correct, then record the decision.
---

# Kosmos Designer

Design in the Kunumi system and **verify the result before claiming it is done**. The brand rules
live in the `kosmos-design-system` skill; this skill is the procedure that applies them and proves
the outcome.

Web only. Nothing here covers print: no MDC margins, no millimetre formats, no CMYK or Pantone.

## Route

1. Read `references/design-loop.md` and follow all nine steps. Do not skip step 5.
2. Read `references/critique-checklist.md` before looking at a render.
3. For any brand value — a color, a type variable, a logo file, an asset — consult the
   **`kosmos-design-system`** skill rather than recalling it. That skill owns `tokens.json`.

## The engine

One entry point, in the sibling `kosmos-design-system` package. Resolve it first — your working
directory is the user's project, not this skill directory, so a relative path will not find it:

```bash
# Resolve the engine once. Works under either install route (symlinked skill package or
# marketplace copy) and from any working directory. `find -L` is required: a local-dev install
# symlinks the skill package, and find does not follow symlinks by default.
KOSMOS=$(dirname "$(find -L ~/.claude/skills ~/.claude/plugins/cache \
  -maxdepth 7 -name kunumi_critic.py 2>/dev/null | head -1)")

# Working inside the repository itself instead? Point at it directly:
#   KOSMOS=skills/kosmos-design-system/scripts
```

```bash
python3 "$KOSMOS/kunumi_critic.py" review artifact.html --canvas 1920x1080  # render + lint + see
python3 "$KOSMOS/kunumi_critic.py" lint   artifact.html --json              # static pass only
python3 "$KOSMOS/kunumi_critic.py" render artifact.html --probe             # engine available?
python3 "$KOSMOS/kunumi_critic.py" rules  --scope web.new                   # what is enforced
python3 "$KOSMOS/kunumi_critic.py" decisions --search hero                  # already decided?
python3 "$KOSMOS/kunumi_lookup.py" sources --identity instituto             # approved assets
```

`review` is the command for almost every task. If `$KOSMOS` comes back empty, say so rather than
guessing a path — it means neither install route is present.

## Nonnegotiables of the loop

- **Read precedent before proposing.** `decisions --search <topic>`. A decision already made is
  not yours to remake silently.
- **Never claim visual verification you did not perform.** If `render --probe` reports no engine,
  say so in the delivery and mark the artifact unverified.
- **Clear every `blocker` and `violation`.** For each remaining `advisory` or `note`, either fix it
  or write one sentence of justification. Silence is not a justification.
- **A clean lint is not a passed review.** The checklist exists because the rules that matter most
  — hierarchy, reading order, breathing room, whether a headline breaks mid-word — are the ones no
  linter can evaluate.
- **Declare the scope you used.** If it is not `web.new`, state which documented tension applies.
  Relaxing a rule always costs an entry in `decisions/`.
- **Annotate what you build.** `data-kunumi-frame` on every deliverable surface,
  `data-kunumi-role` on semantic nodes, `data-kunumi-exempt` on anything that is not brand
  artifact. Without them the render cannot be framed and the linter cannot tell chrome from work.
- **Cap at three cycles.** If blockers survive three passes, stop and report what is blocking
  rather than iterating silently.
