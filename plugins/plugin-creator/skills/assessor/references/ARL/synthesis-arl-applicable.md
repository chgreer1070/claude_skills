# Synthesis: Specific Systems for Plugin-Creator ARL

What specific systems and processes from the six analyzed frameworks directly support the plugin-creator's autonomous refinement loop?

**Source documents**: framework-analysis-bmad-method.md, framework-analysis-gastown.md, framework-analysis-gsd.md, framework-analysis-octocode.md, framework-analysis-ralph.md, framework-analysis-sam.md, autonomous-refinement-loop-research.md, human-out-of-loop-prerequisites.md

**Date**: 2026-02-13

---

## 1. ARL Requirements Recap

The autonomous refinement loop must support this workflow:

> Assess a skill or agent in a plugin and have a plan of refinements and improvements made, followed by reviewing those changes for sanity and feasibility towards the goal of the skill, followed by creating new skills if they don't fit with the current skill, followed by reviewing the skill again recursively until there's no additional improvements found for its desired purpose/goal (or a given number of recursions).
>
> -- autonomous-refinement-loop-research.md, line 11

### The Loop Structure

```
Assess --> Plan --> Implement --> Review --> Recurse (or Stop)
```

### Six Requirements Extracted from Research Documents

| # | Requirement | Source |
|---|------------|--------|
| R1 | **Front-loading to minimize human gates** | human-out-of-loop-prerequisites.md, Section 4: "every point where a human would pivot, decide, review, or quality-check gets asked and clarified at the start" |
| R2 | **Convergence detection** | autonomous-refinement-loop-research.md, line 56: "Track finding count per iteration. If iteration N >= iteration N-1, stop." |
| R3 | **Content-loss prevention** | autonomous-refinement-loop-research.md, line 53: "Before/after token count per skill. Semantic diff -- every heading and code fence in the original must appear somewhere in the result." |
| R4 | **Purpose drift detection** | autonomous-refinement-loop-research.md, line 57: "Compare skill's description at iteration 0 vs iteration N. If description changed, purpose drifted -- flag for review." |
| R5 | **Proportionality checking** | autonomous-refinement-loop-research.md, line 50: "Compare change scope (files touched, lines changed) against finding severity. High-scope changes for low-severity findings get flagged." |
| R6 | **Downstream impact analysis** | autonomous-refinement-loop-research.md, line 51: "Grep all inbound references to modified skills/agents. If anything references what we're changing, verify the contract still holds." |

### Additional Requirements from Prerequisites Analysis

| # | Requirement | Source |
|---|------------|--------|
| R7 | **Verifiable findings (no false positives)** | human-out-of-loop-prerequisites.md, Section 2: "Cross-reference each finding against the source file with line evidence. False positives have no line evidence." |
| R8 | **Plan-to-implementation fidelity** | human-out-of-loop-prerequisites.md, Section 2: "Diff the plan's expected outputs against actual outputs. Every acceptance criterion gets a pass/fail." |
| R9 | **Split justification** | autonomous-refinement-loop-research.md, line 55: "A new skill must have at least 3 independent trigger scenarios. If it only gets invoked from the parent, it's not a skill -- it's a reference file." |
| R10 | **Escalation triggers** | human-out-of-loop-prerequisites.md, Section 4: "When autonomous loop cannot proceed, escalation to human is automatic with clear context." |

---

## 2. Direct Imports

For each ARL requirement, the framework with the most directly importable solution.

