# Feature Context: Process Quality Discipline for SAM Pipeline

## Document Metadata

- **Generated**: 2026-03-01
- **Input Type**: simple_description (with pre-verified fact-check results and groomed backlog item)
- **Source**: Feature request to add issue classification, root-cause analysis, scenario-as-target, and proportional response to the SAM pipeline
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The SAM pipeline treats every issue the same way: plan it, implement it, verify it works. But different issue types need fundamentally different treatment depths. This feature adds:

1. **Issue Classification Taxonomy** -- 5 types: procedural | defect | recurring-pattern | missing-guardrail | unbounded-design
2. **Root-Cause Analysis Integration** -- 5 Whys for traceable failures (type 2), 6 Sigma/DMAIC for recurring patterns (type 3)
3. **Scenario-as-Target Principle** -- every issue identifies what scenario exposed the problem and verifies THAT is what improves
4. **Proportional Response** -- grooming requires appropriate analysis depth per type; completion gates verify proportionality

Files to modify: `TASK_FILE_FORMAT.md`, `groom-backlog-item/SKILL.md`, `complete-implementation/SKILL.md`, `verify/SKILL.md`, `feature-verifier.md` (both plugins).

Pre-verified: 5 Whys (VERIFIED), 6 Sigma DMAIC (VERIFIED), GSD/BMAD-METHOD issue classification (REFUTED -- neither has it; this is novel design).

---

## Core Intent Analysis

### WHO (Target Users)

Two distinct user types operate the SAM pipeline:

1. **Human operators** -- project owners who create backlog items, review groomed output, approve plans, and evaluate implementation quality
2. **AI agents** -- orchestrator agents (`/implement-feature`, `/complete-implementation`), groomer agents (`@backlog-item-groomer`), verifier agents (`@feature-verifier`), and the `/groom-backlog-item` skill that classifies and refines issues

Both are consumers of the quality discipline. The human benefits from appropriate analysis depth (not over-engineering procedural fixes, not under-analyzing recurring defects). The AI agents benefit from explicit routing logic (which analysis method to apply, what verification criteria to check).

### WHAT (Desired Outcome)

The SAM pipeline gains the ability to:

1. **Classify issues by type** before choosing a response strategy, using 5 categories stored in task metadata
2. **Apply the right analytical method** per type: no analysis for procedural fixes, 5 Whys for traceable defects, 6 Sigma/DMAIC for recurring patterns, guardrail gap analysis for type 4, and design-framing for unbounded problems
3. **Track the scenario that exposed the problem** and verify that the scenario itself is what improves (not just the symptom)
4. **Gate completion proportionally** -- verification checks that the response depth matched the issue type

Success looks like: a recurring defect (type 3) cannot pass completion gates without evidence of a guardrail or process change added to prevent recurrence, while a procedural fix (type 1) passes gates with a simple find-and-replace sweep.

### WHEN (Trigger Conditions)

The classification and proportional response activate at three pipeline stages:

1. **During grooming** (`/groom-backlog-item`) -- when an issue is being refined, the groomer classifies its type and determines the required analysis method
2. **During task creation** (task template) -- when tasks are generated, the metadata carries the classification, scenario target, and analysis method forward
3. **During completion** (`/complete-implementation`, `/verify`, `@feature-verifier`) -- when implementation is being verified, the gates check that the response was proportional to the type and that the scenario was addressed

### WHY (Problem Being Solved)

Observed pain points from recent sessions:

