<img src="assets/kunumi-icon-urucum.png" alt="Kunumi" width="200">

# Kosmos Design System

Claude Code plugin that ships a single skill, [`kosmos-design-system`](skills/kosmos-design-system/SKILL.md),
for designing and reviewing artifacts in the approved Kunumi, Instituto Kunumi, and Kunumi
Unlimited visual **and verbal** systems — web and UI, slides, charts, social assets, and copy.

Authority is the **Brandbook Kunumi Final (2025)**; colors and type were read from that file's own
design variables. Local-first: every approved asset the skill uses is bundled in the repository, so
it works with no network and no Figma access.

## Layout

```text
.claude-plugin/
  plugin.json                 # plugin manifest
  marketplace.json            # single-plugin marketplace, source "./"
assets/                       # plugin icons
skills/
  kosmos-design-system/
    SKILL.md                  # routing instructions (required)
    references/               # brand standards, loaded only when relevant
      tokens.json             # single source of truth for color and type
      brand-foundations.md    # always read; identity, color, composition
      typography.md           # the two-family type system
      logo-governance.md      # clear space, minimum size, co-branding, misuse
      brand-voice.md          # messages, tone axes, DOs/DON'Ts, naming
      visual-behavior.md      # brand architecture, formats, Versus symbol
      design-rules.json       # rule and scope definitions for the review engine
    scripts/                  # kunumi_lookup.py, the index builder, and the review engine
      kunumi_critic.py        # rules | lint | render | review | decisions
      kunumi_design/          # findings, rules, scan, render, checks, adapters
    decisions/                # design decision log (precedent the designer reads and appends to)
    assets/local/             # marks, Figtree, Space Grotesk, Instituto artwork
    assets/web/               # CSS tokens and animated template preview
  kosmos-designer/
    SKILL.md                  # the loop: propose, render, lint, look, correct, record
    references/
      design-loop.md          # the nine steps
      critique-checklist.md   # the questions no linter can answer
scripts/
  validate-skills.py          # frontmatter, reference links, token consistency
  build_bundle.py             # self-contained bundle for publishing
tests/                        # pytest; fixtures are deliberately non-compliant artifacts
```

`skills/` at the plugin root is auto-discovered by Claude Code — the manifest carries no skill path.

## Reviewing an artifact

The brand rules are enforced, not only described. One entry point:

From a clone:

```bash
CRITIC=skills/kosmos-design-system/scripts/kunumi_critic.py

python3 $CRITIC review artifact.html --canvas 1920x1080  # render + lint + hand off to the eye
python3 $CRITIC lint   artifact.html --json              # static pass only
python3 $CRITIC rules  --scope web.new                   # what is enforced, and on whose authority
python3 $CRITIC render artifact.html --probe             # is a render engine available?
python3 $CRITIC decisions --search gradient              # what was already decided
```

From an installed skill, in any project. `find -L` is required, because a local-dev install
symlinks the skill package and `find` does not follow symlinks by default:

```bash
KOSMOS=$(dirname "$(find -L ~/.claude/skills ~/.claude/plugins/cache \
  -maxdepth 7 -name kunumi_critic.py 2>/dev/null | head -1)")
python3 "$KOSMOS/kunumi_critic.py" review artifact.html
```

Four severities. `blocker` and `violation` fail the run (exit 2 and 1); `advisory` and `note` do
not. `note` exists so the linter can surface a documented tension without crying wolf — the
failure mode that gets a linter muted.

Rules that can be derived from `references/tokens.json` are derived from it, so changing a token
changes the rule. Rules whose authority is prose live in `references/design-rules.json` as data.
Every finding cites the reference file and anchor it came from.

**Rendering is optional.** With no engine reachable, `lint` still runs and reports the
measurement rules as skipped rather than passing them by default — `rulesSkipped` is in every
report, so silence stays auditable. The engine is found in this order: an importable `playwright`,
then `KUNUMI_RENDER_CMD`, then `uv run --with playwright`, then an installed Chrome or Edge.

```bash
uv sync --group dev && uv run pytest
```

## What Works Offline

- approved marks;
- Figtree (body) and Space Grotesk (display);
- Instituto static artwork and lightweight motion;
- CSS tokens and the animated HTML template preview;
- the extracted slide-layout, visual-pattern, and design-token references;
- semantic source lookup.

