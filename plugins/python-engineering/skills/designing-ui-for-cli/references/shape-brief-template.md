# Shape Brief Template for TUI

A structured artifact that guides CLI/TUI implementation through discovery, not guesswork. Adapted from impeccable's `reference/shape.md` 3-phase shape command.

The brief is design planning only — it does NOT contain code. It produces the thinking that makes code good, then hands off to implementation.

## Philosophy

Most AI-generated CLIs fail not because of bad code, but because of skipped thinking. They jump to "here's a Rich panel" without asking "what is the user trying to accomplish?" This template inverts that: understand deeply first, so implementation is precise.

## Phase 1: Discovery Interview

Do NOT write any code or make any design decisions during this phase. The only job is to understand the feature deeply enough to make excellent design decisions later.

This is a required interaction, not optional guidance. Ask the questions in conversation, adapting based on answers. Do not dump them all at once; have a natural dialogue. STOP and call the AskUserQuestion tool to clarify.

### Interview cadence

Discovery must include at least one user-answer round unless PRODUCT.md, DESIGN.TUI.md / DESIGN.md, or an already-confirmed brief directly answers the needed design inputs. With a sparse prompt, do **not** synthesize a complete brief for confirmation on the first response.

- Use the harness's structured question tool when one exists. Otherwise, ask directly in chat and stop.
- Ask **2-3 questions per round**, then wait for answers.
- Treat PRODUCT.md and DESIGN.TUI.md / DESIGN.md as anchors; they reduce repeated questions but do **not** replace shape for craft. Shape is task-specific.
- Round 1 **covers**: purpose, audience/context, and success or emotional outcome.
- Round 2 **covers**: content/data/states and scope/fidelity.
- Round 3 **covers**: visual direction, constraints, and anti-goals when still unresolved.

### Purpose & Context

- What is this feature for? What problem does it solve?
- Who specifically will use it? (Not "users"; be specific: role, context, frequency)
- What does success look like? How will you know this feature is working?
- What's the user's state of mind when they reach this feature? (Rushed? Exploring? Anxious? Focused?)

### Content & Data

- What content or data does this feature display or collect?
- What are the realistic ranges? (Minimum, typical, maximum, e.g., 0 items, 5 items, 500 items)
- What are the edge cases? (Empty state, error state, first-time use, power user)
- Is any content dynamic? What changes and how often?

### Design Direction

Force a visual decision on three fronts. Skip anything PRODUCT.md or DESIGN.TUI.md / DESIGN.md already answers; ask only what's missing.

- **Colour strategy for this surface.** Pick one: Restrained / Committed / Full palette / Drenched. Can override the project default if the surface earns it (e.g. a Drenched welcome splash inside an otherwise Restrained product). See [colour-strategy.md](./colour-strategy.md).
- **Theme via scene sentence.** Write one sentence of physical context for this surface: who uses it, where, under what ambient light, in what mood. The sentence forces dark vs light vs auto vs high-contrast. If it doesn't, add detail until it does. See [theme-decision.md](./theme-decision.md).
- **Two or three named anchor references.** Specific products, brands, objects. Not adjectives like "modern" or "clean". For TUI, name actual CLIs (`btop`, `lazygit`, `bun`, `gh`, `k9s`) — not "developer tool aesthetic".

### Scope

Always ask. Sketch quality and shipped quality are different outputs; do not guess between them.

- **Fidelity.** Sketch / mid-fi / high-fi / production-ready?
- **Breadth.** One subcommand / a flow / a whole surface?
- **Interactivity.** Static output / interactive prompt / Textual full-screen app?
- **Time intent.** Quick exploration, or polish until it ships?

Scope answers are task-scoped. Do not write them to PRODUCT.md or DESIGN.TUI.md / DESIGN.md; carry them through the design brief only.

### Constraints

- Are there technical constraints? (Python version, framework, performance budget, terminal-emulator support)
- Are there content constraints? (Localisation, dynamic text length, user-supplied content)
- Width range and tier requirements? (80 / 100 / 120 / ≥160 cells)
- Accessibility requirements beyond NO_COLOR and non-TTY fallback?

### Anti-Goals

- What should this NOT be? What would be a wrong direction?
- What's the biggest risk of getting this wrong?

## Phase 1.5: Visual Direction Probe

**Skipped for TUI work.** Terminal output is not viable for image-generation probes — terminal cells, text styles, and ANSI palettes are not produced by image-generation tools, and rasterised mockups are not faithful to the cell-grid medium. The brief proceeds without probes.

