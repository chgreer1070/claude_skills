---
name: claude-plugins-reference-2026
description: Reference guide for Claude Code plugins system (January 2026). Use when creating, distributing, or understanding plugins, plugin.json schema, marketplace configuration, bundling skills/commands/agents/hooks/MCP/LSP, or plugin validation.
---

# Claude Code Plugins System - Complete Reference (January 2026)

Plugins bundle multiple Claude Code capabilities (skills, commands, agents, hooks, MCP servers, LSP servers) into distributable packages.

---

## plugin.json Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Plugin description with trigger keywords",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "commands": ["./commands"],
  "agents": [
    "./agents/agent-one.md",
    "./agents/agent-two.md"
  ],
  "skills": ["./skills/skill-one", "./skills/skill-two"],
  "hooks": "./hooks.json",
  "mcpServers": "./.mcp.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/"
}
```

### Required Fields

| Field  | Type   | Constraints                                 |
| ------ | ------ | ------------------------------------------- |
| `name` | string | Kebab-case, unique identifier, max 64 chars |

### Recommended Fields

| Field         | Type   | Purpose                                  |
| ------------- | ------ | ---------------------------------------- |
| `version`     | string | Semantic versioning (X.Y.Z)              |
| `description` | string | Max 1024 chars, include trigger keywords |
| `author`      | object | `{name, email?, url?}`                   |
| `homepage`    | string | Documentation URL                        |
| `repository`  | string | Source code URL                          |
| `license`     | string | SPDX identifier                          |
| `keywords`    | array  | Marketplace discoverability              |

### Component Paths

| Field          | Type          | Format Requirements                                       |
| -------------- | ------------- | --------------------------------------------------------- |
| `commands`     | string/array  | Directory path or array of paths                          |
| `agents`       | array         | **MUST be array of individual .md file paths** (see note) |
| `skills`       | string/array  | Directory paths containing SKILL.md                       |
| `hooks`        | string/object | Path to hooks.json or inline object                       |
| `mcpServers`   | string/object | Path to .mcp.json or inline object                        |
| `lspServers`   | string/object | Path to .lsp.json or inline object                        |
| `outputStyles` | string        | Directory path                                            |

<agents_critical_note>

**CRITICAL: agents field validation**

Despite documentation suggesting `agents` accepts "string|array", the validator **rejects directory strings**.

The model MUST use an array of individual file paths:

```json
// WRONG - validation fails with "agents: Invalid input"
"agents": "./agents/"
"agents": "./agents"

// CORRECT - validation passes
"agents": [
  "./agents/code-reviewer.md",
  "./agents/test-runner.md"
]
```

**Verified**: 2026-01-23 via `claude plugin validate` command.

</agents_critical_note>

---

## Directory Structure

```
plugin-name/
├── .claude-plugin/           # REQUIRED metadata directory
│   └── plugin.json          # REQUIRED manifest (only file here)
├── commands/                 # Slash command files (.md)
├── agents/                   # Agent definitions (.md)
├── skills/                   # SKILL.md directories
│   ├── skill-one/
│   │   ├── SKILL.md
│   │   └── references/
│   └── skill-two/
│       └── SKILL.md
├── hooks.json               # Hook configurations
├── .mcp.json                # MCP server definitions
├── .lsp.json                # LSP server configurations
├── scripts/                 # Helper scripts for hooks
├── LICENSE
├── CHANGELOG.md
└── README.md
```

**Critical**: `.claude-plugin/` contains ONLY `plugin.json` - never put components here.

---

## Distribution Methods

### Marketplace (Recommended)

```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "Team Name",
    "email": "team@example.com"
  },
  "metadata": {
    "description": "Marketplace description",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "plugin-one",
      "source": "./plugins/plugin-one"
    },
    {
      "name": "plugin-two",
      "source": { "source": "github", "repo": "owner/repo" }
    }
  ]
}
```

### Plugin Sources

| Type          | Format                                         |
| ------------- | ---------------------------------------------- |
| Relative path | `"./plugins/my-plugin"`                        |
| GitHub        | `{ "source": "github", "repo": "owner/repo" }` |
| Git URL       | `{ "source": "url", "url": "https://..." }`    |

### Installation Commands

```bash
# Add marketplace
/plugin marketplace add owner/repo
/plugin marketplace add https://gitlab.com/company/plugins.git
/plugin marketplace add ./local-marketplace

# Install plugin
/plugin install plugin-name@marketplace-name
/plugin install plugin-name@marketplace-name --scope project
/plugin install plugin-name@marketplace-name --scope local