| ARL Requirement | Best Source | Specific Mechanism | Adaptation Needed |
|----------------|-------------|-------------------|-------------------|
| **R1: Front-loading** | SAM | **RT-ICA gate**: Classify every prerequisite as AVAILABLE/DERIVABLE/MISSING. Block if any MISSING. Produces ARTIFACT:GOAL, ARTIFACT:THRESHOLDS, ARTIFACT:GUARDRAILS, ARTIFACT:TOOLCHAIN. (framework-analysis-sam.md, Section D) | Adapt artifact types: ARTIFACT:GOAL -> refinement goal YAML. ARTIFACT:THRESHOLDS -> convergence exit criteria. ARTIFACT:GUARDRAILS -> immutability constraints. Replace SAM's generic prerequisites with ARL-specific ones: purpose anchor, baseline metrics, dependency graph, validator config. |
| **R2: Convergence detection** | Ralph | **Multi-signal termination**: (1) Completion promise string detected in output. (2) Task exhaustion -- no open tasks remain. (3) Safety limits -- max iterations, max runtime, max cost, consecutive failures. (4) Loop detection -- 90% fuzzy similarity on sliding window of 5 outputs. (framework-analysis-ralph.md, Section C) | Replace "completion promise" with "assessment score above threshold." Replace "task exhaustion" with "finding count = 0 at severity >= threshold." Keep safety limits and loop detection as-is. Add ARL-specific signal: "score improvement delta < threshold." |
| **R3: Content-loss prevention** | None (novel requirement) | No framework implements structural content preservation checking. The closest mechanism is SAM's boundary verification between stages (framework-analysis-sam.md, Section C), but it validates artifacts, not content inventories within artifacts. | **Must build from scratch.** autonomous-refinement-loop-research.md specifies the method: before/after token count, heading inventory, code fence inventory. Implementation: pre-iteration snapshot of structural elements -> post-iteration diff -> block if any element missing without explicit delete approval. |
| **R4: Purpose drift detection** | Ralph + SAM (composite) | Ralph's **memory system** captures purpose-relevant state. SAM's **forensic review** validates against original goals. Neither specifically tracks description-level drift. | **Composite solution** -- see Section 3.1 below. |
| **R5: Proportionality checking** | GSD | **Deviation rules** (framework-analysis-gsd.md, Section C): Rules 1-3 auto-fix (bugs, missing critical, blockers) with tracking. Rule 4 STOP for architectural changes. Severity tiers determine authority level. | Replace GSD's 4 rules with ARL severity-to-scope mapping: info -> max 5 lines changed. minor -> max 1 file changed. major -> max 3 files changed. critical -> unlimited but must cite. Thresholds from ARTIFACT:THRESHOLDS during front-loading. |
| **R6: Downstream impact analysis** | Gas Town + OctoCode (composite) | Gas Town's **dependency graph** (bead references, convoy tracking -- framework-analysis-gastown.md, Section C). OctoCode's **LSP-first research flow** with mandatory lineHint (framework-analysis-octocode.md, Section E.4). | **Composite solution** -- see Section 3.2 below. |
| **R7: Verifiable findings** | OctoCode | **Mandatory evidence requirements**: file:line citations required for all claims. "FORBIDDEN thinking" pattern intercepts guessing. Hint-driven tool chaining ensures research is grounded. (framework-analysis-octocode.md, Section E.2, E.6) | Adapt to ARL: every assessment finding must include file:line citation. Findings without citations are automatically classified as false positives and dropped. Validation: grep cited line in source file -- if text does not match, finding is stale. |
| **R8: Plan-to-implementation fidelity** | GSD | **Self-check in executors**: After writing SUMMARY.md, verify claims by checking files exist on disk and commits exist in git history. (framework-analysis-gsd.md, Section E.9). Plus **goal-backward verification**: "What must be TRUE? What must EXIST? What must be WIRED?" (framework-analysis-gsd.md, Section E.3) | Adapt: after each implementation step, verify: (1) files listed in plan actually changed (git diff check), (2) acceptance criteria from task file are pass/fail against current state, (3) no unplanned files modified (scope check). |
| **R9: Split justification** | BMAD (partial) | BMAD's **adversarial review** forces finding issues -- "no looks good allowed" (framework-analysis-bmad-method.md, Section C). Apply adversarially to split proposals. | Adapt: before splitting, an adversarial reviewer must find >= 3 independent trigger scenarios for the proposed new skill. If fewer than 3 found, the split is rejected and content stays as a reference file. This threshold from autonomous-refinement-loop-research.md line 55. |
| **R10: Escalation triggers** | Gas Town | **Tiered escalation protocol** with categories: decision, help, blocked, failed, emergency, gate_timeout, lifecycle. Structured routing: Worker -> Deacon -> Mayor -> Overseer. (framework-analysis-gastown.md, Section C) | Simplify to 3 tiers for ARL: (1) Auto-resolve: retry with different approach. (2) Escalate to orchestrator: request re-planning. (3) Escalate to human: present findings and ask for direction. Map ARL-specific triggers to each tier. |