This skip is intentional and not a fallback. Do not request the user install image-generation tooling; do not generate web mocks as a proxy for terminal output. Move directly to Phase 2.

## Phase 2: Design Brief

After the interview, synthesise everything into a structured design brief. Present it to the user for explicit confirmation before considering this run complete. Stop after asking for confirmation; do not proceed to implementation in the same response unless the user has already approved the brief.

### Brief Structure

**1. Feature Summary** (2-3 sentences)
What this is, who it's for, what it needs to accomplish.

**2. Primary User Action**
The single most important thing a user should do or understand here.

**3. Design Direction**
Colour strategy (Restrained / Committed / Full palette / Drenched) + the theme scene sentence + 2-3 named anchor references (specific CLIs, not adjectives). Reference PRODUCT.md and DESIGN.TUI.md / DESIGN.md where they already answer, and note any per-surface overrides.

**4. Scope**
Fidelity, breadth, interactivity, and time intent from the Scope section of the interview. Task-scoped; these do not persist beyond the brief.

**5. Layout Strategy**

- **Width tier.** Which of 80 / 100 / 120 / ≥160 cells is the primary target. Primary commands MUST render readably at 80 cells; wider tiers are progressive enhancement.
- **Textual layout type.** `vertical` / `horizontal` / `grid` / `dock` (or "plain Rich console" if not running under Textual).
- **Spatial hierarchy.** What gets emphasis, what's secondary, how information flows down the cell grid. Describe the visual hierarchy and rhythm, not specific TCSS rules.

**6. Key States**
List every state the feature needs. For each, note what the user needs to see and feel:

- **default** — the normal happy path
- **empty** — no data, first-time use, nothing to show
- **loading** — only when the operation is >200ms; describe spinner, progress text, or streamed output
- **error** — failure mode; exit code, stderr message, recovery hint
- **end** — success / clean exit; what the final frame looks like
- **cancellation** — Ctrl-C handling; what gets cleaned up, what gets reported
- **non-TTY** — piped output behaviour; ANSI stripped, progress suppressed, line-oriented output

**7. Interaction Model**
How users interact with this feature. Keybindings, prompt cadence, subcommand flow, focus order. What happens on Tab, Enter, Esc, Ctrl-C? What feedback do they get? What's the flow from invocation to completion?

**8. Content Requirements**
What copy, labels, empty-state messages, error messages, and microcopy are needed. Note any dynamic content and its realistic ranges. Specify:

- **stdout vs stderr separation.** Data on stdout; status, progress, and errors on stderr. Pipeable output stays on stdout only.
- **Verbosity levels mapped to content.** What appears at default, at `-v`, at `-vv`. What `--quiet` suppresses.

**9. Recommended References**
List the `references/*.md` files the implementer should load for this brief. Select from the Stage 3 section of the SKILL.md Reference Loading Guide by matching the library stack identified in Section 4 (scope/libraries). Do not list all references — only those matching the actual library scope.

**10. Open Questions**
Anything unresolved that the implementer should resolve during build.

### ASCII fidelity inventory

Adapted from impeccable's mock fidelity inventory in `reference/craft.md` lines 96-108. Before implementation, inventory the visible ingredients of the brief that must survive into code:

- **Status symbol set** — exact glyphs and their meanings (e.g. `✓` success, `✗` error, `…` pending, `▸` active). Status symbols always occupy column 0.
- **Panel border style** — `round` / `thick` / `heavy` / `double` / `dashed` / `ascii` / `none`, and which panels carry borders versus which are borderless.
- **Header glyph** — the dominant masthead character or sequence (e.g. PyFiglet font name, Unicode block character, or "no header").
- **Splash-screen layout if any** — for brand-CLI surfaces only: composition, focal element, dwell time, skip behaviour.

For each ingredient, decide how it will be implemented: TCSS variable, Rich style string, PyFiglet rendering, ASCII art file, or explicitly accepted omission.

Treat the inventory as a **north star**, not a frame-by-frame trace. If the live result lacks the brief's major visible ingredients, the implementation is wrong.

---

## Worked example: a database migration tool

A filled-out brief illustrating each section. The example is for `dbmig`, a hypothetical CLI for applying schema migrations.

**1. Feature Summary**
A subcommand `dbmig apply` that runs pending migrations against a target database. Used by backend engineers during deploys and by SREs during incident remediation. Must report pass/fail per migration and a final summary.

