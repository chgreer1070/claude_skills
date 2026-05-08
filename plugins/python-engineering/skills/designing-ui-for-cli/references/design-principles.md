# Design principles

Strategic principles for CLI / TUI work in this skill. Each rule below is load-bearing for the 7-stage workflow; violating any of them produces output that fails the AI slop test, the audit, or the polish checklist.

## Information density without intimidation

Power users want dense layouts with many terminals visible. Beginners need to not feel overwhelmed. Solve this with progressive disclosure: simple by default, powerful when you explore.

## Status at a glance

The core UX promise is "glance and know what's done." Status indicators must be scannable in under a second across many terminals. No reading required — use shape, colour, and position together. Never use shape alone (excludes screen-reader users) and never use colour alone (excludes colour-blind users and NO_COLOR pipelines).

## Density progression rule

Output verbosity is a stack with three named levels. Each level adds content; no level removes information from the level below.

| Level | Invocation | Content |
|---|---|---|
| Default | bare command | One line per item: status glyph, identifier, state. Suitable for piping; suitable for "is this done yet?" Shows what changed; suppresses what didn't. |
| Verbose | `-v` | Default plus per-item context: timing, source, target, action description. One screen per operation. |
| Debug | `-vv` | Verbose plus introspection: full paths, environment values, intermediate steps, decision rationale. Suitable for bug reports. |

Rules:

- Default mode must be useful on its own; `-v` is enrichment, not "now finally readable"
- A user who runs `-vv` accepts a wall of text; do not paginate or filter at this level
- Quiet mode (`--quiet` / `-q`) is a separate axis: it suppresses default-level chrome (banners, summaries) but still reports state changes and errors
- Pipe-detected mode (stdout is not a TTY) takes precedence over the verbosity level: ANSI is stripped, progress bars suppressed, output becomes line-oriented

## Status-position rule (The Status Column Rule)

Status symbols always occupy column 0 of a row. Position is the affordance.

- Column 0 = state (`✓`, `✗`, `⚠`, `…`, `▸`)
- Column 1 = identifier (the noun the row is about)
- Remaining columns = description, timing, target

Consequences of putting status anywhere other than column 0:

- Users cannot scan a column with their eye to find failures
- Filtering with `grep '^✗'` breaks
- Screen readers in linearised terminal mode lose the "this row is a failure" cue at the top of the announcement

This is a per-row rule. Multi-line output (e.g. an error block under a failed row) places the status glyph on the first line in column 0; subsequent lines indent past column 0 and carry no glyph.

## Scene-sentence theme rule

Dark vs. light is never a default. Before choosing, write one sentence of physical scene — who uses this, where, under what ambient light, in what mood. If the sentence doesn't force the answer, it's not concrete enough. Add detail until it does. For the full method, worked TUI examples, and light-terminal considerations, see [theme-decision.md](./theme-decision.md).

## Match implementation complexity to the aesthetic vision

Maximalism needs elaborate code; minimalism needs precision. A Drenched splash screen demands disciplined cell-grid alignment, careful frame timing, and a Unicode-fallback strategy — minimalism in the implementation produces a maximalist *look* that crumbles on any non-default terminal. A Restrained product CLI demands precise typographic spacing, exact column alignment, and consistent status vocabulary — sloppy implementation produces a "minimalist" look that reads as unfinished.

Interpret creatively. Vary across projects; never converge on the same choices. The skill is capable of extraordinary work. Don't hold back.

This principle is paired with the absolute ban on under-implementing: if the aesthetic vision calls for a Drenched welcome screen, do not ship a beige fallback "to be safe". Either commit to the implementation work or change the colour strategy in the shape brief.

## Cross-references

- [register-decision.md](./register-decision.md) — brand-CLI vs product-CLI register choice (drives which permissions and bans apply)
- [theme-decision.md](./theme-decision.md) — scene-sentence method, full TUI scene examples, light-terminal-default consideration
- [colour-strategy.md](./colour-strategy.md) — Restrained / Committed / Full / Drenched levels with TUI value mappings
- [anti-references.md](./anti-references.md) — match-and-refuse pattern table; the inverse of the principles above
- [ai-slop-test.md](./ai-slop-test.md) — two-altitude category-reflex check that the principles above are designed to pass
