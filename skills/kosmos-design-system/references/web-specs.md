# Web Specifications

The **Brandbook Kunumi Final (2025)** was drawn for graphic and print material. It prints colour,
type, the mark and composition, but no breakpoint, grid, interaction state, component, favicon or
social pixel format. This file specifies those for the web.

Every value below is **product layer** unless it says brandbook. Product-layer values come from
the Kosmos Figma library (which mirrors `tokens.json`, not the reverse), from a platform
convention (WCAG 2.2, Open Graph, the web-app manifest), or from a channel's published format.
They are subordinate to the brandbook and open to revision. Values marked **proposed** still await
brand approval.

`tokens.json` holds every number here. `assets/web/kunumi-tokens.css` implements them. Change the
token file first.

## Authority layers

| Layer | Examples | May change by |
| --- | --- | --- |
| Brandbook | Paleta principal, the two families and eight variables, 10px card radius, 30px card padding, 360px text column, 28px lockup minimum, 1X clear space | brand decision only |
| Product | tonal steps, semantic roles, dark theme, spacing scale, breakpoints, grid, elevation, focus ring, components, icons | a decision in `decisions/` |
| Platform | 24px minimum target (WCAG 2.5.8), focus visible (2.4.7), 3:1 non-text contrast (1.4.11), OG 1200×630, favicon and manifest sizes | the platform |

## Breakpoints and grid

Mobile-first. Write `min-width` queries at the two breakpoints and nothing else
(`layout.breakpoint-scale`). A `max-width` query may sit up to 1px below a breakpoint
(`767.98px`) so it meets the matching `min-width` without overlap.

| Range | Columns | Gutter | Page margin | Figma grid |
| --- | --- | --- | --- | --- |
| below 768px | 4 | 16px | 24px | Grid/Mobile 375 |
| from 768px | 8 | 24px | 48px | Grid/Tablet 768 |
| from 1440px | 12 | 24px | 96px | Grid/Desktop 1440 |

The kit exposes the grid as custom properties that change at each breakpoint:
`--kunumi-grid-columns`, `--kunumi-grid-gutter`, `--kunumi-page-margin`. Every gutter and margin is
a `--kunumi-space-*` step.

```html
<main class="kunumi-container">
  <div class="kunumi-grid">
    <section style="grid-column: 1 / -1">…</section>
  </div>
</main>
```

**Dois por dois** is the brandbook's composition principle: two major horizontal blocks, two major
vertical blocks, then subdivide. Read it onto the column grid (6 + 6 at desktop, 4 + 4 at tablet,
stacked on mobile). It does not mean four cards.

A slide replica keeps its stage's own breakpoints (`template-preview.html` uses 720 and 480).
Declare it `web.deck-derived` and the finding drops to a note. See decision 0029.

## Containers and measure

- **Container:** 1248px of content (`--kunumi-container`), which is 1440 − 2 × 96. `.kunumi-container`
  adds the page margin on both sides and centres.
- **Text measure:** body stops at `58ch` (`.kunumi-body`). A display title stops at `18ch`
  (`.kunumi-display`), wider than mixed case would need because uppercase runs 15–20% wider.
- **Brandbook text column:** 360px (`--kunumi-text-column`), for side columns and captions.

## Fluid type and the product ramp

The brandbook variables are measured on a 1920×1080 stage. On the web the stage size is the
ceiling, reached at wide viewports, never the default:

| Class | Minimum | Preferred | Maximum |
| --- | --- | --- | --- |
| `.kunumi-display` | 2.5rem (40px) | 7vw | 180px, `Abertura/Título` |
| `.kunumi-category` | 1.25rem (20px) | 2vw | 35px, `Abertura/Categoria` |
| `.kunumi-body` | 1rem (16px) | 1.5vw | 20px, `Miolo/Texto` |

Dense product views use a product ramp. Decision 0019 admits one only when it keeps two brandbook
steps at their literal values, typically 22px `Miolo/Título` and 13px `Cabecalho/Menu`, with
16px body. The Kosmos Figma `UI/*` ramp (48 / 32 / 24 / 18 display, 18 / 16 / 14 / 12 text) keeps
neither anchor. It sits in `tokens.json#typography.productRamp` as **proposed** and is not in the
CSS until decision 0034 is ruled on.

## Themes

Light is the default and `:root` carries it. Dark is **opt-in** (decision 0030):

| Class | Behaviour |
| --- | --- |
| none | light |
| `.kunumi-theme-dark` | dark, always |
| `.kunumi-theme-auto` | follows `prefers-color-scheme` |

Only semantic roles flip; raw palette tokens never do (decision 0007). Paint with roles:

