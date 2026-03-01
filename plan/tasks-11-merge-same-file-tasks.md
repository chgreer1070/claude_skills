---
description: "Add same-file task merging rules to swarm-task-planner and plan-validator agents"
version: "1.0"
feature: merge-same-file-tasks
issue: 316
tasks:
  - T1: Update swarm-task-planner (python3-development) with Components 1-4
  - T2: Update swarm-task-planner (development-harness) with Components 1-4
  - T3: Update plan-validator (python3-development) with Components 5-7
  - T4: Update plan-validator (development-harness) with Components 5-7
  - T5: Cross-plugin consistency verification and linting
---

# Task Plan: Merge Same-File Tasks into Single Agent Assignment

Fixes #316

## Context Manifest

- [Architecture spec](./architect-merge-same-file-tasks.md) — Components 1-7, acceptance criteria, verification strategy
- [Feature context](./feature-context-merge-same-file-tasks.md) — Discovery research, gap analysis, use scenarios
- [swarm-task-planner (python3-development)](../plugins/python3-development/agents/swarm-task-planner.md) — Target file for Components 1-4
- [swarm-task-planner (development-harness)](../plugins/development-harness/agents/swarm-task-planner.md) — Target file for Components 1-4 (same content)
- [plan-validator (python3-development)](../plugins/python3-development/agents/plan-validator.md) — Target file for Components 5-7
- [plan-validator (development-harness)](../plugins/development-harness/agents/plan-validator.md) — Target file for Components 5-7 (same content)

---

## Task T1: Update swarm-task-planner.md (python3-development) — All Four Components

```yaml
---
task: T1
title: "Update swarm-task-planner (python3-development) with same-file merging section, parallelization update, Phase 5 validation item, and success metric"
status: not-started
agent: service-docs-maintainer
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
parallelize-with: [T3]
reason: "T1 and T3 modify different files (swarm-task-planner.md vs plan-validator.md) so no file conflict"
handoff: "Report: file path modified, sections added/changed, line counts before and after, any divergence from architecture spec"
---
```

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

---

## Task T2: Update swarm-task-planner.md (development-harness) — All Four Components

```yaml
---
task: T2
title: "Update swarm-task-planner (development-harness) with same-file merging section, parallelization update, Phase 5 validation item, and success metric"
status: not-started
agent: service-docs-maintainer
dependencies: [T1]
priority: 1
complexity: low
accuracy-risk: medium
parallelize-with: [T4]
reason: "T2 and T4 modify different files (swarm-task-planner.md vs plan-validator.md) so no file conflict. T2 depends on T1 to ensure content consistency."
handoff: "Report: file path modified, sections added/changed, confirmation that new content matches T1 output"
---
```

## Context

This task applies the same four components from the [architecture spec](./architect-merge-same-file-tasks.md) to the development-harness copy of swarm-task-planner.md. The development-harness copy uses `role:` (not `agent:`) in its YAML frontmatter template and does not have `(UPDATED)` suffixes on section headers.

The Same-File Task Merging section content must be identical to what was added in T1. The surrounding section structure differs slightly (no `(UPDATED)` suffixes, `role:` instead of `agent:`), so insertion points must be adapted.

## Objective

Add the same four components (same-file merging section, parallelization update, Phase 5 validation item, success metric question) to the development-harness swarm-task-planner agent file, matching the content added in T1.

## Required Inputs

- [Architecture spec Components 1-4](./architect-merge-same-file-tasks.md) — exact section content
- [swarm-task-planner (development-harness)](../plugins/development-harness/agents/swarm-task-planner.md) — current file content
- T1 output — the completed python3-development file, for content consistency reference

## Requirements

### Component 1: New Same-File Task Merging section

1. Insert `## Same-File Task Merging` section after `## Parallelization and Conflict Avoidance` and before `## Working Process`
2. Section content is identical to what T1 added

### Component 2: Updated Parallelization section

