---
name: Beads Backend Integration Reference
description: Precise technical reference system for DH plugin backend comparison — proof-sheet clarity, fidelity-coded tables, zero decoration.
colors:
  press-white: "oklch(99% 0.002 250)"
  proof-copy: "oklch(97% 0.005 250)"
  galley-ink: "oklch(12% 0.01 250)"
  caption-gray: "oklch(42% 0.01 250)"
  register-mark: "oklch(56% 0.01 250)"
  hairline: "oklch(89% 0.005 250)"
  hairline-soft: "oklch(94% 0.003 250)"
  decision-violet: "oklch(94% 0.035 300)"
  decision-violet-rule: "oklch(84% 0.04 300)"
  decision-violet-surface: "oklch(97% 0.018 300)"
  bridge-lime: "oklch(93% 0.10 128)"
  bridge-lime-rule: "oklch(82% 0.10 128)"
  direct-green-bg: "oklch(89% 0.07 145)"
  direct-green-ink: "oklch(28% 0.12 145)"
  adapted-amber-bg: "oklch(91% 0.08 90)"
  adapted-amber-ink: "oklch(30% 0.10 75)"
  bridge-orange-bg: "oklch(88% 0.07 48)"
  bridge-orange-ink: "oklch(28% 0.12 38)"
  gap-red-bg: "oklch(88% 0.05 18)"
  gap-red-ink: "oklch(28% 0.10 12)"
  layer-agents: "oklch(96% 0.025 280)"
  layer-mcp: "oklch(96% 0.025 200)"
  layer-hooks: "oklch(96% 0.025 35)"
  layer-skills: "oklch(96% 0.025 145)"
  layer-cli: "oklch(96% 0.015 250)"
typography:
  display:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "clamp(34px, 5vw, 52px)"
    fontWeight: 800
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "clamp(22px, 3vw, 32px)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  label:
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace"
    fontSize: "11px"
    fontWeight: 400
    letterSpacing: "0.08em"
rounded:
  sm: "4px"
  md: "8px"
  pill: "20px"
spacing:
  xs: "12px"
  sm: "16px"
  md: "24px"
  lg: "40px"
  xl: "72px"
components:
  layer-chip-agents:
    backgroundColor: "{colors.layer-agents}"
    textColor: "oklch(35% 0.10 280)"
    rounded: "{rounded.pill}"
    padding: "3px 8px 3px 5px"
  layer-chip-mcp:
    backgroundColor: "{colors.layer-mcp}"
    textColor: "oklch(32% 0.10 200)"
    rounded: "{rounded.pill}"
    padding: "3px 8px 3px 5px"
  layer-chip-skills:
    backgroundColor: "{colors.layer-skills}"
    textColor: "oklch(30% 0.12 145)"
    rounded: "{rounded.pill}"
    padding: "3px 8px 3px 5px"
  cell-direct:
    backgroundColor: "{colors.direct-green-bg}"
    textColor: "{colors.direct-green-ink}"
  cell-adapted:
    backgroundColor: "{colors.adapted-amber-bg}"
    textColor: "{colors.adapted-amber-ink}"
  cell-bridge:
    backgroundColor: "{colors.bridge-orange-bg}"
    textColor: "{colors.bridge-orange-ink}"
  cell-gap:
    backgroundColor: "{colors.gap-red-bg}"
    textColor: "{colors.gap-red-ink}"
  size-chip:
    backgroundColor: "transparent"
    textColor: "{colors.register-mark}"
    rounded: "{rounded.pill}"
    padding: "1px 7px"
---

# Design System: Beads Backend Integration Reference

## 1. Overview

**Creative North Star: "The Proof Sheet"**

A proof sheet is the last document before the press run — every mark is deliberate, every color is coded, every column earns its place. This reference document is that artifact: the technical record a developer opens to resolve a single question ("does beads support X?") and closes in under ten seconds. Everything in the visual system serves that scan.

The aesthetic is that of precision technical publishing — Inter at high weights for editorial authority, JetBrains Mono for all metadata and labels, OKLCH-calibrated tonal neutrals that read as paper under daylight. Decoration is prohibited not as a stylistic choice but as a functional one: any visual element that doesn't carry information is noise that slows the scan.

Color in this system is exclusively semantic. The four-color fidelity traffic light (Direct, Adapted, Bridge, Gap) is the most important visual element in the document — it answers "how well does this map?" faster than the cell copy does. The five-hue layer taxonomy (Agents, MCP, Hooks, Skills, CLI) and the two zone tints (Decision Violet, Bridge Lime) are the only other chromatic elements. Every other surface is a neutral from the press-and-proof scale.

