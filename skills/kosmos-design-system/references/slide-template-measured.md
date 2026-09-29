# Measured geometry of the Kunumi slide template

Source: `Kunumi - Template de Slides.pdf`, 13 pages exported by the Kunumi design team
(footer numbering 44–72, so this is a subset of a larger deck). Native page size 1440×810pt,
which is the `geometry.stage` 1920×1080 canvas at 0.75. **Every value below is in px on the
1920×1080 stage** (pt × 1.3333).

Method: text position, size and colour from `pdftohtml -xml`; shape geometry, stroke widths and
dash patterns from `pdftocairo -svg`; margins and gradient stops sampled from a 96-dpi raster.
Nothing here is estimated from a proportion.

## Read this first: what is current and what is historical

The deck sets **every title in Figtree, sentence case, 0% tracking**. `typography.md` states that
PP Neue Machina / Space Grotesk, uppercase, +3% tracking supersedes "any earlier instruction to
set Kunumi work entirely in Figtree". So this template predates that rule.

| Dimension | Status | Why |
|---|---|---|
| Margins, grid, box and rule geometry, spacing, leading ratios | **current** | typeface-independent |
| Neutral and accent palette | **current** | every colour resolves to the institutional palette |
| Title typeface, case, tracking | **historical** | brandbook 2025 replaced it |
| Absolute title sizes and title/body ratios | **historical, use with care** | measured on sentence-case Figtree; uppercase Inktrap at +3% carries different optical mass at the same px |
| `#000000` fills, `#FFFFFF` body text | **historical defect** | Chumbo replaces black; white is never a text colour |

## Canvas and chrome

The chrome is the only part of the template that holds a fixed position on every page.

| Element | Measurement |
|---|---|
| Side margin | **57px** left and right |
| Top / bottom margin | **43px** |
| Logo mark + tagline | x 57..229 (w 173), y 43..100 (h 58) |
| `kunumi` wordmark | x 1701..1862 (w 162), y 54..89 (h 36); right edge on the 57px margin |
| Chapter label (footer) | 20px Figtree, left 57, ink band y 1018..1036 |
| Page number | 21px `#999999`, right edge 1869 — Google Slides auto-number placeholder, set in ArialMT. An artifact of the tool, **not** a rule: it ignores both the margin and the type stack |
| Title slot | glyph origin x **201**, y **150**, 43px SemiBold (identical on the two pages that carry a standard title) |

The content block does not share the chrome's 57px margin. The densest pages start at x **146**
and run 1619px wide (right edge 1765, gap 155). Title-bearing pages start at x 201. There is no
single content margin in this template; 146 and 201 are both real.

## Type scale, measured

`64 / 53 / 48 / 43 / 32 / 31 / 27 / 22 / 21 / 19 / 17 / 16 / 11`

| px | Weight | Role in the deck |
|---|---|---|
| 64 | Medium / Regular | chapter list, phase display |
| 53 | SemiBold | keyword hero |
| 48 | SemiBold | chapter path |
| 43 | SemiBold | slide title |
| 31–32 | SemiBold / Regular | column head, eyebrow above a display |
| 27 | Light (on dark) / Regular | lead copy, section label |
| 21 | Regular | default body |
| 19–20 | Regular | dense body, footer label |
| 16–17 | Regular / Medium | table cells, captions |
| 11 | Light + Regular mixed | logo tagline |

On dark grounds body copy drops to **Figtree Light** — a deliberate compensation for optical
bolding, used consistently on every dark page.

## Leading and paragraph spacing

| Size | Baseline pitch | Ratio |
|---|---|---|
| 64px | 88px | **137.5%** |
| 27px | 37px | **137.0%** |
| 17px | 20px | 117.6% |
| 16px | 19px | 118.8% |

Large text (≥27px) is set at **137%**. Dense small text sits at ~118%, which is Figtree's natural
single spacing rather than a chosen value.

**Paragraph spacing is exactly 2× the line height** — one empty line, no partial values. Verified
at 17px (40px gaps on 20px leading) and at 27px (74px gaps on 37px leading).

