# Visual critique checklist

Answer every question **in writing**, against the render, before delivering. Each one carries a
stated failure condition, so the answer is a judgment and not an impression. "Looks good" is not
an answer to any of these.

These are exactly the questions no linter can answer. That is why they are here and why step 5 of
the loop cannot be skipped.

## Hierarchy

1. **Is there one dominant message?**
   Fails when two elements compete for first read, or when nothing is clearly first.
2. **Does the eye land where the content wants it to?**
   Name the element you land on. Fails when that is not the intended entry point.
3. **Is the reading order unambiguous?**
   Trace it. Fails when two plausible orders exist.
4. **Does this surface do one job?**
   Fails when you need "and" to describe its purpose.

## Type

5. **Does any display line break mid-word?**
   Fails on any mid-word break. The token sheet sets `overflow-wrap: break-word` and deliberately
   no hyphenation, so a long word at a large size will split rather than hyphenate. Fix by
   shortening the copy, changing the measure, or lowering the size — never by adding hyphenation.
6. **Is every title actually uppercase in the render?**
   Fails on any sentence-case title *of two lines or fewer*. The static pass checks the
   declaration; only the render shows what the browser did with it.
6a. **Does any title run past two rendered lines?**
   Then it must be Figtree SemiBold, sentence case, tracking 0 — not the display face (decision
   0012, enforced by `typography.display.long-title`). Prefer cutting the title to two lines;
   reach for Figtree when every word is load-bearing.
6b. **If a long line is marked `statement`, does it earn the label?**
   A statement asserts something about the brand on a surface whose job is to open. A line that
   describes what is on the surface is a title, and marking it `statement` to clear 6a is the one
   way this exemption gets abused (decision 0018). One statement per surface.
7. **Did the display face resolve, or did it fall back?**
   PP Neue Machina is commercial and not bundled. If Space Grotesk rendered instead, that is
   correct — but say so on delivery.
8. **Is the body measure comfortable?**
   Fails below roughly 45 or above roughly 75 characters per line.
9. **Is the title inside 1.6x to 3.1x the body, for this slide's role?**
   Measured across the team's own template in `slide-template-measured.md`. The `5x - 7.5x` in
   `tokens.scaleRatios.title` is stated against the grid unit, not against body size, and
   decision 0006 read it against the wrong denominator — see decision 0010.
9a. **Is surplus vertical space actually a defect here?**
   Usually not. The team's template floats a content band in as little as 19% of the canvas
   height, centred rather than top-filled. Answer a vertical hole by centring the band or adding
   real information — never by inflating the title until the gap closes.

## Color

10. **Is Urucum a selective accent rather than an all-over fill?**
   Estimate the share of the surface it covers. Fails when it reads as a background.
11. **Is text legible against everything behind it?**
    Check every element sitting on a gradient, photograph, pixel field, or kaleidoscope. Fails on
    any label whose ground is busy enough to compete.
12. **Does the artifact read as Kunumi rather than as generic?**
    Fails when the palette and type could belong to anyone.

## The mark

13. **Does the mark hold 1X clear space on all four sides?**
    X is the symbol's square module. No pixel value is published, so measure it proportionally off
    the render. Fails when anything enters the perimeter.
14. **Is the mark's polarity right for its ground?**
    Positive on light, negative on dark. Fails on a positive mark on Chumbo, or a negative mark on
    Gelo.
15. **Is the mark's optical weight balanced against its neighbours?**
    Bounding-box height is not optical height. Fails when the mark reads visibly heavier or
    lighter than what it sits with.

## Composition

16. **Is there enough breathing room?**
    Fails when any edge feels crowded, or when the margin is inconsistent between sides that
    should match.
17. **Is the alignment intentional throughout?**
    Fails on any element that is nearly-but-not aligned to a neighbour.
18. **Is the density right for the medium?**
    Fails when a slide reads like a document, or a page reads like a poster.

## Motion, when present

19. **Does anything loop that should not?**
    Fails on an infinite attention effect over controls or essential copy.
20. **Is there a reduced-motion path, and does the artifact still work under it?**
    Re-render with `--reduced-motion`. Fails when content depends on animation to be legible.

## Honesty

21. **Can you state what is still wrong?**
    An artifact with no remaining compromise is rare. Naming the compromise is the answer; having
    none and saying so without having looked is the failure.
