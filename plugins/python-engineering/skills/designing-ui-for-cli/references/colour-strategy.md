# Colour Strategy for TUI

A four-level commitment axis for choosing how much colour a CLI surface carries. Adapted from impeccable's `SKILL.md` "Color" section and `reference/colorize.md` for terminal palettes.

## Anchor rule

**Pick the level BEFORE picking colours.** The strategy is a commitment to dosage; the specific hues come second. Reversing the order produces colour-by-association rather than colour-by-function.

## The four levels

### Restrained

Tinted neutrals + one accent ≤10%. Product default; brand minimalism.

The "≥10% accent" rule applies ONLY to Restrained — the other three levels exceed it on purpose. Do not collapse every design to Restrained by reflex.

**TUI substitutions:**

- Terminal-default text colour + one accent (Rich `cyan` or `magenta`, or TCSS `$accent`)
- Status colours (green `success`, yellow `warning`, red `error`) are semantic and **do not count toward the 10% accent budget** — they have a separate, non-decorative role
- Examples: most subcommand-driven CLIs (`git`, `kubectl`, `terraform`); the default state for any product-CLI

### Committed

One saturated colour carries 30–60% of the surface. Brand default for identity-driven pages.

**TUI substitutions:**

- Brand colour anchors headers + primary panel borders + splash glyph
- Examples: `bun` orange in titles, first column, and active widget borders; `pnpm` amber in the same roles; `uv` purple
- Used on identity surfaces (install scripts, top-level CLI welcome, brand-led one-shot tools)

### Full palette

3–4 named roles, each used deliberately. Brand campaigns; product data viz.

**TUI substitutions:**

- Dashboards in the style of `btop`, `lazygit`, `k9s`
- Each colour carries category meaning — CPU vs MEM vs NET; pod-state classes (Running / Pending / Failed / Succeeded)
- Explicit TCSS variable → category mapping required; colours are not interchangeable
- More than four named roles produces the rainbow-vomit failure mode — stop at four

### Drenched

The surface IS the colour. Brand heroes, campaign pages.

**TUI substitutions:**

- Full-screen branded splash, marketing CLI demos
- Restricted to one screen — welcome or outro, never sustained
- Terminal is a working surface, not a billboard
- Almost always brand-cli register; almost never appropriate for product-cli

## Register doctrine

SOURCE: `colorize.md` lines 7-14 (impeccable 3.0.7).

**Brand-CLI:** palette IS voice. Pick a strategy first per the four levels above and follow its dosage. Committed, Full palette, and Drenched deliberately exceed the ≤10% rule; that rule is Restrained only. Unexpected combinations are allowed; a dominant colour can own the surface when the chosen strategy calls for it.

**Product-CLI:** semantic-first and almost always Restrained. Accent colour is reserved for primary action, current selection, and state indicators. Not decoration. Every colour has a consistent meaning across every subcommand.

## The 60-30-10 rule

SOURCE: `color-and-contrast.md` lines 36-42 (impeccable 3.0.7).

About **visual weight**, not pixel count:

- **60%** — terminal default text + neutrals (background, default foreground, dim text)
- **30%** — secondary border styles, dim text, inactive states
- **10%** — accent for primary action, focus, active selection

The common mistake: using the accent everywhere because it is "the brand colour." Accents work *because* they are rare. Overuse kills their power.

Status colours (success / warning / error) are semantic and **do not count toward the 10% accent budget**.

## Constraint pragma

Terminal palettes are bounded by emulator support. Always specify a 16-colour fallback alongside the truecolor target.

```text
Truecolor target:   $accent: oklch(70% 0.15 280)   (TCSS, when supported)
16-colour fallback: $accent: magenta               (Rich named, always works)
```

Tools running in CI buffers, plain `xterm`, or `TERM=dumb` see only the fallback. Test the fallback path explicitly — do not assume truecolor.

## WCAG contrast matrix

SOURCE: `color-and-contrast.md` lines 47-55 (impeccable 3.0.7).

| Content type | AA minimum | AAA target |
|---|---|---|
| Body text | 4.5:1 | 7:1 |
| Large text (18px+ or 14px bold equivalent — use for PyFiglet headings) | 3:1 | 4.5:1 |
| UI components, icons, status glyphs | 3:1 | 4.5:1 |
| Non-essential decorations | none | none |

Test against likely terminal backgrounds: `#000`, `#1c1c1c` (common dark), `#fff`, `#f5f5f5` (common light). A palette that passes only on the developer's preferred theme fails the contrast gate.

The placeholder-text gotcha: dim text used as a "muted" cue still needs 4.5:1 against the background. Most light-grey-on-white dim styling fails WCAG.

## Dangerous colour combinations

SOURCE: `color-and-contrast.md` lines 58-66 (impeccable 3.0.7), with TUI examples.

| Combination | Failure mode | TUI example |
|---|---|---|
| Light grey on white | The #1 accessibility fail | Rich `dim white` text on a light terminal background |
| Grey text on coloured background | Washed out and dead on colour | `dim white` on a coloured panel border fill |
| Red on green (or vice versa) | 8% of men cannot distinguish | ANSI-16 `red` status next to `green` status without shape difference |
| Blue on red | Vibrates visually | `blue` text on a `red` error panel |
| Yellow on white | Almost always fails contrast | `bright_yellow` warning on a light terminal |
| Thin light text on images | Unpredictable contrast | Dim text overlaid on a `pyfiglet` filled-character banner |

Never use pure `#000` for large areas. Pure gray and pure black do not exist in nature; real shadows and surfaces always have a colour cast. Where truecolor is available, use a near-black with chroma 0.005-0.01 toward the brand hue. Where only ANSI-16 is available, the named `black` is acceptable.

## Status by shape, not colour alone

Status indicators must be distinguishable without colour. Use a glyph in column 0 plus a label; colour reinforces but does not carry the signal.

```text
[OK]   build succeeded
[WARN] deprecated flag --foo
[FAIL] connection refused
```

vs. colour-only (fails for colourblind users and `NO_COLOR=1` runs):

```text
build succeeded          (green)
deprecated flag --foo    (yellow)
connection refused       (red)
```

The shape-first form survives `NO_COLOR=1`, monochrome terminals, and screen-reader-via-terminal modes. It costs three to five characters of width per row; that is the price of inclusion.

## Cross-references

- Theme decision (dark / light / auto / high-contrast): see `./theme-decision.md`
- Register decision (brand-cli vs product-cli): see `./register-decision.md`
- AI slop reflex check (category-driven palette traps): see `./ai-slop-test.md`
- Audit dimension covering contrast and `NO_COLOR`: see `./audit-checklist.md`
