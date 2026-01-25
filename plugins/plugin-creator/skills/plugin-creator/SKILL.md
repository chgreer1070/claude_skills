---
name: plugin-creator
description: 'Complete workflow for creating Claude Code plugins including planning, research, design, implementation, and verification phases. Use when creating new plugins, writing plugin.json manifests, creating SKILL.md files, or structuring plugin directories. Integrates with rt-ica for prerequisite verification and verify skill for completion checks.'
---

# Claude Code Plugin Creator

This skill guides you through creating a complete Claude Code plugin with proper planning, research, design, and verification phases.

---

## Phase 0: RT-ICA Prerequisite Check

<prerequisite_checkpoint>

**STOP. Before creating any plugin, perform RT-ICA assessment.**

Invoke the `rt-ica` skill to verify prerequisites:

```text
RT-ICA SUMMARY
==============

Goal:
- Create a Claude Code plugin for [purpose]

Success Output:
- Functional plugin that [specific outcome]

Conditions (reverse prerequisites):
1. Purpose clarity | Requires: Clear problem statement | Why: Determines plugin scope
2. Target users | Requires: Who will use this | Why: Shapes UX decisions
3. Component selection | Requires: Skills vs Commands vs Agents vs Hooks | Why: Architecture
4. Existing solutions | Requires: Check for similar plugins | Why: Avoid duplication
5. Source material | Requires: Documentation/APIs to encode | Why: Content accuracy
6. Verification method | Requires: How to test the plugin works | Why: Quality gate

Verification:
- [Check each condition: AVAILABLE / DERIVABLE / MISSING]

Decision:
- [APPROVED / BLOCKED]
```

**IF BLOCKED**: Request missing information before proceeding.

**IF APPROVED**: Continue to Phase 1.

</prerequisite_checkpoint>

---

## Phase 1: Research

Before writing any files, gather information:

### 1a. Check Existing Plugins

```bash
# Search for similar plugins in this repository
ls plugins/ | grep -i [keyword]

# Check if capability already exists
grep -r "[capability]" plugins/*/skills/*/SKILL.md
```

### 1b. Identify Source Material

For skills that encode domain knowledge:

- Official documentation URLs
- API references
- Best practices guides
- Existing code patterns

**Verification requirement**: Every factual claim in the skill must cite its source.

### 1c. Determine Component Types

| Need                     | Component  | When to Use                             |
| ------------------------ | ---------- | --------------------------------------- |
| Modify Claude's behavior | Skill      | Domain knowledge, workflows, patterns   |
| User-invoked action      | Command    | `/command` style interactions           |
| Delegatable specialist   | Agent      | Sub-agent for Task tool                 |
| Automatic triggers       | Hook       | Pre/post tool execution, session events |
| External tools           | MCP Server | API integrations, databases             |

---

## Phase 2: Design

### 2a. Plugin Architecture

Document before implementing:

```text
PLUGIN DESIGN
=============

Name: [kebab-case-name]
Purpose: [one sentence]
Target Users: [who benefits]

Components:
- Skills: [list with brief purpose]
- Commands: [list with brief purpose]
- Agents: [list with brief purpose]
- Hooks: [list with trigger and action]
- MCP Servers: [list with capabilities]

Dependencies:
- External tools: [list]
- Other plugins: [list]
- Environment: [requirements]
```

### 2b. Skill Content Planning

For each skill, outline:

1. **Activation triggers** - When should Claude load this?
2. **Core instructions** - What behavior changes?
3. **Reference material** - What detailed docs are needed?
4. **Examples** - What patterns should be shown?

---

## Phase 3: Implementation

### Step 1: Create Directory Structure

```text
my-plugin/
├── .claude-plugin/           # REQUIRED: metadata directory
│   └── plugin.json          # REQUIRED: only file in .claude-plugin/
├── commands/                 # Optional: slash command files (.md)
├── agents/                   # Optional: agent definitions (.md)
├── skills/                   # Optional: skill directories
│   └── my-skill/
│       ├── SKILL.md
│       └── references/      # Optional: detailed reference docs
├── hooks/                    # Optional: hook configurations
│   └── hooks.json
├── .mcp.json                # Optional: MCP server definitions
├── scripts/                 # Optional: helper scripts for hooks
├── LICENSE
└── README.md
```

