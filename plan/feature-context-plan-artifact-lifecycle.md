# Feature Context: Plan Artifact Lifecycle Policy

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: simple_description (issue #117 with human design decision resolved)
- **Source**: Feature request "Plan artifact diverges from implementation without update mechanism"
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The research/plan from Phase 2-3 was committed early as a markdown file. During implementation (Phase 5), decisions changed -- the MCP server grew from planned scope, analysis dimensions were rebalanced, hook patterns shifted. The plan was never updated to reflect actual implementation. After compaction, the stale plan became a potential source of confusion.

**Human design decision (resolved)**: Human decision artifacts (backlog items, grooming output, interview transcripts, decisions) are versioned and immutable -- they capture original intent and must be preserved as the historical record. Generated plans (feature-context, architect specs, task files) must follow that intent. Plans may propose alternatives to the user after research/fact-checking reveals problems, but must never diverge from human intent autonomously.

**Implementation goal**: Define and enforce a plan artifact lifecycle policy that classifies artifacts, ensures generated plans track implementation without silently diverging from human intent, surfaces divergence for approval, adds a freshness check to `/complete-implementation`, and documents the policy.

---

## Core Intent Analysis

### WHO (Target Users)

Two distinct groups interact with plan artifacts:

1. **Human operators** -- project owners who write backlog items, provide grooming feedback, approve plans, and return to plan artifacts after compaction or between sessions to understand what was decided and why. These users have few touch points with the SAM workflow; their original documents set expectations.

2. **AI agents** -- orchestrator agents (`/implement-feature`, `/complete-implementation`), implementation agents (`/start-task`), and quality gate agents (`@context-refinement`, `@doc-drift-auditor`, `@feature-verifier`) that read plan artifacts as ground truth when making implementation decisions.

### WHAT (Desired Outcome)

From the user's perspective, success means:

- Plan artifacts in `plan/` are trustworthy after implementation completes. A human returning to `plan/feature-context-{slug}.md` or `plan/architect-{slug}.md` after compaction finds content that reflects what was actually built, not stale pre-implementation speculation.
- Human decision artifacts (backlog items, grooming output) remain immutable -- they are the historical record of intent, never silently modified by agents.
- When implementation requires changes that differ from human-established intent, the divergence is surfaced to the human for approval rather than silently absorbed.
- The `/complete-implementation` quality gates detect when generated plan artifacts have drifted from the actual implementation.

### WHEN (Trigger Conditions)

The problem manifests in two scenarios:

1. **Post-implementation, post-compaction**: A human (or agent in a new session) reads plan artifacts and encounters stale information that no longer matches the codebase. There is no signal that the plan is outdated.

2. **During implementation**: An agent making decisions during `/start-task` reads the architect spec or feature-context for guidance, but the spec describes a design that was already changed by earlier tasks. The agent may implement against the stale spec or diverge further without recording the deviation.

### WHY (Problem Being Solved)

The SAM workflow creates plan artifacts in Phases 1-4 (`/add-new-feature`) and then implements them in Phase 5 (`/implement-feature`). Once created, plan artifacts are never revisited or updated. This creates three concrete problems:

1. **Post-compaction confusion**: After context compaction, plan artifacts may be the primary source of "what was decided." Stale plans lead agents (and humans) to make decisions based on outdated information.

2. **No distinction between human-authored and generated artifacts**: Backlog items and grooming output record human intent and must never change. Generated plans (feature-context, architect specs, task files) reflect research and design that may legitimately need updating. The SAM workflow does not currently distinguish between these two categories.

3. **Silent divergence from human intent**: During implementation, agents may discover that a planned approach does not work and silently adjust. The human's original intent (captured in backlog items and grooming feedback) is never re-consulted, and the divergence is never surfaced for approval.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Context Refinement Agent (Task-Scoped Drift Detection)

- **Location**: `plugins/python3-development/agents/context-refinement.md:1-186`
- **Relevance**: This agent already detects drift between planned and implemented code, but only within the scope of a task file's Context Manifest. It compares "what was PLANNED vs what was IMPLEMENTED" (line 29) and appends a "Discovered During Implementation" section to the task file.
- **Reusable**: The drift detection methodology (compare plan vs implementation, categorize findings, append discoveries) could be extended to cover feature-context and architect spec artifacts. Currently, the agent's scope is limited to the Context Manifest section of the task file. It does not check `plan/feature-context-{slug}.md` or `plan/architect-{slug}.md` for staleness.

#### Pattern 2: Doc-Drift-Auditor (Documentation vs Implementation Comparison)

- **Location**: `plugins/python3-development/agents/doc-drift-auditor.md:1-245`
- **Relevance**: This agent compares documentation claims against implementation reality, categorizes findings by severity (Critical/High/Medium/Low), and produces evidence-based reports. It already audits `{project_path}/plan/*.md` files (line 39). However, its focus is on code documentation (CLAUDE.md, architecture.md, etc.), not on the relationship between plan artifacts and their resulting implementation.
- **Reusable**: The severity classification framework (Documented but Unimplemented, Implemented but Undocumented, Outdated Documentation, Mismatched Details) maps directly to plan artifact freshness assessment. The evidence-based reporting format (file:line, commit SHA, quoted text) could be reused.

#### Pattern 3: Feature Verifier (Goal-Backward Verification)

- **Location**: `plugins/python3-development/agents/feature-verifier.md:1-380`
- **Relevance**: The feature verifier starts from the architecture spec and task file to derive "truths" that must hold. It reads plan artifacts as ground truth (line 62-65). This is precisely the agent that would be confused by stale plan artifacts -- it would verify against outdated goals. The verifier does not currently check whether the plan artifacts it reads are still accurate.
- **Reusable**: The three-level verification pattern (Existence, Substantive, Wired) could inform how plan artifact freshness is assessed.

#### Pattern 4: Complete Implementation Phases (Quality Gate Sequence)

- **Location**: `.claude/skills/complete-implementation/SKILL.md:1-66`
- **Relevance**: The complete-implementation skill runs six sequential quality gate phases. An artifact freshness check would need to be inserted into this sequence. The current Phase 6 (context-refinement) is the closest existing phase but only updates the task file's Context Manifest, not the upstream plan artifacts.
- **Reusable**: The phase sequence pattern (delegate to agent, check result, proceed or create follow-up tasks) is the established mechanism for adding new quality gates.

#### Pattern 5: SAM Artifact Table in Local Workflow

- **Location**: `.claude/rules/local-workflow.md:30-37`
- **Relevance**: The SAM workflow documentation already enumerates the plan artifacts and their creators. The table lists four artifact types: feature context, codebase analysis, architecture spec, and task plan. No lifecycle metadata (created, updated, validated) is tracked beyond what agents write during creation.
- **Reusable**: This table is the natural location to document artifact lifecycle categories.

### Existing Infrastructure

**What exists today that this feature could leverage:**

1. **The `context-refinement` agent** already performs planned-vs-implemented comparison but only for the task file's Context Manifest section. Its scope would need broadening to cover feature-context and architect spec artifacts.

2. **The `doc-drift-auditor` agent** already compares documentation against code and produces structured severity reports. It could be extended or a new specialized agent could be created.

3. **The `/complete-implementation` skill** already runs a sequence of quality gate agents. Adding a new phase (or extending Phase 6) is structurally straightforward.

4. **Plan artifact metadata headers** already exist in feature-context files. Every `plan/feature-context-{slug}.md` file has a `## Document Metadata` section with `Generated`, `Input Type`, `Source`, and `Status` fields (observed in `plan/feature-context-process-quality-discipline.md:3-8`, `plan/feature-context-conventional-commits-changelog-refs.md:5-8`, `plan/feature-context-validate-orchestrator-discipline.md:5-8`). Architecture specs have similar but less standardized headers (`plan/architect-sam-task-skills-context.md:3-6`). These metadata headers could be extended with lifecycle fields.

5. **Backlog item files** in `.claude/backlog/` have YAML frontmatter with `status`, `priority`, `added` date, and `type` fields. These are already treated as immutable records of human decisions in practice.

6. **The SAM artifact versioning strategy** was previously completed (`.claude/backlog/completed-sam-artifact-versioning-strategy.md`) -- it implemented storage-agnostic semantic tokens using `ARTIFACT:{TYPE}({SCOPE_OR_ID})` with disambiguators. This prior work may provide a foundation for artifact classification.

### Code References

- `plugins/python3-development/agents/context-refinement.md:21-46` -- Steps that compare planned vs implemented, limited to task file Context Manifest
- `plugins/python3-development/agents/context-refinement.md:50-51` -- Decision point: drift found or not
- `plugins/python3-development/agents/doc-drift-auditor.md:38-39` -- Lists `{project_path}/plan/*.md` as audit target
- `plugins/python3-development/agents/doc-drift-auditor.md:125-131` -- Severity classification framework
- `.claude/skills/complete-implementation/SKILL.md:52-53` -- Phase 6 context-refinement invocation
- `.claude/rules/local-workflow.md:30-37` -- Artifact table in planning phase
- `.claude/rules/local-workflow.md:209-222` -- Quality gate phase sequence
- `.claude/docs/TASK_FILE_FORMAT.md:129-153` -- YAML frontmatter field definitions (no lifecycle fields)
- `plan/feature-context-process-quality-discipline.md:3-8` -- Existing metadata header pattern
- `.claude/backlog/completed-sam-artifact-versioning-strategy.md:1-11` -- Prior versioning strategy work

---

## Use Scenarios

### Scenario 1: Human Returns After Compaction

**Actor**: Human operator
**Trigger**: Human returns to a project after context compaction. They open `plan/architect-{slug}.md` to understand what was built.
**Goal**: Get an accurate understanding of the implemented architecture.
**Expected Outcome**: Either the architect spec reflects the actual implementation, or it carries a clear marker indicating which sections diverged and pointing to where the current truth lives (e.g., the updated Context Manifest in the task file). The human is never misled by stale content without a warning.

### Scenario 2: Agent Reads Plan During Later Task Execution

**Actor**: Implementation agent executing Task N (where Tasks 1 through N-1 already changed the plan)
**Trigger**: Agent invokes `/start-task` and reads the architecture spec to understand the design.
**Goal**: Make implementation decisions based on accurate design information.
**Expected Outcome**: The architect spec either reflects current decisions or includes annotations about what changed. The agent is not silently misled by stale design decisions.

### Scenario 3: Implementation Diverges from Human Intent

**Actor**: Implementation agent during `/start-task`
**Trigger**: Agent discovers during implementation that the planned approach (from the architect spec, which was derived from the human's backlog item) does not work -- perhaps an API does not exist, or a dependency constraint was missed.
**Goal**: Change the approach without silently abandoning the human's original intent.
**Expected Outcome**: The divergence is recorded. At the `/complete-implementation` quality gate, the divergence is surfaced to the human for review. The backlog item (human decision artifact) remains untouched. The generated plan artifact is updated only after human approval.

### Scenario 4: Quality Gate Detects Stale Plan

**Actor**: `/complete-implementation` orchestrator
**Trigger**: All tasks are marked COMPLETE and the quality gate sequence begins.
**Goal**: Detect that plan artifacts no longer match the implemented codebase.
**Expected Outcome**: The freshness check compares key claims in `plan/feature-context-{slug}.md` and `plan/architect-{slug}.md` against the actual implementation. If divergence is found, it is reported in a structured format (similar to doc-drift-auditor's severity report) and surfaced to the human. The plan is not auto-corrected.

### Scenario 5: Backlog Item Preserved as Historical Record

**Actor**: Human operator reviewing project history
**Trigger**: Human wants to understand the original intent behind a feature.
**Goal**: Find the unmodified original backlog item and grooming output.
**Expected Outcome**: The backlog item in `.claude/backlog/` and any grooming artifacts retain their original content. No agent has modified them during implementation. They serve as the historical record of what the human asked for and why.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | No artifact classification system exists. The SAM workflow does not distinguish between human-decision artifacts (immutable) and generated artifacts (mutable but intent-bound). | Without classification, there is no basis for applying different lifecycle rules to different artifact types. |
| 2 | Behavior | The `context-refinement` agent only updates the task file's Context Manifest. It does not check or update `feature-context-{slug}.md` or `architect-{slug}.md`. | Upstream plan artifacts become stale while only the task file gets drift annotations. |
| 3 | Behavior | No freshness check exists in `/complete-implementation`. The six existing phases do not compare plan artifacts against implementation. | Plan artifact staleness is never detected programmatically. |
| 4 | Behavior | When implementation diverges from the architect spec, there is no mechanism to record the divergence or surface it for human approval. | Silent divergence from human intent goes undetected. |
| 5 | Integration | Existing plan artifacts (8 feature-context files, 8+ architect specs in `plan/`) have no lifecycle markers or artifact-type classification. | Retroactive classification would be needed for existing artifacts. |
| 6 | Scope | The boundary between "updating a generated plan to reflect reality" and "silently diverging from human intent" is not defined. | Without clear rules, agents may either never update plans (staleness) or update them in ways that contradict human intent (unauthorized divergence). |
| 7 | User | It is unclear how divergence approval should be surfaced to the human. Options include: inline in the quality gate output, a separate report file, a backlog item, or blocking the `/complete-implementation` flow. | The mechanism for human review of divergence affects workflow continuity. |
| 8 | Integration | The doc-drift-auditor (Phase 4 of `/complete-implementation`) already audits `plan/*.md` files for documentation drift. Its relationship to a new artifact freshness check needs clarification -- are they complementary, overlapping, or should the freshness check be integrated into the existing auditor? | Risk of duplicate or conflicting audit results. |

---

## Questions Requiring Resolution

### Q1: What constitutes "divergence from human intent" versus "legitimate design refinement"?

- **Category**: Behavior
- **Gap**: Gap #6 -- the boundary between plan updates and intent divergence is undefined
- **Question**: When an implementation agent discovers that a planned approach needs adjustment (e.g., an API changed, a simpler pattern works better), under what conditions should this be treated as "divergence requiring human approval" versus "normal design refinement that should be recorded automatically"? For example: if the architect spec says "use Pattern A" but implementation uses "Pattern A with minor variation B," does that require human approval? What about "replaced Pattern A entirely with Pattern C because A did not work"?
- **Options**:
  - A) Any change that alters the scope, approach, or structure described in the architect spec requires human approval. Minor implementation details (variable names, internal refactoring) do not.
  - B) Only changes that conflict with claims made in the human's original backlog item or grooming output require approval. Changes within the generated plan's scope are auto-recorded.
  - C) All divergences are recorded and reported, but none block the workflow. Human reviews them after completion.
