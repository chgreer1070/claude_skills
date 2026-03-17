---
paths:
  - "plugins/**/*"
  - ".claude-plugin/**/*"
---

# Plugin Development Workflows

## Local Testing Methods

**Option 1 - Session-based loading:**

```bash
claude --plugin-dir ./plugins/plugin-name
```

**Option 2 - Local marketplace:**

```bash
# One-time setup
/plugin marketplace add ./.claude-plugin/marketplace.json

# Install (--scope local keeps gitignored)
/plugin install plugin-name@jamie-bitflight-skills --scope local

# Toggle as needed
/plugin disable plugin-name@jamie-bitflight-skills
/plugin enable plugin-name@jamie-bitflight-skills
```

## Marketplace Maintenance Procedures

**Adding Plugin:**

1. Create structure under `plugins/`
2. Validate: `claude plugin validate plugins/plugin-name/`
3. Add entry to `.claude-plugin/marketplace.json` plugins array (MANDATORY)
4. Bump `metadata.version` minor version (MANDATORY)
5. Validate JSON: `python3 -m json.tool .claude-plugin/marketplace.json`

**Removing Plugin:**

1. Remove `plugins/plugin-name/` directory
2. Remove entry from `.claude-plugin/marketplace.json` (MANDATORY)
3. Bump `metadata.version` (major if breaking, minor if experimental) (MANDATORY)
4. Validate JSON

**Version Bumping:**

- Major (X.0.0): Breaking changes, removed widely-used plugins
- Minor (1.X.0): New plugins, significant additions
- Patch (1.0.X): Bug fixes, documentation only

Complete procedures: [CONTRIBUTING.md](./CONTRIBUTING.md)

## Prerequisite Skills for Plugin Work

Before modifying any plugin file (`plugin.json`, agents, skills, hooks), load these two reference skills:

- `plugin-creator:claude-plugins-reference-2026` — current Claude Code plugin schema, frontmatter fields, and component auto-discovery rules
- `plugin-creator:claude-skills-overview-2026` — current Claude Code skills schema and conventions

**Reason**: Editing plugin files without loading these skills risks schema violations and auto-discovery breakage. Session 2026-03-17 demonstrated this — adding an `agents` key to `plugin.json` without understanding auto-discovery semantics silently dropped 17 of 19 agents.

## plugin.json Auto-Discovery Rules

Claude Code auto-discovers components from default locations within a plugin directory. The `agents`, `skills`, and `commands` keys in `plugin.json` exist ONLY for declaring components in non-default locations.

**Default auto-discovered locations:**

- `agents/` — all `.md` files
- `skills/` — all skill directories containing `SKILL.md`
- `commands/` — all `.md` files
- `hooks/hooks.json` — hooks manifest

```mermaid
flowchart TD
    Q{Are ALL components in default locations?}
    Q -->|Yes — agents/ skills/ commands/ hooks/hooks.json| Omit["Omit agents/skills/commands keys from plugin.json<br>Auto-discovery registers everything"]
    Q -->|No — some components are in non-default paths| Declare["Declare ONLY the non-default paths<br>⚠️ Declaring a subset overrides auto-discovery<br>Unlisted components become invisible"]
    Omit --> Done([All components visible])
    Declare --> Warn["List EVERY component in that key<br>not just the non-default ones"]
    Warn --> Done
```

**Incident record (2026-03-17):** `python3-development` plugin had:

```json
"agents": ["./agents/t0-baseline-capture.md", "./agents/tn-verification-gate.md"]
```

Result: only 2 of 19 agents were registered. The other 17 were invisible to Claude Code because declaring a subset in `agents` overrides auto-discovery — the declared list becomes the complete list.

**Fix**: Remove the `agents` key entirely when all agents are in `agents/`. Auto-discovery registers all of them.

## Skill Validation vs Packaging

**Validation: YES** — Validate skills to ensure quality:

- YAML frontmatter properly formatted
- Required fields present (name, description, tools, model)
- File references correct and target files exist
- Directory structure valid

**Packaging: NO** — Skills in this repository are for local use. They are already in their final location. Do not package skills into .zip files — it creates unnecessary files and serves no purpose for local development.
