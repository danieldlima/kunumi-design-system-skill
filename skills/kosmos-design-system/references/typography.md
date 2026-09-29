# Kunumi Typography

Authority: **Brandbook Kunumi Final (2025)**, typography chapter. Values below were read from
the brandbook's own Figma variables, not inferred. Exact tokens live in `tokens.json`.

This supersedes any earlier instruction to set Kunumi work entirely in Figtree.

## Two Families, Two Jobs

> "As tipografias PP Neue Machina ou Space Grotesk são utilizadas exclusivamente como fontes de
> título, assumindo o papel de destaque visual. Já a Figtree é aplicada como fonte de corpo de
> texto e subtítulos."

| Role | Family | Case | Tracking |
| --- | --- | --- | --- |
| Titles and display | **PP Neue Machina Inktrap**, or **Space Grotesk** | **Always uppercase** | **+3%** |
| Body, subtitles, lists | **Figtree** | Sentence case | **0%** |

Never set body copy in the display face. Never set a title in lowercase. Never typeset a
substitute logo in either family.

### Availability and fallback

PP Neue Machina is a **commercial face from Pangram Pangram** and is not bundled. Space Grotesk
(SIL OFL) is bundled at `assets/local/fonts/SpaceGrotesk/`. Figtree (SIL OFL) is bundled at
`assets/local/fonts/Figtree/`.

For **web delivery, the display face is Space Grotesk**, and PP Neue Machina is not in the stack
at all:

1. **Space Grotesk** — the brandbook's own stated alternate, bundled under the SIL OFL.
2. **Figtree SemiBold, uppercase** — last resort. State the substitution in your delivery note.

PP Neue Machina Inktrap remains the brandbook's first choice, and for print or a desktop deck —
where the licensed file travels with the document — it is still the right answer. It is excluded
from the web stack because it cannot be served: `AGENTS.md` forbids bundling commercial software,
so a browser will never receive it. Naming it anyway meant that a machine which happened to have
it installed rendered titles in a face the delivered page could not use, and the two are not
metrically compatible — "KONSTRUKT" at 100px measures 637.41px in PP Neue Machina against 584.91px
in Space Grotesk. The same HTML broke lines differently depending on whose machine rendered it.

Enforced by `typography.display.no-unservable-face`. Recorded as ADR 0015.

Arial is a body fallback only. Never use Arial for display.

### The long-title exception

**Follow the table above by default. Past two rendered lines, a title goes to Figtree.**

| Title length | Family | Case | Tracking |
| --- | --- | --- | --- |
| Up to 2 rendered lines | PP Neue Machina Inktrap, or Space Grotesk | uppercase | +3% |
| **3 rendered lines or more** | **Figtree SemiBold** | **sentence case** | **0** |

The display face earns its place through uppercase and +3% tracking, and both stop helping at
length. Uppercase removes the word shapes a reader scans by, and positive tracking widens lines
that are already long — so a three-line uppercase Inktrap title is the one place where the
brandbook's title recipe reads worse than body type set large.

The team's own slide template does exactly this. Its chapter page sets "Nome longo do capítulo 2"
in Figtree sentence case, at title size — a long title, handled as a long title. See
`slide-template-measured.md`.

#### An opening statement is exempt

**A statement is not a title, and the two-line limit does not apply to it.** Mark it
`data-kunumi-role="statement"` and it keeps the display face at any length.

The distinction is what the line *does*, not how long it is:

| | Job | Role |
| --- | --- | --- |
| "O futuro informa o presente." | asserts something about the brand | `statement` |
| "Inteligência para o que ainda não tem nome." | asserts something about the brand | `statement` |
| "Duas medidas. Uma conclusão." | describes the two metrics below it | `title` |

A statement is brand voice on a surface whose job is to open — a cover, a section divider. A title
describes what is on the surface. Apply the test to the copy, not to the line count, or the
exemption becomes a way of silencing the rule.

Why it is safe to grant: the brandbook's own `Abertura/Título` is **180px on a 1920 stage**, and a
statement at that size wraps past two lines by design. The argument in ADR 0012 for a two-line
threshold assumed covers wrap to two; measuring the team's own reference slides showed they run
three to five. The threshold is right for titles and wrong for statements, so statements are scoped
out rather than the threshold being raised.

**The exemption is narrow.** It removes the line limit and nothing else: a statement is still
required to be uppercase and tracked +3%, because `typography.display.case` and
`typography.display.tracking` key on the selector cascade rather than on the measured role. One
statement per surface. Recorded as ADR 0018.

Three things the long-title exception is **not**:

