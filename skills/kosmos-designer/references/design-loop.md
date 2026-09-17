# The design loop

Nine steps. The loop exists because knowing the brand rules is not the same as producing work that
follows them: the difference is verification, and verification is what this procedure adds.

Resolve the engine once, before step 0:

```bash
# Resolve the engine once. Works under either install route (symlinked skill package or
# marketplace copy) and from any working directory. `find -L` is required: a local-dev install
# symlinks the skill package, and find does not follow symlinks by default.
KOSMOS=$(dirname "$(find -L ~/.claude/skills ~/.claude/plugins/cache \
  -maxdepth 7 -name kunumi_critic.py 2>/dev/null | head -1)")

# Working inside the repository itself instead? Point at it directly:
#   KOSMOS=skills/kosmos-design-system/scripts
```

## 0. Read precedent

```bash
python3 "$KOSMOS/kunumi_critic.py" decisions --search "<topic>"
python3 "$KOSMOS/kunumi_critic.py" decisions --rule color.prohibition.black
```

Before proposing, not after. If a prior decision covers the case, follow it or supersede it
explicitly — never contradict it silently.

## 1. Frame

State four things out loud before writing anything:

- **Identity** — Kunumi, Kunumi Unlimited, or Instituto Kunumi. Never mix lockups or expressive
  systems unless co-branding was explicitly requested. Kunumi Colab has a name and no documented
  mark: ask rather than invent one.
- **Scope** — `web.new` unless a documented tension applies. `python3 "$KOSMOS/kunumi_critic.py" rules --scope <s>`
  shows what each scope enforces and why it relaxes what it relaxes.
- **Canvas** — the delivery size. `1920x1080` for a slide-shaped surface, `1584x396` for a
  LinkedIn header, a real viewport for a page.
- **Media** — HTML, PNG, Penpot, or several.

## 2. Propose

Write `output/kunumi-design/<slug>/<slug>.html`. HTML is the authoring medium for every output:
PNG is rendered from it and a Penpot proposal is derived from it.

- `<link>` the token sheet: `assets/web/kunumi-tokens.css` from the `kosmos-design-system` skill.
  Use its custom properties rather than literal values.
- Source every mark, background and motion asset through the lookup layer. Never invent a path,
  never redraw a mark, never approximate one with text or CSS:

  ```bash
  python3 "$KOSMOS/kunumi_lookup.py" sources --identity instituto
  python3 "$KOSMOS/kunumi_lookup.py" assets --kind lockup --variant negative
  ```

- **Annotate, or the next three steps cannot work:**
  - `data-kunumi-frame="<name>"` on each surface that is a deliverable. One PNG per frame.
  - `data-kunumi-role="logo|title|statement|body|chart|..."` on semantic nodes, so geometry can
    be measured. `statement` is not a synonym for `title`: it is brand voice on a surface whose
    job is to open, and it is exempt from the two-line display limit (ADR 0018). A line that
    describes what is on the surface is a `title`, however large it is set.
  - `data-kunumi-exempt="<why>"` on any wrapper that is not brand artifact — a viewer, a
    scaffold, a device frame.
  - `data-kunumi-scope="<scope>"` if the artifact's scope differs from the default.

## 3. Render

```bash
python3 "$KOSMOS/kunumi_critic.py" render "$HTML" --canvas 1920x1080 --scale 2 --reduced-motion
```

If `kunumi_critic.py render --probe` reports no engine, continue to step 4 and carry the limitation through to
step 7. Do not pretend the render happened.

## 4. Lint

```bash
python3 "$KOSMOS/kunumi_critic.py" review "$HTML" --canvas 1920x1080 --json
```

`review` runs steps 3 and 4 together and prints the render paths for step 5. Read `rulesSkipped`:
a rule that did not run did not pass.

## 5. See — mandatory, never skipped

Open **every** render with the Read tool and answer `critique-checklist.md` **in writing**.

This is the step the whole loop exists for. A clean lint means no rule with a machine-checkable
value was broken. It says nothing about hierarchy, reading order, whether the eye lands in the
right place, or whether a display headline broke mid-word — and that last one is a real defect
found in this repository's own preview, invisible to every static check.

## 6. Correct

- Every `blocker` and `violation`: fix it.
- Every `advisory` and `note`: fix it, or write one sentence saying why it stands.
- Every checklist answer that failed: fix it.

Return to step 3. **Three cycles maximum.** If blockers survive, stop and report them.

## 7. Deliver

State, explicitly:

- the scope used, and why if it was not `web.new`;
- blocker and violation counts, which must be zero;
- each remaining advisory or note, with its one-sentence justification;
- **whether the render actually ran**, and if not, that the artifact is visually unverified;
- the paths of every file produced.

## 8. Record

Append a decision to the `decisions/` directory beside the engine
(`$KOSMOS/../decisions/`) for:

- any genuine judgment call — a value chosen where the system offers no single answer;
- **always** for a scope relaxation or an accepted advisory;
- any tension found between two reference files.

Copy `decisions/template.md`, take the next id, fill in `rules:` so the entry is findable by the
rule it interprets. The promotion trigger is written into `decisions/README.md`: the third time a
rule is relaxed for the same reason, edit `design-rules.json` instead of writing a fourth entry.

## Not in scope

No print rules. No MDC margins, no millimetre formats, no CMYK or Pantone conversion, no 10mm
minimum. The 28px digital logo minimum stays, because it is a web rule.
