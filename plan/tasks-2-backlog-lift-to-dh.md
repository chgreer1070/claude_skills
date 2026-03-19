---
title: "Tasks: Lift Backlog Skills to development-harness Plugin"
slug: backlog-lift-to-dh
version: "1.0"
status: ready
generated: 2026-03-18
issue: "#843"
sources:
  - plan/feature-context-backlog-lift-to-dh.md
  - plan/codebase/BACKLOG-SKILLS-INVENTORY.md
  - plan/architect-backlog-lift-to-dh.md
tasks:
  - T01: "Move 3 backlog skill directories from .claude/skills/ to plugins/development-harness/skills/"
  - T02: "Update project-level callers to use dh: namespace prefix"
  - T03: "Full validation sweep -- confirm all acceptance criteria pass"
task_exports:
  enabled: false
  directory: "TASK"
acceptance_criteria:
  - "AC1: Three skill directories exist in plugins/development-harness/skills/ with correct file counts (1, 3, 9)"
  - "AC2: Three original directories deleted from .claude/skills/"
  - "AC3: Zero bare-name Skill() calls to the three moved skills in any non-plan, non-intra-dh file"
  - "AC4: All modified files pass prek linting"
  - "AC5: Zero bare-name slash references (/create-backlog-item, /groom-backlog-item, /work-backlog-item) in live files outside plan/ and .claude/backlog/"
---

# Tasks: Lift Backlog Skills to development-harness Plugin

Move three backlog intake skills (`create-backlog-item`, `groom-backlog-item`, `work-backlog-item`)
from project-level `.claude/skills/` into `plugins/development-harness/skills/`. Update all
project-level callers to use the `dh:` namespace prefix. Delete originals after confirming move.

## Execution Order

Tasks are strictly serial. Each depends on the output of its predecessor.

```text
T01 → T02 → T03
```

## Resolved Design Decisions

- Q1: Bare names work within dh plugin (intra-dh callers keep bare names)
- Q2: Project-level callers need `dh:` prefix after move
- Q3: Delete originals after confirming move
- Q4: Canonical prefix is `dh:`
- Q5: Plan artifacts left as-is (historical records)

## NOT In Scope

- `plugins/development-harness/skills/interop/SKILL.md` (intra-dh, Q1)
- `work-backlog-item` internal `Skill()` calls to `create-backlog-item` and `groom-backlog-item` (intra-dh, Q1)
- `plan/*.md` files (historical records, Q5)
- `.claude/skills/backlog/` (MCP server stays project-level)
- `plugins/development-harness/plugin.json` (auto-discovery handles new skill directories)

---

## Context Manifest

Feature: Lift three backlog integration skills from project-level `.claude/skills/` into the
development-harness plugin.

GitHub Issue: #843

Architecture spec: `plan/architect-backlog-lift-to-dh.md`
Feature context: `plan/feature-context-backlog-lift-to-dh.md`
Codebase inventory: `plan/codebase/BACKLOG-SKILLS-INVENTORY.md`

---

## Task T01: Move 3 backlog skill directories from .claude/skills/ to plugins/development-harness/skills/

- **Status**: NOT STARTED
- **Dependencies**: None
- **Priority**: 1
- **Complexity**: Low
- **Agent**: general-purpose
- **Skills**: []
- **Accuracy Risk**: Low

### Context

Three backlog intake skills currently live at project level (`.claude/skills/`). They are being
relocated into the development-harness plugin (`plugins/development-harness/skills/`) to make dh
self-contained. The backlog MCP server at `.claude/skills/backlog/` is NOT moving.

Architecture spec: `plan/architect-backlog-lift-to-dh.md` (Deliverable 1)
Codebase inventory: `plan/codebase/BACKLOG-SKILLS-INVENTORY.md`

### Objective

All three skill directories exist in `plugins/development-harness/skills/` with identical file
contents, originals are deleted from `.claude/skills/`, and linting passes on the 3 new SKILL.md
files.

### Inputs

- Source directories:
  - `.claude/skills/create-backlog-item/` (1 file: SKILL.md)
  - `.claude/skills/groom-backlog-item/` (3 files: SKILL.md + 2 references)
  - `.claude/skills/work-backlog-item/` (9 files: SKILL.md + 8 references)
- Destination parent: `plugins/development-harness/skills/`

### Requirements