- **It is not the availability fallback.** `fallbackOrder` answers "is the face licensed and
  present"; this answers "is the title too long for the face". A licensed PP Neue Machina still
  yields to Figtree at three lines.
- **It is not a licence to lowercase short titles.** At one or two lines, uppercase is required
  and `typography.display.case` still fires.
- **It is not the first move.** Prefer cutting the title to two lines. Reaching for Figtree is
  correct when the words are all load-bearing, not when the title is simply unedited.

The threshold is two lines and not one because the brandbook's own `Abertura/Título` is 180px on a
1920px stage: nearly every real cover wraps to two lines, and a one-line limit would retire the
display face from the covers it was chosen for.

Measured in the render pass by `typography.display.long-title`, which counts rendered line boxes —
wrapping depends on the box, not on the stylesheet. Recorded as ADR 0012.

## Exact Type Variables

Sizes are the brandbook's own values at the 1920×1080 stage. `letterSpacing` is a **percentage**
of the font size — the brandbook stores `3` for the display face, which renders as `0.66px` at
22px, confirming percent rather than pixels.

| Variable | Family / style | Size | Line height | Tracking | Case |
| --- | --- | --- | --- | --- | --- |
| `Abertura/Título` | PP Neue Machina Inktrap Semibold | 180 | 1.1 | +3% | upper |
| `Abertura/Categoria` | PP Neue Machina Inktrap Semibold | 35 | 1.2 | +3% | upper |
| `Miolo/Título` | PP Neue Machina Inktrap Medium | 22 | 34 px | +3% | upper |
| `Cabecalho/Menu` | PP Neue Machina Inktrap Medium | 13 | 1.1 | **+10%** | upper |
| `Miolo/Texto` | Figtree Light | 20 | 1.75 | 0 | none |
| `Miolo/TextoMenorSubtitulo` | Figtree SemiBold | 21 | 1.1 | 0 | none |
| `Miolo/TextoMenor` | Figtree Regular | 18.5 | 1.6 | 0 | none |
| `Lista/Tópico` | Figtree Regular | 20 | 1.0 | 0 | none |

The canonical body block — the brandbook's `Template/Texto` component — is a **360 px** column:
`Miolo/Título` uppercase, then a **60 px** gap, then `Miolo/Texto`.

## Scale and Rhythm

The brandbook expresses scale as ratios against a grid unit rather than a fixed point list.

| Level | Ratio |
| --- | --- |
| Title | **5x – 7.5x** |
| Subtitle | **1.2x – 1.6x** |
| Lead | **1.1x** |
| Body | **x** |

A title occupies **2y** of grid height, where `y` is the grid unit.

Line-height ranges, by level:

| Level | Range |
| --- | --- |
| Display | 110% – 140% |
| Subtitle | 110% – 120% |
| Body | **140% – 175%** |

Body text is generously leaded. Do not tighten it to fit — cut copy instead.

## Emphasis Inside a Sentence

> "Para destacar conteúdos em uma frase, utilize a ferramenta de highlight na cor chumbo ou
> urucum. A cor da tipografia deve acompanhar o fundo. Seu uso deve ser dosado e pontual, evite
> marcar muitas palavras em uma mesma frase. Ele não deve ser aplicado em títulos."

- Highlight color: **Chumbo `#1C2127`** or **Urucum `#F04E44`** only.
- The text color follows the ground it now sits on, so it stays legible inside the highlight.
- Sparing and pointed. Not several words in one sentence.
- **Never on a title.**

In Figma the brandbook builds this with the underline tool, since Figma has no highlight
primitive: apply underline, then set `Thickness: 120%`, `Offset: -100%`, `Skip ink: Off`, and a
custom color with transparency. On the web, use a real background on an inline span.

## Applying This on the Web

`assets/web/kunumi-tokens.css` carries these values as custom properties:
`--kunumi-font-display`, `--kunumi-font`, the `--kunumi-text-*` size ramp, and the matching
tracking and line-height tokens. Prefer the tokens over literal values.

The display, category and body classes scale fluidly with the viewport and reach the stage size
only at wide viewports. `web-specs.md#fluid-type-and-the-product-ramp` lists the clamps and the
status of the product ramp for dense views (decisions 0019 and 0034).

Because the display face is tracked **positive** and set uppercase, never carry over the tight
negative tracking common in display type. Any earlier Kunumi CSS using a negative
`letter-spacing` on a display heading is wrong against this brandbook.

## Gate

- Titles uppercase, in the display face, tracked +3%.
- Body in Figtree at 140–175% line height, tracking 0.
- No Arial in display.
- If the display face fell back past Space Grotesk, say so on delivery.
- Render and read at delivery size before shipping.