---

## 3. Composite Solutions

Where no single framework solves a requirement, combined mechanisms from multiple frameworks.

### 3.1 Purpose Drift Detection (R4)

**Requirement**: Detect when iterative refinement shifts a skill away from its original purpose.

**Component A: Purpose Anchor from SAM**

SAM's Discovery phase captures goals and anti-goals as artifacts (framework-analysis-sam.md, Section D). The RT-ICA gate validates prerequisites before execution.

**Adaptation**: During ARL front-loading, capture the skill's description verbatim as ARTIFACT:PURPOSE_ANCHOR. This becomes the invariant.

```yaml
ARTIFACT:PURPOSE_ANCHOR(SCOPE:skill-name)
description_text: "Complete analysis of plugin structure and quality..."
description_hash: "sha256:a1b2c3..."
captured_at: "iteration-0"
```

**Component B: Memory-Based Tracking from Ralph**

Ralph's memory system records decisions and patterns across iterations (framework-analysis-ralph.md, Section E.6). Memories are injected at each iteration start.

**Adaptation**: After each ARL iteration, record the current description text as a "context" memory. At iteration start, the injected memories include all previous descriptions, enabling the assessment agent to see the drift trajectory.

**Component C: Forensic Review from SAM**

SAM's Forensic Review Agent (Stage 6) validates against original goals using independent context (framework-analysis-sam.md, Section E.2).

**Adaptation**: After each ARL iteration, a forensic review step compares current description against ARTIFACT:PURPOSE_ANCHOR. If the description text changed, flag with severity:

| Change Type | Detection Method | Action |
|-------------|-----------------|--------|
| No change | Exact text match | Continue |
| Wording change (same meaning) | Embedding cosine similarity > 0.90 | Continue with note |
| Scope narrowing | Keywords removed, scope reduced | Flag as WARNING |
| Scope expansion | New capabilities added to description | Flag as BLOCKING -- requires human approval |
| Complete rewrite | Cosine similarity < 0.85 | STOP -- purpose drift confirmed |

**Glue Logic**: The purpose anchor is captured once (front-loading). Each iteration checks against it (forensic review). The memory system tracks the trajectory (Ralph pattern). The thresholds (0.90, 0.85) come from human-out-of-loop-prerequisites.md Section 2 (front-loadable classification).

### 3.2 Downstream Impact Analysis (R6)

**Requirement**: Before modifying a skill/agent, identify and verify all downstream dependencies.

**Component A: Dependency Graph from Gas Town**

Gas Town tracks all references between work units via the beads database (framework-analysis-gastown.md, Section C). Every action is attributed, creating a queryable dependency graph.

**Adaptation**: Before each ARL iteration, build a dependency graph for the target skill:
- Grep all markdown files for `Skill(command: "skill-name")`
- Grep all markdown files for the skill name as a string literal
- Parse plugin.json files for component references
- Store as ARTIFACT:DEPENDENCIES(SCOPE:skill-name)

**Component B: Contract Verification from OctoCode**

OctoCode's gate pattern requires verifying pre-conditions before phase transitions (framework-analysis-octocode.md, Section C). The Triple Lock pattern (STATE/FORBID/REQUIRE) enforces critical checks.

**Adaptation**: After each ARL iteration, re-verify the dependency graph:
1. STATE: "All inbound references to this skill must still resolve."
2. FORBID: "Proceeding if any inbound reference is broken."
3. REQUIRE: "Re-grep all references and verify resolution."

**Component C: Impact Classification from GSD**

GSD's deviation rules classify changes by severity and determine authority level (framework-analysis-gsd.md, Section C).

**Adaptation**: Classify downstream impact:

