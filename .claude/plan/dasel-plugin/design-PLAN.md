# Design Plan: dasel Plugin

Date: 2026-02-19
Status: PENDING VERIFICATION

## Directory Structure

```text
plugins/dasel/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── data-explorer.md      (haiku)
│   ├── dasel-guide.md        (haiku)
│   └── data-analyst.md       (sonnet)
├── skills/
│   ├── dasel-reference/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── selectors-and-syntax.md
│   │       ├── functions.md
│   │       └── format-patterns.md
│   ├── data-exploration/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── format-recipes.md
│   ├── data-transformation/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── transformation-patterns.md
│   └── setup/
│       └── SKILL.md
├── scripts/
│   └── install_dasel.py
└── hooks/
    ├── hooks.json
    └── session-start-dasel-check.js
```

## Tasks (12)

Task 1: Scaffold + plugin.json
Tasks 2-11: All parallel after task 1
Task 12: Final validation after all complete

## Parallelism

Tasks 2-11 can ALL run in parallel after Task 1.
Task 12 depends on all others.

## Agent-Skill Bindings

- data-explorer (haiku): skills: dasel-reference, data-exploration
- dasel-guide (haiku): skills: dasel-reference
- data-analyst (sonnet): skills: dasel-reference, data-transformation

## Key Constraints

- Skills: NO name: field (Claude Code bug)
- Tools: comma-separated strings, NOT YAML arrays
- agents in plugin.json: array of individual file paths
- All paths start with ./
- v3-only syntax
- SHA256 from GitHub API digest field
