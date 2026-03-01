---
description: "Add Process Quality Discipline to SAM pipeline — 7 markdown document edits across schema, grooming, completion gates, verify skill, and both feature-verifier agents"
version: "1.0"
issue: "#314"
tasks:
  - T1: Schema Foundation (TASK_FILE_FORMAT.md + backlog-item-groomed-schema.md)
  - T2: Grooming Classification Steps (groom-backlog-item/SKILL.md)
  - T3: Completion Gate Enhancement (complete-implementation/SKILL.md)
  - T4: Verify Skill Proportional Check (verify/SKILL.md)
  - T5: Feature Verifier python3-development (feature-verifier.md)
  - T6: Feature Verifier development-harness (feature-verifier.md)
  - T7: Taxonomy Validation (classify 5+ recent backlog items)
task_exports:
  enabled: false
  directory: "TASK"
---

# Process Quality Discipline — Task Plan (Issue #314)

## Dependency Graph

```text
T1 (Schema Foundation)
├── T2 (Grooming Steps)        depends on T1
├── T3 (Completion Gate)       depends on T1
├── T4 (Verify Skill)          depends on T1
├── T5 (Feature Verifier p3d)  depends on T1
│   └── T6 (Feature Verifier dh) depends on T5
└── T7 (Taxonomy Validation)   depends on T1, T2
```

## Parallelization Opportunities

After T1 completes: T2, T3, T4, T5 can all run concurrently.
T6 must wait for T5 (content consistency check).
T7 must wait for T1 and T2 (new section names must exist before validation classifies items into them).

---

## SYNC CHECKPOINT 1 (after T1)

**Convergence point**: T1 complete.

**Quality gates**:

- `TASK_FILE_FORMAT.md` Optional Fields table contains rows for `issue-classification`, `scenario-target`, `analysis-method`
- `TASK_FILE_FORMAT.md` JSON Schema properties block contains 3 new property definitions
- `TASK_FILE_FORMAT.md` template YAML block contains 3 optional fields as comments
- `backlog-item-groomed-schema.md` Groomed Sections table contains `Issue Classification` and `Root-Cause Analysis` rows
- `backlog-item-groomed-schema.md` includes format specification blocks for both new sections
- `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` exits 0
- `uv run prek run --files .claude/docs/backlog-item-groomed-schema.md` exits 0

**Proceed**: Start T2, T3, T4, T5 in parallel.

---

## SYNC CHECKPOINT 2 (after T2, T3, T4, T5, T6)

**Convergence point**: T2 + T3 + T4 + T5 + T6 all complete.

**Quality gates**:

- `groom-backlog-item/SKILL.md` step numbering is sequential 1-9
- `complete-implementation/SKILL.md` Phase 2 includes `issue-classification` pass-through instruction
- `verify/SKILL.md` Section 5 (Proportional Response Check) exists; old Section 5 renumbered to 6
- Both `feature-verifier.md` files contain Step 7 (Proportional Response Check) before the final status step
- `uv run prek run --files` exits 0 for all 5 modified files

**Proceed**: Start T7.

---

## SYNC CHECKPOINT 3 (after T7)

**Convergence point**: All tasks complete.

**Quality gates**:

- 5+ recent backlog items classified with rationale
- All 5 classification types represented (or documented absence noted)
- No item fitting multiple types without documented tie-break rationale
- Validation report written to `plan/taxonomy-validation-process-quality-discipline.md`

**Proceed**: Implementation complete. Run `/complete-implementation` on this task file.

---

## Tasks

---

```yaml
---
task: T1
title: "Schema Foundation: TASK_FILE_FORMAT.md and backlog-item-groomed-schema.md"
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
parallelize-with: []
reason: "No dependencies. Both files are schema docs with no overlap. Single task writes both to avoid partial state — groomed-schema must reference field names that are defined in TASK_FILE_FORMAT."
handoff: "Report: lines added to each file, prek lint result for both files, any ambiguities in the architect spec about exact wording."
---
```

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

---

```yaml
---
task: T2
title: "Grooming Classification Steps: groom-backlog-item/SKILL.md"
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: high
accuracy-risk: medium
parallelize-with: [T3, T4, T5]
reason: "T3, T4, T5 are independent files with no content overlap. All can execute concurrently after T1."
handoff: "Report: new step numbers, prek lint result, whether the Mermaid flowchart renders correctly (check node labels use <br> not \\n and = not : for assignments)."
---
```

## Context

This task was planned as a single combined task because it adds two new steps (Step 6 and Step 7) to the same SKILL.md file and renumbers existing steps. A single worker handles all changes to avoid step-numbering conflicts between concurrent edits.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Grooming Integration", "New Step 6: Issue Classification", "New Step 7: Root-Cause Analysis (Conditional)", "Modified Step 8".

Current groom-backlog-item step structure: Step 1 through Step 7. After this task: Step 1-5 unchanged, new Step 6 (Issue Classification), new Step 7 (Root-Cause Analysis), old Step 6 → Step 8, old Step 7 → Step 9.

Fixes #314.

## Objective

Insert Step 6 (Issue Classification with Mermaid flowchart) and Step 7 (conditional Root-Cause Analysis) into the groom-backlog-item skill, renumber old Steps 6-7 to 8-9, update the groomer agent prompt, and update the valid section names list and completion criteria.

## Required Inputs

- Read `.claude/skills/groom-backlog-item/SKILL.md` in full — note the exact text of current Steps 6 and 7, and their line numbers, before any edits
- Read `plan/architect-process-quality-discipline.md` sections: "New Step 6: Issue Classification", "New Step 7: Root-Cause Analysis (Conditional)", "Modified Step 8 (was Step 6): Spawn Groomer Agents", "Grooming Completion Criteria Update", "Valid Section Names Update"
- Read `plan/architect-process-quality-discipline.md` section "Component Architecture" for Mermaid flowchart specification of the classification decision tree

## Requirements

### Step renumbering

1. Rename current `### Step 6: Spawn Groomer Agents` to `### Step 8: Spawn Groomer Agents`
2. Rename current `### Step 7: Write Groomed Content to Item Files` to `### Step 9: Write Groomed Content to Item Files`

### New Step 6: Issue Classification

3. Insert a new `### Step 6: Issue Classification` section AFTER Step 5 and BEFORE the new Step 8 (was Step 6)
4. Step 6 body must include:
   - Purpose: classify the issue type to determine analysis depth and verification criteria
   - The decision flowchart (Mermaid) from the architect spec with 5 classification outcomes
   - Instruction to write the classification to the backlog item: `backlog groom "{title}" --section "Issue Classification" --content "{classification section}"`
   - Note that `scenario-target` is set at this step

### New Step 7: Root-Cause Analysis (Conditional)

5. Insert a new `### Step 7: Root-Cause Analysis (Conditional)` section AFTER Step 6 and BEFORE Step 8
6. Step 7 body must include:
   - Condition: only runs when `issue-classification` is `defect` or `recurring-pattern`
   - For `defect`: invoke `/find-cause` skill, capture evidence chain, write to item via `backlog groom --section "Root-Cause Analysis"`
   - For `recurring-pattern`: perform frequency search via `uv run .claude/skills/backlog/scripts/backlog.py list --format json --status resolved`, filter by keywords, count matches, write 6 Sigma measurement section
   - For `procedural`, `missing-guardrail`, `unbounded-design`: skip this step entirely
   - Note: if the human has already identified the recurrence pattern, skip the search and use the human's assessment