3. Replace the body of `## Parallelization and Conflict Avoidance` with the same three-option list added in T1

### Component 3: New Phase 5 validation item

4. Add validation item 9 "Same-file conflict check" to Phase 5, identical content to T1

### Component 4: Updated success metrics

5. Add the same verification question to the Verification Questions list

## Constraints

- Do not add `(UPDATED)` suffixes to section headers — this copy does not use them
- Preserve the `role:` field naming convention (not `agent:`)
- The Same-File Task Merging section content must be identical to the python3-development copy
- Do not modify the YAML frontmatter block at the top of the file

## Expected Outputs

- File modified: `plugins/development-harness/agents/swarm-task-planner.md`

## Acceptance Criteria

1. `## Same-File Task Merging` section exists between `## Parallelization and Conflict Avoidance` and `## Working Process`
2. The section content is identical to the Same-File Task Merging section in `plugins/python3-development/agents/swarm-task-planner.md`
3. The Parallelization section lists the same three ordered options as the python3-development copy
4. Phase 5 contains item 9 "Same-file conflict check" with identical content
5. Verification Questions list contains the shared Expected Output file path question

## Verification Steps

1. Read the modified file and confirm `## Same-File Task Merging` section exists with all four behavioral contract steps
2. Diff the Same-File Task Merging section between both swarm-task-planner files and confirm they are identical
3. Grep for "Same-file conflict check" and confirm it appears in Phase 5
4. Run `uv run prek run --files plugins/development-harness/agents/swarm-task-planner.md` and confirm exit code 0

## CoVe Checks

- Key claims to verify:
  - The development-harness copy uses `role:` not `agent:`
  - The development-harness copy does NOT have `(UPDATED)` suffixes on section headers
  - Phase 5 currently has 8 numbered validation items
- Verification questions (falsifiable):
  1. Does `plugins/development-harness/agents/swarm-task-planner.md` contain `role:` (not `agent:`) in its Task Structure Requirements?
  2. Is the Parallelization section header `## Parallelization and Conflict Avoidance` (no suffix)?
  3. Are Phase 5 items numbered 1-8 before changes?
- Evidence to collect:
  - Read the file before editing
  - Grep for the Parallelization header
  - Compare T1 output to verify content identity
- Revision rule:
  - If headers differ from expected, adapt insertion points. Content of the new section must still match T1.

---

## Task T3: Update plan-validator.md (python3-development) — Components 5-7

```yaml
---
task: T3
title: "Update plan-validator (python3-development) with upgraded Dimension 5 red flag, new issue example, and blocker severity item"
status: not-started
agent: service-docs-maintainer
dependencies: []
priority: 1
complexity: low
accuracy-risk: medium
parallelize-with: [T1]
reason: "T3 modifies plan-validator.md while T1 modifies swarm-task-planner.md — different files, no conflict"
handoff: "Report: file path modified, three changes applied (red flag upgrade, issue example, severity item), line numbers of changes"
---
```

## Context

This task implements Components 5-7 from the [architecture spec](./architect-merge-same-file-tasks.md) in `plugins/python3-development/agents/plan-validator.md`. The python3-development plan-validator uses `Agent` (not `Role`) field naming, mentions "Python projects" in its role description, and names Dimension 4 as "Agent Capability Match."

## Objective

Upgrade the Dimension 5 same-file red flag from a warning to a blocker with merge recommendation, add a structured issue example for the same-file conflict, and add the same-file conflict to the blocker severity definition.

## Required Inputs

- [Architecture spec Components 5-7](./architect-merge-same-file-tasks.md) — exact replacement text for the red flag, issue example YAML, severity line
- [plan-validator (python3-development)](../plugins/python3-development/agents/plan-validator.md) — current file content

## Requirements

### Component 5: Upgraded Dimension 5 red flag

1. In Dimension 5 (Input/Output Validity), replace the red flag line `- Two tasks write to same file without dependency` with the expanded blocker text from architecture spec Component 5
2. The replacement must include severity label (**BLOCKER**), explanation (edit conflicts), and reporting format

