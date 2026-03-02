# Taxonomy Validation Report — Issue #314

**Date**: 2026-03-02
**Items classified**: 7

## Results

### Fix pre-existing CI check failures on main

**Type**: Bug
**Issue Classification**: defect
**Rationale**: CI tests fail due to specific identifiable bugs — a prettier format assertion mismatch (race condition causes fallback to non-prettier JSON) and stale manifest entries. Root causes are isolated to known code locations.
**Tie-break (if any)**: Could be "procedural" (sweep stale entries), but the test failure has a specific root cause (ENOTEMPTY race condition) that requires targeted fixing, not just a sweep. Defect takes precedence when a root cause exists.

### Reduce session-start context load via rules path-scoping

**Type**: Chore
**Issue Classification**: unbounded-design
**Rationale**: No prior design decision existed about context budget allocation at session start. Optimization primitives (paths scoping, disable-model-invocation) existed but were never applied. The fix requires a design decision about what loads eagerly vs lazily — a design framing exercise, not a bug fix.
**Tie-break (if any)**: None — clearly a design gap, not a defect (the system works as implemented, but the design never addressed context budget).

### SAM: Parser regex false positive on Task Summary Statistics

**Type**: Feature
**Issue Classification**: defect
**Rationale**: The widened task header regex matches non-task sections (e.g., "## Task Summary Statistics") as task headers. Root cause: overly broad regex without negative lookahead or post-parse filter. Fix targets the specific regex pattern.
**Tie-break (if any)**: None — specific bug with identifiable root cause.

### verification-gate: Remove unsubstantiated 95% confidence claim

**Type**: Feature
**Issue Classification**: procedural
**Rationale**: A straightforward sweep-and-fix: locate the unsubstantiated "95% confidence" claim in the plugin files, then either add a citation or remove the percentage. No root-cause analysis needed — the problem is the presence of an uncited claim, and the fix is procedural (find, evaluate, remove/cite).
**Tie-break (if any)**: None — no deeper pattern or design issue. Pure procedural cleanup.

### SAM: Conflicting Review Findings

**Type**: Feature
**Issue Classification**: missing-guardrail
**Rationale**: The SAM framework has no adjudication protocol for when forensic review and self-verification disagree. The gap is the absence of a gate/mechanism to handle review conflicts. The fix is adding a protocol that triggers when conflicting findings are detected.
**Tie-break (if any)**: Could be "unbounded-design" (no design exists for conflict resolution), but the issue is specifically about a missing gate at a known decision point (review stage), not an open-ended design question. Missing-guardrail fits better because the gap is at an identifiable process boundary.

### Agent Large File Write Strategy

**Type**: Feature
**Issue Classification**: recurring-pattern
**Rationale**: The same failure mode (sub-agent timeout/stall on large Write calls) has been observed across multiple agent invocations and different file types. The fix must address the pattern class (large file writes in general), not just one instance. A strategy document plus delegation instruction changes are needed.
**Tie-break (if any)**: None — multiple observed instances of the same failure class confirms recurring-pattern.

### Plugin-Creator Refactor Workflow Disconnects

**Type**: (no type in frontmatter — inferred as Refactor)
**Issue Classification**: recurring-pattern
**Rationale**: Four verified instances of the same defect class — workflow steps that don't pass state to the next step (task IDs not passed, inconsistent tracking APIs, missing completion instructions, non-persistent session state). The fix must address the disconnect pattern across the entire workflow, not just one step.
**Tie-break (if any)**: Could be "missing-guardrail" (no validation that workflow steps are connected), but the primary issue is 4 concrete instances of the same pattern, not the absence of a gate. Fix the pattern first; a guardrail could follow.

## Summary

**Type distribution**:

| Classification | Count | Items |
|---|---|---|
| procedural | 1 | verification-gate: Remove unsubstantiated 95% confidence claim |
| defect | 2 | Fix pre-existing CI check failures on main, SAM: Parser regex false positive |
| recurring-pattern | 2 | Agent Large File Write Strategy, Plugin-Creator Refactor Workflow Disconnects |
| missing-guardrail | 1 | SAM: Conflicting Review Findings |
| unbounded-design | 1 | Reduce session-start context load |

**Types not represented**: All 5 types are represented in this sample.

**Taxonomy gaps**: No items were found that could not fit into exactly one classification type. Two items (CI failures, workflow disconnects) had plausible secondary classifications, but tie-break reasoning consistently resolved to a single primary type. The tie-break heuristic used: when a root cause exists, prefer `defect`; when multiple instances exist, prefer `recurring-pattern`; when a specific process boundary lacks a gate, prefer `missing-guardrail`.

**Recommendation**: **Pass** — The 5-type taxonomy provides complete, unambiguous coverage of the 7 items tested. All 5 types appeared at least once, no item required a new type, and tie-breaks were resolved using the classification flowchart's decision logic. The taxonomy is ready for production use in the grooming workflow.
