---
id: 0004
status: accepted
date: 2026-09-14
scope: web.instituto
artifact: instituto-hero
rules: color.palette.unapproved
tags: instituto, gradient, urucum, checklist
---

# A full-bleed Instituto gradient is not Urucum overuse

## Context

Question 9 of the visual critique checklist asks whether Urucum reads as a selective accent rather
than an all-over fill. An Instituto hero built on `kunuminst_gradiente_01.png` fails that question
on its face: the Urucum-dominant band covers most of the frame.

The two rules pull in opposite directions. `brand-foundations.md` asks for Urucum used
selectively. `color.instituto` documents the signature gradient as Urucum-dominant by
construction — 542 of 1918 band pixels, 28% of the bar, "nearly triple any other stop" — and
`asset-catalog.md` describes the file as a "high-impact static cover or chapter background;
preserve crop and colors".

## Decision

The selective-Urucum rule governs Urucum used as an **accent** in core Kunumi work. It does not
govern the Instituto signature gradient used as supplied artwork, which is a different system with
its own documented dominance.

When reviewing an Instituto artifact, checklist question 9 is answered against the *elements
placed on* the gradient, not against the gradient itself. The gradient is treated as ground.

## Consequence

An Instituto cover or hero may be almost entirely warm. What still has to hold is question 10:
anything placed over the bright band needs checking for contrast, and that is where the real defect
lives. The first artifact built under this decision had exactly that problem — a footer row
spanning the full frame put Gelo text on the brightest orange — and it was fixed by constraining
the footer to the content column, not by dimming the artwork.

Never recolor, re-crop or synthesise a replacement for the gradient to satisfy question 9. If the
warmth is wrong for a piece, choose a different supplied background or a Chumbo ground instead.