### Step 8 (was Step 6) groomer agent prompt update

7. The groomer agent prompt in Step 8 must include 2 new context fields passed to the agent:
   - `Issue Classification:` — output from Step 6
   - `Root-Cause Analysis:` — evidence chain from Step 7, or `N/A - not applicable for this issue type`
8. The prompt must state that the groomer agent does NOT perform classification or root-cause analysis — it receives these as inputs

### Valid section names and completion criteria

9. Update the valid section names list (line ~230 in SKILL.md) to add `Issue Classification` and `Root-Cause Analysis` to the groomed subsections list
10. Add to the completion criteria at the end of the skill:
    - Issue classification assigned for each item (Step 6)
    - Root-cause analysis performed for `defect` and `recurring-pattern` items (Step 7)
    - Classification and analysis passed to groomer agent as context

## Constraints

- Do not alter Steps 1-5
- Do not alter the groomer agent's model (`model: "haiku"`) — the orchestrator (not the groomer) does the classification
- Mermaid flowcharts: use `<br>` for line breaks inside node labels, use `=` not `:` for assignments inside label strings
- All new steps must follow the `### Step N: Name` heading convention used throughout the file
- Do not add new YAML frontmatter fields to the SKILL.md file itself

## Expected Outputs

- `.claude/skills/groom-backlog-item/SKILL.md` — modified in place with 9 numbered steps

## Acceptance Criteria

1. File contains exactly 9 `### Step N:` headings in sequential order (Step 1 through Step 9)
2. `### Step 6: Issue Classification` exists and contains a Mermaid flowchart with all 5 classification outcomes (`procedural`, `defect`, `recurring-pattern`, `missing-guardrail`, `unbounded-design`)
3. `### Step 7: Root-Cause Analysis (Conditional)` exists and contains the condition (`defect` or `recurring-pattern`) and the `/find-cause` invocation for `defect` type
4. `### Step 8: Spawn Groomer Agents` prompt includes `Issue Classification:` and `Root-Cause Analysis:` context fields
5. Valid section names list includes `Issue Classification` and `Root-Cause Analysis`
6. Completion criteria section includes classification and root-cause criteria
7. `uv run prek run --files .claude/skills/groom-backlog-item/SKILL.md` exits 0

## Verification Steps

1. Run `Grep(pattern="### Step", path=".claude/skills/groom-backlog-item/SKILL.md", output_mode="content")` — confirm exactly 9 step headings appear in order
2. Read Step 6 and confirm Mermaid flowchart is present and contains all 5 classification labels
3. Read Step 7 and confirm conditional logic (defect → find-cause, recurring-pattern → frequency search, others → skip)
4. Read Step 8 and confirm `Issue Classification:` and `Root-Cause Analysis:` appear in the agent prompt template
5. Run `Grep(pattern="Issue Classification|Root-Cause Analysis", path=".claude/skills/groom-backlog-item/SKILL.md", output_mode="content")` — confirm both appear in valid section names AND in step bodies
6. Run `uv run prek run --files .claude/skills/groom-backlog-item/SKILL.md` — confirm exit 0

## CoVe Checks

- Key claims to verify:
  - Current Step 6 is "Spawn Groomer Agents" (not some other step)
  - Current Step 7 is "Write Groomed Content to Item Files" (not renumbered already)
  - The Mermaid node label syntax in this skill currently uses `<br>` (confirming repo convention)
- Verification questions (falsifiable):
  1. What are the exact current step headings? Run `Grep(pattern="### Step", path=".claude/skills/groom-backlog-item/SKILL.md", output_mode="content")` before writing any edits
  2. Does the file already contain any reference to `Issue Classification`? Run `Grep(pattern="Issue Classification", path=".claude/skills/groom-backlog-item/SKILL.md")` — if found, this task may be partially done
- Evidence to collect:
  - Current step headings and their line numbers (read the file first)
  - Confirm no prior partial implementation exists
- Revision rule:
  - If any of the new step content is already present, read the full context before editing to avoid duplicating sections.

## Handoff

Return:

- New step count and step heading names (Steps 1-9)
- Confirmation that the Mermaid classification flowchart uses `<br>` for line breaks and `=` for assignments
- `prek` lint result
- Any content that was unclear in the architect spec and how ambiguity was resolved

---

```yaml
---
task: T3
title: "Completion Gate Enhancement: complete-implementation/SKILL.md"
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: low
accuracy-risk: low
parallelize-with: [T2, T4, T5]
reason: "Independent file. Minimal single-line addition to Phase 2. No overlap with T2, T4, T5."
handoff: "Report: exact text added to Phase 2, prek lint result."
---
```

## Context

The architect spec calls for a minimal one-line addition to Phase 2 of the `/complete-implementation` skill. This is the smallest change in the entire feature — one sentence added to an existing phase description.

Architecture spec: `plan/architect-process-quality-discipline.md`, section "Completion Gate Integration".

Fixes #314.

## Objective

Add a single instruction to Phase 2 of `complete-implementation/SKILL.md` that directs the orchestrator to include `issue-classification` metadata in the feature-verifier agent prompt when present.

## Required Inputs

- Read `.claude/skills/complete-implementation/SKILL.md` in full — locate Phase 2 (~line 28)
- Read `plan/architect-process-quality-discipline.md` section "Completion Gate Integration" for the exact new text

## Requirements

1. Locate Phase 2: "Feature Verification (goal-backward)" in the skill
2. Current text: `Launch feature-verifier with the task file path.`
3. Replace with (or append after): `Launch feature-verifier with the task file path. If the task file contains issue-classification metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks.`

## Constraints

- Change is additive only — do not remove, reorder, or reword any other phase
- Do not add new phases
- The instruction must state the CONDITION (`if the task file contains issue-classification metadata`) — not unconditionally

## Expected Outputs

- `.claude/skills/complete-implementation/SKILL.md` — modified in place

## Acceptance Criteria

1. Phase 2 description contains the sentence: "If the task file contains `issue-classification` metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks."
2. No other phases are modified
3. `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` exits 0

## Verification Steps

1. Read `.claude/skills/complete-implementation/SKILL.md` and confirm Phase 2 contains the new instruction
2. Confirm no other phase text was altered
3. Run `uv run prek run --files .claude/skills/complete-implementation/SKILL.md` — confirm exit 0

## Handoff

Return:

- Exact text of Phase 2 after the edit
- `prek` lint result
- Confirmation that no other phases were modified

---

```yaml
---
task: T4
title: "Verify Skill Proportional Check: verify/SKILL.md"
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: medium
accuracy-risk: medium
parallelize-with: [T2, T3, T5]
reason: "Independent file. No overlap with T2, T3, T5."
handoff: "Report: new section numbering, prek lint result, confirmation that old Section 5 was renumbered to Section 6."
---
```

## Context