| Impact Type | Detection | Action |
|-------------|-----------|--------|
| No impact | All references still resolve, no contracts broken | Continue |
| Reference update needed | Skill renamed or path changed | Auto-update all callers atomically |
| Contract broken | Skill's interface changed (new required inputs, removed outputs) | STOP -- architectural change (GSD Rule 4 equivalent) |
| Cascade detected | Callers of callers affected | Expand scope to include transitive dependencies |

**Glue Logic**: Dependency graph built during front-loading (Gas Town pattern). Triple Lock verification after each iteration (OctoCode pattern). Impact classified by severity tier (GSD pattern). Blocking changes escalate to human; non-blocking changes auto-update references.

### 3.3 Convergence with Quality (R2 + R7 + R8)

**Requirement**: Know when to stop iterating, while ensuring each iteration produces verifiable improvements.

**Component A: Multi-Signal Termination from Ralph**

Ralph's four convergence signals (framework-analysis-ralph.md, Section C): completion promise, task exhaustion, safety limits, loop detection.

**Component B: Goal-Backward Verification from GSD**

GSD's verifier works backwards from the desired outcome (framework-analysis-gsd.md, Section E.3): What must be TRUE? What must EXIST? What must be WIRED?

**Component C: Evidence Requirements from OctoCode**

OctoCode requires file:line citations for all claims (framework-analysis-octocode.md, Section E).

**Combined ARL Convergence System**:

```
After each iteration:

1. FINDING COUNT CHECK (from autonomous-refinement-loop-research.md)
   - Count findings at severity >= configured threshold
   - If count >= previous iteration's count: STOP (not converging)
   - If count == 0: CANDIDATE for completion

2. EVIDENCE VERIFICATION (from OctoCode)
   - For each remaining finding: verify file:line citation is current
   - Drop findings where cited line no longer matches (stale findings)
   - Recount after dropping stale findings

3. GOAL-BACKWARD CHECK (from GSD)
   - For each original acceptance criterion: pass or fail?
   - If all pass: CANDIDATE for completion
   - If any fail: continue iterating

4. LOOP DETECTION (from Ralph)
   - Compare assessment output to previous N assessments
   - If >90% similarity: STOP (stuck in cycle)

5. SAFETY LIMITS (from Ralph)
   - Max iterations exceeded: STOP
   - Max token/cost budget exceeded: STOP
   - Consecutive identical findings: STOP (same error N times)

6. COMPLETION DECISION
   - All candidates must agree (finding count = 0 AND goal check passes)
   - Any STOP signal overrides: terminate and report reason
   - Otherwise: continue to next iteration
```

**Glue Logic**: The finding count check is the primary convergence signal. Evidence verification prevents false convergence (findings exist but are stale). Goal-backward check prevents false completion (tasks done but goals not met). Loop detection and safety limits are guard rails against degenerate behavior.

---

## 4. Implementation Priority

Ranked by impact on ARL autonomy, implementation complexity, and dependencies.

### Priority 1: High Impact, Low Complexity, No Dependencies

These can be built first and immediately increase ARL capability.

| # | Solution | Impact | Complexity | What It Enables |
|---|---------|--------|------------|-----------------|
| 1.1 | **Purpose anchor capture** (SAM RT-ICA adaptation) | HIGH -- prevents the most common failure mode (purpose drift) | LOW -- capture skill description at iteration 0, store as YAML | Enables R4 (purpose drift detection) at basic level. Every subsequent mechanism builds on this. |
| 1.2 | **Finding count convergence tracking** (Ralph safety limits adaptation) | HIGH -- prevents infinite loops, the most wasteful failure mode | LOW -- counter file, increment per iteration, compare to previous | Enables R2 (convergence detection) at basic level. Without this, the loop has no stopping criteria. |
| 1.3 | **Structural content inventory** (novel, from autonomous-refinement-loop-research.md) | HIGH -- prevents the most destructive failure mode (content loss) | LOW -- list headings, code fences, links before/after, diff | Enables R3 (content-loss prevention). Mechanical check, no AI judgment needed. |
| 1.4 | **Evidence-backed findings** (OctoCode citation requirement) | MEDIUM -- reduces false positive rate, improving iteration quality | LOW -- require file:line in assessment output, verify via grep | Enables R7 (verifiable findings). Filters noise before planning stage. |

