# orchestrator-discipline

Enforces orchestrator context window discipline via PreToolUse hooks and rules. Prevents the
orchestrator from reading source files it will not edit, running diagnostic commands that
should be delegated, and bypassing delegation with "small change" rationalizations.

## What it does

Installs two non-blocking PreToolUse hooks that fire automatically on every tool call. The
source file read warning fires on `Read` and `Grep` targeting source or config files and
asks whether you will actually edit the file this turn. The diagnostic command gate fires on
`Bash` calls matching tools like `ruff`, `pytest`, or `mypy` and reminds you to delegate
instead. A `rules/CLAUDE.md` file is also loaded into every session with the full
delegation constraint definitions, investigation escalation anti-pattern documentation, and
diagnostic command delegation patterns.

## Skills

- `orchestrator-discipline` — Explains the context window discipline rules, hook behavior,
  and how to apply the falsifiable test before every source file read

## Installation

```bash
/plugin install orchestrator-discipline@jamie-bitflight-skills
```

## Usage

The plugin is active automatically after installation. Hooks fire on every relevant tool
call and inject a context reminder — they do not block legitimate operations.

To review the rules manually:

```text
/orchestrator-discipline
```

---

> **The Ancient Woe**
>
> *The mad king who demands to personally inspect every single scroll in the kingdom, bloating his mind with trivia he will not even edit, and bypassing his royal delegates for "small changes"!*

> **The Bard's Decree**
>
> *"Delegate, thou obsessive sovereign! I place a ward upon thy tools: before thou dost open a source file, thou must prove thou intendst to alter it! Keep thy royal mind clear for grand strategy!"*
