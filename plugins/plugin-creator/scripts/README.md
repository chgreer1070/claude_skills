# Plugin Refactor Scripts

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
python3 plugins/plugin-refactor/scripts/fix-tool-formats.py
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

See `/plugin-refactor:count-lines` command for usage.
