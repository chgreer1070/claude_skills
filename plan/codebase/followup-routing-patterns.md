# Followup Routing Patterns

**Analysis Date:** 2026-03-02
**Feature context:** complete-implementation routing step to prevent follow-up task files from being orphaned when recursion is skipped

---

## 1. Skill Document Patterns

### complete-implementation SKILL.md

**Location:** `.claude/skills/complete-implementation/SKILL.md`

**Frontmatter structure:**

```yaml
---
name: complete-implementation
argument-hint: <task-file-path>
user-invocable: true
description: "..."
metadata:
  version: "1.0.0"
  last_updated: "2026-02-28"
  source: python3-development plugin (local adaptation)
---
```

**Body structure:** Plain prose sections under `## Phase N:` headers (Phases 1–6), then a `## Recursive Follow-up Handling` section. No YAML decision tables — routing logic is expressed as prose plus a code block with the `Skill()` invocation.

**How other skills are referenced:** Via `Skill(skill="...")` invocation blocks in fenced code:

```text
Skill(skill="implement-feature", args="{followup_task_file_path}")
```

Skills are not hyperlinked; they are called by name string.

**Current Recursive Follow-up Handling section** (`.claude/skills/complete-implementation/SKILL.md:57-65`):

```text
## Recursive Follow-up Handling

If Phase 1 creates follow-up task files (expected naming: `plan/tasks-{N}-{slug}-followup-{k}.md`), run:

Skill(skill="implement-feature", args="{followup_task_file_path}")

Then re-run `complete-implementation` on the follow-up task file.
```

This section contains NO routing guard. It describes what to do when recursion happens, but does not prescribe any action when recursion is skipped — the follow-up file is simply untracked.

### work-backlog-item SKILL.md

**Location:** `.claude/skills/work-backlog-item/SKILL.md`

**Relevant patterns for cross-skill invocation:**

- References `create-backlog-item` in `--auto` mode: `Skill(skill: "create-backlog-item", args: "--auto {title}")`
- References `groom-backlog-item`: `Skill(skill: "groom-backlog-item", args: "{item title}")`
- References `add-new-feature`: `Skill(skill: "add-new-feature", args: "{composed feature request}")`

All cross-skill calls use the `Skill(skill: "...")` syntax with `args:` for arguments.

**Backlog update pattern** (`.claude/skills/work-backlog-item/SKILL.md:416-418`):

```bash
uv run .claude/skills/backlog/scripts/backlog.py update "{title}" --plan "plan/tasks-{N}-{slug}.md" -R Jamie-BitFlight/claude_skills
```

Used after `add-new-feature` completes to record the plan file path in the backlog item.

**Backlog add pattern — `--auto` mode** (`.claude/skills/work-backlog-item/SKILL.md:59`):

When `--auto` and no title: invokes `create-backlog-item --auto {title}` to create a new item without user interaction.

---

## 2. Backlog Integration Patterns

### CLI Interface

**Script location:** `.claude/skills/backlog/scripts/backlog.py`

**Invocation:**

```bash
uv run .claude/skills/backlog/scripts/backlog.py <subcommand> [options]
```

### Subcommand: `add`

**Signature** (`.claude/skills/backlog/scripts/backlog.py:856-868`):

```bash
backlog add \
  --title "Item title" \
  --priority P1 \
  --description "Description" \
  [--source "Source"] \
  [--type Feature|Bug|Refactor|Docs|Chore] \
  [--research-first "questions"] \
  [--files "paths"] \
  [--suggested-location "path"] \
  [--create-issue/--no-create-issue]  # default: --create-issue
  [--force]  # skip fuzzy duplicate check
  [-R repo]
```

`--create-issue` defaults to `True`. P0/P1 items auto-create GitHub issues. To skip issue creation: pass `--no-create-issue`.

**Duplicate detection** (`.claude/skills/backlog/scripts/backlog.py:870-880`): Without `--force`, the script scans existing titles with `difflib.SequenceMatcher` at threshold 0.80 and exits code 1 if a duplicate is found. Use `--force` to bypass. In `create-backlog-item --auto` mode, the skill stops on duplicate detection rather than calling `--force`.

