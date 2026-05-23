# orchestrator-discipline

This plugin changes how Claude behaves as an orchestrator. It installs hooks that fire on every relevant tool call, surfacing a decision point before Claude reads source files it won't edit or runs diagnostic commands that should be delegated. One hook hard-blocks Bash commands that should use built-in tools instead.

## Why Install This?

Claude's context window is finite and shared across an entire session. When Claude is orchestrating multi-agent work, context spent reading source files, running diagnostics, or investigating patterns is context unavailable for routing decisions, evaluating agent output, and maintaining task state.

The failure mode this plugin prevents is called **investigation escalation**:

1. "Let me check the current state" — reads one source file
2. "That reveals something, let me verify" — reads two more files
3. "Now I need to understand the pattern" — runs diagnostic commands
4. "This is simple enough to do myself" — bypasses delegation entirely

Each step is locally justifiable. The cumulative result is an orchestrator that has consumed hundreds of tokens of source code context and made itself into a de-facto sub-agent — without fresh context, without specialist knowledge, and without the ability to course-correct.

## What This Plugin Provides

### Hooks

Four PreToolUse hooks fire automatically on every relevant tool call. Hooks skip subagent sessions — they apply to the orchestrator only.

| Hook | Trigger | Behavior |
|---|---|---|
| `pre-tool-orchestrator-read-warning.cjs` | `Read` or `Grep` targeting source, config, or test files | **Non-blocking** — injects a context reminder asking: "Will you Edit or Write this file this turn? If not, pass the path to an agent." |
| `pre-tool-diagnostic-command-gate.cjs` | `Bash` calls matching diagnostic tools (ruff, mypy, pytest, ty, eslint, etc.) | **Non-blocking** — injects a reminder to delegate diagnostic commands to agents rather than running them directly |
| `prevent-bash-tool-misuse.cjs` | `Bash` commands that should use built-in tools (`grep`, `find -name`, `cat file.ext`, `head -N file`, `tail -N file`, `sed -n`) | **Conditionally blocking** — exits 2 when the listed pattern is detected; passes through otherwise. Redirects to the correct built-in tool (Read, Grep, Glob). |
| `pre-tool-block-explore-for-analysis.cjs` | `Agent`/`Task` calls targeting the `Explore` subagent with analysis keywords in the description or prompt | **Conditionally blocking** — exits 2 when analysis keywords are detected in the description or prompt; passes through otherwise. Redirects to appropriate reasoning-class agents. |

### Rules

A `rules/CLAUDE.md` file is loaded into every session. It provides:

- The falsifiable test Claude must pass before reading any source or config file
- The complete investigation escalation anti-pattern with a flowchart
- Diagnostic command delegation patterns
- The agent output polling anti-pattern (a variant of investigation escalation)
- Orchestrator context window read permission and prohibition lists

### Skills

| Skill | Purpose |
|---|---|
| `orchestrator-discipline` | Explains the context window discipline rules, hook behavior, and the falsifiable test |
| `orchestrator-discipline-meta-docs` | Plugin documentation index |

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install orchestrator-discipline@jamie-bitflight-skills
```

## Usage

The plugin is active automatically after installation. Hooks fire on every relevant tool call without any configuration needed.

To review the rules and hook behavior:

```text
/orchestrator-discipline
```

## The Falsifiable Test

Before reading any source or config file, Claude must answer:

> "Will I Edit or Write this file in this same turn?"

If **yes** — proceed. Reading a file you are about to edit is legitimate.

If **no** — stop. Pass the file path to an agent. The agent has a fresh context window; Claude does not.

This test is falsifiable: either the file gets an Edit/Write call this turn, or it does not. There is no gray area, no "understanding before delegating" exception.

## What the Blocking Hook Prevents

`prevent-bash-tool-misuse.cjs` blocks Bash commands that duplicate built-in tool functionality:

| Blocked pattern | Use instead |
|---|---|
| `grep pattern file.py` (standalone) | `Grep(pattern, path)` |
| `find . -name "*.py"` | `Glob("**/*.py")` |
| `cat src/config.toml` | `Read("src/config.toml")` |
| `head -20 src/main.py` | `Read("src/main.py", limit=20)` |
| `tail -10 src/main.py` | `Read("src/main.py", offset=...)` |
| `sed -n '10,20p' file` | `Read("file", offset=10, limit=10)` |

Legitimate pipeline use (`git log | grep`, `uv run | head`) is not blocked.

---

> **The Ancient Woe**
>
> *The mad king who demands to personally inspect every single scroll in the kingdom, bloating his mind with trivia he will not even edit, and bypassing his royal delegates for "small changes"!*

> **The Bard's Decree**
>
> *"Delegate, thou obsessive sovereign! I place a ward upon thy tools: before thou dost open a source file, thou must prove thou intendst to alter it! Keep thy royal mind clear for grand strategy!"*