### Priority 2: High Impact, Medium Complexity, Depends on Priority 1

These build on Priority 1 and significantly increase autonomous capability.

| # | Solution | Impact | Complexity | Dependencies |
|---|---------|--------|------------|--------------|
| 2.1 | **Front-loading session** (SAM RT-ICA + human-out-of-loop-prerequisites.md Section 4) | HIGH -- eliminates most mid-loop human interrupts | MEDIUM -- structured interrogation, YAML artifact generation, RT-ICA gate logic | Needs purpose anchor (1.1) and convergence tracking (1.2) as output targets |
| 2.2 | **Proportionality checking** (GSD deviation rules adaptation) | MEDIUM -- prevents over-engineering, most common waste | MEDIUM -- severity-to-scope mapping, threshold configuration, change scope measurement | Needs front-loading session (2.1) to capture severity weights |
| 2.3 | **Plan-to-implementation fidelity check** (GSD self-check + goal-backward) | MEDIUM -- catches implementation drift before review | MEDIUM -- acceptance criteria extraction from plan, pass/fail evaluation, scope verification | Needs evidence-backed findings (1.4) for acceptance criteria validation |
| 2.4 | **Dependency graph construction** (Gas Town pattern adapted) | MEDIUM -- enables downstream impact analysis | MEDIUM -- grep-based reference discovery, graph construction, storage as artifact | Needs structural content inventory (1.3) for contract definition |

### Priority 3: Medium Impact, High Complexity, Depends on Priority 2

These are the sophisticated mechanisms that approach full autonomy for bounded tasks.

| # | Solution | Impact | Complexity | Dependencies |
|---|---------|--------|------------|--------------|
| 3.1 | **Multi-signal convergence system** (Ralph + GSD + OctoCode composite, Section 3.3 above) | HIGH -- determines when to stop with confidence | HIGH -- combines 6 signals, requires all Priority 1 mechanisms as inputs | Needs 1.1, 1.2, 1.3, 1.4, 2.3 |
| 3.2 | **Purpose drift detection with embedding comparison** (SAM + Ralph composite, Section 3.1 above) | MEDIUM -- catches subtle drift that text comparison misses | HIGH -- requires embedding generation, cosine similarity computation, threshold tuning | Needs purpose anchor (1.1), front-loading session (2.1) |
| 3.3 | **Downstream impact analysis with contract verification** (Gas Town + OctoCode + GSD composite, Section 3.2 above) | MEDIUM -- prevents breaking changes to callers | HIGH -- graph traversal, contract extraction, atomic multi-file updates | Needs dependency graph (2.4) |
| 3.4 | **Adversarial split justification** (BMAD adversarial review adapted for R9) | LOW -- split decisions are rare | HIGH -- adversarial agent must find 3+ independent trigger scenarios | Needs front-loading session (2.1) for scope boundaries |
| 3.5 | **Tiered escalation protocol** (Gas Town adaptation for R10) | MEDIUM -- prevents stuck loops from wasting resources | MEDIUM -- 3-tier routing logic, context packaging for human escalation | Needs convergence system (3.1) to detect stuck states |

### Dependency Graph

```
Priority 1 (foundation, no dependencies):
  1.1 Purpose Anchor
  1.2 Finding Count Convergence
  1.3 Structural Content Inventory
  1.4 Evidence-Backed Findings

Priority 2 (builds on P1):
  2.1 Front-Loading Session -----> depends on 1.1, 1.2
  2.2 Proportionality Checking --> depends on 2.1
  2.3 Plan-Implementation Fidelity -> depends on 1.4
  2.4 Dependency Graph -----------> depends on 1.3

Priority 3 (builds on P2):
  3.1 Multi-Signal Convergence --> depends on 1.1, 1.2, 1.3, 1.4, 2.3
  3.2 Purpose Drift Detection ---> depends on 1.1, 2.1
  3.3 Downstream Impact Analysis -> depends on 2.4
  3.4 Adversarial Split Justification -> depends on 2.1
  3.5 Tiered Escalation ----------> depends on 3.1
```

---

## 5. What Must Be Built From Scratch

