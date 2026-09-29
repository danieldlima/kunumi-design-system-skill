---
id: 0017
status: accepted
date: 2026-09-16
scope: web.new
artifact: references/design-rules.json
rules: artifact.unprovenanced, artifact.stale
tags: provenance, artifact, render, enforcement
---

# Provenance is the half that staleness cannot see

## Context

ADR 0016 made `template-preview.html` renderable and replaced two hand-taken screenshots with four
generated frames. That fixed the instance. It did not stop the next one.

`artifact.stale` compares modification times. A screenshot taken thirty seconds ago is newer than
every source it depicts, so it **passes** — the rule that had been red for two weeks would have
cleared the very file that caused the problem, had it been retaken. Age and origin are different
questions, and only one of them was being asked.

## Decision

`artifact.unprovenanced`, a `violation`: a delivered raster or vector must be named in a
`*.render.json` sitting beside it.

Two scoping choices, both load-bearing:

**It judges only directories that hold at least one `.html`.** That is what separates "this
directory delivers rendered artifacts" from "this directory holds supplied files". Brand marks and
bundled fonts have no HTML beside them and are never asked for a render record, because for them
one would be meaningless. Checked against the repository: the only directories holding both are
`assets/web` and the three under `output/kunumi-design`, all of which carry a record.

**It matches file names, not recorded paths.** `renders` stores absolute paths, so the recorded
value belongs to whichever machine produced it and cannot be compared against a checkout anywhere
else. Making the paths relative was considered and rejected: the CLI prints them for the reader to
open, and a relative path would have to be resolved against a base the reader does not have.

The `--out-dir` in the documented render command is part of this. Render into a temp directory and
the committed record claims files that are not the committed ones — the record would be honest
about its own run and useless as provenance.

## Consequence

The two halves now cover each other. `artifact.stale` catches a render that fell behind its
sources; `artifact.unprovenanced` catches a file that was never a render. A screenshot fails the
second even though it passes the first, which is asserted directly in
`test_unprovenanced_raster_is_flagged`.

A silently skipped frame is also closed off, from the artifact side rather than the engine side.
The render worker still refuses to screenshot an invisible frame — correctly, since a blank PNG
that looks like an artifact is worse than an admitted gap — but an uncaptured frame now has no
escape route: no PNG exists for it, and `test_every_frame_has_a_committed_render` compares frames
against committed files in both directions. That is the exact hole the previews fell through.

The off-screen caveat in `logo_min_height` was rewritten rather than deleted. Its `visible` guard
stays, but it is now justified as a general rule instead of by reference to a file that no longer
behaves that way — nothing in this repository depends on it today, and the next artifact might.

`decisions/README.md` gained the distinction this episode exposed: **a rule left red is not a rule
relaxed, it is a rule ignored**, and the promotion trigger must not fire for it. Counting failures
instead of relaxations would have turned a correct rule into an exception and written the defect
into `design-rules.json`.
