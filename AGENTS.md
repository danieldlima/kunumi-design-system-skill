# Repository Instructions

This repository is a Claude Code plugin holding two skills. Keep both packages focused on
instructions and resources an agent needs at execution time.

- `skills/kosmos-design-system/` — the brand knowledge. Owns `references/tokens.json`, the asset
  indexes, and the review engine (`scripts/kunumi_design/`, `scripts/kunumi_critic.py`), which
  derives its rules from the token layer.
- `skills/kosmos-designer/` — the procedure. Owns the design loop, the visual critique checklist,
  and nothing else. It calls the engine in the sibling package by resolved path.

The split is recorded in `skills/kosmos-design-system/decisions/0001-*.md`. The descriptions must
stay different in kind — knowledge versus action — or the two skills compete to trigger.

The authority for Kunumi brand rules is the **Brandbook Kunumi Final (2025)**. Where the older
deck-derived references disagree with it, the brandbook wins, and the older material must be
labelled deck-derived rather than silently kept as a rule.

- Keep `SKILL.md` present and authoritative in both skill packages.
- Web only. Print rules — MDC margins, millimetre formats, CMYK/Pantone, the 10mm minimum — are
  deliberately out of scope for the designer loop and must not be added to `design-rules.json`.
- Keep frontmatter to `name` and `description`; the description must say when the skill should trigger.
- Keep `SKILL.md` short and procedural. Put detailed standards, schemas, examples, and brand rules in one-level-deep `references/` files.
- Put reusable deterministic utilities in `scripts/` and executable output resources in `assets/`.
- Do not invent Kunumi governance values, brand assets, policy IDs, ACLs, or legal names. Ask for approved source material when it is missing. `Kunumi Colab` is a documented name with no documented mark — do not design a mark or system for it.
- `references/tokens.json` is the single source of truth for color and typography. Change it first, then mirror into `assets/web/kunumi-tokens.css` and `references/brand-foundations.md`.
- Do not add PP Neue Machina to the repository. It is commercial software from Pangram Pangram; only OFL faces (Figtree, Space Grotesk) may be bundled.
- Treat the original templates and approved asset files as the source of truth; do not redraw, recolor, or substitute a mark.
- Run `python scripts/validate-skills.py` after changing either skill. It also verifies that every `references/` path named in `SKILL.md` exists and that the token layer stays consistent and free of prohibited colors.
- Run `python skills/kosmos-design-system/scripts/build_indices.py --check` after touching the slide or pattern indexes.
- Use Conventional Commits in English, branch-based development, and squash merges into `main`.

## The review engine

- `references/tokens.json` stays the single source of truth. Rules that can be derived from it are
  derived in `scripts/kunumi_design/rules.py` — never transcribed into Python. `tests/test_rules_derive.py`
  guards that: it mutates a copy of the token tree and asserts the rules follow.
- `references/design-rules.json` owns values, severities, scopes and authority strings. Python owns
  mechanisms. A check must never branch on its own rule id.
- Every finding must carry an `authority`. That is what makes a contested finding arguable against
  the brandbook instead of deletable.
- Precision is the product; coverage is not. A `blocker` or `violation` that a human judges wrong
  is the failure mode that gets the tool abandoned. Add rules only with a fixture that pins the
  exact ids they trigger, plus a negative control.
- Prefer `demote` over `relax` in a scope: demoting keeps the observation and drops only the alarm.
  A scope that relaxes anything must state `why`.
- Run `uv run pytest` after changing the engine.