### Component 6: New structured issue example

3. Add the structured YAML issue example from architecture spec Component 6 to the `<issue_structure>` section, in the aggregated issues list
4. The example uses `dimension: "input_output_validity"`, `severity: "blocker"`, and includes a `fix_hint` recommending merge

### Component 7: Updated severity definition

5. Add `- Multiple tasks write to same file without dependency chain (edit conflict risk)` to the **blocker** severity definition list in the `<issue_structure>` section

## Constraints

- Do not change Dimension 4 name ("Agent Capability Match" in this copy)
- Do not change role description wording ("Python projects")
- Preserve all existing red flag items in Dimension 5 (only expand the second one)
- Do not modify sections outside Dimension 5 and `<issue_structure>`

## Expected Outputs

- File modified: `plugins/python3-development/agents/plan-validator.md`

## Acceptance Criteria

1. Dimension 5 red flags section contains the expanded blocker text for same-file writes, including "**BLOCKER**" label and "merge into single task or add sequential dependencies" recommendation
2. The `<issue_structure>` aggregated issues list contains a new YAML example with `dimension: "input_output_validity"` and `severity: "blocker"` for same-file conflict
3. The blocker severity definition list includes the same-file conflict item
4. The original first and third red flags ("Input doesn't exist..." and "Output not used...") remain unchanged

## Verification Steps

1. Read Dimension 5 and confirm the second red flag is expanded with BLOCKER severity and merge recommendation
2. Grep for `input_output_validity` in the issue_structure section and confirm the new example exists
3. Read the blocker severity list and confirm it contains "Multiple tasks write to same file without dependency chain"
4. Run `uv run prek run --files plugins/python3-development/agents/plan-validator.md` and confirm exit code 0

## CoVe Checks

- Key claims to verify:
  - The current Dimension 5 red flag text is `- Two tasks write to same file without dependency` (line 172 in python3-development copy)
  - The `<issue_structure>` section contains a blocker severity list
  - Dimension 4 is named "Agent Capability Match" (not "Role-Agent Capability Match")
- Verification questions (falsifiable):
  1. Does line 172 of the python3-development plan-validator contain the exact text `- Two tasks write to same file without dependency`?
  2. Does the blocker severity list currently have 5 items?
  3. Does the aggregated issues example YAML currently have 3 entries?
- Evidence to collect:
  - Read the file to confirm current red flag text
  - Count existing blocker severity items
  - Count existing aggregated issue examples
- Revision rule:
  - If line numbers differ, locate by content pattern. If blocker list has different item count, append to the end of the existing list.

---

## Task T4: Update plan-validator.md (development-harness) — Components 5-7

```yaml
---
task: T4
title: "Update plan-validator (development-harness) with upgraded Dimension 5 red flag, new issue example, and blocker severity item"
status: not-started
agent: service-docs-maintainer
dependencies: [T3]
priority: 1
complexity: low
accuracy-risk: medium
parallelize-with: [T2]
reason: "T4 modifies plan-validator.md while T2 modifies swarm-task-planner.md — different files, no conflict. T4 depends on T3 to ensure content consistency."
handoff: "Report: file path modified, confirmation that changes match T3 output for Dimension 5 and issue_structure sections"
---
```

## Context

This task applies the same three components (5-7) from the [architecture spec](./architect-merge-same-file-tasks.md) to the development-harness copy of plan-validator.md. The development-harness copy uses `Role` (not `Agent`) field naming, mentions "software projects" (not "Python projects"), and names Dimension 4 as "Role-Agent Capability Match."

The Dimension 5 changes and issue_structure additions must be identical to what was added in T3.

## Objective

Apply the same Dimension 5 red flag upgrade, structured issue example, and blocker severity item to the development-harness plan-validator, matching the content from T3.

## Required Inputs