1. Copy `.claude/skills/create-backlog-item/` to `plugins/development-harness/skills/create-backlog-item/` preserving directory structure
2. Copy `.claude/skills/groom-backlog-item/` to `plugins/development-harness/skills/groom-backlog-item/` preserving directory structure
3. Copy `.claude/skills/work-backlog-item/` to `plugins/development-harness/skills/work-backlog-item/` preserving directory structure
4. Verify copies succeeded by checking file counts match expected (1, 3, 9 respectively)
5. Verify reference file integrity -- confirm these specific files exist in destination:
   - `plugins/development-harness/skills/groom-backlog-item/references/issue-classification.md`
   - `plugins/development-harness/skills/groom-backlog-item/references/groomer-agent.md`
   - `plugins/development-harness/skills/work-backlog-item/references/validation-plan.md`
   - `plugins/development-harness/skills/work-backlog-item/references/sam-definition.md`
   - `plugins/development-harness/skills/work-backlog-item/references/example-sessions.md`
   - `plugins/development-harness/skills/work-backlog-item/references/error-handling.md`
   - `plugins/development-harness/skills/work-backlog-item/references/auto-mode.md`
   - `plugins/development-harness/skills/work-backlog-item/references/step-procedures.md`
   - `plugins/development-harness/skills/work-backlog-item/references/github-integration.md`
   - `plugins/development-harness/skills/work-backlog-item/references/close-resolve-procedure.md`
6. Remove originals ONLY after verifying copies (requirements 4-5 pass):
   - `rm -rf .claude/skills/create-backlog-item/`
   - `rm -rf .claude/skills/groom-backlog-item/`
   - `rm -rf .claude/skills/work-backlog-item/`
7. Run linting on each new SKILL.md:
   - `uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md`
   - `uv run prek run --files plugins/development-harness/skills/groom-backlog-item/SKILL.md`
   - `uv run prek run --files plugins/development-harness/skills/work-backlog-item/SKILL.md`

### Constraints

- Do NOT modify any file contents during the move -- this is a pure copy+delete operation
- Do NOT modify `plugins/development-harness/plugin.json` -- auto-discovery handles new skill directories
- Do NOT delete originals before verifying copies exist and have correct file counts
- Do NOT move `.claude/skills/backlog/` -- the MCP server stays project-level

### Expected Outputs

- `plugins/development-harness/skills/create-backlog-item/SKILL.md` (new)
- `plugins/development-harness/skills/groom-backlog-item/SKILL.md` (new)
- `plugins/development-harness/skills/groom-backlog-item/references/issue-classification.md` (new)
- `plugins/development-harness/skills/groom-backlog-item/references/groomer-agent.md` (new)
- `plugins/development-harness/skills/work-backlog-item/SKILL.md` (new)
- `plugins/development-harness/skills/work-backlog-item/references/` (8 files, new)
- `.claude/skills/create-backlog-item/` (deleted)
- `.claude/skills/groom-backlog-item/` (deleted)
- `.claude/skills/work-backlog-item/` (deleted)

### Acceptance Criteria

1. `test -f plugins/development-harness/skills/create-backlog-item/SKILL.md` exits 0
2. `test -f plugins/development-harness/skills/groom-backlog-item/SKILL.md` exits 0
3. `test -f plugins/development-harness/skills/work-backlog-item/SKILL.md` exits 0
4. `test ! -d .claude/skills/create-backlog-item` exits 0
5. `test ! -d .claude/skills/groom-backlog-item` exits 0
6. `test ! -d .claude/skills/work-backlog-item` exits 0
7. All 10 reference files listed in requirement 5 exist at destination paths
8. `uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md` exits 0
9. `uv run prek run --files plugins/development-harness/skills/groom-backlog-item/SKILL.md` exits 0
10. `uv run prek run --files plugins/development-harness/skills/work-backlog-item/SKILL.md` exits 0

### Verification Steps

1. Run: `fdfind -t f . plugins/development-harness/skills/create-backlog-item/ | wc -l` -- expect 1
2. Run: `fdfind -t f . plugins/development-harness/skills/groom-backlog-item/ | wc -l` -- expect 3
3. Run: `fdfind -t f . plugins/development-harness/skills/work-backlog-item/ | wc -l` -- expect 9
4. Run: `test ! -d .claude/skills/create-backlog-item && test ! -d .claude/skills/groom-backlog-item && test ! -d .claude/skills/work-backlog-item && echo "originals removed"` -- expect "originals removed"
5. Run prek on all 3 SKILL.md files per requirement 7 -- expect exit 0 for each

