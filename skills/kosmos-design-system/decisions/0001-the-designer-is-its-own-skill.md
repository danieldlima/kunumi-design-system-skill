---
id: 0001
status: accepted
date: 2026-09-14
scope: web.new
artifact: repository structure
rules: none
tags: structure, skill, invocation
---

# The designer loop is its own skill, not a mode of kosmos-design-system

## Context

The brand rules and the procedure that applies them are different kinds of thing with different
triggers. `kosmos-design-system` answers "what is the Kunumi system"; the designer answers "make
me a Kunumi artifact and prove it is right". `AGENTS.md` asks that `SKILL.md` stay short and
procedural, and the existing one is a routing table that would have to absorb a 150-line loop.

Against the split: the README warns that overlapping installs leave "two copies of the same skill
competing to trigger", and both skills describe Kunumi design work.

## Decision

Two skills in one plugin. `kosmos-designer` carries the loop, the critique checklist and this
decision log; `kosmos-design-system` keeps the brand knowledge, `tokens.json`, and the review
engine that derives its rules from it.

Trigger collision is avoided by making the descriptions different in *kind*: `kosmos-designer` is
phrased around actions (produce, generate, review), `kosmos-design-system` around knowledge
(colors, typography, logo governance). The engine lives beside `tokens.json` because its rules are
derived from it, and `validate-skills.py` already iterates over every directory in `skills/`.

## Consequence

Local development needs **two** symlinks, both documented in the README. `AGENTS.md` no longer
describes a single-skill repository. `kunumi_critic.py` is reached from `kosmos-designer` by a
sibling path, which works under both the symlink and the marketplace copy because the scripts
resolve their own location with `Path(__file__).resolve()`.

Revisit if the two descriptions start competing in practice, or if the loop needs its own model or
tool allowlist — at which point it becomes a subagent rather than a skill.
