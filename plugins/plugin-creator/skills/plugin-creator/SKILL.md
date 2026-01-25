---
name: plugin-creator
description: 'Step-by-step workflow for creating Claude Code plugins. Use when creating new plugins, writing plugin.json manifests, creating SKILL.md files, or structuring plugin directories. All information verified against official documentation.'
---

# Claude Code Plugin Creator

This skill guides you through creating a complete Claude Code plugin with verified, official documentation.

---

## Plugin Creation Workflow

### Step 1: Create Directory Structure

```text
my-plugin/
├── .claude-plugin/           # REQUIRED: metadata directory
│   └── plugin.json          # REQUIRED: only file in .claude-plugin/
├── commands/                 # Optional: slash command files (.md)
├── agents/                   # Optional: agent definitions (.md)
├── skills/                   # Optional: skill directories
│   └── my-skill/
│       └── SKILL.md
├── hooks/                    # Optional: hook configurations
│   └── hooks.json
├── .mcp.json                # Optional: MCP server definitions
├── scripts/                 # Optional: helper scripts for hooks
├── LICENSE
└── README.md
```

**Critical Rule**: `.claude-plugin/` contains ONLY `plugin.json`. All components (commands, agents, skills, hooks) go at the plugin root.

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#plugin-directory-structure>

---

## Step 2: Create plugin.json

### Minimum Valid Manifest

```json
{
  "name": "my-plugin"
}
```

Only the `name` field is required.

### Recommended Manifest

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does and trigger keywords for discovery",
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/you"
  },
  "homepage": "https://docs.example.com/my-plugin",
  "repository": "https://github.com/you/my-plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "skills": ["./skills/my-skill"]
}
```

### All plugin.json Fields

| Field          | Type          | Required | Purpose                                  |
| -------------- | ------------- | -------- | ---------------------------------------- |
| `name`         | string        | Yes      | Kebab-case identifier, max 64 chars      |
| `version`      | string        | No       | Semantic versioning (X.Y.Z)              |
| `description`  | string        | No       | Max 1024 chars, include trigger keywords |
| `author`       | object        | No       | `{name, email?, url?}`                   |
| `homepage`     | string        | No       | Documentation URL                        |
| `repository`   | string        | No       | Source code URL                          |
| `license`      | string        | No       | SPDX identifier (MIT, Apache-2.0, etc.)  |
| `keywords`     | array         | No       | Discovery tags                           |
| `commands`     | string/array  | No       | Path(s) to command files                 |
| `agents`       | string/array  | No       | Path(s) to agent files                   |
| `skills`       | string/array  | No       | Path(s) to skill directories             |
| `hooks`        | string/object | No       | Hook config path or inline               |
| `mcpServers`   | string/object | No       | MCP config path or inline                |
| `lspServers`   | string/object | No       | LSP config path or inline                |
| `outputStyles` | string/array  | No       | Path(s) to output style files            |

**Path Rules**:

- All paths must be relative to plugin root
- All paths must start with `./`
- Custom paths supplement defaults, don't replace them

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#plugin-manifest-schema>

---

## Step 3: Create Skills (Optional)

Skills are the primary way to add capabilities. Create a `SKILL.md` file in a named directory.

### Minimal SKILL.md

```yaml
---
description: What this skill does and when to use it
---

Your instructions here...
```

### Full SKILL.md Template

```yaml
---
name: my-skill
description: 'Detailed description of what this skill does. Include trigger keywords for when Claude should auto-invoke. Use when [situation1], [situation2], or when user mentions [keywords].'
argument-hint: '[expected-arguments]'
allowed-tools: Read, Grep, Glob
model: claude-sonnet-4-20250514
context: fork
agent: Explore
user-invocable: true
disable-model-invocation: false
---

# Skill Title

Your instructions here. Keep under 500 lines.

