---
description: Quick check of skill line counts to identify oversized skills that may need refactoring.
argument-hint: <plugin-or-skill-path>
allowed-tools: Read, Glob, Bash
---

# Count Skill Lines

Quickly check line counts for skills in a plugin or skill directory.

## Arguments

- `$ARGUMENTS`: Path to plugin directory or individual skill directory

## Purpose

Identify skills that exceed recommended size limits:

- **500 lines**: Warning threshold - consider splitting
- **800 lines**: Critical threshold - must split

## Instructions

### Step 1: Run Line Counter Script

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/count-skill-lines.sh "$ARGUMENTS"
```

### Step 2: Display Results

Show table with all skills and their line counts.

### Step 3: Recommendations

For skills over threshold:

- Suggest running `/plugin-refactor:refactor` for comprehensive analysis
- Note which skills are candidates for splitting

## Output Format

```text
| Skill | Total | Body | Status |
|-------|-------|------|--------|
| python3-development | 650 | 580 | WARNING (>500) |
| testing | 320 | 280 | OK |
| async | 850 | 810 | CRITICAL (>800) |

Summary:
  Skills within limits: 1
  Skills over 500 lines (warning): 1
  Skills over 800 lines (critical): 1
```

## Example Usage

```bash
# Check a plugin
/plugin-refactor:count-lines ./plugins/python3-development

# Check a single skill
/plugin-refactor:count-lines ./plugins/python3-development/skills/python3-development
```