### Handoff

Return: file count per destination directory, prek exit codes, confirmation originals deleted.

---

## Task T02: Update project-level callers to use dh: namespace prefix

- **Status**: NOT STARTED
- **Dependencies**: T01
- **Priority**: 2
- **Complexity**: Medium
- **Agent**: general-purpose
- **Skills**: []
- **Accuracy Risk**: Medium

### Context

T01 moved three backlog skills into `plugins/development-harness/skills/`. Project-level callers
still reference these skills by bare name. Per resolved decision Q2, project-level callers need
the `dh:` prefix. Per Q1, intra-dh callers (like `interop/SKILL.md` and `work-backlog-item`'s
internal `Skill()` calls) keep bare names.

Architecture spec: `plan/architect-backlog-lift-to-dh.md` (Deliverable 2)

### Objective

All project-level files that reference the three moved skills use the `dh:` namespace prefix.
Zero bare-name `Skill()` calls or slash references to these skills remain in non-plan,
non-intra-dh files.

### Inputs

- Architecture spec Deliverable 2 for exact before/after patterns
- Files to modify:
  1. `plugins/python3-development/skills/complete-implementation/SKILL.md`
  2. `.claude/CLAUDE.md`
  3. `.claude/hooks/stop-backlog-reminder.cjs`
  4. `plugins/development-harness/skills/create-backlog-item/SKILL.md` (post-move, user-facing next-step suggestions)

### Requirements

#### complete-implementation/SKILL.md updates

1. Update the `Skill()` invocation for `create-backlog-item` to use `dh:create-backlog-item` (architect spec says line ~239 but verify actual line)
2. Update prose reference "what `create-backlog-item` produced" to "what `dh:create-backlog-item` produced" (architect spec says line ~250)
3. Update prose reference "`create-backlog-item --auto`" to "`dh:create-backlog-item --auto`" (architect spec says line ~251)

#### .claude/CLAUDE.md updates

4. Update Session Start line: `/create-backlog-item` to `/dh:create-backlog-item` and `/work-backlog-item` to `/dh:work-backlog-item`
5. Update Request Progression line: `create-backlog-item` to `dh:create-backlog-item` and `work-backlog-item` to `dh:work-backlog-item`
6. Update Backlog Operations line: `/create-backlog-item` to `/dh:create-backlog-item` and `/work-backlog-item` to `/dh:work-backlog-item`

#### stop-backlog-reminder.cjs updates

7. Update Skill() call: `"create-backlog-item"` to `"dh:create-backlog-item"`
8. Update Skill() call: `"work-backlog-item"` to `"dh:work-backlog-item"`

#### create-backlog-item/SKILL.md post-move updates

9. Update user-facing next-step suggestion: `/groom-backlog-item` to `/dh:groom-backlog-item`
10. Update user-facing next-step suggestion: `/work-backlog-item` to `/dh:work-backlog-item`

### Constraints

- Do NOT update intra-dh bare-name references (explicitly out of scope per Q1):
  - `plugins/development-harness/skills/interop/SKILL.md` line 116
  - `plugins/development-harness/skills/work-backlog-item/SKILL.md` lines 177, 217
  - `plugins/development-harness/skills/work-backlog-item/references/step-procedures.md`
- Do NOT update files under `plan/` (historical records per Q5)
- Do NOT update files under `.claude/backlog/` (backlog item files, not call sites)
- Read each file BEFORE editing to verify actual line content matches expected patterns from architect spec. Line numbers in the spec are approximate.

### Expected Outputs

- `plugins/python3-development/skills/complete-implementation/SKILL.md` (modified)
- `.claude/CLAUDE.md` (modified)
- `.claude/hooks/stop-backlog-reminder.cjs` (modified)
- `plugins/development-harness/skills/create-backlog-item/SKILL.md` (modified)

### Acceptance Criteria

1. `grep -c 'Skill(skill.*"create-backlog-item"' plugins/python3-development/skills/complete-implementation/SKILL.md` returns 0 (no bare-name Skill() calls)
2. `grep -c 'dh:create-backlog-item' plugins/python3-development/skills/complete-implementation/SKILL.md` returns at least 1
3. `.claude/CLAUDE.md` contains `/dh:create-backlog-item` and `/dh:work-backlog-item` in Session Start, Request Progression, and Backlog Operations sections
4. `.claude/hooks/stop-backlog-reminder.cjs` contains `dh:create-backlog-item` and `dh:work-backlog-item`
5. `plugins/development-harness/skills/create-backlog-item/SKILL.md` contains `/dh:groom-backlog-item` and `/dh:work-backlog-item` in next-step suggestions