For detailed reference, see [reference.md](./reference.md)
```

### All Frontmatter Fields

| Field                      | Type         | Default         | Purpose                                      |
| -------------------------- | ------------ | --------------- | -------------------------------------------- |
| `name`                     | string       | directory name  | Display name (lowercase, hyphens, max 64)    |
| `description`              | string       | first paragraph | When to use; Claude uses for auto-invocation |
| `argument-hint`            | string       | none            | Autocomplete hint (e.g., `[issue-number]`)   |
| `allowed-tools`            | string/array | none            | Tools without permission prompts             |
| `model`                    | string       | default         | Model when skill is active                   |
| `context`                  | string       | none            | `fork` for isolated subagent                 |
| `agent`                    | string       | general-purpose | Subagent type when `context: fork`           |
| `user-invocable`           | boolean      | true            | `false` hides from `/` menu                  |
| `disable-model-invocation` | boolean      | false           | `true` prevents Claude auto-loading          |
| `hooks`                    | object       | none            | Hooks scoped to skill lifecycle              |

**YAML Warning**: Do NOT use multiline indicators (`>-`, `|`) for descriptions. They break parsing.

**Source**: <https://code.claude.com/docs/en/skills.md>

---

## Step 4: Add Hooks (Optional)

Hooks execute commands or prompts in response to events.

### hooks/hooks.json Example

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Hook Events

| Event              | When                   | Has Matcher |
| ------------------ | ---------------------- | ----------- |
| `PreToolUse`       | Before tool executes   | Yes         |
| `PostToolUse`      | After tool succeeds    | Yes         |
| `Stop`             | Claude finishes        | No          |
| `UserPromptSubmit` | User submits prompt    | No          |
| `SessionStart`     | Session begins/resumes | Yes         |
| `SessionEnd`       | Session ends           | No          |

### Exit Codes

| Code  | Behavior                               |
| ----- | -------------------------------------- |
| 0     | Success, stdout processed              |
| 2     | Blocking error, stderr shown to Claude |
| Other | Non-blocking error, logged only        |

**Environment Variables**:

- `${CLAUDE_PLUGIN_ROOT}` - Absolute path to plugin directory
- `${CLAUDE_PROJECT_DIR}` - Project root directory

**Source**: <https://code.claude.com/docs/en/hooks>

---

## Step 5: Test Locally

### Load Plugin During Development

```bash
claude --plugin-dir ./my-plugin
```

### Load Multiple Plugins

```bash
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

### Debug Mode

```bash
claude --debug --plugin-dir ./my-plugin
```

Shows plugin loading details, errors, and hook execution.

**Source**: <https://code.claude.com/docs/en/plugins.md#test-your-plugins-locally>

---

## Step 6: Validate

### Validation Checklist

- [ ] `plugin.json` has valid JSON syntax
- [ ] `name` field is present (only required field)
- [ ] `plugin.json` is in `.claude-plugin/` directory
- [ ] Components (commands, skills, hooks) are at plugin root, not in `.claude-plugin/`
- [ ] All paths are relative and start with `./`
- [ ] Hook scripts are executable (`chmod +x`)
- [ ] Skills have valid YAML frontmatter
- [ ] No YAML multiline indicators in descriptions

### Debug Command

```bash
claude --debug
```

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#debugging-and-development-tools>

---

## Step 7: Distribute

### Option 1: Plugin Marketplace (Recommended)

Create a `marketplace.json`:

```json
{
  "name": "my-marketplace",
  "repository": "https://github.com/owner/plugins-repo",
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "Plugin description"
    }
  ]
}
```

Users install with:

```bash
/plugin marketplace add owner/repo
/plugin install my-plugin@my-marketplace
```

### Option 2: GitHub Direct

Push to GitHub, users install with:

```bash
/plugin install my-plugin@github-username/repo-name
```

### Option 3: Local Path

```bash
claude plugin marketplace add ./marketplace.json
```

**Source**: <https://code.claude.com/docs/en/plugin-marketplaces.md>

---

## Quick Reference

### Create a New Plugin

```bash
# 1. Create structure
mkdir -p my-plugin/.claude-plugin my-plugin/skills/my-skill

# 2. Create manifest
cat > my-plugin/.claude-plugin/plugin.json << 'EOF'
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "skills": ["./skills/my-skill"]
}
EOF

# 3. Create skill
cat > my-plugin/skills/my-skill/SKILL.md << 'EOF'
---
description: What this skill does and when to use it
---

# My Skill

Instructions here...
EOF

# 4. Test
claude --plugin-dir ./my-plugin
```

---

## Related Skills

For detailed reference documentation:

- **Plugin schema details**: Activate `claude-plugins-reference-2026` skill
- **Skill format details**: Activate `claude-skills-overview-2026` skill
- **Hooks configuration**: Activate `claude-hooks-reference-2026` skill

---

## Sources

All information verified against official Claude Code documentation (January 2026):

- [Create Plugins](https://code.claude.com/docs/en/plugins) - Overview and quickstart
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) - Complete schema and validation
- [Skills Documentation](https://code.claude.com/docs/en/skills) - SKILL.md format
- [Hooks Reference](https://code.claude.com/docs/en/hooks) - Hook configuration
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - Distribution