This system explicitly rejects: the rendered GitHub Markdown look (flat monochrome, undifferentiated table rows, no hierarchy beyond heading size), and the Notion/Confluence wiki aesthetic (emoji bullets, pastel callout card grids, soft rounded everything, generic SaaS feel). This is a printed white paper, not a team wiki.

**Key Characteristics:**
- Tonal neutrals as the base; chromatic color only for data
- Monospace type carries all metadata, labels, and secondary structure
- No shadows; elevation is a 2-point lightness step
- Fidelity traffic light is the primary navigational signal
- Tables are the primary layout unit; cards are used once (decision options)


## 2. Colors: The Press and Proof Palette

Color strategy: **Restrained + Semantic**. The neutral scale carries ~90% of the surface. Chromatic color appears only in data cells, zone backgrounds, and layer classification chips — never ornament.

### Neutral (page foundation)

- **Press White** (`oklch(99% 0.002 250)`): Page surface. The near-white is tinted 0.002 chroma toward 250 (cool blue-gray) so it reads as white without the harshness of pure white.
- **Proof Copy** (`oklch(97% 0.005 250)`): Elevated surfaces — code blocks, table headers, info callouts, pre elements. Two lightness points above Press White; no shadow needed.
- **Galley Ink** (`oklch(12% 0.01 250)`): Primary text. Near-black with minimal cool tint. Never pure black.
- **Caption Gray** (`oklch(42% 0.01 250)`): Secondary text, descriptions, prose within components.
- **Register Mark** (`oklch(56% 0.01 250)`): Labels, metadata, muted annotations, chip text at rest.
- **Hairline** (`oklch(89% 0.005 250)`): Structural borders — section dividers, table column lines, component edges.
- **Hairline Soft** (`oklch(94% 0.003 250)`): Row dividers within tables and label lists. Near-invisible; present only to aid scanning.

### Decision Zone

- **Decision Violet** (`oklch(94% 0.035 300)`): Background for the Open Decisions section — the architectural fork zone. Violet hue (300) signals "requires human input before code." Three tokens: background, rule (borders), and surface (option panels).

### Bridge Zone

- **Bridge Lime** (`oklch(93% 0.10 128)`): Background for the Gaps section — the engineering bridge zone. Lime hue (128) signals "work needed here, but solvable." Three tokens: background, rule, and surface.

### Fidelity Traffic Light (Primary Semantic System)

These four color pairs are the most important chromatic elements. They answer "how well does this MCP tool map to beads?" without reading the cell copy.

- **Direct Green** (bg: `oklch(89% 0.07 145)`, ink: `oklch(28% 0.12 145)`): 1:1 mapping, no data loss.
- **Adapted Amber** (bg: `oklch(91% 0.08 90)`, ink: `oklch(30% 0.10 75)`): Same operation, parameter translation required.
- **Bridge Orange** (bg: `oklch(88% 0.07 48)`, ink: `oklch(28% 0.12 38)`): Wrapper logic required; operation exists in beads.
- **Gap Red** (bg: `oklch(88% 0.05 18)`, ink: `oklch(28% 0.10 12)`): No beads equivalent.

### Layer Taxonomy (5 Hues)

Five distinct hues, each appearing only in layer chip backgrounds, borders, and text. Hue is the only differentiator — lightness and chroma are calibrated to the same perceived intensity across all five so no layer reads as "more important."

- **Agents** (hue 280 — violet): `oklch(96% 0.025 280)` bg
- **MCP Scripts** (hue 200 — teal): `oklch(96% 0.025 200)` bg
- **Hooks** (hue 35 — amber): `oklch(96% 0.025 35)` bg
- **Skills** (hue 145 — green): `oklch(96% 0.025 145)` bg
- **CLI** (hue 250 — cool gray): `oklch(96% 0.015 250)` bg

**The One Signal Rule.** Each color family carries exactly one semantic meaning throughout the document. Green means Direct/Full/No-Change. Orange means Bridge/Partial/Flag. Red means Gap/Missing. Violet means Decision. Lime means Bridge-work. Layer taxonomy hues are used only in layer chips. Never borrow one family's hue for a different purpose.

**The Tonal Proof Rule.** Every surface in this document can be identified by lightness alone: 99% is the page, 97% is elevated, 89%–94% is a hairline or near-invisible separator. No value falls between 94% and 97% or between 89% and 94% by accident.


