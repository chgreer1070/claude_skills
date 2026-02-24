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

## Skill Validation vs Packaging

**Validation: YES** — Validate skills to ensure quality:

- YAML frontmatter properly formatted
- Required fields present (name, description, tools, model)
- File references correct and target files exist
- Directory structure valid

**Packaging: NO** — Skills in this repository are for local use. They are already in their final location. Do not package skills into .zip files — it creates unnecessary files and serves no purpose for local development.
