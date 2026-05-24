# Plugin Deployment Model

## How Claude Code plugins are installed

Claude Code plugins are distributed as self-contained bundles. When a plugin is installed from the marketplace or via `claude plugin install`, it is copied into a plugin cache directory:

```
~/.claude/plugins/cache/<marketplace>/<plugin-name>/<version>/
```

This cache directory has no connection to the source repository. There is no git root. There is no `.claude/utilities/`, no `.claude/skills/`, no `plugins/` directory from the development repository. The plugin exists as an isolated bundle at a path entirely separate from where it was authored.

The environment variable `${CLAUDE_PLUGIN_ROOT}` resolves to the installed plugin's cache directory — not the development repository root.

## What scripts inside a plugin can access

Scripts bundled inside a plugin (`plugins/<name>/scripts/*.py`) can only reliably access:

- Files within their own plugin bundle (`${CLAUDE_PLUGIN_ROOT}/...`)
- Standard system paths (`/usr/lib`, standard Python packages, etc.)
- User home directory paths (`~/.claude/settings.json`, etc.) when those are expected to exist independently of the plugin

They **cannot** access:

- `.claude/utilities/` — this path only exists in the development repository
- `.claude/skills/` — same
- Sibling plugin directories — plugins are installed independently and cannot assume other plugins are present or at a known path
- The development repository root or any path relative to it

## The cross-plugin-boundary constraint

Any utility shared between a plugin script and a `.claude/` script requires that utility to exist in both deployment contexts separately. A single shared file at `.claude/utilities/rich_utils.py` is reachable from `.claude/` scripts running in the user's home directory — but is not reachable from plugin scripts running in the plugin cache.

**Consequence**: when a function exists in both `.claude/` scripts and plugin scripts, it cannot be deduplicated into a single shared file. The correct solutions are:

1. **Duplicate within each plugin** — copy the utility into each plugin's own `scripts/` directory. Accept the duplication. The function is small and stable.
2. **Publish as an installable package** — if the shared utility is large or changes frequently, publish it to PyPI and declare it as a PEP 723 dependency in each script.
3. **Accept the duplication for plugin scripts, deduplicate for `.claude/` scripts** — `.claude/` scripts sharing a utility at `.claude/utilities/` is valid; plugin scripts cannot participate.

## Identifying the deployment context of a script

When analysing a script during codebase analysis or architecture, determine which context it runs in:

| Script location | Deployment context | Can access `.claude/utilities/`? |
|---|---|---|
| `.claude/skills/*/scripts/*.py` | User-level skill — runs from the user's `.claude/` directory | Yes — `.claude/utilities/` is a sibling |
| `.claude/utilities/*.py` | User-level utility — runs from the user's `.claude/` directory | Yes — same directory |
| `plugins/*/scripts/*.py` | Plugin bundle — runs from plugin cache after installation | No — no connection to development repo |

## Implications for grooming and architecture

Any backlog item proposing to extract a shared utility across the plugin boundary must flag this constraint explicitly. The RT-ICA should include a condition:

> "All affected scripts share the same deployment context" | AVAILABLE or MISSING

If scripts span `.claude/` and `plugins/`, this condition is MISSING — the item must be re-scoped before planning.

SOURCE: Claude Code plugin caching behaviour — `plugins/development-harness/CLAUDE.md` plugin caching section; `plugin-creator:claude-plugins-reference-2026` skill.