ARL requirements with no solution in any analyzed framework. These require original design.

### 5.1 Content-Loss Prevention (R3)

**The gap**: No framework implements structural content preservation checking across iterative refinements. SAM verifies artifact boundaries (stage-to-stage handoff integrity), but not internal structural preservation within a single artifact being refined.

**What must be designed**:

A "structural inventory" mechanism that:

1. **Before iteration**: Enumerates structural elements of the target skill:
   - All markdown headings (level + text)
   - All code fences (language + first line as identifier)
   - All markdown links (target path)
   - All frontmatter fields (key + value)
   - Token count (body only, via tiktoken)

2. **After iteration**: Re-enumerates and diffs against pre-iteration inventory.

3. **Classification of changes**:
   - Element moved (present but at different position): OK
   - Element rephrased (heading text changed but same level/position): WARNING
   - Element split (one heading became two): OK if content preserved
   - Element removed: BLOCKING unless explicitly approved in ARTIFACT:GUARDRAILS
   - Element added: OK (refinement typically adds, not removes)

4. **Blocking behavior**: If any BLOCKING removal detected, the iteration's changes are rejected and the loop requests re-implementation with the constraint "preserve element X."

**Design inputs from frameworks**:
- SAM's boundary verification pattern (check at transitions) -- framework-analysis-sam.md, Section C
- Ralph's backpressure model (define evidence, reject if missing) -- framework-analysis-ralph.md, Section C
- autonomous-refinement-loop-research.md line 53 (the specific method: "every heading and code fence in the original must appear somewhere in the result")

### 5.2 Proportionality Mapping (R5)

**The gap**: No framework automatically maps finding severity to acceptable change scope. GSD's deviation rules (framework-analysis-gsd.md, Section C) provide tiered authority but use fixed categories (bug/missing/blocker/architectural), not a parametric severity-to-scope mapping.

**What must be designed**:

A proportionality matrix configured during front-loading:

```yaml
proportionality:
  info:
    max_lines_changed: 10
    max_files_changed: 1
    auto_approve: true
  minor:
    max_lines_changed: 50
    max_files_changed: 3
    auto_approve: true
  major:
    max_lines_changed: 200
    max_files_changed: 10
    auto_approve: false  # requires plan-to-implementation check
  critical:
    max_lines_changed: unlimited
    max_files_changed: unlimited
    auto_approve: false  # requires adversarial review
```

The assessment agent classifies each finding with a severity. The implementation agent's changes are measured (lines changed, files touched). If changes exceed the proportionality threshold for the finding's severity, the iteration is flagged for review.

**Design inputs from frameworks**:
- GSD's 4-tier deviation rules (the tiering pattern) -- framework-analysis-gsd.md, Section C
- Ralph's backpressure (define acceptable evidence, reject if exceeded) -- framework-analysis-ralph.md, Section C
- human-out-of-loop-prerequisites.md, Section 2 (front-loadable: "proportionality thresholds captured once at start")

### 5.3 Split Justification Gate (R9)

**The gap**: No framework evaluates whether extracting content into a new skill/component is justified. BMAD's adversarial review forces finding issues but does not apply to structural decisions. SAM's forensic review validates against goals but does not evaluate component decomposition quality.

**What must be designed**:

A split evaluation protocol that runs when the assessment suggests "extract this content into a new skill":

1. **Trigger scenario enumeration**: The proposer must list >= 3 independent scenarios where a user would invoke the proposed new skill directly (not via the parent skill).

2. **Adversarial challenge**: A reviewer agent attempts to refute each scenario:
   - "Is this scenario actually just a sub-case of the parent skill?"
   - "Would a user searching for this capability find this skill name?"
   - "Can this scenario be served by the parent skill with a parameter?"

3. **Decision**:
   - 3+ surviving scenarios: Split approved
   - 1-2 surviving scenarios: Move content to `references/` (progressive disclosure, not independent skill)
   - 0 surviving scenarios: Keep in parent skill