The `/verify` skill currently has 5 sections (Section 1: Task Type, Section 2: WORKS Check, Section 3: FIXED Check, Section 4: Quality Gates, Section 5: Honesty Check). This task inserts a new Section 5 (Proportional Response Check) and renumbers old Section 5 to Section 6.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Verify Skill Enhancement", "Section Specification: Proportional Response Check", "Quick Reference Update", "Golden Rule Table Update".

Fixes #314.

## Objective

Insert Section 5 (Proportional Response Check) into verify/SKILL.md, renumber old Section 5 (Honesty Check) to Section 6, add the proportional check row to the Quick Reference summary template, and add two rows to the Golden Rule evidence table.

## Required Inputs

- Read `.claude/skills/verify/SKILL.md` in full — locate current Section 5 (Honesty Check), quick reference template (~line 128), Golden Rule table (~line 115)
- Read `plan/architect-process-quality-discipline.md` sections: "Verify Skill Enhancement", full Mermaid flowchart specification, evidence template, quick reference update, Golden Rule table update

## Requirements

### New Section 5

1. Insert `## 5. Proportional Response Check` AFTER Section 4 (Quality Gates) and BEFORE old Section 5 (Honesty Check)
2. Section 5 body must include:
   - Opening: "If the task has an `issue-classification` field in its metadata, verify the response matched the issue type. If no `issue-classification` is present, mark N/A and proceed."
   - The Mermaid decision flowchart from the architect spec — classification type determines which check applies
   - The evidence template block:

     ```text
     EVIDENCE:
     - Issue Classification: [type or "not classified"]
     - Scenario Target: [scenario -> improvement, or "not specified"]
     - Proportional Check: [PASS/FAIL/N/A]
     - Check detail: [what was verified and result]
     ```

### Renumbering

3. Rename `## 5. Honesty Check` (or equivalent heading) to `## 6. Honesty Check`

### Quick Reference template update

4. Add `Proportional Check: [PASS/FAIL/N/A] - Evidence: ___` row to the Quick Reference / VERIFICATION SUMMARY template, positioned between `Fixed Check` and `Quality Gates` rows (per architect spec ordering)

### Golden Rule table update

5. Add 2 rows to the Golden Rule evidence table:
   - `"Root cause fixed"` → `Evidence chain from grooming + fix addresses root cause claim`
   - `"Guardrail added"` → `New gate/check exists and triggers in exposing scenario`

## Constraints

- Sections 1-4 must not be modified
- Mermaid flowcharts: use `<br>` for line breaks inside node labels, use `=` not `:` for assignments inside label strings
- The N/A path (no `issue-classification`) must be the first branch in the flowchart — this ensures the skip behavior is immediately visible

## Expected Outputs

- `.claude/skills/verify/SKILL.md` — modified in place

## Acceptance Criteria

1. File contains `## 5. Proportional Response Check` section with a Mermaid flowchart showing all 5 classification branches plus the N/A branch
2. Old Section 5 (Honesty Check) heading is now `## 6. Honesty Check`
3. Evidence template block appears in Section 5
4. Quick Reference template includes `Proportional Check: [PASS/FAIL/N/A]` row
5. Golden Rule table includes rows for "Root cause fixed" and "Guardrail added"
6. `uv run prek run --files .claude/skills/verify/SKILL.md` exits 0

## Verification Steps

1. Run `Grep(pattern="^## [0-9]", path=".claude/skills/verify/SKILL.md", output_mode="content")` — confirm sections are numbered 1 through 6 with no gaps
2. Read Section 5 and confirm Mermaid flowchart contains an `absent` / N/A branch
3. Read the Quick Reference template and confirm `Proportional Check` row exists
4. Read the Golden Rule table and confirm 2 new rows
5. Run `uv run prek run --files .claude/skills/verify/SKILL.md` — confirm exit 0

## CoVe Checks

- Key claims to verify:
  - Current Section 5 heading text (may be "Honesty Check" or "The Honesty Check" — exact text matters for renaming)
  - The Quick Reference section exists and has a specific format (table vs text block)
  - The Golden Rule table format (markdown table vs inline text)
- Verification questions (falsifiable):
  1. What is the exact heading text of current Section 5? Run `Grep(pattern="^## 5", path=".claude/skills/verify/SKILL.md", output_mode="content")`
  2. Does a Quick Reference or VERIFICATION SUMMARY template exist? Run `Grep(pattern="VERIFICATION SUMMARY|Quick Reference", path=".claude/skills/verify/SKILL.md", output_mode="content")`
  3. Does a Golden Rule table exist? Run `Grep(pattern="Golden Rule|Required Evidence", path=".claude/skills/verify/SKILL.md", output_mode="content")`
- Evidence to collect:
  - Exact heading text of current Section 5 before rename
  - Format of Quick Reference (table row or text block) so the addition matches format
  - Whether Golden Rule table uses pipes (`|`) or prose
- Revision rule:
  - If Quick Reference is a text block (not a table), add the new row as a matching text line. If it is a table, add a table row. Match the existing format exactly.

## Handoff

Return:

- New section numbering (6 sections total)
- Confirmation that the N/A branch is the first branch in the Section 5 Mermaid flowchart
- `prek` lint result
- Format of Quick Reference used (table or text block)

---

```yaml
---
task: T5
title: "Feature Verifier python3-development: add Step 7 Proportional Response Check"
status: not-started
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: medium
accuracy-risk: medium
parallelize-with: [T2, T3, T4]
reason: "Independent file from T2, T3, T4. T6 depends on T5 for content consistency."
handoff: "Report: exact step numbers before and after edit, prek lint result, exact text of the Mermaid flowchart Step 7 label."
---
```

## Context

The `feature-verifier.md` agent in `plugins/python3-development/` currently has 7 steps (Steps 1-7 inside `<verification_process>`). This task inserts a new Step 7 (Proportional Response Check) before the existing final step (Determine Overall Status), which becomes Step 8.

T6 depends on this task to copy the identical Step 7 content to the `development-harness` variant — ensuring they stay in sync.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Feature Verifier Enhancement", "New Step in Both Feature Verifier Agents", "Step Specification: Proportional Response Check", "Update to Status Determination Step", "Update to Success Criteria".

Fixes #314.

## Objective

Insert Step 7 (Proportional Response Check with Mermaid decision flowchart) into `plugins/python3-development/agents/feature-verifier.md`, renumber current final step to Step 8, update Step 8 status determination logic, and add proportional response checklist to `<success_criteria>`.

## Required Inputs

- Read `plugins/python3-development/agents/feature-verifier.md` in full — note exact current step headings and their line numbers, current Step 7 heading text, the `<success_criteria>` block
- Read `plan/architect-process-quality-discipline.md` sections: "Step Specification: Proportional Response Check" (full Mermaid flowchart), "Status output for this step", "Update to Status Determination Step", "Update to Success Criteria"
- Note: this agent uses `<verification_process>` XML wrapper for steps, NOT a bare markdown heading block

## Requirements

### New Step 7: Proportional Response Check