**Output on success:**

```text
Backlog item created.
  Title: {title}
  Priority: {priority}
  File: {filename}
  Issue: #{N}    # if created
Next steps: /groom-backlog-item {title}  /work-backlog-item {title}
```

Exit code 0 on success, 1 on duplicate or missing required fields.

### Subcommand: `update`

**Signature** (`.claude/skills/backlog/scripts/backlog.py:1769-1780`):

```bash
backlog update "<title substring, #N, bare number, or URL>" \
  [--plan PATH] \
  [--status in-progress] \
  [--create-issue] \
  [-R repo]
```

`update` locates item by `find_item()` — title substring (case-insensitive), `#N`, bare number, or GitHub issue URL. Exits code 1 with error if no item found.

`--plan PATH` writes `metadata.plan = PATH` to the per-item frontmatter.

`--status in-progress` sets the `status:in-progress` label on the linked GitHub issue.

### Subcommand: `list` with `--format json`

**Signature** (`.claude/skills/backlog/scripts/backlog.py:1038-1056`):

```bash
backlog list [--format text|json] [--with-status] [--from-github] [--label LABEL] [-R repo]
```

**JSON output shape** (`.claude/skills/backlog/scripts/backlog.py:963-979`):

```json
[
  {
    "section": "P1",
    "title": "Item title",
    "issue": "#42",
    "plan": "plan/tasks-N-slug.md",
    "file_path": ".claude/backlog/p1-item-slug.md",
    "groomed": true,
    "status": "status:in-progress",   // only with --with-status
    "milestone": "v1.1 — Quality Gates"  // only with --with-status
  }
]
```

Items with `_skip=True` (status `done`/`resolved`, or in `Completed` section) are excluded.

### Search-by-Title: `find_item()`

**Location:** `.claude/skills/backlog/scripts/backlog.py:310-333`

```python
def find_item(items: list[dict], selector: str) -> dict | None:
    # Supports: URL, #N, bare number, or title substring
    # Title substring: case-insensitive, first match wins
    selector_lower = selector.lower()
    matches = [it for it in items if selector_lower in it.get("_title", "").lower()]
    return matches[0] if len(matches) == 1 else (matches[0] if matches else None)
```

Returns `None` if no match, returns first match if multiple exist. No error is raised on multi-match at this level — callers handle the ambiguity.

### `--auto` mode in `create-backlog-item`

**Location:** `.claude/skills/create-backlog-item/SKILL.md`

When `$0` is `--auto`:

1. Title comes from `$1` onward — no `AskUserQuestion` calls.
2. Fields derived from research files and context.
3. Every decision logged as `[AUTO] ...` text.
4. GitHub issue creation skipped unless `--create-issue` explicitly passed (added to `backlog add` call as `--no-create-issue`).
5. On duplicate detection: logs `[AUTO] STOP — duplicate detected` and stops without writing.

Invocation pattern (`.claude/skills/create-backlog-item/SKILL.md:163-169`):

```bash
uv run .claude/skills/backlog/scripts/backlog.py add \
  --title "{title}" \
  --priority "{priority}" \
  --description "{description}" \
  --source "{source}" \
  --type "{type}" \
  --no-create-issue \
  -R Jamie-BitFlight/claude_skills
```

---

## 3. Follow-up File Handling

### Naming Convention

**Defined in:** `plugins/python3-development/agents/code-reviewer.md:176-192`

```text
{project_path}/plan/tasks-{N}-{feature-slug}-followup-{issue-number}.md
```

Derivation steps:
1. Read original task file path (e.g., `plan/tasks-4-data-validation.md`)
2. Extract feature slug (`data-validation`)
3. Glob existing plan files to find next available `N`
4. Create: `tasks-{N}-{feature-slug}-followup-{issue-number}.md`

**Example** for `tasks-4-data-validation.md` with two issues found:

- `plan/tasks-5-data-validation-followup-1.md`
- `plan/tasks-6-data-validation-followup-2.md`

### Current Recursion Trigger

**In `complete-implementation/SKILL.md:57-65`:**

