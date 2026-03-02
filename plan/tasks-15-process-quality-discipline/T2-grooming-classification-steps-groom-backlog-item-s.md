---
task: T2
title: "Grooming Classification Steps: groom-backlog-item/SKILL.md"
status: complete
started: 2026-03-02T00:06:00Z
completed: 2026-03-02T00:15:00Z
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: high
accuracy-risk: medium
parallelize-with: [T3, T4, T5]
reason: "T3, T4, T5 are independent files with no content overlap. All can execute concurrently after T1."
handoff: "Report: new step numbers, prek lint result, whether the Mermaid flowchart renders correctly (check node labels use <br> not \\n and = not : for assignments)."
---

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

