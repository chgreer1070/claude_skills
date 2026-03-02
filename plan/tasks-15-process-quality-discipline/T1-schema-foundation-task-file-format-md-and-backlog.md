---
task: T1
title: "Schema Foundation: TASK_FILE_FORMAT.md and backlog-item-groomed-schema.md"
status: complete
started: 2026-03-02T00:00:00Z
completed: 2026-03-02T00:05:00Z
agent: general-purpose
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
parallelize-with: []
reason: "No dependencies. Both files are schema docs with no overlap. Single task writes both to avoid partial state — groomed-schema must reference field names that are defined in TASK_FILE_FORMAT."
handoff: "Report: lines added to each file, prek lint result for both files, any ambiguities in the architect spec about exact wording."
---

## Context

This task was planned as a single combined task to keep the two schema documents consistent — the groomed-schema references field names that must exist in TASK_FILE_FORMAT. Writing both in one task avoids a partial state where the groomed-schema references undefined fields.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Schema Definitions", "New Groomed Sections", "JSON Schema Extension".

These are AI instruction documents. No Python code changes. The `implementation_manager.py` parser already ignores unknown YAML fields (confirmed in `plan/codebase/sam-pipeline-quality.md`, section "Backward Compatibility").

Fixes #314.

## Objective

Add three optional YAML fields (`issue-classification`, `scenario-target`, `analysis-method`) to the task file format specification, and add two new groomed section definitions to the backlog item groomed schema.

## Required Inputs

- Read `.claude/docs/TASK_FILE_FORMAT.md` — locate: Optional Fields table (~line 127-151), JSON Schema properties block (~line 270-353), template YAML block (~line 644), "Possible Future Fields" appendix (~line 896-910)
- Read `.claude/docs/backlog-item-groomed-schema.md` — locate: Groomed Sections table (~line 52), example groomed body (~line 78)
- Read `plan/architect-process-quality-discipline.md` sections: "Schema Definitions" (new fields), "New Groomed Sections" (format specs), "JSON Schema Extension" (exact JSON to add)

## Requirements

### TASK_FILE_FORMAT.md additions

1. Add 3 rows to the Optional Fields table after the `skills` row:

   | Field | Type | Description |
   |-------|------|-------------|
   | `issue-classification` | enum | `procedural`, `defect`, `recurring-pattern`, `missing-guardrail`, `unbounded-design` — analytical depth classification |
   | `scenario-target` | string | `"{scenario that exposed the problem} -> {what should improve}"` |
   | `analysis-method` | enum | `none`, `5-whys`, `6-sigma`, `design-framing` — root-cause method applied during grooming. Default: `none` |

2. Add 3 property definitions to the JSON Schema properties block:

   ```json
   "issue-classification": {
     "type": "string",
     "enum": ["procedural", "defect", "recurring-pattern", "missing-guardrail", "unbounded-design"],
     "description": "Analytical depth classification for the issue this task addresses"
   },
   "scenario-target": {
     "type": "string",
     "description": "What scenario exposed this issue and what specifically should improve"
   },
   "analysis-method": {
     "type": "string",
     "enum": ["none", "5-whys", "6-sigma", "design-framing"],
     "default": "none",
     "description": "Root-cause analysis method applied during grooming"
   }
   ```

3. Add the 3 optional fields as commented examples to the template YAML block.

4. In the "Possible Future Fields" appendix: note these three fields are now defined (or remove them from "possible future" if they appear there).

### backlog-item-groomed-schema.md additions

5. Add 2 rows to the Groomed Sections table (after existing rows):

   | Section | Purpose | Required |
   |---------|---------|----------|
   | **Issue Classification** | Classification type and rationale | When groomed after this feature |
   | **Root-Cause Analysis** | Evidence chain from `/find-cause` or 6 Sigma measurement | When `issue-classification` is `defect` or `recurring-pattern` |