## 3. Typography

**Display/Headline Font:** Inter (system-ui fallback)
**Label/Mono Font:** JetBrains Mono (Fira Code fallback)

**Character:** Inter at 800 weight reads as a type director's headline — compressed, authoritative, no apology. JetBrains Mono at 11px uppercase with tight letter-spacing does the work of every label, table header, eyebrow, and chip: it signals "this is metadata, not prose" without a style change.

### Hierarchy

- **Display** (Inter 800, clamp(34px → 52px), line-height 1.08, letter-spacing -0.03em): Document title only. Appears once. The large negative letter-spacing closes the optical gaps that Inter 800 opens at display sizes.
- **Headline** (Inter 700, clamp(22px → 32px), line-height 1.2, letter-spacing -0.025em): Section titles (h2). Each section gets one.
- **Title** (Inter 600, 18px, line-height 1.3, letter-spacing -0.01em): Subsection headings (h3). Within-section structure.
- **Body** (Inter 400, 1.0625rem / ~17px, line-height 1.6): Prose text in summaries, gap cards, decision option descriptions. Tables do not use body type.
- **Table Body** (Inter 400, 0.875rem / 14px, line-height 1.45): Table cell content. Slightly smaller than body; tables are dense reference material, not reading text.
- **Label / Eyebrow** (JetBrains Mono 400, 11px, uppercase, letter-spacing 0.06–0.08em): Section eyebrows, table column headers, chip text, footer, header metadata. All metadata passes through monospace.
- **Code Inline** (JetBrains Mono, 0.82em of surrounding size): Inline command names, class names, file paths. Rendered in a Proof Copy pill with Hairline border.

**The Monospace Gatekeeping Rule.** If it's a label, a number in a data role, a command name, a status tag, or any piece of metadata, it passes through JetBrains Mono. Prose never appears in monospace. The distinction between sans and mono is the distinction between argument and evidence.


## 4. Elevation

This system is flat. No shadows exist anywhere in the document. Depth is communicated entirely through the 2-point lightness step between `--canvas` (99%) and `--canvas-soft` (97%), reinforced by a `--hairline` border at 89% lightness.

The elevation vocabulary has three levels:
1. **Ground** (`press-white`, 99%): The page. Table rows at rest.
2. **Surface** (`proof-copy`, 97%): Raised elements — code blocks, pre elements, table headers (sticky, so visually above rows), info callouts, phase info panels.
3. **Border** (`hairline`, 89%): The structural edge that separates ground from surface when a lightness step alone is insufficient.

**The Shadow Embargo.** No `box-shadow` appears in this document except within the Mermaid diagram renderer's default output (not controlled by this system). Adding a shadow to any component in this system is prohibited. If an element needs more presence, increase its border weight or use a colored border from the fidelity or layer taxonomy.


## 5. Components

Components in this system are **quiet and load-bearing**. They carry information without announcing themselves. A layer chip identifies without decorating. A fidelity cell signals without shouting. A phase accordion reveals without performance.

### Fidelity Cells

The primary data-carrying component. A full table cell, background-filled, not a chip or badge.

- **Direct** (green): `background: oklch(89% 0.07 145)`, `color: oklch(28% 0.12 145)`, `font-weight: 500`
- **Adapted** (amber): `background: oklch(91% 0.08 90)`, `color: oklch(30% 0.10 75)`, `font-weight: 500`
- **Bridge** (orange): `background: oklch(88% 0.07 48)`, `color: oklch(28% 0.12 38)`, `font-weight: 500`
- **Gap** (red): `background: oklch(88% 0.05 18)`, `color: oklch(28% 0.10 12)`, `font-weight: 500`

### Layer Chips

Pill-shaped, icon-leading, monospace text. Five color variants (Agents, MCP, Hooks, Skills, CLI) plus two backend variants (Beads, GitHub). Icon is a Material Symbol at 13px.

- Shape: `border-radius: 20px`, `padding: 3px 8px 3px 5px` (asymmetric — icon needs less left padding than text)
- Text: JetBrains Mono 10px, uppercase, letter-spacing 0.04em
- Each variant: background at 96% lightness, border at ~78% lightness, text at ~32% lightness (all at matching chroma/hue)

### Priority Chips

Outline-only pills. No background fill. Three variants using border-color and text-color only.

- **High (L)**: border `oklch(70% 0.04 300)`, text `oklch(38% 0.08 300)` — soft violet
- **Med (M)**: border `oklch(70% 0.06 145)`, text `oklch(32% 0.10 145)` — green
- **Low (S)**: border `var(--hairline)`, text `var(--ink-muted)` — neutral