- **Backlog items #311/#312 had 9 quality problems post-implementation** because the completion gates did not evaluate whether the response matched the problem type (session observation, source: groomed backlog item `p1-add-ux-impact-assessment-to-sam-task-template-grooming-and-c.md`)
- **Orchestrator manually edited task status instead of investigating hook failure** (#339) -- a symptom was patched instead of root cause being traced (source: `p1-orchestrator-manually-edited-task-status-instead-of-investig.md`)
- **No mechanism exists to distinguish "fix the typo" from "why does this class of bug keep happening"** -- the pipeline applies the same plan-implement-verify cycle regardless of issue depth

Without this feature, the pipeline normalizes shallow fixes for deep problems and over-engineers simple fixes, wasting both human and AI effort.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Evidence-Chain and Root-Cause Investigation (`/find-cause`)

- **Location**: `.claude/skills/find-cause/SKILL.md:1-275`
- **Relevance**: This skill already implements a structured root-cause investigation methodology (symptom -> mechanism -> proximate cause -> root cause) with evidence chains. The 5 Whys methodology for type 2 defects could reference or compose with this existing investigation protocol. The find-cause skill provides the "how to investigate" discipline; the new feature adds "when to investigate" routing.
- **Reusable**: The evidence-chain format (CLAIM/EVIDENCE/VERIFIED/DEPENDS ON) could serve as the output format for 5 Whys analysis output within groomed items.

#### Pattern 2: Scientific Thinking Hypothesis-Driven Method (`/scientific-thinking`)

- **Location**: `plugins/scientific-method/skills/scientific-thinking/SKILL.md:1-80`
- **Relevance**: Provides hypothesis-driven reasoning (observation -> hypothesis -> prediction -> experiment -> analysis). Overlaps with root-cause analysis for type 2 defects but is broader (used for debugging, architecture, complex refactoring). The new feature's 5 Whys method is more structured and specific than scientific-thinking; they serve different purposes.
- **Reusable**: The scientific-thinking skill could be referenced as a complementary tool for type 5 (unbounded design) issues where hypothesis formulation is needed.

#### Pattern 3: Holistic Linting Root-Cause Resolution Agent

- **Location**: `plugins/holistic-linting/agents/linting-root-cause-resolver.md:1-248`
- **Relevance**: This agent already embodies the "fix the root cause, not the symptom" principle specifically for linting errors. It classifies issues (blocking vs non-blocking), prohibits suppression, and requires investigation before resolution. The philosophy directly parallels the proposed "Scenario-as-Target" principle -- linting errors reveal deeper design issues, not just surface violations. However, this is domain-specific (linting only), while the new feature targets the SAM pipeline broadly.
- **Reusable**: The classification pattern (blocking vs non-blocking with different treatment) is a precedent for proportional response at a simpler scale.

#### Pattern 4: Backlog Item Grooming with RT-ICA and Fact-Check

- **Location**: `.claude/skills/groom-backlog-item/SKILL.md:1-281`
- **Relevance**: The grooming workflow already performs fact-checking (Step 4), RT-ICA assessment (Step 5), and agent-based grooming (Step 6). The new feature adds a classification step between RT-ICA and grooming -- after facts are checked, the issue type would be classified, which then determines the required analysis depth for the groomer agent.
- **Reusable**: The existing fact-check -> RT-ICA -> groom pipeline provides the insertion point for issue classification. The step numbering and groom template format would need to accommodate the new fields.

#### Pattern 5: Task File Metadata Schema (YAML Frontmatter)

- **Location**: `plugins/development-harness/docs/TASK_FILE_FORMAT.md:127-151` (field definitions), lines `262-354` (JSON schema)
- **Relevance**: The task file format already supports optional fields and has a JSON schema for validation. Adding `issue-classification`, `scenario-target`, and `analysis-method` fields would follow the existing extensibility pattern. The schema explicitly states (line 914): "All parsers MUST ignore unknown fields to maintain forward compatibility. New fields added in future versions will be optional and will not break existing task files."
- **Reusable**: The field definition table format, the JSON schema extension pattern, and the "Possible Future Fields" appendix (line 896-910) provide the exact template for adding new fields.

#### Pattern 6: Feature Verifier Goal-Backward Verification

- **Location**: `plugins/python3-development/agents/feature-verifier.md:1-329` and `plugins/development-harness/agents/feature-verifier.md:1-327`
- **Relevance**: The feature verifier already uses goal-backward verification (truths -> artifacts -> key links). The new feature would add a check: "did the fix address the root cause or only the symptom?" This is an additional truth to verify, not a replacement for the existing three-level verification. Both plugin variants would need the same addition.
- **Reusable**: The existing verification status taxonomy (VERIFIED / FAILED / UNCERTAIN) and the GAPS_FOUND output format with follow-up tasks would carry the new checks naturally.

#### Pattern 7: Completion Gates Workflow

- **Location**: `.claude/skills/complete-implementation/SKILL.md:1-66`
- **Relevance**: The current completion workflow runs 6 phases sequentially (code review, feature verification, integration check, doc drift audit, doc update, context refinement). The new proportional verification would enhance Phase 2 (feature verification) primarily, and could add a new phase or extend the existing feature-verifier agent prompt with issue-type-aware checks.
- **Reusable**: The phase-based structure provides a natural extension point.

#### Pattern 8: Verify Skill Checklist

- **Location**: `.claude/skills/verify/SKILL.md:1-138`
- **Relevance**: The verify skill has structured checklists (WORKS check, FIXED check, Quality Gates, Honesty Check). The FIXED check (lines 71-83) already asks "Did I observe the pre-fix state?" and "Does the original problem NO LONGER occur?" -- which aligns with scenario-as-target for bug fixes. The new feature would add a "PROPORTIONAL check" section: was the analysis depth appropriate for the issue type?
- **Reusable**: The checklist format with evidence requirements is directly reusable for the new proportional response verification.

### Existing Infrastructure

**Already exists and can be leveraged:**

1. **Fact-check pipeline** in grooming -- verifies claims before RT-ICA (`groom-backlog-item/SKILL.md:109-131`)
2. **RT-ICA assessment** -- determines information completeness; classification could be added as a condition (`groom-backlog-item/SKILL.md:133-157`)
3. **YAML frontmatter extensibility** -- task file format explicitly supports adding optional fields (`TASK_FILE_FORMAT.md:896-914`)
4. **Groomed item schema** with structured sections -- new fields (Issue Classification, Scenario Target, Analysis Method) would be added to groomed content sections (`backlog-item-groomed-schema.md:50-67`)
5. **Evidence-chain format** in `/find-cause` -- structured CLAIM/EVIDENCE/VERIFIED/DEPENDS ON format for root-cause traces
6. **Backlog item types** already in frontmatter: `type: Feature|Bug|Refactor|Docs|Chore` (`backlog-item-groomed-schema.md:23`) -- but this is coarser than the proposed 5-type issue classification

**Does NOT exist and would be new:**

1. Issue classification taxonomy and routing logic
2. 5 Whys template/format for structured root-cause analysis output
3. 6 Sigma/DMAIC integration for recurring pattern analysis
4. Scenario-as-target fields in task metadata
5. Proportional response verification gates
6. Mapping from backlog item `type` (Bug/Feature/etc.) to issue classification (defect/recurring-pattern/etc.)

### Code References

- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:127-151` -- current required and optional fields for task metadata
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:262-354` -- JSON schema for task validation
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:896-914` -- "Possible Future Fields" appendix showing extensibility intent
- `.claude/skills/groom-backlog-item/SKILL.md:29-102` -- validity check and pre-groom gate
- `.claude/skills/groom-backlog-item/SKILL.md:109-157` -- fact-check and RT-ICA steps (insertion point for classification)
- `.claude/skills/groom-backlog-item/SKILL.md:159-188` -- groomer agent spawning (would need classification context passed)
- `.claude/skills/complete-implementation/SKILL.md:27-30` -- Phase 2 feature verification (enhancement point)
- `.claude/skills/verify/SKILL.md:71-83` -- FIXED check with pre/post observation (closest existing analog to scenario-as-target)
- `plugins/python3-development/agents/feature-verifier.md:86-99` -- Step 2 must-haves establishment (where root-cause check would be added)
- `plugins/development-harness/agents/feature-verifier.md:79-98` -- equivalent Step 2 in development-harness variant
- `.claude/skills/find-cause/SKILL.md:210-228` -- evidence chain format (reusable for 5 Whys output)
- `.claude/agents/backlog-item-groomer.md:33-52` -- RT-ICA procedure in groomer agent (classification could extend this)
- `.claude/docs/backlog-item-groomed-schema.md:50-67` -- groomed section definitions (new sections needed)
- `.claude/backlog/p1-add-ux-impact-assessment-to-sam-task-template-grooming-and-c.md:1-136` -- the groomed backlog item that is the source of this feature request

---

## Use Scenarios

### Scenario 1: Procedural Fix (Type 1)

**Actor**: AI agent (`@backlog-item-groomer` during grooming)
**Trigger**: A backlog item reports "Skill description has a typo in the verb tense"
**Goal**: Classify as procedural, apply minimal analysis, fix and sweep for siblings
**Expected Outcome**: The groomer classifies the issue as `procedural`, sets analysis method to `none`, notes the scenario target as "documentation accuracy." The implementation fixes all instances found by codebase search. Completion gates verify the fix without requiring root-cause analysis -- a simple find-and-fix sweep is proportional.

### Scenario 2: Traceable Defect with Root Cause (Type 2)

**Actor**: Human operator creates a backlog item; AI groomer classifies and analyzes
**Trigger**: A backlog item reports "SubagentStop hook did not update task status to COMPLETE after sub-agent finished"
**Goal**: Classify as defect, apply 5 Whys, trace from symptom to root cause, fix the cause
**Expected Outcome**: The groomer classifies the issue as `defect`, sets analysis method to `5-whys`. The 5 Whys output traces: (1) Status not updated -> (2) Hook script not invoked -> (3) SubagentStop event not fired -> (4) Agent spawned via Agent tool without Skill wrapper -> (5) Hook registration depends on skill frontmatter, not agent invocation. The scenario target is "sub-agent lifecycle hook reliability." Completion gates verify the root cause was addressed (hook fires regardless of invocation method), not just the symptom (manually editing the status).

### Scenario 3: Recurring Defect Pattern (Type 3)

**Actor**: Human operator observes a pattern; AI groomer classifies and measures
**Trigger**: Backlog items #311, #312, and #339 all show the same class of problem -- post-implementation quality issues that completion gates did not catch
**Goal**: Classify as recurring-pattern, apply 6 Sigma thinking, add guardrails
**Expected Outcome**: The groomer classifies as `recurring-pattern`, sets analysis method to `6-sigma`. Analysis measures: 3 occurrences in the last session batch, common factor is "completion gates check task-level success but not scenario-level improvement." A guardrail or process change is added (the scenario-as-target verification itself). Completion gates verify that a guardrail exists to prevent this class of issue from recurring -- not just that the three specific instances were fixed.

### Scenario 4: Missing Guardrail (Type 4)

**Actor**: AI agent during grooming
**Trigger**: A backlog item reports "Orchestrator wrote implementation code directly instead of delegating to a sub-agent"
**Goal**: Classify as missing-guardrail, identify the gap in instructions or gates
**Expected Outcome**: The groomer classifies as `missing-guardrail`, sets analysis method to `none` (or a lightweight gap analysis). The scenario target is "orchestrator delegation enforcement." The fix targets the instruction or gate that should have prevented the orchestrator from writing code directly. Completion gates verify the guardrail now exists and would prevent the scenario from recurring.

### Scenario 5: Unbounded Design Problem (Type 5)

**Actor**: Human operator creates a design-level backlog item
**Trigger**: A backlog item asks "How should the pipeline handle tasks that are partially complete when a session ends?"
**Goal**: Classify as unbounded-design, require problem-space framing before planning
**Expected Outcome**: The groomer classifies as `unbounded-design`, sets analysis method to `design-framing`. The groomed output frames the decision space (options, constraints, trade-offs) rather than prescribing a solution. Planning cannot proceed until the human selects a direction. Completion gates verify that the chosen design was implemented as specified, not that a "best" solution was found.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Relationship between existing backlog `type` field (Feature/Bug/Refactor/Docs/Chore) and the new issue classification taxonomy (procedural/defect/recurring-pattern/missing-guardrail/unbounded-design) is undefined | Confusion about whether these are parallel taxonomies or whether one replaces/extends the other |
| 2 | Behavior | How the groomer agent (`@backlog-item-groomer`) receives and acts on issue classification is unspecified | The groomer agent currently runs on `model: haiku` with limited reasoning; adding classification routing and 5 Whys analysis may exceed its capability |
| 3 | Behavior | Where the 5 Whys analysis output is stored and in what format is unspecified | Without a defined format, 5 Whys output will be inconsistent across grooming sessions |
| 4 | Behavior | How "recurring pattern" (type 3) is detected -- is it manual human classification or does the groomer search for similar past issues? | Automated detection requires cross-referencing past backlog items; manual detection requires human to flag it |
| 5 | Integration | The `implementation_manager.py` parser (`plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`) would need to understand the new YAML fields for status queries and validation | Parser changes needed but not mentioned in the feature request |
| 6 | Scope | Whether the backlog item groomed schema (`backlog-item-groomed-schema.md`) needs new sections or whether existing sections absorb the new fields | The groomed schema is consumed by the `@backlog-item-groomer` agent and the `backlog groom` script |
| 7 | Integration | The `@backlog-item-groomer` agent file references `rt-ica` skill and uses `model: haiku` -- adding issue classification logic may require model upgrade or skill additions | Haiku-class models may not reliably perform 5 Whys root-cause chains |
| 8 | Behavior | What "proportional response verification" concretely checks for each type is not defined with specific pass/fail criteria | Without concrete criteria, the verification step becomes subjective |
| 9 | Scope | Whether this feature applies retroactively to existing task files and backlog items, or only to new ones going forward | Retroactive application would require a migration or batch classification step |

---

## Questions Requiring Resolution

### Q1: Taxonomy coexistence with existing backlog `type` field

- **Category**: Scope
- **Gap**: The backlog item schema already has a `type` field with values `Feature|Bug|Refactor|Docs|Chore`. The proposed issue classification has 5 different values: `procedural|defect|recurring-pattern|missing-guardrail|unbounded-design`. These taxonomies overlap but are not the same.
- **Question**: Are the two taxonomies independent (a Bug can be a procedural fix OR a defect OR a recurring pattern), or does the new classification replace the existing `type` field? If independent, how do they interact during grooming and verification?
- **Options**:
  - A) Independent: `type` describes the work category (Bug/Feature/etc.), `issue-classification` describes the analytical depth needed. A Bug could be procedural (typo in error message) or a defect (root cause needed).
  - B) Replace: The new 5-type taxonomy replaces the existing `type` field entirely.
  - C) Mapping: Certain `type` values map to default classifications (e.g., Bug defaults to `defect`, Docs defaults to `procedural`) that can be overridden during grooming.
- **Why It Matters**: Determines whether the backlog schema needs restructuring or just extension. Affects every downstream consumer of the `type` field.
- **Resolution**: _pending_

### Q2: Groomer agent capability for root-cause analysis

- **Category**: Integration
- **Gap**: The `@backlog-item-groomer` agent uses `model: haiku`, which is optimized for speed and efficiency in structured search and template filling. Adding 5 Whys root-cause analysis (type 2) and 6 Sigma pattern detection (type 3) requires deeper reasoning.
- **Question**: Should root-cause analysis happen within the groomer agent (requiring a model upgrade for certain issue types), or should it be a separate step in the grooming workflow -- e.g., a new agent or skill invoked between RT-ICA and grooming?
- **Options**:
  - A) Upgrade the groomer agent to `model: opus` or `model: sonnet` when issue type is 2 or 3
  - B) Add a new root-cause analysis step in the grooming workflow that runs before the groomer agent, using a separate agent
  - C) Reuse the existing `/find-cause` skill as the root-cause analysis step, then pass its output to the groomer
- **Why It Matters**: Affects the grooming workflow architecture and token costs. Haiku is fast and cheap but may produce shallow 5 Whys chains.
- **Resolution**: _pending_

### Q3: Recurring pattern detection method

- **Category**: Behavior
- **Gap**: Type 3 (recurring-pattern) requires recognizing that the same class of defect has appeared multiple times. This could be detected manually (human flags it) or automatically (groomer searches past items for similar patterns).
- **Question**: How is "recurring" determined? Who or what decides that an issue is type 3 rather than type 2?
- **Options**:
  - A) Human-only: The human creating or reviewing the backlog item explicitly classifies it as recurring
  - B) Semi-automated: During grooming, the groomer searches past closed/resolved items for similar keywords and suggests "this may be a recurring pattern" if matches are found
  - C) Fully automated: A threshold-based rule (e.g., 2+ similar items in the last 30 days) triggers automatic type 3 classification
- **Why It Matters**: Automated detection adds complexity but catches patterns humans might miss. Manual detection is simpler but relies on human memory.
- **Resolution**: _pending_

### Q4: 5 Whys output format and storage location

- **Category**: Behavior
- **Gap**: The feature requests 5 Whys analysis for type 2 defects but does not specify the output format or where it lives.
- **Question**: What format should the 5 Whys output take, and where should it be stored? As a groomed section in the backlog item? As a separate artifact? As part of the task file body?
- **Options**:
  - A) New groomed section `### Root-Cause Analysis` in the backlog item, with a structured Why-1 through Why-N format
  - B) Inline in the `### Reproducibility` section, extending it with causal chain
  - C) Separate artifact file (e.g., `.claude/analysis/root-cause-{slug}.md`) linked from the backlog item