- [Architecture spec Components 5-7](./architect-merge-same-file-tasks.md) — exact replacement text
- [plan-validator (development-harness)](../plugins/development-harness/agents/plan-validator.md) — current file content
- T3 output — the completed python3-development plan-validator file, for content consistency reference

## Requirements

### Component 5: Upgraded Dimension 5 red flag

1. Replace `- Two tasks write to same file without dependency` with the expanded blocker text, identical to T3

### Component 6: New structured issue example

2. Add the same structured YAML issue example to the aggregated issues list in `<issue_structure>`, identical to T3

### Component 7: Updated severity definition

3. Add the same blocker severity item, identical to T3

## Constraints

- Do not change Dimension 4 name ("Role-Agent Capability Match" in this copy)
- Do not change role description wording ("software projects")
- Preserve the `Role` field naming convention
- The three changes (red flag, issue example, severity item) must have identical content to the python3-development copy

## Expected Outputs

- File modified: `plugins/development-harness/agents/plan-validator.md`

## Acceptance Criteria

1. Dimension 5 red flags contain the expanded blocker text, identical to the python3-development copy
2. The aggregated issues list contains the new same-file conflict example, identical to T3
3. The blocker severity list includes the same-file conflict item, identical to T3
4. The original first and third red flags remain unchanged

## Verification Steps

1. Read Dimension 5 and confirm the second red flag matches the python3-development copy
2. Diff the Dimension 5 red flags section between both plan-validator files and confirm the same-file blocker text is identical
3. Diff the blocker severity lists between both files and confirm the new item is identical
4. Run `uv run prek run --files plugins/development-harness/agents/plan-validator.md` and confirm exit code 0

## CoVe Checks

- Key claims to verify:
  - The development-harness copy has the same Dimension 5 red flag text as python3-development before this feature
  - Dimension 4 is "Role-Agent Capability Match" in this copy
- Verification questions (falsifiable):
  1. Does the development-harness plan-validator contain `- Two tasks write to same file without dependency` in Dimension 5?
  2. Is Dimension 4 header `## Dimension 4: Role-Agent Capability Match`?
- Evidence to collect:
  - Read the file to confirm current Dimension 5 content
  - Compare with T3 output after editing
- Revision rule:
  - If the red flag wording differs slightly from the python3-development copy, use the exact wording from the architecture spec Component 5.

---

## Task T5: Cross-Plugin Consistency Verification and Linting

```yaml
---
task: T5
title: "Verify cross-plugin consistency and lint all four modified files"
status: not-started
agent: integration-checker
dependencies: [T1, T2, T3, T4]
priority: 2
complexity: low
accuracy-risk: low
parallelize-with: []
reason: "Must run after all four file modifications are complete"
handoff: "Report: diff results for cross-plugin sections, lint exit codes for all four files, negative check results for excluded files"
---
```

## Context

After all four agent prompt files are modified (T1-T4), this task verifies that cross-plugin copies are consistent and that no unintended files were changed. This is the final quality gate before the feature can be considered complete.

## Objective

Confirm that the Same-File Task Merging sections are identical across both swarm-task-planner copies, that the Dimension 5 changes are identical across both plan-validator copies, that all four files pass linting, and that no excluded files were modified.

## Required Inputs

- `plugins/python3-development/agents/swarm-task-planner.md` (T1 output)
- `plugins/development-harness/agents/swarm-task-planner.md` (T2 output)
- `plugins/python3-development/agents/plan-validator.md` (T3 output)
- `plugins/development-harness/agents/plan-validator.md` (T4 output)

## Requirements

### Cross-plugin consistency

1. Extract the `## Same-File Task Merging` section from both swarm-task-planner files and confirm they are textually identical
2. Extract the Dimension 5 red flags from both plan-validator files and confirm the expanded blocker text is textually identical
3. Extract the blocker severity definition from both plan-validator files and confirm the new item is textually identical

### Linting

4. Run `uv run prek run --files` on all four modified files and confirm exit code 0 for each