1. Insert `## Step 7: Proportional Response Check` INSIDE `<verification_process>`, AFTER Step 6 (Test Edge Cases), BEFORE current Step 7 (Determine Overall Status)
2. Step 7 body must include:
   - Instruction to read task file YAML frontmatter for `issue-classification`, `scenario-target`, and `analysis-method`
   - Skip instruction: "If `issue-classification` is absent: SKIP this step. Existing verification is sufficient."
   - The Mermaid decision flowchart from the architect spec (classification type → check criteria)
   - Status output definition: VERIFIED / FAILED / SKIPPED

### Step renumbering and status update

3. Rename current `## Step 7: Determine Overall Status` to `## Step 8: Determine Overall Status`
4. Update Step 8 status determination logic to include: "VERIFIED requires all existing checks PLUS proportional response check is VERIFIED or SKIPPED" and "GAPS_FOUND if proportional response check is FAILED — include specific failure description"

### Success criteria update

5. Add to `<success_criteria>`:

   ```text
   ### Proportional Response (Step 7)

   - [ ] issue-classification read from task metadata
   - [ ] Proportional checks applied per classification type
   - [ ] Root-cause vs symptom fix verified (for defect type)
   - [ ] Guardrail added and pattern-scoped (for recurring-pattern type)
   - [ ] Results included in overall status determination
   ```

## Constraints

- Steps 1-6 must not be modified
- The new Step 7 must be inside the `<verification_process>` XML block — not outside it
- Mermaid flowcharts: use `<br>` for line breaks in node labels, use `=` not `:` for assignments in label strings
- The SKIP path (`issue-classification` absent) must be explicit as the first conditional branch
- Do not change the `skills` or `model` frontmatter fields

## Expected Outputs

- `plugins/python3-development/agents/feature-verifier.md` — modified in place

## Acceptance Criteria

1. `<verification_process>` block contains exactly 8 step headings (`## Step 1` through `## Step 8`)
2. `## Step 7: Proportional Response Check` exists and contains a Mermaid flowchart with branches for all 5 classification types plus absent/SKIP
3. `## Step 8: Determine Overall Status` exists (was Step 7) and references proportional check results in its logic
4. `<success_criteria>` contains the `### Proportional Response (Step 7)` checklist with all 5 checkbox items
5. `uv run prek run --files plugins/python3-development/agents/feature-verifier.md` exits 0

## Verification Steps

1. Run `Grep(pattern="## Step [0-9]", path="plugins/python3-development/agents/feature-verifier.md", output_mode="content")` — confirm 8 steps in order
2. Read Step 7 and confirm Mermaid flowchart includes `absent` → SKIP branch as well as all 5 classification branches
3. Read Step 8 and confirm proportional check results are referenced in the status determination logic
4. Run `Grep(pattern="Proportional Response", path="plugins/python3-development/agents/feature-verifier.md", output_mode="content")` — confirm it appears in both Step 7 body and `<success_criteria>`
5. Run `uv run prek run --files plugins/python3-development/agents/feature-verifier.md` — confirm exit 0

## CoVe Checks

- Key claims to verify:
  - Current final step is "Determine Overall Status" (not renamed already)
  - Steps are inside `<verification_process>` block (not a top-level heading structure)
  - Current step count is 7 (not 6 or 8)
- Verification questions (falsifiable):
  1. What is the exact current step count inside `<verification_process>`? Run `Grep(pattern="## Step [0-9]", path="plugins/python3-development/agents/feature-verifier.md", output_mode="content")`
  2. Does the file already contain any reference to "Proportional Response"? Run `Grep(pattern="Proportional", path="plugins/python3-development/agents/feature-verifier.md")`
- Evidence to collect:
  - Current step headings and their line numbers
  - Confirm no partial implementation exists
- Revision rule:
  - If any step content related to proportional checks already exists, read it fully before editing. Do not duplicate existing content.

## Handoff

Return:

- Step headings before and after (list of all 8 steps)
- Confirmation that the new Step 7 is inside `<verification_process>` XML block
- Exact Mermaid flowchart title used in Step 7
- `prek` lint result

---

```yaml
---
task: T6
title: "Feature Verifier development-harness: add identical Step 7 Proportional Response Check"
status: not-started
agent: general-purpose
dependencies: [T5]
priority: 3
complexity: medium
accuracy-risk: low
parallelize-with: []
reason: "Depends on T5 for content consistency. T6 copies the Step 7 content from the python3-development version with only the skill-reference difference."
handoff: "Report: diff between python3-development and development-harness versions of Step 7 (should be zero or only the skill reference), prek lint result."
---
```

## Context

The `feature-verifier.md` exists in two plugins: `python3-development` and `development-harness`. Per ADR-005 in the architect spec, the same proportional response check step is added to both agents. The only permitted difference is the existing skill reference difference between the two agents (`python3-development` vs `development-harness`).

T6 depends on T5 to ensure the Step 7 content is finalized before being mirrored. The agent doing T6 should read the completed T5 output and copy it, adjusting only the skill reference if needed.

Architecture spec: `plan/architect-process-quality-discipline.md`, section "ADR-005: Identical Feature Verifier Changes in Both Plugins".

Fixes #314.

## Objective

Apply identical Step 7 (Proportional Response Check) changes to `plugins/development-harness/agents/feature-verifier.md` as were applied in T5 to the python3-development variant, adjusting only for any existing skill reference differences.

## Required Inputs

- Read `plugins/development-harness/agents/feature-verifier.md` in full — note the existing step structure, current step count, `<success_criteria>` block, and the skill reference in the frontmatter (`skills:` field)
- Read `plugins/python3-development/agents/feature-verifier.md` in full AFTER T5 is complete — read the exact Step 7 and Step 8 content that T5 produced
- Read `plan/architect-process-quality-discipline.md` section "ADR-005" to confirm the only permitted difference

## Requirements

1. Apply the identical changes as T5 to this file:
   - Insert Step 7: Proportional Response Check (copy from python3-development version)
   - Rename current final step to Step 8: Determine Overall Status
   - Update Step 8 status logic (copy from python3-development version)
   - Add `### Proportional Response (Step 7)` checklist to `<success_criteria>` (copy from python3-development version)
2. If the `development-harness` agent currently references a different skill name than `python3-development` (e.g., `development-harness` vs `python3-development` in a prompt or skills list), preserve that difference — do not introduce skill references that do not belong in this agent
3. The Mermaid flowchart in Step 7 must be identical between the two files (the flowchart itself does not reference skill names)

## Constraints

- Do not introduce `python3-development` skill references into the `development-harness` agent
- Steps 1-6 must not be modified
- Apply ONLY the changes specified — do not refactor or improve other parts of the file
- New Step 7 must be inside the `<verification_process>` XML block

## Expected Outputs

- `plugins/development-harness/agents/feature-verifier.md` — modified in place

## Acceptance Criteria

1. `<verification_process>` block contains exactly 8 step headings
2. `## Step 7: Proportional Response Check` exists with the same Mermaid flowchart as in the python3-development version
3. Step 8 status determination logic matches the python3-development version
4. `<success_criteria>` contains the `### Proportional Response (Step 7)` checklist
5. The only differences between the two `feature-verifier.md` files are pre-existing differences (skill references, model, description) — NOT the Step 7 content itself
6. `uv run prek run --files plugins/development-harness/agents/feature-verifier.md` exits 0

## Verification Steps

