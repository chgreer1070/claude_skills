# Plugin Creator Scripts

Utility scripts for maintaining Claude Code plugins, skills, agents, and commands.

---

## fix_tool_formats.py

**Purpose**: Fix invalid tool format patterns in Claude Code frontmatter.

### What It Fixes

Claude Code requires tool specifications in YAML frontmatter to use **comma-separated string format**:

```yaml
tools: Read, Grep, Glob, Bash
allowed-tools: Read, Grep, Glob
```

This script automatically converts two invalid formats:

#### 1. YAML List Format → Comma-Separated String

**Before (Invalid)**:

```yaml
allowed-tools:
  - Read
  - Glob
  - Bash
```

**After (Valid)**:

```yaml
allowed-tools: Read, Glob, Bash
```

#### 2. JSON Array Format → Comma-Separated String

**Before (Invalid)**:

```yaml
tools: ["Read", "Grep", "Glob", "Write"]
```

**After (Valid)**:

```yaml
tools: Read, Grep, Glob, Write
```

### Usage

```bash
# Run from anywhere - scans all .claude directories recursively
python3 plugins/plugin-creator/scripts/fix_tool_formats.py
```

### Scan Locations

The script recursively scans:

- `~/.claude/agents/**/*.md`
- `~/.claude/commands/**/*.md`
- `~/.claude/skills/**/SKILL.md`
- `~/repos/**/agents/*.md` (within `.claude` directories)
- `~/repos/**/commands/*.md` (within `.claude` directories)
- `~/repos/**/skills/*/SKILL.md` (within `.claude` directories)

Excludes:

- `.venv/` directories
- `node_modules/` directories
- Files outside `.claude` directories

### Why This Matters

**Context Pollution Prevention**: Invalid formats written by Claude in earlier sessions become "evidence" in future searches, creating a feedback loop where AI learns incorrect patterns from its own mistakes.

**Official Format**: According to [Claude Code documentation](https://code.claude.com/docs/en/sub-agents.md), the `tools` field is:

- **Type**: `string` (comma-separated)
- **Not**: JSON array or YAML list

### Output Example

```
Scanning for markdown files with invalid tool formats...
Found 448 files to check

✓ Fixed: /home/user/.claude/commands/gsd/verify-work.md
✓ Fixed: /home/user/repos/project/.claude/commands/agent-workflow.md

Fixed: 28 files
Skipped: 420 files (no changes needed)
Total: 448 files
```

---

## create_plugin.py

**Purpose**: Interactive plugin scaffolding tool that creates a new Claude Code plugin with proper structure.

### What It Creates

- `.claude-plugin/` directory
- `plugin.json` with validated schema
- Optional `skills/`, `agents/`, `commands/` directories
- Proper plugin structure following official schema

### Usage

```bash
# Interactive mode - prompts for all details
uv run plugins/plugin-creator/scripts/create_plugin.py

# The script will ask for:
# - Plugin name (kebab-case)
# - Description
# - Author information
# - Which directories to create
```

### Validation

The script runs `claude plugin validate` internally before reporting success to ensure the created plugin structure is valid.

---

## plugin_validator.py

**Purpose**: Comprehensive validation tool for Claude Code plugins with token-based complexity measurement.

### Supported Validation Types

- Complete plugins (validates all components)
- Individual SKILL.md files
- Individual agent .md files
- Individual command .md files

### Usage

```bash
# Validate single file or directory
uv run plugins/plugin-creator/scripts/plugin_validator.py {path}

# Validate entire plugin
uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/my-plugin

# Auto-fix issues
uv run plugins/plugin-creator/scripts/plugin_validator.py --fix {path}

# Validate only (no auto-fix)
uv run plugins/plugin_validator.py --check {path}

# Verbose output with details
uv run plugins/plugin-creator/scripts/plugin_validator.py --verbose {path}

# CI mode (no color)
uv run plugins/plugin-creator/scripts/plugin_validator.py --no-color {path}
```

### What It Validates

- **Frontmatter schema:** YAML syntax, required fields, field types, tools/skills format
- **Plugin structure:** plugin.json schema, component paths, version consistency
- **Skill complexity:** Token-based metrics (4000 warning, 6400 error thresholds)
- **Internal links:** Markdown link validity, progressive disclosure
- **Component completeness:** Required files, cross-references

### What It Auto-Fixes

- YAML arrays → comma-separated strings
- Multiline descriptions → single-line quoted strings
- Unquoted descriptions with colons
- Removes `name:` field from plugin skills (Claude Code bug workaround)

### Error Codes

23 error codes across 9 validators - see [ERROR_CODES.md](./ERROR_CODES.md)

### Schema Coverage

| File Type | Required Fields   | Key Optional Fields                                          |
| --------- | ----------------- | ------------------------------------------------------------ |
| Skills    | None              | name, description, model, allowed-tools, user-invocable      |
| Agents    | name, description | model, tools, disallowedTools, permissionMode, skills, hooks |
| Commands  | description       | argument-hint, allowed-tools, model, context, agent          |

---

## validate-task-file.sh

**Purpose**: Validate refactoring task file format and structure.

### Usage

```bash
plugins/plugin-creator/scripts/validate-task-file.sh {task-file-path}
```

### What It Validates

- Task file follows expected format
- Task status values are valid (❌ NOT STARTED, 🔄 IN PROGRESS, ✅ COMPLETE)
- Task metadata is properly structured
- Dependencies reference valid task IDs
- Acceptance criteria are present

### Use Case

Used during plugin refactoring workflows to ensure task files created by the planner agent are properly formatted before execution begins.
