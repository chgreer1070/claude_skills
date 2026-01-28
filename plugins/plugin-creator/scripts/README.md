# Plugin Creator Scripts

Utility scripts for maintaining Claude Code plugins, skills, agents, and commands.

---

## fix-tool-formats.py

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
python3 plugins/plugin-creator/scripts/fix-tool-formats.py
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

============================================================
Fixed: 28 files
Skipped: 420 files (no changes needed)
Total: 448 files
```

---

## count-skill-lines.sh

**Purpose**: Count lines in skill files to identify oversized skills.

See `/plugin-creator:count-lines` command for usage.

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

## validate_frontmatter.py

**Purpose**: Comprehensive YAML frontmatter validation and auto-fix for skills, agents, and commands.

### Supported File Types

- SKILL.md files (skills)
- Agent .md files
- Command .md files (user-level)

### Usage

```bash
# Validate single file
uv run plugins/plugin-creator/scripts/validate_frontmatter.py validate {path}

# Validate all files in directory
uv run plugins/plugin-creator/scripts/validate_frontmatter.py batch {directory}

# Auto-fix issues (dry-run first recommended)
uv run plugins/plugin-creator/scripts/validate_frontmatter.py fix {path} --dry-run
uv run plugins/plugin-creator/scripts/validate_frontmatter.py fix {path}

# Batch fix all files in directory
uv run plugins/plugin-creator/scripts/validate_frontmatter.py fix-batch {directory}
```

### What It Validates

- YAML syntax validity
- No forbidden multiline indicators (`>-`, `|-`)
- Required fields present (varies by file type)
- Field types match schema (string, bool, object)
- Field values within constraints (length, pattern)
- Valid enumeration values (e.g., model: sonnet/opus/haiku/inherit)
- Tools/skills are comma-separated strings (not YAML arrays)

### What It Auto-Fixes

- YAML arrays → comma-separated strings for tools/skills fields
- Multiline descriptions → single-line quoted strings
- Unquoted descriptions containing colons

### Schema Coverage

| File Type | Required Fields   | Key Optional Fields                                          |
| --------- | ----------------- | ------------------------------------------------------------ |
| Skills    | None              | name, description, model, allowed-tools, user-invocable      |
| Agents    | name, description | model, tools, disallowedTools, permissionMode, skills, hooks |
| Commands  | description       | argument-hint, allowed-tools, model, context, agent          |

---

## validate-skill-structure.sh

**Purpose**: Quality checks for skill structure beyond frontmatter validation.

### Usage

```bash
plugins/plugin-creator/scripts/validate-skill-structure.sh {skill-directory}
```

### What It Validates

1. **Frontmatter Presence**: SKILL.md starts with `---` and has proper closing
2. **Name Field**: Present, lowercase, hyphens only
3. **Description Field**: Present, minimum 20 characters, includes trigger phrases
4. **Line Count Limits**:
   - WARN if body >500 lines
   - ERROR if body >800 lines
5. **Progressive Disclosure**: Checks for `references/`, `examples/`, `scripts/` directories
6. **Internal Links**: Validates markdown links with `./` prefix point to existing files

### Exit Codes

- 0: Pass (all checks passed or warnings only)
- 1: Fail (errors found)

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