**Design inputs from frameworks**:
- BMAD's adversarial review ("must find issues, no 'looks good' allowed") -- framework-analysis-bmad-method.md, Section C
- autonomous-refinement-loop-research.md line 55 (the "3 independent trigger scenarios" threshold)
- OctoCode's FORBIDDEN thinking pattern (intercept "I assume this split is good") -- framework-analysis-octocode.md, Section E.6

### 5.4 Iteration State File

**The gap**: No framework provides a dedicated convergence tracking artifact for iterative refinement loops. Ralph has task exhaustion tracking and Gas Town has convoy completion tracking, but neither tracks per-iteration quality metrics across a refinement loop.

**What must be designed**:

An iteration state file updated after each loop pass:

```yaml
# .arl/state/skill-name/iteration-state.yaml
scope: "plugin-creator/skills/assessor"
purpose_anchor_hash: "sha256:a1b2c3..."
iterations:
  - iteration: 0
    timestamp: "2026-02-13T10:00:00Z"
    findings_count: 12
    findings_by_severity: { critical: 2, major: 4, minor: 3, info: 3 }
    token_count: 5200
    structural_elements: 47  # headings + code fences + links
    validator_results:
      schema: pass
      structure: pass
      token_count: warn  # above 4000 threshold
    description_hash: "sha256:d4e5f6..."
    description_similarity_to_anchor: 1.0
  - iteration: 1
    timestamp: "2026-02-13T10:15:00Z"
    findings_count: 7
    findings_by_severity: { critical: 0, major: 3, minor: 2, info: 2 }
    token_count: 4800
    structural_elements: 47  # preserved
    validator_results:
      schema: pass
      structure: pass
      token_count: warn
    description_hash: "sha256:d4e5f6..."  # unchanged
    description_similarity_to_anchor: 1.0
    delta:
      findings_resolved: 5
      findings_new: 0
      token_delta: -400
      structural_elements_removed: 0
      structural_elements_added: 0
convergence:
  max_iterations: 5
  current_iteration: 1
  severity_floor: "minor"
  min_improvement_delta: 2  # findings
  consecutive_zero_improvement: 0
  status: "CONVERGING"  # CONVERGING | STALLED | COMPLETE | STOPPED
```

**Design inputs from frameworks**:
- Ralph's safety limits (max iterations, consecutive failures as structured data) -- framework-analysis-ralph.md, Section C
- GSD's STATE.md (living project memory, sub-100 lines) -- framework-analysis-gsd.md, Section B
- SAM's artifact tokens (typed, scoped, storage-agnostic addressing) -- framework-analysis-sam.md, Section C
- autonomous-refinement-loop-research.md lines 56-59 (convergence criteria: finding count, severity floor, score delta)

### 5.5 Baseline Metrics Snapshot

**The gap**: No framework captures a comprehensive quality baseline before beginning iterative refinement. Ralph captures a prompt; GSD captures STATE.md; SAM captures discovery artifacts. None capture the specific pre-refinement quality metrics needed for delta tracking.

**What must be designed**:

A baseline snapshot taken at iteration 0:

```yaml
# .arl/state/skill-name/baseline.yaml
captured_at: "2026-02-13T10:00:00Z"
target_file: "plugins/plugin-creator/skills/assessor/SKILL.md"

# Structural inventory
headings:
  - level: 1
    text: "Assessor Skill"
    line: 5
  - level: 2
    text: "Assessment Methodology"
    line: 12
  # ... all headings

code_fences:
  - language: "yaml"
    first_line: "ARTIFACT:GOAL(SCOPE:skill-name)"
    line: 45
  # ... all code fences

links:
  - text: "framework analysis"
    target: "./references/ARL/framework-analysis-bmad-method.md"
    line: 78
  # ... all links

frontmatter:
  description: "Complete analysis of plugin structure..."
  user-invocable: true
  # ... all fields

# Metrics
token_count_body: 5200
token_count_total: 5400
line_count_body: 620
heading_count: 23
code_fence_count: 8
link_count: 15

# Validation results
validators:
  plugin-validator:
    exit_code: 0
    errors: []
    warnings: ["W003: token count 5200 exceeds 4000 threshold"]
  validate-skill-structure:
    exit_code: 0
    errors: []
    warnings: ["body >500 lines"]
```