### Verification Steps

1. Run: `grep -rn 'Skill(skill.*[":].*create-backlog-item' --include='*.md' --include='*.cjs' . | grep -v 'dh:create-backlog-item' | grep -v plan/ | grep -v '.claude/backlog/' | grep -v 'plugins/development-harness/skills/work-backlog-item/'` -- expect zero matches
2. Run: `grep -rn 'Skill(skill.*[":].*groom-backlog-item' --include='*.md' --include='*.cjs' . | grep -v 'dh:groom-backlog-item' | grep -v plan/ | grep -v '.claude/backlog/' | grep -v 'plugins/development-harness/skills/work-backlog-item/'` -- expect zero matches
3. Run: `grep -rn 'Skill(skill.*[":].*work-backlog-item' --include='*.md' --include='*.cjs' . | grep -v 'dh:work-backlog-item' | grep -v plan/ | grep -v '.claude/backlog/' | grep -v 'plugins/development-harness/skills/interop/'` -- expect zero matches
4. Run: `uv run prek run --files plugins/python3-development/skills/complete-implementation/SKILL.md` -- expect exit 0
5. Run: `uv run prek run --files .claude/CLAUDE.md` -- expect exit 0
6. Run: `uv run prek run --files .claude/hooks/stop-backlog-reminder.cjs` -- expect exit 0
7. Run: `uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md` -- expect exit 0

### CoVe Checks

- Key claims to verify:
  - The architect spec's line numbers (~239, ~250, ~251 in complete-implementation/SKILL.md) are approximate -- actual content must be matched by string, not line number
  - `.claude/hooks/stop-backlog-reminder.cjs` lines 8-9 contain the expected Skill() patterns
  - `create-backlog-item/SKILL.md` lines 197-198 contain `/groom-backlog-item` and `/work-backlog-item`
- Verification questions:
  1. Does `grep 'create-backlog-item' plugins/python3-development/skills/complete-implementation/SKILL.md` return the lines described in the architect spec?
  2. Does `grep 'Skill.*backlog' .claude/hooks/stop-backlog-reminder.cjs` match lines 8-9 patterns?
  3. Does `grep '/groom-backlog-item\|/work-backlog-item' plugins/development-harness/skills/create-backlog-item/SKILL.md` return lines 197-198?
- Evidence to collect:
  - Read each file before editing; confirm exact string to match
- Revision rule:
  - If any grep pattern does not match, read the file to find the actual pattern and update the edit accordingly. Do not guess line numbers.

### Handoff

Return: list of files modified, before/after snippet per edit, grep verification output confirming
zero bare-name references remain.

---

## Task T03: Full validation sweep -- confirm all acceptance criteria pass

- **Status**: NOT STARTED
- **Dependencies**: T02
- **Priority**: 3
- **Complexity**: Low
- **Agent**: general-purpose
- **Skills**: []
- **Accuracy Risk**: Low

### Context

T01 moved three skill directories. T02 updated all project-level callers. This task runs the
full validation suite from the architecture spec to confirm everything is correct.

Architecture spec: `plan/architect-backlog-lift-to-dh.md` (Deliverable 3)

### Objective

All 6 validation checks from the architect spec pass. Zero bare-name references to the three
moved skills remain in live (non-plan, non-backlog) files.

### Inputs

- Architecture spec Deliverable 3 (6 checks)
- Expected state: 3 skill dirs in `plugins/development-harness/skills/`, originals deleted, all callers updated with `dh:` prefix

### Requirements

Run each of the following checks and report pass/fail:

#### Check 1: No bare-name Skill() references in live files

1. Run: `grep -r 'Skill(skill.*[":].*create-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan . | grep -v 'dh:create-backlog-item'`
2. Run: `grep -r 'Skill(skill.*[":].*groom-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan . | grep -v 'dh:groom-backlog-item'`
3. Run: `grep -r 'Skill(skill.*[":].*work-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan . | grep -v 'dh:work-backlog-item'`

Expected: zero matches for all three. Exception: intra-dh bare names in
`plugins/development-harness/skills/work-backlog-item/` and
`plugins/development-harness/skills/interop/` are valid and expected.

