---
task: "T2"
title: "Update swarm-task-planner (development-harness) with same-file merging section, parallelization update, Phase 5 validation item, and success metric"
status: complete
agent: "service-docs-maintainer"
dependencies: ["T1"]
priority: 1
complexity: low
started: "2026-03-01T00:00:00Z"
completed: "2026-03-01T01:25:00Z"
---

## Task T1: Update swarm-task-planner (python3-development) with same-file merging section, parallelization update, Phase 5 validation item, and success metric

**Status**: COMPLETE
**Agent**: service-docs-maintainer
**Dependencies**: None
**Priority**: 1
**Complexity**: Medium
**Completed**: 2026-03-01T01:10:00Z

## Context

This task implements Components 1-4 from the [architecture spec](./architect-merge-same-file-tasks.md) in a single file: `plugins/python3-development/agents/swarm-task-planner.md`. All four components target this same file, so they are merged into one task to avoid edit conflicts — applying the exact rule this feature defines.

The python3-development copy uses `agent:` (not `role:`) in its YAML frontmatter template, has `(UPDATED)` suffixes on some section headers, and references concrete agent names (not abstract roles) in the Agent Assignment Rules table.

## Objective

Add same-file task merging behavioral rules, update the parallelization section, add a Phase 5 validation item, and add a success metric verification question to the python3-development swarm-task-planner agent file.

## Required Inputs

- [Architecture spec Components 1-4](./architect-merge-same-file-tasks.md) — exact section content, insertion points, and behavioral contract
- [swarm-task-planner (python3-development)](../plugins/python3-development/agents/swarm-task-planner.md) — current file content

## Requirements

### Component 1: New Same-File Task Merging section

1. Insert a new `## Same-File Task Merging` section after the existing `## Parallelization and Conflict Avoidance (UPDATED)` section (before `## Working Process`)
2. Include the full behavioral contract from architecture spec Component 1: detect overlap, merge decision, merge requirements/acceptance criteria, document merge rationale
3. Include both exceptions (sequential dependency already exists, different agents required)
4. Include the illustrative before/after example

### Component 2: Updated Parallelization section

5. Replace the body of the `## Parallelization and Conflict Avoidance (UPDATED)` section with the new content from architecture spec Component 2
6. The updated section lists three options: PREFERRED (merge), ALTERNATIVE (chain with dependencies), LAST RESORT (split by sections)
7. Include the rationale paragraph explaining why merge is preferred

### Component 3: New Phase 5 validation item

8. Add validation item 9 ("Same-file conflict check") to Phase 5 in the `## Working Process` section, after the existing item 8 (YAML frontmatter completeness)
9. Item must include the three sub-bullets: count tasks per Expected Output file, MERGE required if count > 1 without dependency chain, WARNING if count > 1 with dependency chain

### Component 4: Updated success metrics

10. Add the verification question "Do any two tasks share an Expected Output file path without being dependency-chained or merged?" to the Verification Questions list at the end of the file

## Constraints

- Do not modify the YAML frontmatter block at the top of the file
- Do not change existing section content except for the Parallelization section body (Component 2)
- Do not rename or remove `(UPDATED)` suffixes on existing section headers
- Preserve the `agent:` field naming convention (not `role:`)
- Do not modify Agent Assignment Rules table

## Expected Outputs

- File modified: `plugins/python3-development/agents/swarm-task-planner.md`

## Acceptance Criteria

### Same-File Task Merging section (Component 1)

1. A `## Same-File Task Merging` section exists between `## Parallelization and Conflict Avoidance (UPDATED)` and `## Working Process`
2. The section contains the four-step behavioral contract (detect overlap, merge decision, merge requirements, document rationale)
3. Both exception clauses are present (sequential dependency, different agents)
4. The illustrative before/after example is included

### Parallelization section update (Component 2)

5. The `## Parallelization and Conflict Avoidance (UPDATED)` section body lists three ordered options: PREFERRED merge, ALTERNATIVE chain, LAST RESORT split
6. The rationale paragraph is present

### Phase 5 validation item (Component 3)

7. Phase 5 Plan Validation contains item 9 "Same-file conflict check" with three sub-bullets

### Success metric (Component 4)

8. The Verification Questions list at end of file contains the shared Expected Output file path question

## Verification Steps

1. Read the modified file and confirm `## Same-File Task Merging` section exists with all four behavioral contract steps
2. Read the Parallelization section and confirm three ordered options with "PREFERRED" as the first
3. Grep for "Same-file conflict check" in the file and confirm it appears in Phase 5
4. Read the Verification Questions list and confirm the new question about shared Expected Output file paths is present
5. Run `uv run prek run --files plugins/python3-development/agents/swarm-task-planner.md` and confirm exit code 0

## CoVe Checks

- Key claims to verify:
  - The python3-development copy uses `agent:` not `role:` in its Task Structure Requirements
  - The python3-development copy has `(UPDATED)` suffixes on some headers
  - Phase 5 currently has 8 numbered validation items (the new one is item 9)
- Verification questions (falsifiable):
  1. Does `plugins/python3-development/agents/swarm-task-planner.md` line 256 contain `agent:` (not `role:`)?
  2. Does the Phase 5 section have items numbered 1-8 before this task's changes?
  3. Is the Parallelization section header `## Parallelization and Conflict Avoidance (UPDATED)`?
- Evidence to collect:
  - Read the file before editing to confirm current structure
  - Grep for `## Parallelization` to find exact header text
  - Count existing Phase 5 validation items
- Revision rule:
  - If the header does not have `(UPDATED)` suffix, use the header as-is. If Phase 5 has a different item count, adjust numbering accordingly.