| Role | Light | Dark |
| --- | --- | --- |
| `--kunumi-ground` | Gelo | Chumbo |
| `--kunumi-ink` | Chumbo | Gelo |
| `--kunumi-ink-muted` | Grafite | neutral-300 `#C9C7C1` |
| `--kunumi-border` | Concreto | Gelo 28% |
| `--kunumi-border-subtle` | Chumbo 14% | Gelo 16% |
| `--kunumi-hairline` | Chumbo 8% | Gelo 10% |
| `--kunumi-surface-raised` | white (the one exception) | neutral-800 `#262B31` |
| `--kunumi-accent` | Urucum | Urucum |
| `--kunumi-accent-hover` / `-press` | urucum-600 `#D7423A` / urucum-700 | urucum-400 / urucum-300 |
| `--kunumi-accent-text` (**proposed**) | urucum-700 `#BC392F`, 4.89:1 | urucum-400 `#F26058`, 5.08:1 |
| `--kunumi-on-accent` | Chumbo | Chumbo |
| `--kunumi-accent-fill-hover` / `-press` | urucum-400 / urucum-300 `#F47D75` | same |
| `--kunumi-ink-hover` | neutral-700 `#363940` | neutral-200 `#E1E1DE` |
| `--kunumi-focus-ring` | Urucum | urucum-400 |
| `--kunumi-surface-disabled` | neutral-200 | neutral-800 |
| `--kunumi-ink-disabled` | neutral-400 `#9A9A97` | neutral-400 |

The tonal steps (`#F47D75`, `#F26058`, `#D7423A`, `#BC392F`, `#E1E1DE`, `#C9C7C1`, `#9A9A97`,
`#363940`, `#262B31`) are admitted only as role values. They are not brand colours and never
appear as free accents.

**Small accented text** uses `--kunumi-accent-text`, never full Urucum: Urucum on Gelo is 3.13:1
and fails 4.5:1. Full Urucum as text starts at 24px (decision 0022). In dark, keep small accent
text off `--kunumi-surface-raised`: urucum-400 on neutral-800 is 4.48:1.

## States

Every interactive element has five states: default, hover, active, focus-visible, disabled.

- **Hover and active** change the fill or the wash, over `--kunumi-fast` (180ms) with
  `--kunumi-ease`. Reduced motion collapses the transition.
- **Focus-visible** is a 2px `--kunumi-focus-ring` outline, offset 2px (**proposed**), drawn on the
  element, never on a mark inside it (`logo.no-effects`). The token sheet draws it for every
  interactive element, so linking it satisfies `interaction.focus-visible`. The ring clears the
  3:1 non-text floor: Urucum on Gelo 3.13:1, urucum-400 on Chumbo 5.08:1.
- **Never remove an outline on `:focus`** without drawing a replacement on the same selector or
  on a `:focus-visible` rule (`interaction.focus-outline-removed`, a violation). To drop the ring
  for pointer focus only, write `:focus:not(:focus-visible) { outline: none }`.
- **Disabled** uses the `disabled` attribute or `aria-disabled="true"`, the disabled surface and
  ink, and the `not-allowed` cursor. Disabled controls are exempt from contrast minimums, so
  colour must not be the only signal. Never fade the whole control with `opacity` alone.

## Components

### Button

`.kunumi-button`, from the Kosmos Figma Button. Radius is the brandbook's 10px card radius; the
label is Figtree Medium, sentence case, tracking 0.

| Variant | Class | Fill | Label | Hover |
| --- | --- | --- | --- | --- |
| primary | `.kunumi-button` | Urucum | **Chumbo** | urucum-400 |
| secondary | `--secondary` | ink | ground | ink-hover |
| outline | `--outline` | transparent, border role | ink | ink at 8% |
| ghost | `--ghost` | transparent | ink | ink at 8% |

The primary label is Chumbo, not Gelo: Chumbo on Urucum is 4.53:1, Gelo on Urucum 3.13:1
(decision 0032). Because the label is dark, hover **lightens** the fill; darkening it to
urucum-600 would drop the label to 3.65:1.

| Size | Class | Height | Inline padding | Gap | Icon | Label |
| --- | --- | --- | --- | --- | --- | --- |
| xs | `--xs` | 28 | 8 | 4 | 14 | 12 |
| sm | `--sm` | 32 | 12 | 4 | 16 | 12 |
| default | — | 40 | 16 | 8 | 18 | 14 |
| lg | `--lg` | 44 | 24 | 8 | 20 | 16 |

Figma draws the default at 38px; the web uses 40px so every height is on the 4px scale.