- **Why It Matters**: Determines whether the groomed schema and groomer agent template need new sections, and whether downstream consumers (task planner, feature verifier) can find the analysis.
- **Resolution**: _pending_

### Q5: Proportional verification -- concrete pass/fail criteria per type

- **Category**: Behavior
- **Gap**: The feature states completion gates should verify "proportional response" but does not define the specific pass/fail criteria for each of the 5 types.
- **Question**: What are the concrete verification checks for each issue type? For example, what must be TRUE for a type 3 (recurring-pattern) implementation to pass verification that would NOT be required for a type 1 (procedural)?
- **Options** (example criteria, needs user validation):
  - Type 1 (procedural): Did the fix address all instances found by codebase search? (sweep verification)
  - Type 2 (defect): Is there a documented root-cause chain? Does the fix target the root cause, not the symptom?
  - Type 3 (recurring): Was a guardrail, instruction update, or process change added to prevent recurrence?
  - Type 4 (missing-guardrail): Does the new guardrail trigger in the scenario that exposed the gap?
  - Type 5 (unbounded-design): Was the chosen design direction implemented as specified, with documented trade-offs?
- **Why It Matters**: Without concrete criteria, verification degrades to subjective judgment. The feature verifier agent needs executable checks.
- **Resolution**: _pending_