# Manage
/plugin enable plugin-name
/plugin disable plugin-name
/plugin update plugin-name
/plugin uninstall plugin-name
```

---

## Installation Scopes

| Scope     | Settings File                 | Use Case                     |
| --------- | ----------------------------- | ---------------------------- |
| `user`    | `~/.claude/settings.json`     | Personal, global (default)   |
| `project` | `.claude/settings.json`       | Team, shared via git         |
| `local`   | `.claude/settings.local.json` | Project-specific, gitignored |
| `managed` | `managed-settings.json`       | Enterprise, admin-controlled |

---

## Bundled Capabilities

### Commands

- Location: `commands/` directory
- Format: Markdown with frontmatter
- Namespace: `/plugin-name:command-name`

### Agents

- Location: `agents/` directory
- Format: Markdown with frontmatter
- Auto-delegation by Claude

### Skills

- Location: `skills/` with `SKILL.md`
- Auto-activation by Claude
- Progressive disclosure support

### Hooks

- Location: `hooks.json` or `plugin.json` inline
- Events: PreToolUse, PostToolUse, Stop, etc.
- Use `${CLAUDE_PLUGIN_ROOT}` for paths

### MCP Servers

- Location: `.mcp.json`
- Types: http, stdio
- Auto-start when plugin enabled

### LSP Servers

- Location: `.lsp.json`
- Requires binary installation
- Code intelligence features

---

## Environment Variables

| Variable                | Description                       |
| ----------------------- | --------------------------------- |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory |
| `${CLAUDE_PROJECT_DIR}` | Project root directory            |

---

## Validation

### Validation Workflow

The model MUST validate plugins before installation or distribution:

```bash
# Step 1: Validate plugin manifest
claude plugin validate ./my-plugin

# Step 2: If validation passes, test loading
claude --plugin-dir ./my-plugin

# Step 3: Install to marketplace
/plugin install my-plugin@marketplace-name
```

### Validation Commands

```bash
# CLI (from terminal)
claude plugin validate .
claude plugin validate ./path/to/plugin

# In Claude Code session
/plugin validate .
/plugin validate ./path/to/plugin
```

### Validation Output

**Success with warnings**:

```text
Validating plugin manifest: ./my-plugin/.claude-plugin/plugin.json

⚠ Found 1 warning:

  ❯ author: No author information provided. Consider adding author details

✔ Validation passed with warnings
```

**Failure**:

```text
Validating plugin manifest: ./my-plugin/.claude-plugin/plugin.json

✘ Found 1 error:

  ❯ agents: Invalid input

✘ Validation failed
```

### Common Validation Errors

| Error Message             | Cause                                        | Fix                                                                |
| ------------------------- | -------------------------------------------- | ------------------------------------------------------------------ |
| `agents: Invalid input`   | Used directory string instead of file array  | Change `"agents": "./agents/"` to `"agents": ["./agents/file.md"]` |
| `name: Required`          | Missing name field                           | Add `"name": "plugin-name"`                                        |
| `Invalid JSON syntax`     | Malformed JSON (missing comma, extra quotes) | Validate JSON with `python3 -m json.tool plugin.json`              |
| `commands: Invalid input` | Incorrect path format                        | Ensure paths start with `./`                                       |

### Pre-Validation Checklist

Before running `claude plugin validate`, verify:

- [ ] `.claude-plugin/plugin.json` exists and contains valid JSON
- [ ] `name` field is present and kebab-case
- [ ] All paths start with `./`
- [ ] `agents` field is an array of individual `.md` file paths
- [ ] Referenced directories and files exist
- [ ] No path traversal (`../`) in any path

### Testing Without Installation

```bash
# Load plugin for current session only
claude --plugin-dir ./my-plugin

# Load multiple plugins
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

---

## Enterprise Features

```json
{
  "enabledPlugins": {
    "code-formatter@company-tools": true
  },
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": { "source": "github", "repo": "org/plugins" }
    }
  },
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme-corp/approved-plugins" }
  ]
}
```

| Setting                              | Effect            |
| ------------------------------------ | ----------------- |
| `strictKnownMarketplaces: []`        | Complete lockdown |
| `strictKnownMarketplaces: [sources]` | Allowlist only    |
| `strictKnownMarketplaces: undefined` | No restrictions   |

---

## Constraints

- Plugins copied to cache, not used in-place
- Cannot reference files outside plugin directory (`../` fails)
- LSP servers require separate binary installation
- All paths must be relative, start with `./`
- Path traversal (`..`) not allowed
- Scripts must be executable (`chmod +x`)
- Reserved marketplace names: `claude-code-marketplace`, `anthropic-plugins`

---

## Private Repository Authentication

| Service   | Environment Variable         | Scope             |
| --------- | ---------------------------- | ----------------- |
| GitHub    | `GITHUB_TOKEN` or `GH_TOKEN` | `repo`            |
| GitLab    | `GITLAB_TOKEN` or `GL_TOKEN` | `read_repository` |
| Bitbucket | `BITBUCKET_TOKEN`            | read access       |

---

## Sources

- [Create Plugins](https://code.claude.com/docs/en/plugins)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Discover and Install Plugins](https://code.claude.com/docs/en/discover-plugins)