**Critical Rule**: `.claude-plugin/` contains ONLY `plugin.json`. All components go at plugin root.

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#plugin-directory-structure>

### Step 2: Create plugin.json

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

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#plugin-manifest-schema>

### Step 3: Create Skills

#### SKILL.md Template

```yaml
---
name: my-skill
description: 'Detailed description including trigger keywords. Use when [situation1], [situation2], or when user mentions [keywords].'
allowed-tools: Read, Grep, Glob
---

# Skill Title

[Core instructions - keep under 500 lines]

## Section with Detailed Guidance

[Instructions for specific scenarios]

For complete reference, see [reference.md](./references/reference.md)

---

## Sources

- [Source 1](https://example.com/docs) - What this covers
- [Source 2](https://example.com/api) - What this covers
```

#### Frontmatter Fields

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

**YAML Warning**: Do NOT use multiline indicators (`>-`, `|`) for descriptions.

**Source**: <https://code.claude.com/docs/en/skills.md>

### Step 4: Add Hooks (Optional)

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

| Event              | When                   | Has Matcher |
| ------------------ | ---------------------- | ----------- |
| `PreToolUse`       | Before tool executes   | Yes         |
| `PostToolUse`      | After tool succeeds    | Yes         |
| `Stop`             | Claude finishes        | No          |
| `UserPromptSubmit` | User submits prompt    | No          |
| `SessionStart`     | Session begins/resumes | Yes         |
| `SessionEnd`       | Session ends           | No          |

**Source**: <https://code.claude.com/docs/en/hooks>

---

## Phase 4: Verification

<verification_checkpoint>

**STOP. Before claiming the plugin is complete, invoke the `verify` skill.**

### Verification Checklist

```text
VERIFICATION SUMMARY:
Task Type: FEATURE
Works Check: [PASS/FAIL]
Quality Gates: [PASS/FAIL]
Honesty Check: [PASS/FAIL]

EVIDENCE:
```

### Plugin-Specific Checks

- [ ] `plugin.json` has valid JSON syntax
- [ ] `name` field matches directory name
- [ ] `plugin.json` is in `.claude-plugin/` directory (not plugin root)
- [ ] Components (commands, skills, hooks) are at plugin root
- [ ] All paths are relative and start with `./`
- [ ] Skills have valid YAML frontmatter (no multiline indicators)
- [ ] Hook scripts are executable (`chmod +x`)
- [ ] All factual claims cite sources
- [ ] No orphaned reference files (all linked from SKILL.md)

### Test Locally

```bash
claude --plugin-dir ./my-plugin
```

### Debug Mode

```bash
claude --debug --plugin-dir ./my-plugin
```

**Only mark complete when all checks pass with evidence.**

</verification_checkpoint>

---

## Phase 5: Documentation & Distribution

### Generate README

Use the `plugin-docs-writer` agent:

```text
Task(
  agent="plugin-docs-writer",
  prompt="Generate README.md for the plugin at ./plugins/my-plugin"
)
```

### Assess Quality

Use the `plugin-assessor` agent before distribution:

```text
Task(
  agent="plugin-assessor",
  prompt="Assess the plugin at ./plugins/my-plugin for marketplace readiness"
)
```

### Distribution Options

**Option 1: Plugin Marketplace (Recommended)**

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

**Option 2: GitHub Direct**

```bash
/plugin install my-plugin@github-username/repo-name
```

**Source**: <https://code.claude.com/docs/en/plugin-marketplaces.md>

---

## Related Skills

| Skill                           | Purpose                                |
| ------------------------------- | -------------------------------------- |
| `rt-ica`                        | Pre-planning prerequisite verification |
| `verify`                        | Post-implementation completion checks  |
| `claude-plugins-reference-2026` | Complete plugin.json schema            |
| `claude-skills-overview-2026`   | Complete SKILL.md format               |
| `claude-hooks-reference-2026`   | Hook configuration details             |

| Agent                | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `plugin-assessor`    | Structural validation and quality scoring |
| `plugin-docs-writer` | README.md generation                      |

---

## Sources

All information verified against official Claude Code documentation (January 2026):

- [Create Plugins](https://code.claude.com/docs/en/plugins) - Overview and quickstart
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) - Complete schema
- [Skills Documentation](https://code.claude.com/docs/en/skills) - SKILL.md format
- [Hooks Reference](https://code.claude.com/docs/en/hooks) - Hook configuration
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - Distribution