## Sources Not Bundled

Slide decks are not bundled. A Kunumi or Instituto source deck, heavy motion or video, a channel
guide, portraits, historical/client material, and the annual report are all outside the bundle.
When a task needs one, the skill asks for the approved file instead of substituting or
reconstructing it. `references/slide-layouts.md` still carries the full extracted layout system,
so the skill can specify slide work precisely before a deck is supplied.

**PP Neue Machina Inktrap**, the brandbook's first-choice display face, is commercial software from
Pangram Pangram and is not redistributed here. Space Grotesk — the alternate the brandbook itself
names — is bundled under the SIL OFL and is **the display face for every web artifact**. PP Neue
Machina is deliberately absent from the CSS stack: it can never be served to a browser, and leaving
it in meant a machine with a local copy rendered titles in a face the delivered page could not use.
See ADR 0015.

Two chapters of the brandbook, the Instituto and Colab deep dives, were not reachable through the
Figma MCP page enumeration and are therefore not extracted. **Kunumi Colab** consequently has a
documented name but no documented mark; the skill asks rather than inventing one.

## Install

Pick one of the two routes below — installing both leaves two copies of the same skill competing
to trigger.

### Local development

Symlink each **skill package**, not the repository root, so every personal skill directory
contains `SKILL.md` directly:

```bash
ln -s "$PWD/skills/kosmos-design-system" ~/.claude/skills/kosmos-design-system
ln -s "$PWD/skills/kosmos-designer"      ~/.claude/skills/kosmos-designer
```

The links point at the working tree, so edits take effect in the next session with no reinstall.
Both are needed: `kosmos-designer` reaches the review engine through a sibling path that resolves
correctly under either install route.
Verify the link resolves:

```bash
ls -l ~/.claude/skills/kosmos-design-system/SKILL.md
```

### Shareable install

```bash
claude plugin marketplace add .
claude plugin install kosmos-design-system@kosmos-design-system
```

This route copies the plugin into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, so
it captures a snapshot: later edits to the repository do not appear until the version is bumped and
the plugin reinstalled. Prefer the symlink while developing the skill. Verify with:

```bash
claude plugin details kosmos-design-system
```

`claude plugin details` only knows about plugins — it reports "not found" for a symlinked personal
skill even when that skill is installed and working.

Start a new session after either route so the skill is discovered.

## Use

Prompts that route to the skill:

- Create this artifact in the correct Kunumi identity using local assets first.
- Build a presentation from a supplied Kunumi or Instituto source deck.
- Find the approved logo, background, or channel template for this task.

Query the bundled indexes instead of reading them wholesale — run from the skill directory:

```bash
python scripts/kunumi_lookup.py tokens
python scripts/kunumi_lookup.py resolve "Instituto gradient"
python scripts/kunumi_lookup.py sources --identity instituto
python scripts/kunumi_lookup.py slides --tag chart
python scripts/kunumi_lookup.py patterns --medium slides --tag data-viz
```

The primary brand accent is Urucum `#F04E44`. Chumbo `#1C2127` and Gelo `#F0F0F0` replace black
and white, which the brandbook prohibits as brand colors. Titles are set in the display face,
**always uppercase**, tracked **+3%**; body is Figtree at 140–175% line height.

`references/tokens.json` is the single source of truth. `assets/web/kunumi-tokens.css` mirrors it
for web work, and `validate-skills.py` fails the build if the two drift.

## Standalone Bundle

Build a self-contained copy outside the repository when publishing or sharing:

```bash
python scripts/build_bundle.py --bundle-dir /tmp/kosmos-design-system-plugin
```

Repository metadata is excluded.

## Development Workflow

- Keep `SKILL.md` short and procedural; put standards, schemas, and examples in `references/`.
- Edit `references/tokens.json` first when a token changes, then mirror it into
  `assets/web/kunumi-tokens.css` and `references/brand-foundations.md`.
- Run `python scripts/validate-skills.py` before opening or merging a branch. It checks frontmatter,
  that every `references/` path named in `SKILL.md` exists, and that the token layer is consistent
  and free of prohibited colors.
- Use short-lived branches, Conventional Commits in English, and squash merges into `main`.