6. Add format specification blocks for both new sections after the table. Use the exact formats from the architect spec:

   Issue Classification format:

   ```markdown
   ### Issue Classification

   **Type**: procedural | defect | recurring-pattern | missing-guardrail | unbounded-design
   **Rationale**: {1-2 sentence explanation of why this classification was chosen}
   **Analysis Method**: none | 5-whys | 6-sigma | design-framing
   **Scenario Target**: {what scenario exposed this} -> {what should improve}
   ```

   Root-Cause Analysis format (5-whys variant and 6-sigma variant — include both, labelled).

7. Add a brief example of an `### Issue Classification` section to the Example Groomed Body section.

## Constraints

- All new fields are OPTIONAL — do not change any required/optional indicators for existing fields
- Do not reorder or remove existing rows from either file
- Do not modify the Python schema parser or any `.py` file
- Use the exact enum values from the architect spec — no paraphrasing
- Use 3 backtick fences for code blocks; use 4 backticks if nesting inside a 4-backtick outer fence

## Expected Outputs

- `.claude/docs/TASK_FILE_FORMAT.md` — modified in place
- `.claude/docs/backlog-item-groomed-schema.md` — modified in place

## Acceptance Criteria

1. `TASK_FILE_FORMAT.md` Optional Fields table contains exactly these 3 new rows: `issue-classification`, `scenario-target`, `analysis-method` with correct types and descriptions
2. `TASK_FILE_FORMAT.md` JSON Schema properties block contains all 3 property definitions with correct enum arrays
3. `TASK_FILE_FORMAT.md` template YAML block references the 3 new optional fields (as comments or empty examples)
4. `backlog-item-groomed-schema.md` Groomed Sections table contains `Issue Classification` and `Root-Cause Analysis` rows with their Required conditions
5. `backlog-item-groomed-schema.md` includes the complete format specification for `### Issue Classification` section
6. `backlog-item-groomed-schema.md` includes the complete format specification for `### Root-Cause Analysis` (both 5-whys and 6-sigma variants)
7. `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` exits 0
8. `uv run prek run --files .claude/docs/backlog-item-groomed-schema.md` exits 0

## Verification Steps

1. Read `.claude/docs/TASK_FILE_FORMAT.md` and confirm all 3 new rows appear in the Optional Fields table
2. Read the JSON Schema block and confirm the 3 new property definitions are present with correct enum values
3. Run `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` — confirm exit 0
4. Read `.claude/docs/backlog-item-groomed-schema.md` and confirm the 2 new section rows appear in the Groomed Sections table
5. Confirm format specifications for both new sections appear after the table
6. Run `uv run prek run --files .claude/docs/backlog-item-groomed-schema.md` — confirm exit 0

## CoVe Checks

- Key claims to verify:
  - The JSON Schema properties block in TASK_FILE_FORMAT.md is at approximately line 270-353 (not some other location)
  - The "Possible Future Fields" appendix is at approximately line 896-910 and may or may not list these field names
  - The Optional Fields table is after the required fields and includes a `skills` row that precedes the insertion point
- Verification questions (falsifiable):
  1. Does TASK_FILE_FORMAT.md contain a JSON Schema block with `"properties"` key? Find it with `Grep(pattern='"properties"', path='.claude/docs/TASK_FILE_FORMAT.md')`
  2. Does the Optional Fields table end with a `skills` row? Find with `Grep(pattern='skills', path='.claude/docs/TASK_FILE_FORMAT.md', output_mode='content')`
  3. Does the "Possible Future Fields" appendix mention any of the 3 new field names? Find with `Grep(pattern='issue-classification|scenario-target|analysis-method', path='.claude/docs/TASK_FILE_FORMAT.md', output_mode='content')`
- Evidence to collect:
  - Actual line numbers of the Optional Fields table, JSON Schema block, and "Possible Future Fields" appendix
  - Whether the appendix currently lists any of the 3 field names (to decide: add note vs remove from list)
- Revision rule:
  - If the appendix already lists any of the 3 field names, remove them from the "possible future" list and add a note that they were implemented in Issue #314. If not listed, no change to the appendix section header is needed.

## Handoff

Return:

- Summary of lines added to each file (approximate line ranges)
- Confirmation that all 3 JSON Schema properties were inserted with correct enum arrays
- `prek` lint result for both files (pass/fail)
- Any discrepancy found between the architect spec field definitions and what was written

