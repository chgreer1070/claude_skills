---
task: T7
title: "Taxonomy Validation: classify 5+ recent backlog items using the new 5-type taxonomy"
status: complete
started: 2026-03-02T00:19:00Z
completed: 2026-03-02T00:22:00Z
agent: general-purpose
dependencies: [T1, T2]
priority: 4
complexity: medium
accuracy-risk: low
parallelize-with: []
reason: "Depends on T1 (field definitions exist in schema) and T2 (Issue Classification section format exists in groom skill). T7 is the validation gate for the taxonomy."
handoff: "Report: items classified, distribution across types, any items that did not fit a single type, path to validation report."
---

## Context

ADR-004 in the architect spec notes that the new taxonomy cannot be validated against historical items without this step. The groomed backlog item for #314 (Acceptance Criteria #7) requires classifying at least 5 recent backlog items to confirm coverage and usability of the 5-type taxonomy.

This task does NOT modify the target SKILL.md files. It produces a validation report as a new file at `plan/taxonomy-validation-process-quality-discipline.md`.

Architecture spec: `plan/architect-process-quality-discipline.md`, sections "Testing Strategy" and "Validation Approach", subsection 1 (Taxonomy validation).

T1 must be complete so that the field definitions exist (confirming valid enum values). T2 must be complete so that the Issue Classification section format is defined (the validation uses this format when writing each classification).

Fixes #314.

## Objective

Classify at least 5 recent backlog items using the `issue-classification` taxonomy, confirm each fits exactly one type, and write the results to a validation report.

## Required Inputs

- Read `plugins/development-harness/docs/TASK_FILE_FORMAT.md` after T1 — locate the `issue-classification` enum values and their meanings
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

