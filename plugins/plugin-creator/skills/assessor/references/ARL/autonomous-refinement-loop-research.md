# Autonomous Refinement Loop — Research Document

Removing the human from the assess → plan → implement → review → recurse loop. This document captures what a human checks at each gate, what machine-verifiable conditions would replace those checks, and what infrastructure is missing today.

This document describes research findings for future implementation. It is not an executable skill.

---

## Desired Workflow

Assess a skill or agent in a plugin and have a plan of refinements and improvements made, followed by reviewing those changes for sanity and feasibility towards the goal of the skill, followed by creating new skills if they don't fit with the current skill, followed by reviewing the skill again recursively until there's no additional improvements found for its desired purpose/goal (or a given number of recursions).

---

## What the Human Checks at Each Step

### After Assessment/Planning

- Are the findings real problems or false positives?
- Does the plan address the actual intent of the skill, or is it optimizing for metrics that don't matter?
- Are the proposed changes proportional to the issues found, or is it over-engineering?
- Will the changes break something downstream that the assessor didn't account for?

### After Implementation

- Did the agent do what the plan said, or did it drift?
- Is the result functionally equivalent to what existed before (no content loss)?
- Do the changes actually improve the skill for its stated purpose, or just satisfy the audit rubric?

### After "Create New Skill" Decisions

- Does the extracted content genuinely belong in a separate skill, or is the split artificial?
- Will users find and invoke the new skill, or did we just fragment something that worked better as one piece?

### During Recursion

- Is the loop converging or oscillating (fix A breaks B, fix B breaks A)?
- Are the remaining findings worth fixing, or are we chasing diminishing returns?
- Has the skill's original purpose drifted through successive rewrites?

---

## What Would Replace the Human

Each of those checks maps to a verifiable condition:

| Human Judgment | Machine-Verifiable Replacement |
|---|---|
| Are findings real? | Cross-reference each finding against the source file with line evidence. False positives have no line evidence. |
| Is the plan proportional? | Compare change scope (files touched, lines changed) against finding severity. High-scope changes for low-severity findings get flagged. |
| Will changes break downstream? | Grep all inbound references to modified skills/agents. If anything references what we're changing, verify the contract still holds. |
| Did implementation match plan? | Diff the plan's "expected outputs" against actual outputs. Every acceptance criterion in the task file gets a pass/fail. |
| No content loss? | Before/after token count per skill. Semantic diff — every heading and code fence in the original must appear somewhere in the result. |
| Do changes serve the skill's purpose? | Re-read the skill's description after changes. Does the body still deliver what the description promises? If the description had to change, that's a flag. |
| Is the split justified? | A new skill must have at least 3 independent trigger scenarios. If it only gets invoked from the parent, it's not a skill — it's a reference file. |
| Is the loop converging? | Track finding count per iteration. If iteration N has >= findings as iteration N-1, stop. |
| Has purpose drifted? | Compare the skill's description at iteration 0 vs iteration N. If the description changed, the purpose drifted — flag for review. |
| Diminishing returns? | Define a threshold — if remaining findings are all severity "info" or the score improvement per iteration drops below a delta, stop. |

---

## What's Not in Place Today

### 1. No Purpose Anchor

Nothing records "this is what the skill is supposed to do" at the start and checks it at the end. The description field exists but nothing treats it as an invariant.

### 2. No Content-Loss Detection

`/ensure-complete` re-runs the assessor and does code review, but doesn't diff before/after to verify nothing was dropped.

### 3. No Convergence Tracking

No state file records finding counts per iteration. Each invocation is stateless.

### 4. No Proportionality Check

The assessor produces findings and the implementer acts on all of them. Nothing asks "is this change worth its blast radius?"

### 5. No Downstream Impact Analysis

The assessor audits inbound references (bidirectional coherence in the lifecycle audit) but the implementation step doesn't re-verify those references after changes.

### 6. No Split Justification Gate

`/refactor-skill` splits based on line count and domain boundaries, but doesn't verify the resulting skills are independently useful.

---

## Relationship to Existing Skills

The audit dimensions added in the lifecycle audit skills solve some of these — they detect coherence gaps and dead components. But they run before implementation, not after. The gap is in the post-implementation verification loop and the convergence machinery.

### Existing Pipeline (Manual)

```
/refactor-plugin → review → /implement-refactor → /ensure-complete → if follow-up tasks → /implement-refactor → repeat
```

Each step requires human invocation today.

### Existing Skills Involved

| Command | What It Does |
|---|---|
| `/plugin-creator:refactor-plugin <path>` | Runs assessor → creates plan files → pauses for review → optionally runs implement-refactor |
| `/plugin-creator:assessor <name>` | 4-tier assessment (structural + lifecycle audits) → design map → task file → context gathering |
| `/plugin-creator:implement-refactor <slug>` | Executes tasks from a task file created by assessor |
| `/plugin-creator:ensure-complete <task-file>` | Validates refactoring results, creates follow-up tasks if issues remain |
| `/plugin-creator:audit-skill-lifecycle <path>` | 7-dimension skill workflow coherence audit |
| `/plugin-creator:audit-agent-lifecycle <path>` | 8-dimension agent capability validation audit |
| `/plugin-creator:audit-skill-completeness <path>` | 8-category quality scoring against Anthropic patterns |
