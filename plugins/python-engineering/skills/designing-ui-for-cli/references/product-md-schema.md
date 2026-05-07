# PRODUCT.md schema (TUI / CLI)

PRODUCT.md is the per-project strategic contract for a CLI or TUI. It answers who the tool is for, what it exists to do, and what it must never feel like. Visual decisions (palette, glyphs, border styles, panel layout) belong in `DESIGN.TUI.md` / `DESIGN.md`, not here.

This file is the question template for the inline interview that runs when PRODUCT.md is missing. After writing the file, re-run `scripts/load-design-context.py` so the fresh PRODUCT.md lands in conversation before resuming the original task.

## File layout

PRODUCT.md contains six fixed sections in this exact order. Header text must match character-for-character.

```markdown
# Product

## Register

product-cli

## Users
[Who they are, their context, the job to be done, and the operating context]

## Product Purpose
[What this CLI does, why it exists, what success looks like]

## Brand Personality
[Voice, tone, 3-word personality, emotional goals]

## Anti-references
[2-3 specific CLI tools the project must NOT feel like, plus the trait being avoided]

## Design Principles
[3-5 strategic principles derived from the conversation]

## Accessibility & Inclusion
[NO_COLOR support, non-TTY fallback, verbosity levels, colour-blind safety, screen-reader notes]
```

## Field rules

### Register

The Register field is a bare value. No prose, no commentary.

- `brand-cli` — design IS the moment. Surfaces include installer banners, demo recording surfaces, marketing CLI commands (`bun create`, `gh demo`), splash-on-first-run, scrolling welcome flows.
- `product-cli` — design SERVES the task. Surfaces include subcommand trees, persistent dashboards, settings panels, data tables, authenticated/configured flows.

Form a register hypothesis from repo signals before asking the user:

- Brand-CLI signals: installer banners, demo recording surfaces, marketing CLI commands (`bun create`, `gh demo`), splash-on-first-run, scrolling welcome flows.
- Product-CLI signals: subcommand trees, persistent dashboards, settings panels, data tables, authenticated/configured flows.

If the signal is split (e.g. a developer tool with a marketing-grade installer), ask the user which register describes the **primary** surface. The register can be overridden per task later; PRODUCT.md carries one default.

### Users

Includes who they are, the job to be done, and an explicit **Operating context** line:

- Shell (bash / zsh / fish / PowerShell / cmd).
- Terminal emulators expected (iTerm2, Alacritty, Windows Terminal, GNOME Terminal, tmux, plain xterm).
- TTY-vs-piped expectation (interactive only / piped only / both).
- Width range (e.g. 80–200 cells).
- Colour-support floor (16-colour / 256-colour / truecolor).

The operating context constrains every later visual decision; capture it before any design work begins.

### Product Purpose

What the CLI does, why it exists, what success looks like for the user. Strategic, not visual.

### Brand Personality

3-word personality, voice, tone, emotional goals. Domain-agnostic — the same personality framework applies whether the CLI ships data tables or marketing demos.

### Anti-references

Name 2–3 specific CLI tools the project must NOT feel like, plus the trait being avoided. Adjectives alone are not enough.

Examples:

- "Not lolcat-coloured" — rainbow ANSI as a personality substitute.
- "Not htop-style brutalist" — every cell screams; no rest for the eye.
- "Not cargo-installer-verbose" — wall of progress lines on every command.

Anti-references feed the AI slop test (see `ai-slop-test.md`) and the audit Anti-Patterns dimension.

### Design Principles

3–5 strategic principles like "practice what you preach", "show, don't tell", "expert confidence". NOT visual rules like "use OKLCH" or "magenta accent".

Hard rule: do NOT ask about colours, fonts, radii, or visual styling here. Those belong in DESIGN.TUI.md / DESIGN.md, not PRODUCT.md.

### Accessibility & Inclusion

Capture as concrete commitments, not aspirations:

- `NO_COLOR` — when set, the CLI emits no ANSI colour escapes; status conveyed by shape, prefix, or text.
- Non-TTY fallback — when stdout is not a TTY, ANSI is stripped, progress bars are suppressed, and output is line-oriented.
- `--quiet` / `--verbose` / `-v` / `-vv` levels — what each level shows and hides.
- Colour-blind safety — status conveyed by shape (`✓` / `✗` / `!` / `⏵`), not colour alone; tested for deuteranopia, protanopia, tritanopia.
- Terminal screen-reader limits — full-screen Textual layouts are not screen-reader friendly; document which surfaces fall back to line-oriented output for screen-reader users.

## Interview cadence

Run an interview before writing PRODUCT.md. Do not turn a one-sentence request into a complete inferred PRODUCT.md and ask for blanket confirmation.

- Ask 2–3 questions per round, then wait for answers.
- Use inferred answers as hypotheses or options, not as finished facts.

Round 1 — register confirmation, users and purpose, desired outcome:

1. Does the register hypothesis (`brand-cli` / `product-cli`) match the user's intent for this surface?
2. Who uses this CLI, in what shell and terminal, and what job are they completing?
3. What does success look like — what state is the user in after the command finishes?

Round 2 — brand personality, references, anti-references, accessibility:

1. Three words for the personality, plus 1–2 specific reference CLIs that feel right.
2. 2–3 specific CLI tools this must NOT feel like, and the trait being avoided.
3. Accessibility commitments: NO_COLOR, non-TTY, verbosity levels, colour-blind safety, screen-reader fallback.

After at least one real user-answer round, you may propose inferred answers, but the user must confirm them before you write PRODUCT.md.

## Minimum viable interview

Never synthesize PRODUCT.md from the original task prompt alone.

Cover at minimum: register confirmation, users and purpose with operating context, brand personality, anti-references, accessibility needs. Skip a question only when the answer is directly discoverable from repo docs and the user has confirmed the inferred value.

## After writing

Re-run the loader so the fresh PRODUCT.md lands in conversation:

```bash
uv run plugins/python-engineering/skills/designing-ui-for-cli/scripts/load-design-context.py
```

The loader's full JSON output must appear in the session before any subsequent stage runs. If PRODUCT.md was written as part of resuming a Shape (or later) task, resume at Shape with the freshly-loaded context — earlier outputs that were synthesized without PRODUCT.md are stale.

## Cross-references

- `design-md-schema.md` — visual contract; everything excluded from PRODUCT.md belongs here.
- `register-decision.md` — first-match-wins priority for register ambiguity.
- `ai-slop-test.md` — uses Anti-references for the second-altitude category-reflex check.
- `audit-checklist.md` — Anti-Patterns & Slop dimension references the Anti-references list.
