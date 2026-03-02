---
description: "Route follow-up task files to backlog instead of orphaning them when recursion is skipped in complete-implementation (Fixes #381)"
version: "1.0"
tasks:
  - T1: Replace Recursive Follow-up Handling section in complete-implementation/SKILL.md
  - T2: Update Recursive Follow-up section and data flow diagram in local-workflow.md
task_exports:
  enabled: false
  directory: "TASK"
---

# Task Plan: Follow-up Task File Routing to Backlog

## Context

**Backlog item**: complete-implementation: route follow-up task files to backlog instead of orphaning
**GitHub Issue**: #381
**Priority**: P1
**Feature slug**: followup-routing
**Architecture spec**: [plan/architect-followup-routing.md](./architect-followup-routing.md)
**Codebase analysis**: [plan/codebase/followup-routing-patterns.md](./codebase/followup-routing-patterns.md)
**Feature context**: [plan/feature-context-followup-routing.md](./feature-context-followup-routing.md)

**Problem statement**: The `complete-implementation` skill's "Recursive Follow-up Handling" section
unconditionally recurses into `/implement-feature` when the `code-reviewer` creates follow-up task
files. When the orchestrator skips recursion (session timeout, deferred scope, context compaction),
follow-up files are orphaned at `plan/` with no backlog item and no rediscovery path. This has
occurred 3+ times.

**Resolution**: Replace the unconditional recursion with a 4-step routing workflow:
1. Detect follow-up files from code-reviewer ARTIFACTS output (with glob fallback)
2. For each file, search backlog by title keywords derived from the filename
3. Link to existing backlog item or create a new one — BEFORE the recursion decision
4. Recurse only if follow-up priority is High AND feature slug matches parent; otherwise defer

**Architecture decisions** (from architect spec, all accepted):
- ADR-1: Routing logic lives in SKILL.md as orchestrator instructions (no new Python script)
- ADR-2: "Same priority" = follow-up file `## Priority` field is `High`
- ADR-3: "Same session scope" = same feature slug extracted from filename
- ADR-4: Backlog item always created/linked BEFORE recursion decision
- ADR-5: Follow-up detection uses ARTIFACTS as primary + glob as fallback

---

## Dependency Analysis

T1 and T2 write to different files and have no content dependency on each other.
They can run in parallel immediately.

```text
Priority 1 (no dependencies, parallel):
  T1: complete-implementation/SKILL.md
  T2: local-workflow.md
```

---

## Sync Checkpoint

**After T1 + T2 complete:**

- Both files pass `uv run prek run --files <file>` with exit code 0
- T1 output contains all 4 routing steps (detect, search, link/create, gate)
- T2 output reflects the new routing behavior with updated data flow diagram
- No orphaning path exists in either document (unconditional recursion is gone)

---

## Tasks

---

### Task T1: Replace Recursive Follow-up Handling section in complete-implementation/SKILL.md

---
task: T1
title: Replace Recursive Follow-up Handling section in complete-implementation/SKILL.md
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
parallelize-with: ["T2"]
issue-classification: missing-guardrail
scenario-target: "Orchestrator skips recursion -> follow-up task file is orphaned without backlog tracking"
---

## Context

This task was identified from architecture spec [plan/architect-followup-routing.md](./architect-followup-routing.md)
as the primary skill document change for Issue #381.

The current `## Recursive Follow-up Handling` section in
`.claude/skills/complete-implementation/SKILL.md` (lines 75-83) reads:

```text
If Phase 1 creates follow-up task files (expected naming: `plan/tasks-{N}-{slug}-followup-{k}.md`), run:

Skill(skill="implement-feature", args="{followup_task_file_path}")

Then re-run `complete-implementation` on the follow-up task file.
```

This section contains no backlog integration and no routing guard. When the orchestrator skips
recursion, follow-up files are silently orphaned. The section must be replaced with a 4-step
routing workflow that always links follow-up files to backlog items before deciding on recursion.

**Files to read before starting:**

- `.claude/skills/complete-implementation/SKILL.md` — the skill document to modify (read it first)
- `plan/architect-followup-routing.md` — architecture decisions, step-by-step routing design,
  filename-to-title derivation algorithm, error handling table, and flowcharts

## Objective

Replace the `## Recursive Follow-up Handling` section in
`.claude/skills/complete-implementation/SKILL.md` with a 4-step routing workflow that ensures
every follow-up task file is linked to a backlog item before any recursion decision is made.

## Required Inputs