**2. Primary User Action**
See, at a glance, which migrations applied successfully and which failed — without reading the full log.

**3. Design Direction**

- Colour strategy: Restrained. Terminal default + one accent (Rich `cyan`) on subcommand title and per-row migration name. Status colours green / yellow / red for pass / skip / fail are semantic and outside the accent budget.
- Theme scene sentence: "An on-call SRE running migrations from a laptop terminal at 2am during a production incident, eyes tired, attention split across Slack and a runbook." Forces dark.
- Anchor references: `alembic`, `flyway`, `kubectl rollout status`. Not "modern" or "clean".

**4. Scope**
High-fi, production-ready. One subcommand surface. Non-interactive output (Rich console, no Textual app). Polish until ships.

**5. Layout Strategy**

- Width tier: 80 cells primary, 100/120 progressive enhancement (more columns visible).
- Textual layout type: not applicable — plain Rich console output.
- Spatial hierarchy: header line → per-migration row table (status column, name column, duration column) → final summary panel.

**6. Key States**

- **default** — header, then streaming per-migration rows, then summary panel.
- **empty** — "No pending migrations. Database is at revision abc123." (single line, exit 0).
- **loading** — for individual migrations >200ms: per-row spinner with elapsed time; for the run as a whole: streaming output, no overall progress bar (count not knowable in advance for some backends).
- **error** — failed migration row turns red; subsequent migrations skip with yellow `skipped`; summary panel shows fail count and the first failed migration name; exit code 1; stderr carries the SQLSTATE and error text.
- **end** — summary panel: applied count, skipped count, failed count, total duration; exit 0 on success.
- **cancellation** — Ctrl-C during a migration: rolls back the current migration, prints "Cancelled. Rolled back {name}.", exit code 130; rolled-back migrations show as `cancelled` (yellow).
- **non-TTY** — ANSI stripped, no spinner, line-oriented `STATUS NAME DURATION` per migration, summary as plain text. Stdout stays parseable.

**7. Interaction Model**
Non-interactive. Keybindings: Ctrl-C cancels. No prompts on the happy path. `--dry-run` flag prints the planned migration list without applying. `--yes` skips the confirmation gate when running against a production DSN.

**8. Content Requirements**

- stdout: per-migration result line, summary panel.
- stderr: progress dots while connecting, SQL error text on failure, the runbook URL hint on failure.
- Verbosity: default = one line per migration + summary. `-v` adds elapsed time per migration. `-vv` adds the SQL statements as they run. `--quiet` shows only the final summary line.
- Empty-state copy: "No pending migrations. Database is at revision {rev}."
- Error-message formula: what failed, why (SQLSTATE), how to fix (link to runbook).

**9. Recommended References**

- `render-patterns.md` — Rich Table and Panel composition for the per-row output and final summary.
- `colour-strategy.md` — confirms Restrained level and the status-colour-outside-budget rule.
- `theme-decision.md` — confirms the dark default decision is sentence-driven, not reflex.
- `typer-ui-patterns.md` — `--dry-run` / `--yes` / `-v` / `-vv` / `--quiet` flag wiring.

**10. Open Questions**

- Does the underlying migration library expose a callable list of pending migrations before apply, or only a streaming generator? Affects whether a count-based progress bar is feasible at any verbosity.
- Should `--quiet` honour stderr suppression, or only stdout? Default is stdout only.

### ASCII fidelity inventory (for the example)

- Status symbol set: `✓` applied, `↷` skipped, `✗` failed, `⊘` cancelled, `…` running. Column 0 always.
- Panel border style: `round` for the summary panel; no border on the per-migration rows.
- Header glyph: plain bold text `dbmig apply`. No PyFiglet, no decorative border. Aligns with Restrained / product-CLI register.
- Splash-screen layout: none. Product-CLI register; splash on every invocation is banned.

Implementation decisions for each ingredient: status symbols → Rich style strings on a fixed mapping table; summary panel → `rich.panel.Panel(border_style="cyan")`; header → `rich.text.Text("dbmig apply", style="bold cyan")`; no PyFiglet dependency.

---

## User-confirmation gate

STOP and call the AskUserQuestion tool to clarify. Ask for explicit confirmation of the brief before finishing. If the user disagrees with any part, revisit the relevant discovery questions. A shape run is incomplete until the brief is confirmed.

Once confirmed, the brief is complete and is handed off to implementation.