1. Run `Grep(pattern="## Step [0-9]", path="plugins/development-harness/agents/feature-verifier.md", output_mode="content")` — confirm 8 steps
2. Read Step 7 in development-harness and confirm Mermaid flowchart is identical to python3-development Step 7
3. Run `uv run prek run --files plugins/development-harness/agents/feature-verifier.md` — confirm exit 0
4. Run `Grep(pattern="python3-development", path="plugins/development-harness/agents/feature-verifier.md", output_mode="content")` — confirm no new python3-development skill references were introduced

## Handoff

Return:

- Confirmation that Step 7 Mermaid flowchart is identical between both plugin versions
- Any pre-existing differences between the two files (skill references, etc.) that were preserved
- `prek` lint result

---

```yaml
---
task: T7
title: "Taxonomy Validation: classify 5+ recent backlog items using the new 5-type taxonomy"
status: not-started
agent: general-purpose
dependencies: [T1, T2]
priority: 4
complexity: medium
accuracy-risk: low
parallelize-with: []
reason: "Depends on T1 (field definitions exist in schema) and T2 (Issue Classification section format exists in groom skill). T7 is the validation gate for the taxonomy."
handoff: "Report: items classified, distribution across types, any items that did not fit a single type, path to validation report."
---
```

## Context

ADR-004 in the architect spec notes that the new taxonomy cannot be validated against historical items without this step. The groomed backlog item for #314 (Acceptance Criteria #7) requires classifying at least 5 recent backlog items to confirm coverage and usability of the 5-type taxonomy.

This task does NOT modify the target SKILL.md files. It produces a validation report as a new file at `plan/taxonomy-validation-process-quality-discipline.md`.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Testing Strategy" and "Validation Approach", subsection 1 (Taxonomy validation).

T1 must be complete so that the field definitions exist (confirming valid enum values). T2 must be complete so that the Issue Classification section format is defined (the validation uses this format when writing each classification).

Fixes #314.

## Objective

Classify at least 5 recent backlog items using the `issue-classification` taxonomy, confirm each fits exactly one type, and write the results to a validation report.

## Required Inputs

- Read `.claude/docs/TASK_FILE_FORMAT.md` after T1 — locate the `issue-classification` enum values and their meanings
- Read `.claude/docs/backlog-item-groomed-schema.md` after T1 — locate the Issue Classification section format
- List recent backlog items: run `uv run .claude/skills/backlog/scripts/backlog.py list --format json` — select at least 5 recent items across different work types (Bug, Feature, Docs, Refactor, Chore)
- For each selected item, read its file at `.claude/backlog/{slug}.md`
- Read `plan/architect-process-quality-discipline.md` sections: "Field: `issue-classification`", value semantics table, and use scenarios (5 scenario examples)

## Requirements

1. Select at least 5 recent backlog items from the backlog. Aim to select items that span different `metadata.type` values (Bug, Feature, Docs) to test cross-type coverage
2. For each item, apply the classification flowchart from T2 (Step 6 in groom-backlog-item) and assign one of the 5 classification values
3. Write a short rationale (1-2 sentences) for each classification, following the `### Issue Classification` section format
4. Identify any item that could plausibly fit two types — document the tie-break reasoning
5. Write a summary section noting which types appeared and which did not, and whether any gap or ambiguity was found in the taxonomy definitions
6. Write the validation report to `plan/taxonomy-validation-process-quality-discipline.md`

## Constraints

- Do not modify any SKILL.md, agent .md, or backlog item files — this is a read-and-report task
- Do not use placeholder or hypothetical items — classify actual items from the backlog
- If fewer than 5 items exist in the backlog, classify all available items and note the count

## Expected Outputs

- `plan/taxonomy-validation-process-quality-discipline.md` — new file with classification results

Report structure:

```markdown
# Taxonomy Validation Report — Issue #314

**Date**: {date}
**Items classified**: {N}

## Results

### {Item Title}

**Type**: {metadata.type from frontmatter}
**Issue Classification**: {procedural | defect | recurring-pattern | missing-guardrail | unbounded-design}
**Rationale**: {1-2 sentences}
**Tie-break (if any)**: {if item could fit two types, explain the decision}

[repeat for each item]

## Summary

**Type distribution**: {table showing count per classification value}
**Types not represented**: {list any of the 5 types not seen in sample}
**Taxonomy gaps**: {any item descriptions that felt ambiguous or did not fit}
**Recommendation**: {pass / needs refinement — with rationale}
```

## Acceptance Criteria

1. Report file exists at `plan/taxonomy-validation-process-quality-discipline.md`
2. Report contains at least 5 classified items, each with type, classification, and rationale
3. Each item is classified into exactly one of the 5 valid enum values
4. Report includes a summary table showing distribution across classification types
5. Any ambiguous items have documented tie-break reasoning
6. Report includes a pass/needs-refinement recommendation

## Verification Steps

1. Read `plan/taxonomy-validation-process-quality-discipline.md` — confirm it exists and contains at least 5 items
2. Confirm each classified item uses a valid enum value from `{procedural, defect, recurring-pattern, missing-guardrail, unbounded-design}`
3. Confirm the summary section includes a distribution table
4. Confirm the report ends with a pass/needs-refinement recommendation

## Handoff

Return:

- Total items classified
- Type distribution (how many per classification value)
- Whether any taxonomy gaps were found
- Path to report: `plan/taxonomy-validation-process-quality-discipline.md`
- Pass/needs-refinement verdict

---

## Context Manifest

_Generated by context-gathering agent on 2026-03-01_

### Resource Index

| Resource | Path | Used By |
|----------|------|---------|
| Architecture spec | `plan/architect-process-quality-discipline.md` | All tasks |
| Feature context | `plan/feature-context-process-quality-discipline.md` | Background only |
| Codebase analysis | `plan/codebase/sam-pipeline-quality.md` | T1, T5, T6 |
| Task file format spec | `.claude/docs/TASK_FILE_FORMAT.md` | T1 (modify), T7 (read) |
| Groomed schema | `.claude/docs/backlog-item-groomed-schema.md` | T1 (modify) |
| Groom skill | `.claude/skills/groom-backlog-item/SKILL.md` | T2 (modify) |
| Complete-implementation skill | `.claude/skills/complete-implementation/SKILL.md` | T3 (modify) |
| Verify skill | `.claude/skills/verify/SKILL.md` | T4 (modify) |
| Feature verifier (python3) | `plugins/python3-development/agents/feature-verifier.md` | T5 (modify) |
| Feature verifier (harness) | `plugins/development-harness/agents/feature-verifier.md` | T6 (modify) |
| Backlog script | `.claude/skills/backlog/scripts/backlog.py` | T7 (read) |

---

### How This Currently Works: The SAM Pipeline and Its Quality Gates

The SAM pipeline is a collection of AI instruction documents (SKILL.md files and agent .md files) that govern how work items are discovered, planned, implemented, and verified. No Python code changes are required for this feature — every change targets these markdown instruction files. This distinction is foundational: the `implementation_manager.py` parser is explicitly designed to ignore unknown YAML fields, so adding new optional fields to task metadata requires no parser changes.

The pipeline has four stages relevant to this feature.

