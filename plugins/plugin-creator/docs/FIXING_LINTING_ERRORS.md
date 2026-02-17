# Fixing Linting Errors in Claude Skills

This guide documents the process for fixing linting errors in Claude Code skills, based on the plugin-validator.py tool.

## Quick Start

1. **Run the validator** to identify issues:
   ```bash
   uv run plugins/plugin-creator/scripts/plugin-validator.py <file-path>
   ```

2. **Review error codes** in [ERROR_CODES.md](./ERROR_CODES.md)

3. **Fix the issues** following the guidance below

4. **Re-run validation** to confirm fixes

## Common Error Types and Fixes

### Broken Internal Links (LK001)

**Symptom**: `❌ [LK001] internal-links: Broken link: [Title](./path/to/file.md) (file not found)`

**Diagnosis Steps**:
1. Identify the broken link path in the error message
2. Determine if the referenced file exists elsewhere in the repository
3. Calculate the correct relative path from the linking file

**Fix Process**:

```bash
# Step 1: Find if the referenced file exists elsewhere
find . -name "filename.md" -not -path "./.venv/*"

# Step 2: Calculate relative path
# From: /path/to/source/SKILL.md
# To: /path/to/target/file.md
# Result: ../../target/file.md

# Step 3: Update the link in the source file
# Before: [Title](./../non-existent/file.md)
# After: [Title](../../correct/path/file.md)
```

**Example**:

Issue: `agent-creator/SKILL.md` referenced `./../knowledge/workflow-diagrams/asset-decision-tree.md` which didn't exist.

Solution: Updated to point to the existing `../plugin-creator/references/workflow-diagram.md`

### Missing or Incorrect Skill References (LK001)

**Symptom**: Link to non-existent skill like `claude-skills-reference-2026`

**Fix Process**:
1. Search for similar skill names: `ls plugins/plugin-creator/skills/`
2. Identify the correct skill name (e.g., `claude-skills-overview-2026`)
3. Update the link with the correct name

### Relative Path Depth Issues

**Common Mistake**: Using wrong number of `../` in relative paths

**Fix**:
```bash
# Check your current location
pwd
# Example: /repo/plugins/plugin-creator/skills/agent-creator

# Check target location
ls -la ../plugin-creator/references/workflow-diagram.md
# If this works, path is: ../plugin-creator/references/workflow-diagram.md

# For .claude/skills/ subdirectories, add extra ../ levels
# From: /repo/.claude/skills/agent-creator/SKILL.md
# To: /repo/plugins/plugin-creator/skills/plugin-creator/references/workflow-diagram.md
# Path: ../../../plugins/plugin-creator/skills/plugin-creator/references/workflow-diagram.md
```

## Validation Workflow

### Local Testing

```bash
# 1. Install dependencies
uv sync

# 2. Validate specific files
uv run plugins/plugin-creator/scripts/plugin-validator.py path/to/SKILL.md

# 3. Validate all plugin-creator skills
uv run plugins/plugin-creator/scripts/plugin-validator.py \
  $(find plugins/plugin-creator/skills -type f -name 'SKILL.md')

# 4. Validate entire repository (as CI does)
uv run plugins/plugin-creator/scripts/plugin-validator.py \
  $(find plugins .claude -type f \( -name 'SKILL.md' -o -path '*/agents/*.md' \
    -o -path '*/commands/*.md' -o -name 'plugin.json' \) \
    -not -path './.venv/*' -not -path './node_modules/*' 2>/dev/null)
```

### Understanding Validation Results

**Exit codes**:
- `0`: All files passed (warnings are OK)
- `1`: One or more files failed (hard errors)

**Severity levels**:
- ✅ `PASSED`: No issues
- ⚠️ `Warning`: Non-blocking recommendations (e.g., SK006 complexity)
- ❌ `Error`: Blocking failure (e.g., LK001 broken link)

**Warnings vs Errors**:
- **Warnings** like SK006 (complexity) are recommendations to refactor but don't block CI
- **Errors** like LK001 (broken links) block CI and must be fixed

## CI Integration

The GitHub Actions workflow runs validation on all plugins:

```yaml
- name: Validate plugins
  run: |
    uv run plugins/plugin-creator/scripts/plugin-validator.py \
      $(find plugins .claude -type f \( -name 'SKILL.md' -o -path '*/agents/*.md' \
        -o -path '*/commands/*.md' -o -name 'plugin.json' \) \
        -not -path './.venv/*' -not -path './node_modules/*' 2>/dev/null)
```

**Viewing CI Failures**:
1. Go to the GitHub Actions run page
2. Look for the "Validate plugins" step
3. Scroll to the validation summary showing passed/failed counts
4. Search for `❌` to find specific failures

## Skills for Assistance

The plugin-creator plugin provides skills to help with fixing issues:

- **refactor-skill**: For addressing SK006/SK007 complexity warnings
- **write-frontmatter-description**: For addressing SK005 description issues
- **plugin-creator**: General plugin structure guidance

Invoke with: `/plugin-creator:skill-name`

## Reference Documentation

- [ERROR_CODES.md](./ERROR_CODES.md) - Complete error code reference
- [ARCHITECTURE.md](../references/ARCHITECTURE.md) - Validator architecture
- [USAGE.md](../references/USAGE.md) - Plugin creator usage guide

## Tips

1. **Fix broken links first** - They're usually quick wins
2. **Run validation frequently** - Don't wait until CI fails
3. **Use relative paths with `./`** - Required for internal links
4. **Check for duplicates** - Skills in `.claude/` may duplicate `plugins/` content
5. **Understand symlinks** - Some `.claude/` entries may be symlinks to plugins

## Case Study: Fixing Broken Links in Plugin-Creator Skills

**Problem**: 2 broken internal links in plugin-creator skills caused CI failure

**Files affected**:
- `plugins/plugin-creator/skills/agent-creator/SKILL.md`
- `plugins/plugin-creator/skills/claude-hooks-reference-2026/SKILL.md`
- `.claude/skills/agent-creator/SKILL.md` (duplicate)
- `.claude/skills/delegate/SKILL.md`

**Process**:
1. Ran validator locally to reproduce CI failure
2. Identified broken links: non-existent `asset-decision-tree.md` and `claude-skills-reference-2026`
3. Searched for similar files: found `workflow-diagram.md` and `claude-skills-overview-2026`
4. Calculated correct relative paths
5. Updated all 4 files
6. Validated fixes locally
7. Committed and pushed

**Result**: 4/4 files passing, 0 hard errors (down from 2 errors)