#### Check 2: Skill directories exist in destination

4. Run: `test -f plugins/development-harness/skills/create-backlog-item/SKILL.md && echo PASS || echo FAIL`
5. Run: `test -f plugins/development-harness/skills/groom-backlog-item/SKILL.md && echo PASS || echo FAIL`
6. Run: `test -f plugins/development-harness/skills/work-backlog-item/SKILL.md && echo PASS || echo FAIL`

#### Check 3: Originals removed

7. Run: `test ! -d .claude/skills/create-backlog-item && test ! -d .claude/skills/groom-backlog-item && test ! -d .claude/skills/work-backlog-item && echo PASS || echo FAIL`

#### Check 4: Reference file integrity

8. Verify all 10 reference files exist at destination (list from T01 requirement 5)

#### Check 5: Linting passes

9. Run prek on all modified files:
   - `uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md`
   - `uv run prek run --files plugins/development-harness/skills/groom-backlog-item/SKILL.md`
   - `uv run prek run --files plugins/development-harness/skills/work-backlog-item/SKILL.md`
   - `uv run prek run --files plugins/python3-development/skills/complete-implementation/SKILL.md`
   - `uv run prek run --files .claude/CLAUDE.md`
   - `uv run prek run --files .claude/hooks/stop-backlog-reminder.cjs`

#### Check 6: Broader bare-name sweep (slash references)

10. Run: `grep -rn '/create-backlog-item\|/groom-backlog-item\|/work-backlog-item' --include='*.md' --include='*.cjs' --exclude-dir=plan --exclude-dir=.claude/backlog . | grep -v 'dh:'`

Expected: zero matches. Any matches are additional callers that need the `dh:` prefix -- report
them as findings.

### Constraints

- This task is read-only validation -- do NOT modify any files
- If any check fails, report the failure clearly with the exact output but do NOT attempt fixes (those would be follow-up tasks)
- Intra-dh bare names (in `plugins/development-harness/skills/`) are expected and valid -- filter them from Check 1 results

### Expected Outputs

- No file changes (validation only)
- Validation report in handoff

### Acceptance Criteria

1. Check 1 returns zero unexpected bare-name Skill() references
2. Check 2 confirms all 3 SKILL.md files exist at destination
3. Check 3 confirms all 3 original directories are deleted
4. Check 4 confirms all 10 reference files exist at destination
5. Check 5 shows all prek runs exit 0
6. Check 6 returns zero unexpected bare-name slash references

### Verification Steps

1. Each check command above is itself a verification step -- run them in sequence
2. Compile results into a pass/fail summary table
3. Overall verdict: PASS only if all 6 checks pass

### Handoff

Return: pass/fail table for all 6 checks, any unexpected grep matches, overall PASS/FAIL verdict.

---

## Context Manifest

Generated by context-gathering agent on 2026-03-18

### How This Currently Works: Backlog Skills Ecosystem

When a user invokes a backlog-related workflow, the request routes to three orchestrator-facing skills located at project level (`.claude/skills/`): `create-backlog-item`, `groom-backlog-item`, and `work-backlog-item`. These skills manage the end-to-end backlog lifecycle — capturing new items, refining them through grooming, and bridging them into SAM planning.

**Current Architecture (Before Move)**:

The three skills live in `.claude/skills/` where they are discoverable project-wide:
- `.claude/skills/create-backlog-item/SKILL.md` (1 file) — Guides item capture in three modes: guided intake (interactive), quick entry, or fully autonomous. Validates required fields, detects duplicates, invokes `mcp__backlog__backlog_add` MCP tool, and optionally creates GitHub Issues for P0/P1 items.
- `.claude/skills/groom-backlog-item/SKILL.md` + 2 references — Orchestrates autonomous backlog refinement. Spawns parallel teams of agents (fact-checker, impact-analyst, rtica-assessor, classifier, groomer) sized based on issue complexity. Writes groomed content back to per-item files via MCP tools. Contains complex Mermaid workflows that agents must follow exactly.
- `.claude/skills/work-backlog-item/SKILL.md` + 8 references — Bridges backlog items into SAM planning (`/add-new-feature`). Routes based on invocation mode (interactive browser, `--auto`, `close`, `resolve`, `setup-github`, etc.). Three-strategy fallback chain to match items by substring, type/topic filter, or LLM semantic match. Enforces RT-ICA gate before planning. Contains extensive reference documentation for modes, procedures, and decision trees.

