---
name: designing-ui-for-cli
description: "Use before writing any CLI display/output code — produces a UI design plan covering colour palette, status indicators, output hierarchy, error display, empty states, and non-TTY behaviour for apps using Typer, Rich, Textual, or Questionary. Triggers on CLI UI/UX tasks: output formatting, display design, interactive prompts, visual consistency, TUI layout, progress display, or dashboard design."
user-invocable: false
---
# CLI UI Design

Before any display or output code is written, produce a UI design plan and get alignment. This skill governs how output is structured and presented consistently across the whole CLI application.

## Golden Path — Required Before Implementing Any Display Code

Follow this sequence every time:

**Step 1 — Identify libraries in scope**

Determine which of the following are used (check pyproject.toml and imports):

- **Typer** — command definition, help text, argument types
- **Rich** — console output, tables, panels, progress, syntax highlighting
- **Textual** — full TUI applications, reactive widgets, keyboard navigation
- **Questionary** — interactive prompts, menus, confirmations

**Step 2 — Load relevant reference files**

Load only the files that match the in-scope libraries (see Reference Loading Guide below).

**Step 3 — Produce a UI design plan**

Write a concise plan covering all six of:

1. **Colour palette** — primary, secondary, accent, error, warning, success (use Rich named colours or Textual CSS variables — no hex unless Textual CSS)
2. **Status indicators** — one symbol + colour per state (running, success, warning, error, skipped); scannable by shape alone without reading
3. **Output hierarchy** — what goes to stdout vs stderr; how verbose/quiet modes change output; Rich markup level
4. **Error display pattern** — how validation errors, runtime errors, and unexpected exceptions are formatted and where they appear
5. **Empty state handling** — what the user sees when a list/table has no rows, a search returns nothing, or a resource doesn't exist yet
6. **Non-TTY behaviour** — what happens when stdout is piped or redirected: strip colours, fall back to plain text, suppress progress bars

**Step 4 — Get alignment before implementing**

Present the plan. Do not write any display code until the plan is confirmed.

## Reference Loading Guide

Load reference files based on what is in scope. Do not load files for libraries not in use.

### Always load when Rich is in scope

- `./references/render-patterns.md` — tables, panels, progress, status, themes, dashboard layout
- `./references/rich-extras.md` — multi-task progress, syntax highlighting, tree displays
- `./references/rich-gaps.md` — pager, console.rule, console.screen, escape(), Table.grid, MofNCompleteColumn

### Always load when Questionary is in scope

- `./references/questionary-patterns.md` — prompt types, Style, Choice, validation
- `./references/questionary-advanced.md` — form(), unsafe_ask, conditional prompts, password/path/rawselect

### Always load when Textual is in scope (load all — Textual requires the full picture)

- `./references/textual-basics.md` — App structure, reactive, querying, events
- `./references/textual-interactivity.md` — key bindings, mouse, focus, custom messages, actions
- `./references/textual-layout.md` — layout types, sizing, docking, scrolling
- `./references/textual-styling.md` — CSS selectors, colours, borders, pseudo-classes
- `./references/textual-widgets.md` — all widget types, custom widgets
- `./references/textual-advanced.md` — @on decorator, reactive advanced, @work, screen modes, testing
- `./references/textual-builder-skill.md` — textual-builder workflow guide
- `./references/textual-tui-skill.md` — TUI skill with workers, modals, screens, testing
- `./references/tui-layouts.md`, `./references/tui-styling.md`, `./references/tui-widgets.md`, `./references/tui-official-guides-index.md` — aperepel TUI reference

### Load when Typer output or help text is in scope

- `./references/typer-ui-patterns.md` — output hierarchy, rich_markup_mode, help panels, pretty_exceptions

### Load when animated or branded splash screens are needed

- `./references/animation-patterns.md` — PyFiglet splash screens, ASCII art, animated loading

### Load when Pydantic models carry CLI data

- `./references/model-patterns.md` — Pydantic v2 models for CLI data
- `./references/pydantic-cli-patterns.md` — pydantic-settings, ValidationError formatting, FilePath

### Load for design principles and what to avoid

- `./references/design-principles.md` — progressive disclosure, status at a glance
- `./references/anti-references.md` — what to avoid

## Design Principles

### Information Density Without Intimidation

Progressive disclosure: simple by default, powerful when explored.

- Default output: one status line per item — pass/fail/warning with count
- Verbose mode (`-v`): per-item detail
- Debug mode (`-vv`): full context, raw values

Never dump everything at once. Let the user pull depth they need.

### Status at a Glance

Status indicators must be scannable in under one second using shape, colour, and position — no reading required.

| State | Symbol | Rich colour | Rule |
|---|---|---|---|
| Running | `⠸` (spinner) | `cyan` | Animated while active |
| Success | `✓` | `green` | Always leftmost in row |
| Warning | `!` | `yellow` | Same position as success |
| Error | `✗` | `red` | Same position as success |
| Skipped | `–` | `dim` | Visually quieter than success |

- Shape alone (not just colour) must distinguish states — colour-blind safe
- Position consistent: status symbol always in column 0 of a row
- No reading required: the pattern is scannable before comprehension kicks in

## Anti-References — What to Avoid

See `./references/anti-references.md` for full detail. Summary:

- **Generic SaaS rounded cards/gradients** — Rich panels are not web cards; avoid decorating every output block with a box border
- **Hacker aesthetic** — no green-on-black, no Matrix-style animations, no `lolcat` colouring
- **Electron bloat feel** — CLI output must feel instant; avoid multi-second spinners on operations that complete in milliseconds; never add artificial delay
- **Overly playful** — no excessive emoji, no mascot ASCII art in regular command output, no animation where static text suffices

## Code Quality

Load `./references/code-quality-patterns.md` for naming, function design, and error handling conventions when implementing display logic.

## Dependencies

```bash
uv add typer textual pydantic tinydb questionary pyfiglet python-dateutil
```