### Negative check

5. Run `git diff --name-only` and confirm that ONLY the four expected agent prompt files were modified — no changes to `implementation_manager.py`, `task_status_hook.py`, `TASK_FILE_FORMAT.md`, `start-task/SKILL.md`, or `implement-feature/SKILL.md`

## Constraints

- This is a verification-only task — do not modify any files
- If inconsistencies are found, report them with exact line differences; do not attempt to fix

## Expected Outputs

- Verification report (in handoff) confirming consistency, lint, and negative check results
- No files created or modified

## Acceptance Criteria

1. The `## Same-File Task Merging` section is textually identical in both swarm-task-planner files
2. The Dimension 5 expanded blocker red flag text is textually identical in both plan-validator files
3. The blocker severity list addition is textually identical in both plan-validator files
4. All four files pass `uv run prek run --files` with exit code 0
5. `git diff --name-only` shows only the four expected files (no changes to excluded files)

## Verification Steps

1. Diff the Same-File Task Merging sections:

    ```bash
    diff <(sed -n '/^## Same-File Task Merging/,/^## /p' plugins/python3-development/agents/swarm-task-planner.md) \
         <(sed -n '/^## Same-File Task Merging/,/^## /p' plugins/development-harness/agents/swarm-task-planner.md)
    ```

2. Run linting on all four files:

    ```bash
    uv run prek run --files plugins/python3-development/agents/swarm-task-planner.md
    uv run prek run --files plugins/development-harness/agents/swarm-task-planner.md
    uv run prek run --files plugins/python3-development/agents/plan-validator.md
    uv run prek run --files plugins/development-harness/agents/plan-validator.md
    ```

3. Run the negative check:

    ```bash
    git diff --name-only | grep -E "(implementation_manager|task_status_hook|TASK_FILE_FORMAT|start-task/SKILL|implement-feature/SKILL)"
    ```

    Must return empty.

---

## SYNC CHECKPOINT: Review-Reflect-Revise

- Convergence point: T1 + T2 + T3 + T4 outputs verified by T5
- Quality gates:
  - All acceptance criteria met for T1-T4
  - Cross-plugin content consistency confirmed (T5)
  - Linting passes on all four files (T5)
  - No excluded files modified (T5)
- Reflection questions:
  - Do the swarm-task-planner changes integrate smoothly with existing Phase 3/Phase 5 content?
  - Do the plan-validator Dimension 5 changes align with the existing issue_structure format?
  - Are there any follow-up tasks needed (e.g., updating clear-cove-task-design skill)?
- Proceed to completion only after T5 passes

---

## Dependency Graph

```text
T1 (swarm-task-planner p3d)  ──┐
                               ├── T2 (swarm-task-planner dh) ──┐
                               │                                 │
T3 (plan-validator p3d) ───────┤                                 ├── T5 (verification)
                               ├── T4 (plan-validator dh) ──────┘
                               │
T1 can parallelize with T3
T2 can parallelize with T4
T5 depends on all four
```

## Parallelization Summary

| Parallel Group | Tasks | Reason |
| -------------- | ----- | ------ |
| Group A | T1, T3 | Different files: swarm-task-planner.md vs plan-validator.md |
| Group B | T2, T4 | Different files: swarm-task-planner.md vs plan-validator.md (after T1/T3 complete) |
| Sequential | T5 | Requires all four file modifications complete |

## References

- [Architecture spec](./architect-merge-same-file-tasks.md)
- [Feature context](./feature-context-merge-same-file-tasks.md)
- [TASK_FILE_FORMAT.md](../.claude/docs/TASK_FILE_FORMAT.md)
- [SAM local workflow documentation](../.claude/rules/local-workflow.md)
- GitHub Issue: [#316](https://github.com/Jamie-BitFlight/claude_skills/issues/316)

SOURCE: Architecture spec and feature context generated 2026-03-01 from session observation in #128 validate-agent-browser. Task plan authored 2026-03-01.