**Stage 1: Grooming** (`/groom-backlog-item`). The grooming skill prepares backlog items to be "DEEP" (Detailed, Estimated, Emergent, Prioritized) before planning. It runs 7 numbered steps: Step 1 (parse arguments and load backlog), Step 2 (validity check), Step 3 (extract item details), Step 4 (fact-check claims), Step 5 (RT-ICA assessment per item), Step 6 (spawn groomer agents — currently the insertion point for the new Steps 6 and 7), and Step 7 (write groomed content to item files). Steps 6 and 7 will be renumbered to Steps 8 and 9 after the two new steps are inserted between Step 5 and the current Step 6. The groomer agent (`@backlog-item-groomer`) runs on `model: haiku` and is intentionally kept to structured template filling — it does NOT perform reasoning-intensive operations like root-cause analysis or issue classification. Those run in the orchestrator context (the main Claude session, typically sonnet or opus).

The valid section names for groomed content currently are (from `groom-backlog-item/SKILL.md` line 230): top-level: `Fact-Check`, `RT-ICA`. Groomed subsections: `Reproducibility`, `Priority`, `Impact`, `Scope`, `Output / Evidence`, `Dependencies`, `Research`, `Skills`, `Agents`, `Prior Work`, `Files`, `Decision`. The two new sections `Issue Classification` and `Root-Cause Analysis` must be added to this list in T2.

**Stage 2: Task metadata** (`TASK_FILE_FORMAT.md`). The task file format uses YAML frontmatter as of v2.0. The currently defined optional fields (after the required `task`, `title`, `status` fields) are: `agent`, `dependencies`, `priority`, `complexity`, `created`, `started`, `completed`, `blocked-by`, `parallelize-with`, `skills`. The Optional Fields table lives at line ~137 of `TASK_FILE_FORMAT.md`, with the `skills` row being the last entry. The JSON Schema properties block is at lines ~270–353. The "Possible Future Fields" appendix is at lines ~898–911 and lists `estimate-hours`, `actual-hours`, `assignee`, `labels`, `epic`, `sprint`, `verification-agent`, `retry-count`, `last-error` — none of the three new fields appear there, so T1 does not need to remove anything from that appendix, only note that the new fields are now defined. The template YAML block is at line ~644.

**Stage 3: Completion gates** (`complete-implementation/SKILL.md`). The completion skill runs 6 sequential phases: Phase 1 (code-reviewer), Phase 2 (feature-verifier), Phase 3 (integration-checker), Phase 4 (doc-drift-auditor), Phase 5 (service-docs-maintainer, conditional), Phase 6 (context-refinement). Phase 2 currently reads: "Launch `feature-verifier` with the task file path." T3 adds a single conditional sentence after this: "If the task file contains `issue-classification` metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks." No new phases are added.

**Stage 4: Verification** (`verify/SKILL.md` and `feature-verifier.md`). The `/verify` skill has 5 sections (Section 1: Task Type and Strategy, Section 2: The WORKS Check, Section 3: The FIXED Check, Section 4: Quality Gates, Section 5: Honesty Check). T4 inserts a new Section 5 (Proportional Response Check) before the current Section 5, which becomes Section 6. The Quick Reference summary template at line ~128 currently has rows for Works Check, Fixed Check, Quality Gates, and Honesty Check — a new Proportional Check row is added between Fixed Check and Quality Gates. The Golden Rule table at line ~115 gains two new rows. The `feature-verifier.md` agent (in both plugins) uses a `<verification_process>` XML wrapper containing `## Step N:` headings. The python3-development version currently has Steps 1–7 where Step 7 is "Determine Overall Status". The development-harness version has a Step 0 (Read Language Manifest) plus Steps 1–7, making it structurally slightly different in the front matter but the same in the final step. Both become 8-step agents (plus Step 0 in development-harness) after T5 and T6.

### How This Feature Changes the Pipeline

This feature is purely additive. All new fields are optional and all new steps have explicit N/A or skip paths for unclassified tasks. The core change is introducing proportional verification discipline: the depth of analysis at grooming time must match the issue type, and the verification gates must confirm that this proportionality was maintained.

The grooming workflow gains two new steps between RT-ICA and the groomer agent spawn. Step 6 (Issue Classification) classifies the issue into one of five types using a Mermaid decision flowchart. Step 7 (Root-Cause Analysis) is conditional — it only runs for `defect` and `recurring-pattern` classifications, invoking the `/find-cause` skill (for defect) or performing a frequency search (for recurring-pattern). For `procedural`, `missing-guardrail`, and `unbounded-design` types, Step 7 is skipped entirely. After these two steps run, the groomer agent receives the classification and analysis output as additional context in its prompt.

The verification phase gains a new check section in both the `/verify` skill and both `feature-verifier.md` agents. The check reads `issue-classification` from task YAML frontmatter. If absent, it outputs N/A and skips. If present, it applies type-specific criteria from the proportional verification criteria table defined in `plan/architect-process-quality-discipline.md`.

### Domain Knowledge: The 5-Type Issue Classification Taxonomy

The taxonomy has five mutually exclusive types. Workers applying T7 (Taxonomy Validation) must understand the semantics of each type because the classification decision uses these definitions.

`procedural` — Surface-level fix with no investigation needed. Examples: typo corrections, naming conventions, formatting changes. Analysis method: `none`. Verification check: sweep completeness (codebase search returns zero remaining instances).

`defect` — A traceable failure where a cause chain can be documented from symptom to root cause. Investigation required. Analysis method: `5-whys`. The 5 Whys methodology (verified sources: FlowFuse, Lean.org) asks "why" iteratively (typically 5 times) until the root cause is reached. Each "why" must be supported by evidence. Verification checks: (1) fix targets the root cause identified in the evidence chain, not just the symptom; (2) the scenario that exposed the defect now succeeds.

`recurring-pattern` — The same defect class has appeared 2 or more times. The focus shifts from fixing the instance to preventing recurrence. Analysis method: `6-sigma`. The 6 Sigma DMAIC framework (verified sources: GoLeanSixSigma.com, SixSigma.us) measures frequency, identifies common factors, and adds a guardrail. Verification checks: (1) a guardrail, instruction, or process change was added; (2) the guardrail covers the defect CLASS (not just the specific instance observed).

`missing-guardrail` — The system allowed a bad outcome that a gate or instruction should have prevented. Focus is on identifying and closing the gap in the instruction set or validation logic. Analysis method: `none` (or lightweight gap analysis). Verification check: new guardrail triggers in the exposing scenario.

`unbounded-design` — No clear right answer exists. The problem space must be framed (options, constraints, trade-offs) before a direction can be chosen. Analysis method: `design-framing`. Verification checks: (1) implementation matches the chosen design direction; (2) trade-offs are documented.

**Critical rule**: These two taxonomies are independent. The existing backlog `type` field (`Feature|Bug|Refactor|Docs|Chore`) describes WORK CATEGORY (what kind of deliverable). The new `issue-classification` field describes ANALYTICAL DEPTH (how much investigation the problem requires). A Bug can be `procedural` (typo in error message) or `defect` (root cause needed). A Feature can be `unbounded-design` or `missing-guardrail`. No mapping table is needed or required between the two taxonomies.