- **Why It Matters**: This determines whether the freshness check is a blocking gate or an informational report, and what threshold triggers human escalation.
- **Resolution**: _pending_

### Q2: Should the freshness check be a new phase in `/complete-implementation` or an extension of the existing context-refinement phase?

- **Category**: Integration
- **Gap**: Gap #3 and Gap #8 -- no freshness check exists, and relationship to existing agents is unclear
- **Question**: The `/complete-implementation` skill currently has six phases. Should artifact freshness checking be: (a) a new Phase 7, (b) an expansion of Phase 6 (context-refinement), or (c) an expansion of Phase 4 (doc-drift-auditor)? The context-refinement agent already compares planned vs implemented but only for the Context Manifest. The doc-drift-auditor already audits plan/*.md files but focuses on documentation accuracy, not plan-to-implementation tracking.
- **Options**:
  - A) Extend Phase 6 (context-refinement) to also cover feature-context and architect spec freshness
  - B) Add a new Phase 7 with a dedicated agent
  - C) Extend Phase 4 (doc-drift-auditor) to include plan artifact freshness as a severity category
- **Why It Matters**: Determines whether an existing agent is modified or a new agent is created, affecting scope and complexity.
- **Resolution**: _pending_

### Q3: What should happen to existing plan artifacts in `plan/`?

- **Category**: Scope
- **Gap**: Gap #5 -- existing artifacts have no lifecycle markers
- **Question**: There are currently 8 feature-context files and 8+ architect specs in the `plan/` directory with no lifecycle metadata. Should existing artifacts be retroactively classified and marked? If so, should they be marked as "stale" (since implementation has already occurred without freshness tracking) or "unvalidated"?
- **Options**:
  - A) Retroactively add lifecycle markers to all existing artifacts
  - B) Apply the new policy only to artifacts created after the policy is in place
  - C) Add a minimal marker (e.g., `artifact-type: generated`) to existing files without full freshness validation
- **Why It Matters**: Determines whether this feature includes a migration step for existing artifacts.
- **Resolution**: _pending_

### Q4: How should divergence be surfaced to the human?

- **Category**: User
- **Gap**: Gap #7 -- the mechanism for human review is not defined
- **Question**: When the freshness check detects divergence between plan artifacts and implementation, how should it be communicated to the human? The existing `/complete-implementation` phases produce reports and follow-up task files but do not block on human input.
- **Options**:
  - A) Write a divergence report to `.claude/reports/` (similar to doc-drift-auditor) and continue; human reviews asynchronously
  - B) Create a backlog item documenting the divergence, linking to the stale artifact and the actual implementation
  - C) Block the `/complete-implementation` flow and require human acknowledgment before proceeding
  - D) Annotate the plan artifact itself with divergence markers (inline warnings in the markdown)
- **Why It Matters**: Blocking affects workflow automation. Backlog items integrate with existing tracking. Reports may be missed. Inline annotations modify the artifacts themselves.
- **Resolution**: _pending_

### Q5: Should the policy documentation live in `local-workflow.md` only, or also in individual skill/agent files?

- **Category**: Scope
- **Gap**: Gap #1 -- no artifact classification system exists
- **Question**: The feature request specifies documenting the policy in `.claude/rules/local-workflow.md`. However, the agents that need to enforce the policy (`context-refinement`, `doc-drift-auditor`, `/start-task`) each have their own instruction files. Should the policy be documented centrally only (in `local-workflow.md`) with agents referencing it, or should each agent's instructions be updated to include the relevant lifecycle rules?
- **Options**:
  - A) Central policy in `local-workflow.md` only; agents reference it
  - B) Central policy in `local-workflow.md` plus relevant sections embedded in each affected agent/skill
  - C) Standalone policy document at `.claude/docs/plan-artifact-lifecycle.md` referenced from `local-workflow.md` and agent files
- **Why It Matters**: Agents loaded as sub-agents may not read `local-workflow.md`. If the policy is not in their agent file, they will not follow it.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Plan artifacts in `plan/` are classified into two categories: human-decision artifacts (immutable, versioned) and generated artifacts (mutable but intent-bound)
2. Generated plan artifacts are checked for freshness against actual implementation during `/complete-implementation` quality gates
3. When divergence between a generated plan and the implementation is detected, it is surfaced to the human (not auto-resolved) via a defined mechanism
4. The `context-refinement` agent (or a new/extended agent) covers feature-context and architect spec freshness, not just the task file Context Manifest
5. Existing plan artifacts receive appropriate lifecycle markers (scope dependent on Q3 resolution)
6. The artifact lifecycle policy is documented in SAM workflow documentation and in agent instructions where enforcement occurs
7. The distinction between "legitimate design refinement" and "divergence from human intent" has a defined threshold (dependent on Q1 resolution)

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