Not specified yet: **destructive**, which waits for an approved error colour. Figma's **link**
variant is a text link, not a button. Figma's **Gradient hover** paints the Instituto gradient and
belongs only to `web.instituto` work.

### Icon button

`.kunumi-icon-button`: square, the height of the matching size, same colour system. xs (28) and sm
(32) sit below the 44px touch recommendation: pointer-dense surfaces only, never a primary touch
target.

### Input

**Proposed**. The Kosmos library has none yet. Until one is approved: 4px control radius
(`--kunumi-radius-sm`), the border role, ink text, the focus ring, and a visible label. A
placeholder is never the only label.

### Navigation

`.kunumi-nav` holds links set in `.kunumi-menu`, the brandbook's `Cabecalho/Menu` at its literal
13px, +10%, uppercase. Items are 44px tall. Mark the current page with `aria-current="page"`; the
kit draws an Urucum rule under it, so the state does not rely on text colour alone.

```html
<nav class="kunumi-nav" aria-label="Principal">
  <a class="kunumi-menu" href="/" aria-current="page">Início</a>
  <a class="kunumi-menu" href="/sobre">Sobre</a>
</nav>
```

## Target size

Every pointer target is at least **24×24px** (WCAG 2.5.8). Primary touch targets are **44×44px**.

## Icons

No approved Kunumi icon set exists. The Kosmos Figma Iconography page is a utility set labelled as
invented. When a surface needs icons: line drawings on a 20px grid, 1.75 stroke, round caps and
joins, `currentColor`, sized 14 / 16 / 18 / 20 to the button they sit in (`.kunumi-icon`). An icon
never stands in for the brand mark or the symbol.

## Digital formats

### The mark on screen

Clear space is **1X** on every side, where X is the square module of the symbol. The symbol is 3X
tall and so is the lockup, so X is one third of the rendered lockup height. This table is
arithmetic on that rule, not a new rule:

| Lockup height | X, clear space per side |
| --- | --- |
| 28px (the minimum) | 9.33px |
| 32px | 10.67px |
| 40px | 13.33px |
| 48px | 16px |
| 64px | 21.33px |

The 28px minimum is printed for the positive RGB lockup only. Other versions and the symbol alone
have no printed minimum; ask for one rather than extrapolating (`logo-governance.md`).

### Favicon and app icons

**Proposed** (decision 0035). Resample the approved symbol from `assets/local/brand-marks/shared/`;
never redraw it (decision 0028).

| Use | Size |
| --- | --- |
| `<link rel="icon" type="image/svg+xml">` | vector, when an approved SVG exists |
| `<link rel="icon" sizes="32x32">` | 32 |
| `<link rel="icon" sizes="48x48">` | 48 |
| `<link rel="apple-touch-icon">` | 180 |
| web app manifest | 192 and 512 (also the maskable icon) |

The brandbook prints no minimum for the symbol alone and no favicon polarity. Both need approval.
Until then, check the favicon at 32px in light and dark browser tabs.

### Sharing image

Every published page carries `og:title`, `og:image` at **1200×630** with `og:image:width` and
`og:image:height` declared, and a `rel="icon"` link. Declare `data-kunumi-scope="web.published"`
and `artifact.social-meta` checks it.

### Social formats

Channel sizes change; re-check the channel before a campaign. Keep essential copy away from crops
and platform chrome.

| Channel | Format | Size |
| --- | --- | --- |
| LinkedIn | page header (use the supplied template) | 1584×396 |
| LinkedIn | link share | 1200×627 |
| LinkedIn | square post | 1080×1080 |
| LinkedIn | portrait post | 1080×1350 |
| Instagram | portrait feed | 1080×1350 |
| Instagram | square feed | 1080×1080 |
| Instagram | story / reel cover | 1080×1920, type out of the top and bottom 250px |
| YouTube | thumbnail | 1280×720 |
| YouTube | channel banner | 2560×1440, safe area 1546×423 centred |

A social asset is a composition, not a scaled page: one focal image, one headline, one brand
signature (`medium-playbooks.md`).

## What the engine checks

| Spec | Rule | Severity |
| --- | --- | --- |
| Breakpoints | `layout.breakpoint-scale` | advisory |
| A focus style exists | `interaction.focus-visible` | advisory |
| Outline not removed without replacement | `interaction.focus-outline-removed` | violation |
| Sharing metadata on a published page | `artifact.social-meta` (scope `web.published`) | advisory |
| Gutters, margins, component padding | `geometry.spacing-scale` | advisory |
| Lockup height | `logo.min-height` (after render) | violation |
| Tonal steps used only as role values, target size, clear space, theme flip, disabled signal, icon legibility | checklist only (`kosmos-designer` critique) | — |