**How Callers Currently Invoke Them**:

Project-level callers use bare slash syntax — `/create-backlog-item`, `/groom-backlog-item`, `/work-backlog-item` — because the skills are at project level. These patterns appear in:
1. `.claude/CLAUDE.md` (line 32, Session Start procedures; line 226, Request Progression; line 256, Backlog Operations)
2. `.claude/hooks/stop-backlog-reminder.cjs` (lines 8-9, end-of-session reminders)
3. `plugins/python3-development/skills/complete-implementation/SKILL.md` (lines ~239, ~250-251, in recursive follow-up routing)
4. Each skill's own user-facing suggestions (e.g., create-backlog-item suggests "Next steps: /groom-backlog-item {title}")

**Intra-Plugin Callers (Important Distinction)**:

Within `plugins/development-harness/`, the `interop/SKILL.md` and the moved skills themselves will use bare names (no `dh:` prefix) because they work within the same plugin. This is the "intra-plugin bare names" rule from the architect spec Q1 decision. These continue to work after the move without changes:
- `plugins/development-harness/skills/interop/SKILL.md:116` invokes `Skill(skill="work-backlog-item", args="#N")`
- `plugins/development-harness/skills/work-backlog-item/SKILL.md:177` invokes `Skill(skill: "create-backlog-item", args: "--auto {title}")`
- `plugins/development-harness/skills/work-backlog-item/SKILL.md:217` invokes `Skill(skill: "groom-backlog-item", args: "{item title}")`

**MCP Server (NOT Moving)**:

The backlog MCP server lives at `.claude/skills/backlog/` and stays project-level. All three skills invoke it via `mcp__backlog__*` tool calls (backlog_add, backlog_list, backlog_view, backlog_groom, backlog_update, backlog_close, backlog_resolve). This is the canonical store for backlog item state and GitHub Issue sync logic.

**Plugin Context After Move**:

The development-harness plugin is a harness for controlled experimentation with features before they are released to marketplace. Moving backlog intake skills into dh makes the plugin self-contained — users running in dh context have all three backlog skills available without needing to reference project-level skills. This supports faster iteration on backlog workflow enhancements within the harness.

### For New Feature Implementation: What Needs to Connect

#### T01: Directory Move

Copy three skill directories verbatim from `.claude/skills/` to `plugins/development-harness/skills/`, preserving all subdirectories and file contents. No file modification during the copy. Delete originals only after verifying:
1. Destination files exist with correct counts (1, 3, 9 files respectively)
2. All reference files are present at destination paths
3. Linting passes on all three SKILL.md files in destination

**Critical invariant**: The reference links within each skill (e.g., `[validation-plan.md](./references/validation-plan.md)`) remain valid because directory structure is preserved. All `./references/` relative links continue to work.

**Plugin auto-discovery**: The `plugins/development-harness/plugin.json` has no explicit `skills` array, so auto-discovery will register the three new SKILL.md files automatically. No manifest edits needed.

#### T02: Project-Level Caller Updates

Four files reference the moved skills and need `dh:` prefix for project-level calls:

1. **`plugins/python3-development/skills/complete-implementation/SKILL.md`** (lines ~239, ~250-251):
   - `Skill(skill: "create-backlog-item", ...)` → `Skill(skill: "dh:create-backlog-item", ...)`
   - Prose references: "what `create-backlog-item` produced" → "what `dh:create-backlog-item` produced"
   - Prose references: "`create-backlog-item --auto`" → "`dh:create-backlog-item --auto`"

2. **`.claude/CLAUDE.md`** (three locations):
   - Line 32 (Session Start): `/create-backlog-item` → `/dh:create-backlog-item`, `/work-backlog-item` → `/dh:work-backlog-item`
   - Line 226 (Request Progression): same updates
   - Line 256 (Backlog Operations): same updates

3. **`.claude/hooks/stop-backlog-reminder.cjs`** (lines 8-9):
   - `Skill(skill: "create-backlog-item", ...)` → `Skill(skill: "dh:create-backlog-item", ...)`
   - `Skill(skill: "work-backlog-item", ...)` → `Skill(skill: "dh:work-backlog-item", ...)`

4. **`plugins/development-harness/skills/create-backlog-item/SKILL.md`** (lines ~197-198, after move):
   - User-facing next-step suggestions: `/groom-backlog-item {title}` → `/dh:groom-backlog-item {title}`
   - User-facing next-step suggestions: `/work-backlog-item {title}` → `/dh:work-backlog-item {title}`

