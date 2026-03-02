---
task: T4
title: "Verify Skill Proportional Check: verify/SKILL.md"
status: complete
started: 2026-03-02T00:06:00Z
completed: 2026-03-02T00:15:00Z
agent: general-purpose
dependencies: [T1]
priority: 2
complexity: medium
accuracy-risk: medium
parallelize-with: [T2, T3, T5]
reason: "Independent file. No overlap with T2, T3, T5."
handoff: "Report: new section numbering, prek lint result, confirmation that old Section 5 was renumbered to Section 6."
---

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