### Size Chips

Inline tag following a task title. Outline only, muted, smallest possible footprint.

- `border: 1px solid var(--hairline)`, `color: var(--ink-muted)`, `border-radius: 20px`, `padding: 1px 7px`
- JetBrains Mono 10px, uppercase. Values: S, M, L, XL.

### Phase Accordion (`<details>` element)

List of collapsible phase sections. Marker is a monospace `+` / `−` character — not a chevron icon. Summary row uses Inter 600, 1rem. Each phase is separated by a single `--hairline` border.

- Closed: `+` at left in `var(--ink-muted)`; summary bold text
- Open: `−` replaces `+`; content area padded `0 0 24px 32px` (aligned past the marker)
- Blocked phase: summary carries a `.phase-tag.blocked` chip with `border: 1px solid var(--cell-orange-ink)`, `color: var(--cell-orange-ink)` — the only place orange appears in non-cell context

### Coverage Status Inline

Inline span used in table cells. Icon (Material Symbol) + text, both colored.

- Full: `var(--cell-green-ink)` — check_circle icon
- Partial: `var(--cell-yellow-ink)` — adjust icon
- None: `var(--cell-red-ink)` — do_not_disturb_on icon

### Info Callout (`.phase-info`)

Used at the top of opened phase sections to provide architectural context. Not a card.

- `background: var(--canvas-soft)`, `border: 1px solid var(--hairline)`, `border-radius: 8px`, `padding: 12px 14px`
- Inter 400, 0.8125rem, `color: var(--ink-mid)`, line-height 1.5
- No heading, no icon, no border accent. It is a block of contextual text, nothing more.

### Table Header Row

Sticky. JetBrains Mono 11px, uppercase, letter-spacing 0.06em, `color: var(--ink-muted)`. Background `var(--canvas)` — same as page, so it disappears into the surface when not scrolled.

**The No-Chrome Rule.** No component in this system uses `border-left` or `border-right` as an accent stripe. No glassmorphism. No drop shadows. No gradient fills. If an element needs chromatic emphasis, use a full background tint from the established semantic palette.


## 6. Do's and Don'ts

### Do
- **Do** use fidelity cell colors (Direct Green, Adapted Amber, Bridge Orange, Gap Red) exclusively to signal mapping fidelity. Never borrow these colors for other purposes.
- **Do** run all labels, table headers, eyebrows, chip text, command names, and numeric metadata through JetBrains Mono. The sans/mono split is the system's primary hierarchy signal.
- **Do** keep Inter at weights 600–800 for headings. At smaller sizes (below 16px), Inter 400 or 500 only.
- **Do** add new sections using the established section rhythm: `72px` vertical padding, `eyebrow` in monospace above the `h2`, content below.
- **Do** add new layer types using the existing chip pattern: assign a hue, derive background at 96% lightness, border at ~78%, text at ~32%, same chroma as existing chips.
- **Do** use `--canvas-soft` (97%) as the background for any elevated container (code block, info panel, pre element). The 2-point lightness step is the elevation system.
- **Do** keep the fidelity key visible above any table that uses fidelity cells. The traffic light is only useful if its legend is on-screen.

### Don't
- **Don't** render this like GitHub Flavored Markdown — no plain-list tables, no undifferentiated rows, no heading-only hierarchy. This is a precision reference document, not a README.
- **Don't** introduce the Notion or Confluence wiki aesthetic: no emoji-led bullet lists, no pastel callout card grids, no soft-rounded everything, no generic SaaS wiki feel.
- **Don't** add `box-shadow` to any component. The Shadow Embargo is absolute.
- **Don't** use `border-left` or `border-right` greater than 1px as a colored accent stripe on any element.
- **Don't** use gradient text (`background-clip: text`). Emphasis via weight or size only.
- **Don't** add a "decorative" section — no hero metrics, no illustration panels, no ornamental color blocks. Every visual element carries data or structure.
- **Don't** use the fidelity traffic-light hues (green/amber/orange/red) outside of fidelity cells and coverage-status chips. These colors are a vocabulary; borrowing one to mean something else corrupts the signal.
- **Don't** use the layer taxonomy hues (violet/teal/amber/green/gray) outside of layer chips and the layer legend. Five hues for five layers — no spillover.
- **Don't** add new top-level section types without a corresponding semantic color or structural marker from the established vocabulary. Unnamed zones have no visual grammar.
