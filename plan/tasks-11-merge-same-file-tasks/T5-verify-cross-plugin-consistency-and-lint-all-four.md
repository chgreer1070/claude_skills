---
task: "T5"
title: "Verify cross-plugin consistency and lint all four modified files"
status: complete
agent: "integration-checker"
dependencies: ["T1", "T2", "T3", "T4"]
priority: 2
complexity: low
completed: "2026-03-01T01:30:00Z"
---

## Task T4: Update plan-validator (development-harness) with upgraded Dimension 5 red flag, new issue example, and blocker severity item

**Status**: COMPLETE
**Agent**: service-docs-maintainer
**Dependencies**: Task T3
**Priority**: 1
**Complexity**: Low
**Started**: 2026-03-01T00:00:00Z
**Completed**: 2026-03-01T01:25:00Z

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