```text
If Phase 1 creates follow-up task files (expected naming: `plan/tasks-{N}-{slug}-followup-{k}.md`),
run Skill(skill="implement-feature") then re-run complete-implementation.
```

**In `.claude/rules/local-workflow.md` (Recursive Follow-up section, lines 238-245):**

```text
If Phase 1 (code review) creates follow-up task files (naming: plan/tasks-{N}-{slug}-followup-{k}.md),
the workflow recurses:
1. Run /implement-feature on the follow-up task file
2. Run /complete-implementation on the follow-up task file
```

**Gap:** Neither document specifies what happens when recursion does NOT run (e.g., the orchestrator decides to skip it, or the session ends before recursion). The follow-up file exists at `plan/` but is not registered in any backlog item, has no GitHub issue, and is invisible to `/work-backlog-item`.

### Existing Follow-up Files

None exist in `plan/` at analysis date (Glob on `plan/tasks-*-*-followup-*.md` returned no results).

### Task File Structure for Follow-ups

**Defined in:** `plugins/python3-development/agents/code-reviewer.md:195-238`

The follow-up format is a hybrid YAML frontmatter + markdown body:

```yaml
---
tasks:
  - task: "Brief description of the fix needed"
    status: pending
    parent_task: "{original_task_file_path}"
---
```

```markdown
# Task: {Brief Title}

## Parent Task
- Original: `{original_task_file_path}`
- Review Date: {YYYY-MM-DD}

## Status
- [ ] Pending

## Priority
{High/Medium/Low}

## Description
{What needs to be done and why}

## Acceptance Criteria
- [ ] {Specific criterion 1}

## Files to Modify
- `{file_path}:{line_numbers}` - {what to change}

## Verification Steps
1. {Command to verify criterion 1}
```

This format differs from the primary task file format used by the SAM pipeline. The primary format (e.g., `tasks-2-validator-ux-coverage.md`) uses YAML frontmatter with feature-level metadata (`feature`, `status`, `created`, `source`, `target-file`) and `## Task N:` sections with `**Status**`, `**Priority**`, `**Agent**` fields. Follow-up files use a simpler structure targeted at single-issue remediation.

---

## 4. create-backlog-item Skill: --auto Mode

**Location:** `.claude/skills/create-backlog-item/SKILL.md`

The `--auto` mode is designed for agent-to-agent invocation without human in the loop.

**Key behaviors:**

| Normal behavior | `--auto` substitution |
|---|---|
| Interactive title prompt | Title from `$1` onward |
| Interactive priority prompt | Inferred from description keywords |
| Interactive description prompt | Derived from research files |
| Duplicate → ask user | Log and STOP without writing |
| P0/P1 GitHub issue offer | Skip — no issue created unless `--create-issue` passed |

**Invocation from within another skill:**

```text
Skill(skill: "create-backlog-item", args: "--auto {title}")
```

This is the pattern used in `work-backlog-item` when a backlog item is not found and `AUTO_MODE=true` (`.claude/skills/work-backlog-item/SKILL.md:59`).

**Script call generated by `--auto`** (`.claude/skills/create-backlog-item/SKILL.md:163-169`):

```bash
uv run .claude/skills/backlog/scripts/backlog.py add \
  --title "{title}" \
  --priority "{priority}" \
  --description "{description}" \
  --source "Agent task — auto-derived from {filename}" \
  --type "{type}" \
  --no-create-issue \
  -R Jamie-BitFlight/claude_skills
```

The `--no-create-issue` flag is always included in `--auto` mode unless `--create-issue` is explicitly passed by the caller.

---

## 5. Code Reviewer Agent: Follow-up File Creation

### Agent Definition

**Primary source:** `plugins/python3-development/agents/code-reviewer.md`

**Frontmatter:**

```yaml
---
name: code-reviewer
description: Performs holistic code review and validation after feature implementation...
  Creates follow-up task files when issues are found.
model: sonnet
permissionMode: acceptEdits
color: yellow
skills: subagent-contract, python3-development, python3-development:validation-protocol, holistic-linting
---
```

**No local `.claude/agents/code-reviewer.md` exists** (Glob returned no results for that path).

### SOP Step 6: Create Follow-up Tasks