## Title-to-body ratio, measured

| Slide role | Title | Body | Ratio |
|---|---|---|---|
| Phase display | 64 | 21 | **3.05x** |
| Content slide | 43 | 17 | **2.53x** |
| Keyword slide | 53 | 27 | **1.96x** |
| Resource slide | 27 | 16 | 1.69x |
| Column slide | 31 | 19 | 1.63x |

The measured range is **1.6x – 3.1x**. No slide in this export reaches 5x. See ADR 0010.

## Vertical occupancy

Surplus vertical space is the template's normal state, not a defect.

| Page | Content band | Share of canvas height |
|---|---|---|
| Timeline (phase) | y 397..603 | **19%** — 397px empty above, 443px below |
| Column comparison | y 430..700 | 25% |
| Keyword | y 353..850 | 46% |
| Gantt / table | y 146..1000 | 79% |

A single content band floating in a mostly empty canvas is a first-class layout here, and the band
sits near the vertical centre rather than filling from the top.

## Grid

- **3-column grid** on the table page: columns of **534px**, gutters **9–10px**, content width 1619px from x 146.
- **Month/time gridlines** at a uniform **89.6px** pitch.
- Stacked banner bars: h **42–43px**, vertical gap **9–10px**.
- Gantt bars: h **37px**, row pitch 49–55px.
- Legend chips: **260×37px**, gap 11px.

## Diagram and timeline language

This is the team's convention, measured. It replaces the dialect invented in the 2026-09-14
session — see ADR 0011.

| Element | Measurement |
|---|---|
| Node box | **corner radius 0** (bezier control points are degenerate), fill CONCRETO `#B4ADA4`, **no stroke**, label centred in Gelo |
| Node width | constant **148px**, independent of surplus space |
| Node height | **38 / 65 / 92px**, driven by line count |
| Highlighted node | solid URUCUM `#F04E44` |
| Label box on a timeline | h **56px** (one line) / **81px** (two lines) |
| Connector | **2px** Chumbo, orthogonal elbows, solid triangular arrowhead **9×7px** |
| Vertical stub | **2px**, Concreto — Urucum for the marked one; 121px from label to axis |
| Zone separator | dotted, 2px wide, **dash 2px / gap 6px**, Concreto, full height (y 186..959) |
| Timeline axis | **0.8px hairline**, Chumbo; the thinnest line in the deck |
| Timeline node | circle **12–15px**; filled = reached, hollow = pending |
| Full-bleed rule | **1.9px** Grafite, x −1..1920 — rules bleed off both edges |

## Colour, as measured

Every colour resolves to the institutional palette, with three exceptions.

| Measured | Token | Use in the deck |
|---|---|---|
| `#F0F0F0` | GELO | light ground; text on dark |
| `#1C2127` | CHUMBO | body ink; dark ground |
| `#F04E44` | URUCUM | the one marked item per slide |
| `#B4ADA4` | CONCRETO | diagram nodes, dotted guides, table header cells |
| `#5E5E5E` | GRAFITE | full-bleed rules, table theme bar, emphasis column |
| `#000000` | — | **off-palette**: month heads, timeline label boxes. Should be Chumbo |
| `#FFFFFF` | — | **off-palette as text**: body copy on the keyword page. Should be Gelo |
| `#D5D5D5` | — | off-palette hairline, one occurrence |

Urucum marks exactly one item per slide — one phase, one month, one node, one bar, one chapter.
That restraint is the most consistent single behaviour in the whole export.

## Gradient

The chapter-divider bar is **30px tall** and bleeds off the right edge. Stops sampled across its
width:

`0% #3B3F6F` → `12% #4F5496` → `25% #73568C` → `37% #9F5272` → `50% #D04F54` → `62% #E94C43` →
`75% #EF503D` → `87% #EE5E39` → `100% #EF6536`

Indigo into violet into red into orange, with Urucum `#F04E44` crossing at ≈55%.