- `.claude/skills/complete-implementation/SKILL.md` — file to modify
- `plan/architect-followup-routing.md` — Step 1-4 design, filename-to-title algorithm,
  error handling table, flowcharts (Component Design section)
- `plan/codebase/followup-routing-patterns.md` — verified CLI command signatures for
  `backlog.py list`, `backlog.py update --plan`, `create-backlog-item --auto`
- `.claude/rules/local-workflow.md` — confirms existing skill invocation syntax patterns

## Requirements

### Routing step content

1. Replace the current `## Recursive Follow-up Handling` section (lines 75-83) with the
   4-step routing workflow defined in `plan/architect-followup-routing.md` Component Design section.
2. Step 1 (Detect): Extract follow-up file paths from the code-reviewer's ARTIFACTS `Task files:`
   list. If list is empty or absent, run a confirmatory glob: `plan/tasks-*-{slug}-followup-*.md`
   where `{slug}` is extracted from the parent task file path. If both are empty, skip routing.
3. Step 2 (Search): Derive a human-readable search title from each follow-up filename using this
   algorithm: strip directory prefix, strip `.md`, strip `tasks-{N}-` prefix, strip
   `-followup-{k}` suffix, replace hyphens with spaces. Run:
   `uv run .claude/skills/backlog/scripts/backlog.py list --format json -R Jamie-BitFlight/claude_skills`
   and check each item's `title` field for case-insensitive substring match against the derived
   title keywords.
4. Step 3 (Link or Create): If a match is found, run:
   `uv run .claude/skills/backlog/scripts/backlog.py update "{matched_title}" --plan "{followup_path}" -R Jamie-BitFlight/claude_skills`
   If no match is found, invoke `Skill(skill: "create-backlog-item", args: "--auto {derived_title}")`,
   then run `backlog.py update "{derived_title}" --plan "{followup_path}" -R Jamie-BitFlight/claude_skills`.
   If `backlog.py update` exits code 1 after creation (title mismatch), re-list and retry using
   the most recently added item's exact title.
5. Step 4 (Recursion Gate): Only recurse when BOTH conditions are true: (a) follow-up file slug
   matches parent task file slug, AND (b) follow-up file `## Priority` section contains `High`.
   If recursion: run `Skill(skill="implement-feature", args="{followup_path}")` then re-run
   `complete-implementation`. If deferred: log the follow-up path, backlog item title, priority
   value, and scope match result.

### Error handling

6. Include error handling inline with each step, matching the error handling table in
   `plan/architect-followup-routing.md`: missing `## Priority` section defaults to Medium (defer);
   unexpected filename format creates a new backlog item with the full filename as title;
   `create-backlog-item --auto` duplicate detection is treated as "match found."

### Document integrity

7. Preserve all content outside the `## Recursive Follow-up Handling` section unchanged.
8. Preserve the existing YAML frontmatter of the SKILL.md file exactly.
9. All code fences in the replacement section must have language specifiers
   (use `bash` for shell commands, `text` for Skill invocations).
10. Blank lines before and after all fenced code blocks (MD031).

## Constraints

- Do not add a new Python script. Routing logic is orchestrator instructions only (ADR-1).
- Do not change the `## Priority` values on the recursion gate — only `High` qualifies (ADR-2).
- Do not modify any section outside `## Recursive Follow-up Handling`.
- Do not remove the `## Post-Phase-6: Surface Divergence Findings` section.
- All backlog operations must go through `backlog.py`, not direct file writes to `.claude/backlog/`.
- Skill invocations use the exact syntax: `Skill(skill: "name", args: "...")` for `args:` form or
  `Skill(skill="name", args="...")` for `=` form — match the existing pattern in the file.

## Expected Outputs

- `.claude/skills/complete-implementation/SKILL.md` modified: `## Recursive Follow-up Handling`
  section replaced with 4-step routing workflow

## Acceptance Criteria

1. The `## Recursive Follow-up Handling` section exists and contains Steps 1, 2, 3, and 4 as
   distinct labeled subsections.
2. Step 1 references both ARTIFACTS detection and the glob pattern
   `plan/tasks-*-{slug}-followup-*.md` as fallback.
3. Step 2 includes the filename-to-title derivation algorithm (5-step strip sequence) and the
   `backlog.py list --format json` command with `-R Jamie-BitFlight/claude_skills`.
4. Step 3 contains both branches: match found (`backlog.py update --plan`) and no match
   (`create-backlog-item --auto` then `backlog.py update --plan`), plus the title-mismatch retry.
5. Step 4 flowchart or decision logic requires BOTH slug match AND `High` priority for recursion;
   deferred path logs the follow-up path and reason.