**Location:** `plugins/python3-development/agents/code-reviewer.md:122-125`

```text
### Step 6: Create Follow-up Tasks

For each significant issue found, create a task file in `{project_path}/plan/` following the existing task format.
```

The agent creates follow-up files using `Write` tool. It does not invoke the backlog script. No backlog item is created as part of follow-up file generation.

### Naming Convention (Critical)

**Location:** `plugins/python3-development/agents/code-reviewer.md:175-192`

The agent is explicitly instructed to:

1. Read the original task file path
2. Extract the feature slug
3. Glob existing files to find next available `N`
4. Create `tasks-{N}-{feature-slug}-followup-{issue-number}.md`

### Output Format

**Location:** `plugins/python3-development/agents/code-reviewer.md:241-254`

```text
STATUS: DONE
SUMMARY: {one_paragraph_summary_of_review_findings}
ARTIFACTS:
  - Files reviewed: {count}
  - Issues found: {count}
  - Tasks created: {count}
  - Task files: {list of task file paths}
RISKS:
  - {critical_issues_requiring_attention}
NOTES:
  - {recommendations_for_improvement}
```

The output includes a `Task files:` list in `ARTIFACTS`. This list is the only mechanism currently available for the orchestrator (`complete-implementation`) to discover what follow-up files were created.

---

## 6. Key Constraints for Routing Implementation

### Constraint: backlog.py is the sole interface

**Source:** `.claude/CLAUDE.md` (Backlog Operations section):

```text
Single interface: Use .claude/skills/backlog/scripts/backlog.py for all backlog and GitHub issue
CRUD. Editing per-item files directly or using gh for issue CRUD bypasses sync logic — use the script.
```

Any routing step that creates or updates backlog items MUST go through `backlog.py add` or `backlog.py update`.

### Constraint: `--auto` skips GitHub issue creation by default

`create-backlog-item --auto` adds `--no-create-issue` unless caller passes `--create-issue`. A routing step using `--auto` would create a local-only backlog item with no GitHub issue.

### Constraint: Fuzzy duplicate detection exits code 1

`backlog add` without `--force` exits code 1 if similarity ≥ 0.80. A routing step that calls `backlog add` must handle this exit code or pass `--force`.

### Constraint: `update --plan` requires an existing item

`backlog update` locates the item via `find_item()`. If no item exists, it exits code 1. A routing step cannot use `update --plan` without first confirming or creating the item.

### Constraint: Follow-up file path is knowable at routing time

The follow-up file naming (`plan/tasks-{N}-{slug}-followup-{k}.md`) is deterministic from the code reviewer's output. The `ARTIFACTS: Task files:` list in the code reviewer's STATUS output is the discovery source.

### Constraint: No local `.claude/agents/code-reviewer.md`

Only `plugins/python3-development/agents/code-reviewer.md` exists. The routing logic in `complete-implementation` must reference the plugin-level agent, consistent with the current pattern in `local-workflow.md` Phase 1 agent table.

---

## 7. Backlog Item File Format

### Per-item file format

**Location:** `.claude/backlog/*.md` — YAML frontmatter with research-style metadata

```yaml
---
name: "Item title"
description: "Item description"
metadata:
  source: "..."
  added: "YYYY-MM-DD"
  priority: "P1"
  issue: "#42"
  plan: "plan/tasks-N-slug.md"
  status: "open"
  groomed: "YYYY-MM-DD"
---
```

### Filename convention

`{priority-lowercase}-{slug}.md`, e.g., `p1-followup-routing-prevention.md`

Slug is derived by `_title_to_slug()` (`.claude/skills/backlog/scripts/backlog.py:167-180`): lowercase, non-alphanumeric stripped, spaces to hyphens, max 60 chars.

### Priority-to-section mapping

**Location:** `.claude/skills/backlog/scripts/backlog.py:195-203`

```python
prefix_to_section = {
    "p0-": "P0",
    "p1-": "P1",
    "p2-": "P2",
    "idea-": "Ideas",
    "ideas-": "Ideas",
    "completed-": "Completed",
    "medium-": "P1",
}
```

---

_Pattern analysis: 2026-03-02_