**Classification decision flowchart** (from architect spec, embedded in T2's Step 6 and T4's Section 5):

```text
Is this a typo/naming/formatting/surface fix?
  YES → procedural
  NO →
    Has this same problem class appeared 2+ times?
      YES → recurring-pattern
      NO →
        Is there a traceable failure with identifiable cause chain?
          YES → defect
          NO →
            Did the system allow a bad outcome that a gate should have prevented?
              YES → missing-guardrail
              NO → unbounded-design
```

### Domain Knowledge: Root-Cause Analysis Methods

**5 Whys (for `defect` type)**: Each "why" is stated as a CLAIM, supported by EVIDENCE, marked VERIFIED (yes/no), and linked to the prior claim with DEPENDS ON. The chain continues until the root cause is reached — a finding that is actionable and specific. The output format is the CLAIM/EVIDENCE/VERIFIED/DEPENDS ON structure used by the `/find-cause` skill. Workers doing T2 must embed invocation of `/find-cause` into Step 7 for defect items.

**6 Sigma DMAIC (for `recurring-pattern` type)**: The measurement section documents frequency (N occurrences in a time period), common factors (what the occurrences share), and affected scope. The analysis section identifies the root cause pattern (why this class of defect recurs) and the missing guardrail. The improvement section proposes the specific guardrail with a verification method. Workers doing T2 must embed a frequency search step (using `uv run .claude/skills/backlog/scripts/backlog.py list --format json --status resolved`) and the 6 Sigma measurement section format into Step 7 for recurring-pattern items.

### Dependencies Between Tasks

T1 is the foundation for all other tasks. It defines the field names, enum values, and section formats that all other tasks reference. No other task may start until T1 is complete.

T2, T3, T4, T5 are independent of each other (different files with no content overlap) but all depend on T1. After T1 completes the sync checkpoint, these four tasks can run concurrently.

T6 depends on T5. The development-harness `feature-verifier.md` agent must receive the exact Step 7 content that T5 produced in the python3-development version. T6's agent reads the completed T5 output and copies it, adjusting only for pre-existing skill reference differences between the two agents. The Mermaid flowchart in Step 7 must be identical between both files.

T7 depends on T1 and T2. T1 must be complete so the enum values exist in the schema (valid classification values are known). T2 must be complete so the Issue Classification section format exists in the grooming skill (T7 uses this format when writing each classification in the validation report).

### Critical Technical Details Workers Must Know

**Mermaid flowchart syntax rules** (enforced by prek linting): Use `<br>` for line breaks inside node labels. Use `=` (not `:`) for assignments inside label strings. Never use `\n` inside node labels. This rule applies to: the classification flowchart in T2 (Step 6), the proportional response flowchart in T4 (Section 5), and the proportional response flowchart in T5/T6 (Step 7). Violation causes lint failures.

**Backtick nesting rule**: The repo uses 3-backtick fences for code blocks by default. When a code block appears inside a 4-backtick outer fence, the inner block uses 3 backticks. Skill and agent markdown files regularly contain code blocks inside outer fences. Workers must match the existing fence depth of the file section they are editing.

**XML block containment in feature-verifier.md**: All `## Step N:` headings in `feature-verifier.md` must appear INSIDE the `<verification_process>...</verification_process>` XML block. The new Step 7 in T5 and T6 must be inserted inside this block. The `<success_criteria>` block is a separate XML block following `</verification_process>` — the Proportional Response checklist items go inside `<success_criteria>`.

**development-harness variant has Step 0**: The `plugins/development-harness/agents/feature-verifier.md` has a `## Step 0: Read Language Manifest (if available)` before Step 1. This step does not exist in the python3-development version. Workers doing T6 must not remove Step 0 when renumbering. The existing Step 7 (Determine Overall Status) becomes Step 8. The final step count in development-harness will be: Step 0 + Steps 1–8 = 9 total step headings (compared to 8 in python3-development).

**Backward compatibility is guaranteed, not inferred**: The architect spec (ADR-001) explicitly confirms that `implementation_manager.py` already ignores unknown YAML fields. Workers on T1 do NOT need to modify any Python file. The evidence for this is documented in `plan/codebase/sam-pipeline-quality.md`: "Fields not consumed by `implementation_manager.py`: `complexity`, `created`, `blocked-by`, `parallelize-with`, `accuracy-risk`." The new fields follow this same ignore-by-default pattern.

