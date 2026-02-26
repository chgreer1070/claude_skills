# Autonomous Refinement Loop — Research Document

This document defines the problem space for the Autonomous Refinement Loop (ARL). It captures what a human checks at each gate, what kinds of machine-verifiable conditions would need to replace those checks, and what capabilities are missing today.

This is a problem statement and requirements document. It describes what needs to happen and why. It does not prescribe how to build it — no schemas, thresholds, file layouts, or tool selections. See `ARL-agent-instructions.md` for scope boundary rationale.

**Relationship to other ARL documents:**

- This document → defines the problem (what the human does, what's missing)
- [Human-Out-of-Loop Prerequisites](./human-out-of-loop-prerequisites.md) → analyzes the conditions under which human gates can be removed
- `ARL-agent-instructions.md` → governs the expert panel process that produces the logical process design

---

## Research Questions This Document Addresses

This document primarily advances these research questions (from `ARL-agent-instructions.md` Section 1a):

- **Primary:** Under what conditions can human judgment at iterative refinement loop gates be replaced by machine-verifiable conditions, and what are the failure modes when those conditions are insufficient?
- **Secondary #1:** What patterns for autonomous loop control exist across the surveyed frameworks, and which are implemented?
- **Secondary #2:** For each ARL requirement (R1–R10), what is the minimum set of logical conditions that must hold for the gate to operate without human intervention?

---

## Desired Workflow

Assess a skill or agent in a plugin and have a plan of refinements and improvements made, followed by reviewing those changes for sanity and feasibility towards the goal of the skill, followed by creating new skills if they don't fit with the current skill, followed by reviewing the skill again recursively until there's no additional improvements found for its desired purpose/goal (or a given number of recursions).

---

## What the Human Checks at Each Step

These are the judgment points where a human currently intervenes. Each represents a gate where the loop cannot proceed autonomously without some form of machine-verifiable replacement.

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

## What Must Replace the Human

Each human check maps to a category of verifiable condition. The table below describes what each replacement must achieve — the logical requirement — not how to build it.

| Human Judgment | What the Replacement Must Achieve | ARL Requirement |
|---|---|---|
| Are findings real? | Distinguish genuine issues from false positives before acting on them. A finding without verifiable evidence should not trigger changes. | R3 (Validity filtering) |
| Is the plan proportional? | Evaluate whether the scope of proposed changes is proportional to the severity of the findings. Flag when blast radius exceeds what the finding warrants. | R8 (Proportionality) |
| Will changes break downstream? | Identify all inbound references to modified components. After changes, verify those references still resolve and contracts still hold. | R9 (Downstream impact) |
| Did implementation match plan? | Compare what was planned against what was produced. Every stated acceptance criterion must be checkable as pass or fail. | R4 (Plan quality gates) |
| No content loss? | Detect whether semantic units (sections, headings, behavioral blocks, examples) present before changes are still present after. Reorganization is acceptable; silent deletion is not. | R6 (Content-loss detection) |
| Do changes serve the skill's purpose? | Maintain a record of the skill's stated intent from before any changes. Check whether changes move toward or away from that intent. | R5 (Purpose anchor) |
| Is the split justified? | A new skill created by splitting must be independently viable — invocable in multiple distinct contexts, not only from its parent. | R10 (Split justification) |
| Is the loop converging? | Track whether the loop is producing fewer findings per iteration (converging), the same findings (stalled), or alternating between states (oscillating). | R7 (Convergence tracking) / R2 (Loop detection) |
| Has purpose drifted? | Compare the skill's stated intent at iteration 0 against its state at iteration N. Detect when successive changes have shifted the skill away from its original purpose. | R5 (Purpose anchor) |
| Diminishing returns? | Determine when remaining findings are not worth the cost of fixing them. The loop should stop when continuing produces less value than stopping. | R7 (Convergence tracking) |

---

## What's Not in Place Today (Infrastructure Gaps)

These gaps describe what the ARL currently lacks. For each gap, the description covers what capability is missing and why it matters. The expert panel process (governed by `ARL-agent-instructions.md`) will determine the logical process design for addressing each gap.

For the expanded gap analysis including prior expert panel findings, see `ARL-agent-instructions.md` Section 9.

### 1. No Purpose Anchor

Nothing records "this is what the skill is supposed to do" at the start and checks it at the end. The description field exists but nothing treats it as an invariant. Without a purpose anchor, successive iterations can drift the skill away from its original intent without any gate detecting the change.

### 2. No Content-Loss Detection

`/ensure-complete` re-runs the assessor and does code review, but doesn't diff before/after to verify nothing was dropped. Content can be silently removed during refactoring, and the current pipeline has no mechanism to detect it.

### 3. No Convergence Tracking

No state is maintained across iterations. Each invocation is stateless — it does not know how many iterations have occurred, what findings were present in previous iterations, or whether the finding count is increasing or decreasing.

### 4. No Proportionality Check

The assessor produces findings and the implementer acts on all of them. Nothing evaluates whether the scope of a proposed fix is proportional to the severity of the finding it addresses. Low-severity findings can trigger high-scope changes without any gate questioning whether the change is worth it.

### 5. No Downstream Impact Analysis

The assessor audits inbound references (bidirectional coherence in the lifecycle audit) but the implementation step doesn't re-verify those references after changes. A change that breaks a downstream consumer is not detected until someone independently encounters the breakage.

### 6. No Split Justification Gate

`/refactor-skill` splits based on line count and domain boundaries, but doesn't verify the resulting skills are independently useful. A skill that only gets invoked from its parent is a reference file, not a skill — but no gate checks for this.

### 7. No Loop Detection

No mechanism detects whether the loop is oscillating (fix A breaks B, fix B breaks A) or producing diminishing returns. Without this, the loop can run indefinitely without converging.

### 8. No Validity Filtering

Findings from the assessor are treated as equally valid. No mechanism distinguishes high-confidence findings (with file:line evidence) from low-confidence ones (pattern-matched or inferred). False positives consume iteration budget and can introduce regressions.

### 9. No Plan Quality Gates

Plans produced by the planning step are not validated before execution. A plan that is internally inconsistent, addresses the wrong findings, or proposes disproportionate changes proceeds without challenge.

---

## Relationship to Existing Skills

The audit dimensions added in the lifecycle audit skills solve some of these — they detect coherence gaps and dead components. But they run before implementation, not after. The gap is in the post-implementation verification loop and the convergence machinery.

### Existing Pipeline (Manual)

<eg>
/refactor-plugin → review → /implement-refactor → /ensure-complete → if follow-up tasks → /implement-refactor → repeat
</eg>

Each step requires human invocation today. The research question is whether and under what conditions these human gates can be replaced with machine-verifiable conditions.

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
