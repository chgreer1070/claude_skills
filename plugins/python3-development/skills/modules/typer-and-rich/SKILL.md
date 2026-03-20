---
name: typer-and-rich
description: Best practices and anti-patterns for Typer and Rich CLI applications — prevents common AI mistakes like Rich table wrapping in non-TTY, incorrect console output handling, testing Rich-formatted output, and integration pitfalls. Load alongside the typer and rich API reference skills when building CLI applications.
user-invocable: false
---

# Typer and Rich Best Practices

Correctness patterns for building CLI applications with Typer and Rich, focused on non-TTY environments and common failure modes. For API reference, load the dedicated skills:

- `Skill(skill="python3-development:typer")` — Typer CLI framework API reference
- `Skill(skill="python3-development:rich")` — Rich terminal UI API reference

## Non-TTY and Programmatic Usage

See [./references/non-tty-patterns.md](./references/non-tty-patterns.md) — Console behavior without TTY, width defaults, force_terminal vs width, Progress/Live in non-interactive contexts, environment variables.

## Rich Table Width Measurement

See [./references/rich-tables.md](./references/rich-tables.md) — width measurement pattern that prevents wrapping at 80 columns in non-TTY output.

## Testing Patterns

See [./references/testing-patterns.md](./references/testing-patterns.md) — capturing Rich output in pytest, CliRunner with Rich, snapshot testing, common assertion mistakes.

## Exception Chain Prevention

See [./references/exception-handling.md](./references/exception-handling.md) — Typer exception chain prevention with `AppExit` and `AppExitRich` patterns. Read when implementing error handling in Typer CLI applications.

## Working Script Examples

See [./assets/typer_examples/](./assets/typer_examples/index.md) — working scripts demonstrating non-TTY display solutions. Read when troubleshooting display and layout of terminal applications.

See [./assets/python-cli-demo.py](./assets/python-cli-demo.py) — complete working CLI demo with all patterns (PEP 723 shebang, Typer + Rich integration, modern Python 3.11+, async processing). Read when creating a new CLI tool as a reference implementation.