**Key distinction**: Intra-dh bare names (e.g., `work-backlog-item` calling `create-backlog-item` with bare name) are explicitly NOT changed per Q1 decision.

#### T03: Validation Sweep

Confirms all acceptance criteria pass — a read-only verification task with no file modifications.

### Technical Reference Details

#### Directory Structure — Source vs Destination

**Source** (before move):
```text
.claude/skills/create-backlog-item/
  SKILL.md

.claude/skills/groom-backlog-item/
  SKILL.md
  references/
    issue-classification.md
    groomer-agent.md

.claude/skills/work-backlog-item/
  SKILL.md
  references/
    validation-plan.md
    sam-definition.md
    example-sessions.md
    error-handling.md
    auto-mode.md
    step-procedures.md
    github-integration.md
    close-resolve-procedure.md
```

**Destination** (after move):
```text
plugins/development-harness/skills/create-backlog-item/
  SKILL.md

plugins/development-harness/skills/groom-backlog-item/
  SKILL.md
  references/
    issue-classification.md
    groomer-agent.md

plugins/development-harness/skills/work-backlog-item/
  SKILL.md
  references/
    validation-plan.md
    sam-definition.md
    example-sessions.md
    error-handling.md
    auto-mode.md
    step-procedures.md
    github-integration.md
    close-resolve-procedure.md
```

#### Skill Invocation Patterns

**Project-level calls** (after move):
```bash
Skill(skill: "dh:create-backlog-item", args: "--auto {title}")
Skill(skill: "dh:groom-backlog-item", args: "{title}")
Skill(skill: "dh:work-backlog-item", args: "resolve {title}")
```

**Intra-dh bare-name calls** (unchanged after move):
```bash
Skill(skill: "create-backlog-item", args: "--auto {title}")         # from work-backlog-item/SKILL.md:177
Skill(skill: "groom-backlog-item", args: "{title}")               # from work-backlog-item/SKILL.md:217
Skill(skill: "work-backlog-item", args: "#N")                     # from interop/SKILL.md:116
```

#### Linting Requirements

Each SKILL.md file uses prek (Rust-based pre-commit replacement):
```bash
uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md
uv run prek run --files plugins/development-harness/skills/groom-backlog-item/SKILL.md
uv run prek run --files plugins/development-harness/skills/work-backlog-item/SKILL.md
```

Also lint the four modified caller files:
```bash
uv run prek run --files plugins/python3-development/skills/complete-implementation/SKILL.md
uv run prek run --files .claude/CLAUDE.md
uv run prek run --files .claude/hooks/stop-backlog-reminder.cjs
uv run prek run --files plugins/development-harness/skills/create-backlog-item/SKILL.md  # post-move
```

#### MCP Tool Invocations (Unchanged)

All three skills continue to invoke the same MCP tools after the move — skill location does not affect MCP calls:
- `mcp__backlog__backlog_add` — create new items (create-backlog-item)
- `mcp__backlog__backlog_list` — load items (groom-backlog-item, work-backlog-item)
- `mcp__backlog__backlog_view` — fetch specific item (work-backlog-item)
- `mcp__backlog__backlog_groom` — write groomed content (groom-backlog-item)
- `mcp__backlog__backlog_update` — update item fields (complete-implementation for follow-up routing)
- `mcp__backlog__backlog_close` — dismiss items (work-backlog-item)
- `mcp__backlog__backlog_resolve` — mark items complete (work-backlog-item, complete-implementation)

The MCP server at `.claude/skills/backlog/` remains at project level and is the source of truth for all backlog state.

#### No Plugin Manifest Changes

The `plugins/development-harness/plugin.json` does NOT need manual edits because:
1. Auto-discovery scans `skills/` subdirectories for SKILL.md files
2. All three new SKILL.md files will be registered automatically
3. No `skills` array is declared in plugin.json (which would override auto-discovery)

#### Critical Paths and File Locations

Source paths (before move):
- `.claude/skills/create-backlog-item/SKILL.md`
- `.claude/skills/groom-backlog-item/SKILL.md` and `references/` (2 files)
- `.claude/skills/work-backlog-item/SKILL.md` and `references/` (8 files)