**Design inputs from frameworks**:
- human-out-of-loop-prerequisites.md, Section 3 ("Quality baselines: Token count, heading inventory, code fence count, link graph. Current validation status.")
- SAM's artifact system (typed, scoped, versioned) -- framework-analysis-sam.md, Section C
- OctoCode's mandatory evidence requirements (file:line citations) -- framework-analysis-octocode.md, Section E

---

## 6. Implementation Roadmap Summary

### Phase 1: Foundation (Priority 1 items)

Build the minimal infrastructure that enables tracked, non-destructive iteration:

1. **Baseline snapshot** (5.5) -- capture pre-refinement state
2. **Purpose anchor** (1.1) -- capture description as invariant
3. **Structural content inventory** (1.3 / 5.1) -- enumerate elements, diff after changes
4. **Finding count tracker** (1.2) -- counter file, convergence check
5. **Evidence requirement** (1.4) -- file:line citations required in assessment output

After Phase 1, the ARL can iterate with basic safety: content loss detected, convergence tracked, purpose anchored, findings verified. Human reviews results at end of loop.

### Phase 2: Autonomy (Priority 2 items)

Build the mechanisms that eliminate human gates within the loop:

6. **Front-loading session** (2.1) -- structured interrogation, YAML artifact generation
7. **Iteration state file** (5.4) -- comprehensive per-iteration tracking
8. **Proportionality mapping** (2.2 / 5.2) -- severity-to-scope thresholds
9. **Plan-implementation fidelity** (2.3) -- acceptance criteria verification
10. **Dependency graph** (2.4) -- reference discovery, contract verification

After Phase 2, the ARL can run multiple iterations without human intervention for well-scoped tasks. Human provides initial configuration and reviews final result.

### Phase 3: Sophistication (Priority 3 items)

Build the advanced mechanisms that handle edge cases and complex scenarios:

11. **Multi-signal convergence** (3.1) -- 6-signal stopping system
12. **Purpose drift detection with embeddings** (3.2) -- cosine similarity tracking
13. **Downstream impact analysis** (3.3) -- graph traversal, contract verification
14. **Split justification gate** (3.4 / 5.3) -- adversarial trigger scenario evaluation
15. **Tiered escalation** (3.5) -- 3-tier routing to auto/orchestrator/human

After Phase 3, the ARL handles complex refinement tasks including multi-file changes, dependency-aware modifications, and principled stopping decisions.

---

## Summary: Framework Contribution Map

Which framework contributed what to the ARL design:

| Framework | Primary Contributions |
|-----------|----------------------|
| **SAM** | Front-loading architecture (RT-ICA gate), artifact-based state management, forensic review independence, deterministic backpressure principle |
| **Ralph** | Convergence detection (multi-signal termination, loop detection, safety limits), fresh context as recovery, memory system for cross-iteration learning, backpressure philosophy |
| **GSD** | Proportionality via deviation rules, goal-backward verification, self-check in executors, context window management, wave-based parallelism |
| **OctoCode** | Evidence requirements (file:line citations), FORBIDDEN thinking pattern, gate pattern (Pre-Conditions/Gate Check/FORBIDDEN/ALLOWED/On Failure), hint-driven research |
| **BMAD** | Adversarial review ("must find issues"), scope-adaptive planning, implementation readiness gate, scale-domain classification |
| **Gas Town** | Tiered escalation protocol, dependency tracking, self-cleaning workers, three-layer state architecture, nondeterministic idempotence |

No single framework provides a complete ARL solution. The design requires:
- SAM's structure (how to organize the pipeline)
- Ralph's dynamics (how to detect convergence and recover from failure)
- GSD's verification (how to check that execution matches intent)
- OctoCode's rigor (how to ensure findings are real)
- BMAD's adversarialism (how to force honest quality assessment)
- Gas Town's resilience (how to handle failure and escalation)

Three critical mechanisms (content-loss prevention, proportionality mapping, split justification, iteration state tracking, baseline snapshots) must be built from scratch as they address the ARL's unique requirement of iterative self-improvement -- a scenario none of the analyzed frameworks were designed for.
