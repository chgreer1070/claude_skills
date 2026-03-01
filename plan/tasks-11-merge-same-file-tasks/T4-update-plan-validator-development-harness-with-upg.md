---
task: "T4"
title: "Update plan-validator (development-harness) with upgraded Dimension 5 red flag, new issue example, and blocker severity item"
status: complete
agent: "service-docs-maintainer"
dependencies: ["T3"]
priority: 1
complexity: low
started: "2026-03-01T00:00:00Z"
completed: "2026-03-01T01:25:00Z"
---

## Task T3: Update plan-validator (python3-development) with upgraded Dimension 5 red flag, new issue example, and blocker severity item

**Status**: COMPLETE
**Agent**: service-docs-maintainer
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Started**: 2026-03-01T00:00:00Z
**Completed**: 2026-03-01T01:10:00Z

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