Destination paths (after move):
- `plugins/development-harness/skills/create-backlog-item/SKILL.md`
- `plugins/development-harness/skills/groom-backlog-item/SKILL.md` and `references/` (2 files)
- `plugins/development-harness/skills/work-backlog-item/SKILL.md` and `references/` (8 files)

Files to update with `dh:` prefix:
- `plugins/python3-development/skills/complete-implementation/SKILL.md`
- `.claude/CLAUDE.md`
- `.claude/hooks/stop-backlog-reminder.cjs`
- `plugins/development-harness/skills/create-backlog-item/SKILL.md` (post-move)

---

## Discovered During Implementation

_Session Date: 2026-03-18_

During implementation, we discovered that the architect spec's claim that "all `./references/` relative
links within each skill directory remain valid because the directory structure is preserved" was only
partially true. While intra-skill references (e.g., `./references/validation-plan.md`) stayed valid,
cross-skill links pointing upward to `.claude/docs/` and `.claude/skills/` broke because the path depth
changed from `.claude/skills/{skill}/` (2 levels deep) to `plugins/development-harness/skills/{skill}/`
(4 levels deep). This required fixing all upward-traversal links during T01.

Additionally, the architect spec documented only 3 reference updates in `complete-implementation/SKILL.md`
(lines 239, 250, 251), but the actual file contained 6 bare prose references that needed `dh:` prefix
updates (also lines 274, 287, 358, 371). The `create-backlog-item/SKILL.md` lines 197-198 next-step slash
references were missed in T02 and caught post-review.

**Key Discoveries:**

1. **Path depth change breaks cross-directory upward links**: Moving from `.claude/skills/{skill}/` to
   `plugins/development-harness/skills/{skill}/` adds two directory levels. Any link using `../../` to
   reach `.claude/docs/` or `.claude/skills/` must become `../../../../`. Three LK001-flagged broken links
   were fixed in `work-backlog-item/SKILL.md` during T01. Future moves of project-level skills into
   plugins must audit all upward-traversal relative paths for depth correction.

2. **github-integration.md cross-skill link required deeper path correction**: `references/github-integration.md`
   had `../../gh/references/issue-stories.md` which resolved correctly at the old depth but broke at plugin
   depth. Fixed to `../../../../../.claude/skills/gh/references/issue-stories.md`. Any reference file
   pointing to sibling `.claude/skills/` directories requires similar depth correction when moved into
   `plugins/`.

3. **complete-implementation/SKILL.md bare reference count was undercounted in spec**: The architect spec
   documented 2 prose references at lines 250-251. The actual scan found 6 prose locations (lines 250,
   251, 274, 287, 358, 371) requiring `dh:` prefix. Future specs for caller-update tasks should use grep
   to enumerate ALL instances rather than enumerating by line number.

4. **create-backlog-item/SKILL.md next-step suggestions missed in T02**: Lines 197-198 contain user-facing
   slash command suggestions (`/groom-backlog-item`, `/work-backlog-item`). These appear in the file that
   was moved (not the caller files listed in T02), and were caught during post-T02 review. The spec listed
   them under Deliverable 2 File 4, but the T02 task description did not surface them prominently enough
   for the implementing agent.

5. **Intra-dh bare names confirmed working**: `interop/SKILL.md` and `work-backlog-item/SKILL.md` internal
   bare-name `Skill()` calls to sibling skills were left unchanged and confirmed correct per Q1 resolution.
   Bare names resolve within the calling plugin's own namespace without requiring a `dh:` prefix.

### Updated Technical Details

- Path depth change formula: old depth 2 (`.claude/skills/{skill}/`) to new depth 4
  (`plugins/development-harness/skills/{skill}/`). Upward-traversal chains gain 2 `../` segments per hop.
- `complete-implementation/SKILL.md` total dh: prefix updates: 7 locations (1 `Skill()` call + 6 prose references).
- `create-backlog-item/SKILL.md` post-move updates: lines 197-198 (next-step slash command suggestions).

### Gotchas for Future Developers

- When moving any skill from `.claude/skills/` into `plugins/{plugin-name}/skills/`, run `prek` linting
  immediately after the copy step (before deleting originals) to catch LK001 broken relative links before
  the originals are gone.
- Enumerate all bare-name references in caller files using grep rather than manual line-number enumeration
  in the spec. Spec-level line number enumeration drifts and undercounts.
- Skill files that are being moved AND updated should be listed in both the move task and the caller-update
  task descriptions to avoid missing the updates.