6. Error handling is present for: missing `## Priority` (default Medium, defer), unexpected
   filename format, and `create-backlog-item --auto` duplicate detection.
7. All content outside `## Recursive Follow-up Handling` is unchanged (verified by diffing other
   section headers).
8. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` exits code 0.

## Verification Steps

1. Read `.claude/skills/complete-implementation/SKILL.md` after modification and confirm the
   section headers Phase 1 through Phase 6, Post-Phase-6, and Recursive Follow-up Handling
   are all present with correct content.
2. Grep for the old unconditional recursion text to confirm it is gone:
   `grep -n "If Phase 1 creates follow-up" .claude/skills/complete-implementation/SKILL.md`
   Expected result: zero matches, or one match inside Step 1 description only (not as the
   sole routing instruction).
3. Grep for Step labels:
   `grep -n "Step [1234]" .claude/skills/complete-implementation/SKILL.md`
   Expected: at least 4 matches (one per step).
4. Grep for the backlog update command:
   `grep -n "backlog.py update" .claude/skills/complete-implementation/SKILL.md`
   Expected: at least 2 matches (one for each branch of Step 3).
5. Grep for the recursion gate condition:
   `grep -n "High" .claude/skills/complete-implementation/SKILL.md`
   Expected: at least one match in the routing section specifying High priority as the gate.
6. Run linter:
   `uv run prek run --files .claude/skills/complete-implementation/SKILL.md`
   Expected: exit code 0 with no MD031 or other errors.

## CoVe Checks

- Key claims to verify:
  - `backlog.py update` accepts a title substring as selector and exits code 1 when not found
  - `create-backlog-item --auto` mode uses `--no-create-issue` by default
  - Follow-up filename format `tasks-{N}-{slug}-followup-{k}.md` is correct per code-reviewer agent
- Verification questions:
  1. Does `backlog.py update` use `find_item()` which does case-insensitive title substring
     matching and exits code 1 on no match? Confirm by reading
     `.claude/skills/backlog/scripts/backlog.py` lines 1768-1802.
  2. Does `create-backlog-item --auto` always include `--no-create-issue` in its `backlog add`
     call? Confirm by reading `.claude/skills/create-backlog-item/SKILL.md` lines 163-169.
  3. Does the code-reviewer agent naming convention produce `tasks-{N}-{slug}-followup-{k}.md`?
     Confirm by reading `plugins/python3-development/agents/code-reviewer.md` lines 175-192.
- Evidence to collect:
  - Confirm `find_item()` function signature and exit code behavior at
    `.claude/skills/backlog/scripts/backlog.py` lines 310-333
  - Confirm `--no-create-issue` flag in create-backlog-item auto mode at
    `.claude/skills/create-backlog-item/SKILL.md` lines 163-169
  - Confirm follow-up file naming at
    `plugins/python3-development/agents/code-reviewer.md` lines 175-192
- Revision rule:
  If any check reveals a different command signature, flag name, or behavior than described in
  the architecture spec, update the routing instructions to match the actual behavior and note
  what changed in the handoff.

## Handoff

Return:
- Confirmation that `## Recursive Follow-up Handling` was replaced
- Paste or quote the final Step 4 recursion gate condition as written (for cross-reference with T2)
- Result of `uv run prek run --files .claude/skills/complete-implementation/SKILL.md`
- Any deviations from the architecture spec and what was substituted

---

### Task T2: Update Recursive Follow-up section and data flow diagram in local-workflow.md

---
task: T2
title: Update Recursive Follow-up section and data flow diagram in local-workflow.md
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: low
accuracy-risk: low
parallelize-with: ["T1"]
---

## Context

This task was identified from architecture spec [plan/architect-followup-routing.md](./architect-followup-routing.md)
as the reference documentation update for Issue #381.

The current `### Recursive Follow-up` subsection in `.claude/rules/local-workflow.md`
(lines 258-264) reads:

```text
### Recursive Follow-up

If Phase 1 (code review) creates follow-up task files (naming: `plan/tasks-{N}-{slug}-followup-{k}.md`),
the workflow recurses:

1. Run `/implement-feature` on the follow-up task file
2. Run `/complete-implementation` on the follow-up task file
```

This description omits the new backlog routing step and presents recursion as unconditional.
The data flow diagram section (lines 365-366) also shows unconditional recursion with
`Recurse: /implement-feature + /complete-implementation` without mentioning the routing gate.

Both must be updated to reflect the routing behavior introduced by T1.

**Files to read before starting:**

