---
name: complete-implementation
argument-hint: <task-file-path>
user-invocable: true
description: "Holistic completion workflow after a feature's tasks are marked COMPLETE: code review, feature verification, integration check, documentation drift audit/update, and context refinement. Creates follow-up task files when issues are found."
compatibility: Python 3.11+
metadata:
  version: "1.0.0"
  last_updated: "2026-03-02"
---
# Complete Implementation (Quality Gates + Recursion)

You MUST validate that the implemented feature meets its goals and quality gates. If follow-up task files are created, route them to backlog items first, then recurse only when the follow-up matches the current scope and priority (see Recursive Follow-up Handling section).

<task_file>
$ARGUMENTS
</task_file>

---

## Phase 1: Code Review

Launch `code-reviewer` with the task file path.

---

## Phase 2: Feature Verification (goal-backward)

Launch `feature-verifier` with the task file path.

---

## Phase 3: Integration Check

Launch `integration-checker` with the task file path.

---

## Phase 4: Documentation Drift Audit

Launch `doc-drift-auditor` with the task file path (audit-only).

---

## Phase 5: Documentation Update (if drift found)

If drift exists or docs must be updated for the feature, launch `service-docs-maintainer`.

---

## Phase 6: Context Refinement

Launch `context-refinement` to update the task file Context Manifest with discoveries from implementation (only if needed).

---

## Recursive Follow-up Handling

After all six phases complete, route any follow-up task files created by Phase 1 (code-reviewer) to the backlog before deciding on recursion. This ensures no follow-up file is orphaned when the orchestrator skips recursion.

### Step 1: Detect Follow-up Files

Extract file paths from the `Task files:` list in the code-reviewer's ARTIFACTS output (the `STATUS: DONE` block from Phase 1).

If the `Task files:` list is empty or absent, run a confirmatory glob:

```bash
plan/tasks-*-{slug}-followup-*.md
```

Where `{slug}` is extracted from the parent task file path (`plan/tasks-{N}-{slug}.md` -- strip `tasks-{N}-` prefix and `.md` suffix).

If both ARTIFACTS and glob return empty: skip the entire routing section (no follow-ups to route).

**Error handling**: If a glob returns files from a different feature slug, filter results to only include files matching the parent task file's slug.

### Step 2: Search Backlog by Title Keywords

For each follow-up file, derive a search title from the filename using this algorithm:

```text
Input:  plan/tasks-8-data-validation-followup-1.md
Step 1: Strip directory prefix      --> tasks-8-data-validation-followup-1.md
Step 2: Strip .md extension         --> tasks-8-data-validation-followup-1
Step 3: Strip tasks-{N}- prefix     --> data-validation-followup-1
Step 4: Strip -followup-{k} suffix  --> data-validation
Step 5: Replace hyphens with spaces --> data validation
Output: "data validation"
```

Search the backlog for an existing item matching these keywords:

```bash
uv run .claude/skills/backlog/scripts/backlog.py list --format json -R Jamie-BitFlight/claude_skills
```

Parse the JSON output. For each item, check if the derived title keywords appear (case-insensitive substring match) in the item's `title` field.

**Error handling**: If `backlog.py list` fails, log the error, skip the search, and proceed to Step 3 as "no match found" for each follow-up. If the follow-up filename does not match the expected `tasks-{N}-{slug}-followup-{k}.md` pattern, log a warning and use the full filename (without directory prefix and `.md` extension) as the derived title.

### Step 3: Link or Create Backlog Item

Based on Step 2 result, for each follow-up file:

**Match found** -- attach follow-up as plan to the existing backlog item:

```bash
uv run .claude/skills/backlog/scripts/backlog.py update "{matched_item_title}" --plan "{followup_file_path}" -R Jamie-BitFlight/claude_skills
```

**No match found** -- create a new backlog item, then attach the follow-up as plan:

```text
Skill(skill: "create-backlog-item", args: "--auto {derived_title}")
```

Then attach the follow-up file as the plan:

```bash
uv run .claude/skills/backlog/scripts/backlog.py update "{derived_title}" --plan "{followup_file_path}" -R Jamie-BitFlight/claude_skills
```

**Error handling**:

- If `backlog.py update` exits code 1 after creation (title mismatch between what `create-backlog-item` produced and what `update` searched for): re-run `backlog.py list --format json`, find the most recently added item, and retry the `update` with its exact title. If the retry also fails, log the error and continue to the next follow-up file.
- If `create-backlog-item --auto` logs `[AUTO] STOP -- duplicate detected`: treat this as "match found" -- run `backlog.py update` on the duplicate's title to attach the plan.

### Step 4: Recursion Gate

For each follow-up file, evaluate two conditions. BOTH must be true for recursion.

**Condition 1 -- Same session scope (ADR-3)**: The follow-up file's slug matches the parent task file's slug. Extract the slug from each filename: strip the `tasks-{N}-` prefix, then strip `-followup-{k}.md` for the follow-up or `.md` for the parent. Compare the two slugs.

**Condition 2 -- High priority (ADR-2)**: Read the follow-up file content and extract the `## Priority` section. Only `High` qualifies for immediate recursion.

**If BOTH conditions are met** -- recurse immediately:

```text
Skill(skill="implement-feature", args="{followup_task_file_path}")
```

Then re-run `complete-implementation` on the follow-up task file.

**If EITHER condition is NOT met** -- defer to backlog:

Log: `Follow-up {followup_path} linked to backlog item "{title}" -- deferred (priority: {priority}, scope: {same|different}).`

Do not recurse. The follow-up is tracked in the backlog and can be picked up later via `/work-backlog-item`.

**Error handling**: If the follow-up file has no `## Priority` section, default to `Medium` (defer). Log: `No priority found in {followup_path}, defaulting to Medium (deferred).`
