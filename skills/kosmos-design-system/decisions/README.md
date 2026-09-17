# Design decisions

What separates a senior designer from a rule set is **precedent**: "we solved this before, this
way, for this reason." No linter and no skill carries that. This directory does.

The designer reads this before proposing (step 0 of the loop) and appends to it after a verdict
(step 8). Without the append, every correction evaporates and the same argument is had again.

## When to write an entry

- Always, for a **scope relaxation**. A rule switched off without a recorded reason is a rule
  quietly deleted.
- Always, for an **accepted advisory or note**. The one-sentence justification given at delivery
  belongs here, where the next person will find it.
- For a genuine **judgment call** — a value chosen where the system offers no single answer.
- For a **tension between two reference files**, which is a defect in the sources, not in the
  artifact.

Do not write an entry for ordinary work that followed the rules. This is precedent, not a diary.

## The promotion trigger

**The third time a rule is relaxed for the same reason, edit `references/design-rules.json`
instead of writing a fourth entry.**

Without that trigger this directory becomes a log of repeated exceptions rather than a mechanism
that improves the rules. Three occurrences is enough evidence that the rule, not the artifact, is
wrong.

**A rule left red is not a rule relaxed. It is a rule ignored**, and the trigger must not fire for
it. The trigger assumes three relaxations prove the rule wrong; a finding that simply stayed
unfixed proves nothing about the rule. `artifact.stale` sat red on the committed previews for two
weeks and was correct every single time — the artifact was wrong, and promoting the rule to an
exception would have codified the defect. Count relaxations, not failures.

## Format

Copy `template.md`, take the next free id, keep the frontmatter parseable. `rules:` is the join
key — it is how `kunumi_critic.py decisions --rule <id>` finds every prior ruling on a rule.

Statuses: `proposed`, `accepted`, `superseded-by-NNNN`. Never delete an entry; supersede it.

## Reading them

```bash
python ../scripts/kunumi_critic.py decisions
python ../scripts/kunumi_critic.py decisions --search gradient
python ../scripts/kunumi_critic.py decisions --rule color.prohibition.black
python ../scripts/kunumi_critic.py decisions --status proposed
```