### Q6: Scope of feature verifier changes across plugins

- **Category**: Integration
- **Gap**: The feature request lists both `plugins/python3-development/agents/feature-verifier.md` and `plugins/development-harness/agents/feature-verifier.md` for modification. These two agents are nearly identical but have minor differences (Python-specific skills vs language-agnostic skills).
- **Question**: Should the root-cause vs symptom check be identical in both agents, or should the development-harness version be more general? The python3-development version references `python3-development` skill; the development-harness version references `development-harness` skill.
- **Options**:
  - A) Identical check added to both agents (copy-paste with skill reference difference)
  - B) Add to development-harness only; python3-development inherits via the harness layer
  - C) Add a shared reference document both agents include
- **Why It Matters**: Drift between the two agents is a known risk. Identical changes reduce drift but create a maintenance burden.
- **Resolution**: _pending_

### Q7: Retroactive application to existing items

- **Category**: Scope
- **Gap**: The feature adds new metadata fields. Existing task files and backlog items do not have these fields.
- **Question**: Should existing backlog items and task files be classified retroactively, or should the new fields apply only to items created after the feature is implemented?
- **Options**:
  - A) Forward-only: New fields are optional; existing items work without them; classification happens on next grooming
  - B) Retroactive batch: A migration script or grooming session classifies recent items
  - C) On-demand: Items are classified when they are next touched (groomed, worked, or verified)
- **Why It Matters**: Forward-only is simpler but means the taxonomy cannot be validated against existing items. Retroactive provides validation data but adds scope.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Add `issue-classification`, `scenario-target`, and `analysis-method` fields to the SAM task file YAML frontmatter schema in `TASK_FILE_FORMAT.md`, with validation rules and documentation
2. Add issue classification step to the grooming workflow in `groom-backlog-item/SKILL.md`, positioned after fact-check/RT-ICA and before groomer agent spawning
3. Add root-cause analysis requirement for type 2 (defect) and type 3 (recurring-pattern) issues during grooming, using a defined output format
4. Add scenario-as-target field to groomed item schema (`backlog-item-groomed-schema.md`) and groomer agent template
5. Add proportional response verification to completion gates (`complete-implementation/SKILL.md`) and the verify checklist (`verify/SKILL.md`), with type-specific pass/fail criteria
6. Add root-cause vs symptom check to both feature verifier agents (`feature-verifier.md` in python3-development and development-harness)
7. Validate the 5-type taxonomy against at least 5 recent backlog items to confirm coverage

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section with concrete acceptance criteria per goal
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design via `@python-cli-design-spec`
