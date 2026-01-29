---
description: "Check skill line counts to identify oversized skills exceeding recommended limits (500 lines warning, 800 lines critical). Use when auditing plugin structure before refactoring, planning skill splits, or validating skill complexity. Displays table with line counts and status indicators (OK, WARNING, CRITICAL). Complements the refactor-plugin workflow for comprehensive plugin analysis."
argument-hint: <plugin-or-skill-path>
allowed-tools: Read, Glob, Bash
model: inherit
context: fork
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

- Suggest running `/plugin-creator:refactor-plugin` for comprehensive analysis
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
/plugin-creator:count-lines ./plugins/python3-development

# Check a single skill
/plugin-creator:count-lines ./plugins/python3-development/skills/python3-development
```