- `.claude/rules/local-workflow.md` — the file to modify (read it first)
- `plan/architect-followup-routing.md` — the "Modified Component: local-workflow.md" section
  (lines 183-197) and the data flow section (lines 199-237) for the exact replacement content

## Objective

Update the `### Recursive Follow-up` subsection and the data flow diagram in
`.claude/rules/local-workflow.md` to accurately describe the routing behavior: detect follow-up
files, link each to a backlog item (new or existing), then recurse only if same slug AND High
priority.

## Required Inputs

- `.claude/rules/local-workflow.md` — file to modify
- `plan/architect-followup-routing.md` — replacement content for Recursive Follow-up section
  (lines 183-197) and data flow (lines 199-237)

## Requirements

### Recursive Follow-up subsection

1. Replace the body of `### Recursive Follow-up` (currently lines 258-264) with a description
   of the new 6-point routing behavior from `plan/architect-followup-routing.md`:
   1. Follow-up files detected from code-reviewer ARTIFACTS output (with glob fallback)
   2. Each follow-up is searched against backlog by title keywords from filename
   3. Match found: `backlog update --plan` attaches the follow-up
   4. No match: `create-backlog-item --auto` creates item, then `backlog update --plan` attaches
   5. Recursion only if same feature slug AND follow-up priority is High
   6. Otherwise: deferred to backlog, no recursion

### Data flow diagram

2. In the data flow diagram (the `\`\`\`text` block near the bottom of the file), replace the
   existing follow-up recursion lines:
   ```text
   ├─ [If follow-up tasks created]
   │    └─ Recurse: /implement-feature + /complete-implementation
   ```
   With the new routing representation:
   ```text
   ├─ [If follow-up task files created by code-reviewer]
   │    ├─ Route each follow-up:
   │    │    ├─ Search backlog by title keywords from filename
   │    │    ├─ Match found: backlog update --plan {followup_path}
   │    │    └─ No match: create-backlog-item --auto, then backlog update --plan
   │    └─ Gate: same slug AND High priority -> Recurse: /implement-feature + /complete-implementation
   │             otherwise -> Deferred to backlog (no recursion)
   ```

### Document integrity

3. Preserve all other sections unchanged, including section headers, agent file tables, and
   CLI tool documentation.
4. All code fences must have language specifiers. The data flow diagram uses `text`.
5. Blank lines before and after all fenced code blocks (MD031).

## Constraints

- Do not add new sections or headings outside the two areas specified.
- Do not modify the Phase Sequence table, Agent File Locations table, or Cross-Plugin Dependency section.
- Do not change line content outside the `### Recursive Follow-up` subsection and the
  follow-up lines in the data flow diagram.

## Expected Outputs

- `.claude/rules/local-workflow.md` modified: `### Recursive Follow-up` subsection updated,
  data flow diagram follow-up lines updated

## Acceptance Criteria

1. The `### Recursive Follow-up` subsection describes the 6-point routing behavior, not
   unconditional recursion.
2. The subsection mentions: backlog search, `backlog update --plan`, `create-backlog-item --auto`,
   same-slug condition, High-priority condition, and deferral.
3. The data flow diagram includes a routing block between "follow-up tasks created" and
   "Recurse: /implement-feature + /complete-implementation".
4. The data flow diagram shows the gate condition (same slug AND High priority) before recursion.
5. No content outside the two target areas has changed (verified by reading all other section
   headers and their immediate content).
6. `uv run prek run --files .claude/rules/local-workflow.md` exits code 0.

## Verification Steps

1. Read `.claude/rules/local-workflow.md` after modification and confirm the `### Recursive Follow-up`
   subsection no longer says "the workflow recurses" as its first statement.
2. Grep for the old unconditional description:
   `grep -n "workflow recurses" .claude/rules/local-workflow.md`
   Expected: zero matches.
3. Grep for routing keywords:
   `grep -n "backlog update\|create-backlog-item\|same.*slug\|High priority\|deferred" .claude/rules/local-workflow.md`
   Expected: at least 4 distinct matches covering the routing behavior.
4. Grep for the data flow gate:
   `grep -n "Gate\|same slug\|High priority" .claude/rules/local-workflow.md`
   Expected: at least one match in the data flow diagram block.
5. Run linter:
   `uv run prek run --files .claude/rules/local-workflow.md`
   Expected: exit code 0 with no MD031 or other errors.

## Handoff

Return:
- Confirmation that `### Recursive Follow-up` subsection was replaced
- Confirmation that the data flow diagram routing block was added
- Result of `uv run prek run --files .claude/rules/local-workflow.md`
- Paste the final data flow diagram routing block as written (4-6 lines)