**Possible Future Fields appendix**: The three new fields (`issue-classification`, `scenario-target`, `analysis-method`) do NOT currently appear in the "Possible Future Fields" appendix at lines 898–911 of `TASK_FILE_FORMAT.md`. The appendix lists only: `estimate-hours`, `actual-hours`, `assignee`, `labels`, `epic`, `sprint`, `verification-agent`, `retry-count`, `last-error`. Therefore T1 only needs to ADD a note that these fields are now defined (Issue #314) — it does NOT need to remove any existing rows.

**complete-implementation skill Phase 2 exact current text**: The current Phase 2 text (lines 27–29 of `complete-implementation/SKILL.md`) is:

```text
## Phase 2: Feature Verification (goal-backward)

Launch `feature-verifier` with the task file path.
```

T3 appends one sentence to make it:

```text
## Phase 2: Feature Verification (goal-backward)

Launch `feature-verifier` with the task file path. If the task file contains `issue-classification` metadata, include it in the agent prompt so the feature verifier can apply proportional verification checks.
```

No other phases are modified. The condition (`if the task file contains issue-classification metadata`) is mandatory — the instruction must not be unconditional.

**verify skill Section 5 current exact heading**: The current Section 5 heading is `## 5. Honesty Check` (line 102 of `verify/SKILL.md`). T4 must rename this to `## 6. Honesty Check`. The Quick Reference template at line ~128 currently has: `Works Check`, `Fixed Check`, `Quality Gates`, `Honesty Check` rows. The new `Proportional Check` row is inserted between `Fixed Check` and `Quality Gates`.

**Groomer agent prompt in Step 8 (was Step 6)**: After T2's changes, the groomer agent prompt in Step 8 must include two new context fields:

```text
Issue Classification:
{classification section from Step 6}

Root-Cause Analysis:
{evidence chain from Step 7, or 'N/A - not applicable for this issue type'}
```

The prompt must explicitly state that the groomer agent does NOT perform classification or root-cause analysis — it receives these as inputs and incorporates them into groomed output.

**Taxonomy Validation report format** (for T7): The report is a NEW file at `plan/taxonomy-validation-process-quality-discipline.md`. It is not a modification of any existing file. The report must classify at least 5 real backlog items using `uv run .claude/skills/backlog/scripts/backlog.py list --format json`. Each classified item entry must include: Type (from frontmatter `metadata.type`), Issue Classification (one of the 5 enum values), Rationale (1-2 sentences), and Tie-break reasoning (if the item could plausibly fit two types). The report concludes with a distribution table and a pass/needs-refinement recommendation.

### Technical Reference Details

#### Files Modified by Each Task

| Task | File | Change Type | Key Locations |
|------|------|-------------|---------------|
| T1 | `.claude/docs/TASK_FILE_FORMAT.md` | Extend | Optional Fields table (~line 150), JSON Schema (~lines 270–353), template YAML (~line 644), Possible Future appendix (~lines 898–911) |
| T1 | `.claude/docs/backlog-item-groomed-schema.md` | Extend | Groomed Sections table (~line 52), format specs after table (~line 67), example body (~line 78) |
| T2 | `.claude/skills/groom-backlog-item/SKILL.md` | Extend | Insert Steps 6+7 after Step 5 (~line 157), renumber Steps 6→8 (~line 159) and 7→9 (~line 187), update groomer prompt, update valid section names (line 230), update completion criteria (line 270) |
| T3 | `.claude/skills/complete-implementation/SKILL.md` | Extend | Phase 2 description (lines 27–29) |
| T4 | `.claude/skills/verify/SKILL.md` | Extend | Insert Section 5 after Section 4 (~line 98), rename old Section 5→6 (line 102), Quick Reference (~line 128), Golden Rule table (~line 115) |
| T5 | `plugins/python3-development/agents/feature-verifier.md` | Extend | Insert Step 7 inside `<verification_process>` after Step 6 (line ~185), rename Step 7→8 (line ~185), update Step 8 status logic, add checklist to `<success_criteria>` (line ~301) |
| T6 | `plugins/development-harness/agents/feature-verifier.md` | Extend | Same as T5 — insert Step 7 after Step 6 (line ~196), rename Step 7→8 (line ~202), update Step 8, update `<success_criteria>` (line ~298) |
| T7 | `plan/taxonomy-validation-process-quality-discipline.md` | Create new | New file |

#### New YAML Fields (Exact Definitions for T1)

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

Optional Fields table rows to insert after the `skills` row (T1):

```text
| `issue-classification` | enum | `procedural`, `defect`, `recurring-pattern`, `missing-guardrail`, `unbounded-design` — analytical depth classification | `"defect"` |
| `scenario-target` | string | `"{scenario that exposed the problem} -> {what should improve}"` | `"Hook did not fire -> fires regardless of invocation method"` |
| `analysis-method` | enum | `none`, `5-whys`, `6-sigma`, `design-framing` — root-cause method applied during grooming. Default: `none` | `"5-whys"` |
```

#### Groomed Schema Section Formats (Exact Definitions for T1)

Issue Classification section format:

```markdown
### Issue Classification

**Type**: procedural | defect | recurring-pattern | missing-guardrail | unbounded-design
**Rationale**: {1-2 sentence explanation of why this classification was chosen}
**Analysis Method**: none | 5-whys | 6-sigma | design-framing
**Scenario Target**: {what scenario exposed this} -> {what should improve}
```

Root-Cause Analysis section format (5-whys variant):

```markdown
### Root-Cause Analysis

**Method**: 5-whys
**Classification**: defect

#### Evidence Chain

1. CLAIM: {symptom observed}
   EVIDENCE: {source}
   VERIFIED: yes
   DEPENDS ON: none (symptom)

2. CLAIM: {why 1}
   EVIDENCE: {source}
   VERIFIED: yes
   DEPENDS ON: 1

**Root Cause**: {single actionable statement}
**Scenario Target**: {what scenario exposed this} -> {what should improve}
```

Root-Cause Analysis section format (6-sigma variant):

```markdown
### Root-Cause Analysis

**Method**: 6-sigma
**Classification**: recurring-pattern

#### Measurement

- **Frequency**: {N occurrences in {time period or batch}}
- **Common factors**: {what the occurrences share}
- **Affected scope**: {what parts of the system are impacted}

#### Analysis

- **Root cause pattern**: {why this class of defect recurs}
- **Missing guardrail**: {what gate or instruction should prevent this}

#### Improvement

- **Proposed guardrail**: {specific instruction, gate, or check to add}
- **Verification**: {how to confirm the guardrail works}
```

#### Proportional Verification Criteria Table (Exact Definitions for T4 and T5/T6)

| Classification | Check | Pass Criteria | Fail Criteria |
|---------------|-------|---------------|---------------|
| `procedural` | Sweep completeness | Codebase search for the pattern returns zero remaining instances | Instances of the same pattern remain unfixed |
| `defect` | Root cause addressed | Fix targets the root cause claim from evidence chain | Fix addresses only the symptom; root cause remains |
| `defect` | Scenario verification | The scenario in `scenario-target` produces expected behavior | Exposing scenario still fails or was worked around |
| `recurring-pattern` | Guardrail added | New gate, check, instruction, or validation exists | No prevention mechanism added; only the instance was fixed |
| `recurring-pattern` | Guardrail coverage | Guardrail applies to the defect CLASS | Guardrail only catches the exact case, not the pattern |
| `missing-guardrail` | Gate gap filled | Guardrail triggers in the exposing scenario | Guardrail does not trigger in the exposing scenario |
| `unbounded-design` | Design implemented as specified | Implementation matches the design direction the human selected | Implementation deviates without documented rationale |
| `unbounded-design` | Trade-offs documented | Architecture spec or task file records what was chosen and rejected | No documentation of decision space or trade-offs |
| (absent) | No proportional check | Skip — existing WORKS/FIXED/Quality Gates apply | N/A |

#### Feature Verifier Step 7 Evidence Template (Exact Definition for T5/T6)

```text
EVIDENCE:
- Issue Classification: [type or "not classified"]
- Scenario Target: [scenario -> improvement, or "not specified"]
- Proportional Check: [PASS/FAIL/N/A]
- Check detail: [what was verified and result]
```

#### Verify Skill Quick Reference After T4 Edit

```text
VERIFICATION SUMMARY:
Task Type: [FIX/FEATURE/REFACTOR/DOCS/INVESTIGATION]
Works Check: [PASS/FAIL] - Evidence: ___
Fixed Check: [PASS/FAIL/N/A] - Evidence: ___
Proportional Check: [PASS/FAIL/N/A] - Evidence: ___
Quality Gates: [PASS/FAIL] - Evidence: ___
Honesty Check: [PASS/FAIL]

VERDICT: [COMPLETE / NOT COMPLETE - reason]
```

#### Golden Rule Table Additions (for T4)

```text
| "Root cause fixed" | Evidence chain from grooming + fix addresses root cause claim |
| "Guardrail added"  | New gate/check exists and triggers in exposing scenario       |
```

#### Success Criteria Checklist Added to Both feature-verifier.md Agents (T5/T6)

```text
### Proportional Response (Step 7)

- [ ] issue-classification read from task metadata
- [ ] Proportional checks applied per classification type
- [ ] Root-cause vs symptom fix verified (for defect type)
- [ ] Guardrail added and pattern-scoped (for recurring-pattern type)
- [ ] Results included in overall status determination
```

#### Linting Command for All Modified Files

```bash
uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md
uv run prek run --files .claude/docs/backlog-item-groomed-schema.md
uv run prek run --files .claude/skills/groom-backlog-item/SKILL.md
uv run prek run --files .claude/skills/complete-implementation/SKILL.md
uv run prek run --files .claude/skills/verify/SKILL.md
uv run prek run --files plugins/python3-development/agents/feature-verifier.md
uv run prek run --files plugins/development-harness/agents/feature-verifier.md
```

Each command must exit 0 before the task for that file is considered complete. These are the definitive acceptance criteria verification commands.
