# Human-Out-of-Loop Prerequisites

Research analysis identifying what must be known, measured, and verified before autonomous refinement loops can operate without human review gates.

**Date:** 2026-02-13
**Status:** Research Analysis
**Purpose:** Design requirements for autonomous skill refinement capabilities

---

## 1. Universalities Across Documents

### Common Patterns: Where Human Judgment Is Required

All documents identify these recurring human decision points:

**1. Goal Alignment Verification**

- **SAM/SSE Framework:** "Planning stage BLOCKS if prerequisites missing" - human must verify completeness before proceeding (stateless-software-engineering-framework.md, lines 90-91)
- **Process Realignment:** "Review and restate the goal and intent to the user until user approves" (process_realignment.md, line 32)
- **Autonomous Refinement Research:** "Does the plan address the actual intent of the skill, or is it optimizing for metrics that don't matter?" (autonomous-refinement-loop-research.md, line 20)

**Pattern:** All methodologies require explicit goal confirmation before execution. Without human input, systems optimize for wrong objectives.

**2. Proportionality Judgment**

- **SAM Framework:** No explicit proportionality check exists
- **Autonomous Refinement Research:** "Are the proposed changes proportional to the issues found, or is it over-engineering?" (line 21)
- **Process Realignment:** Complexity assessment determines artifact granularity - "Simple: Single-module, no external interfaces" vs "Complex: Cross-system, infrastructure, hardware" (lines 43-47)

**Pattern:** Change scope must match problem severity. Systems lack intuition for "is this fix worth its blast radius?"

**3. Downstream Impact Assessment**

- **SAM Framework:** "Verification at boundaries - Every stage validates previous stage's output" (README.md, line 152)
- **Autonomous Refinement Research:** "Will the changes break something downstream that the assessor didn't account for?" (line 22)
- **Process Realignment:** "ARTIFACT:ICD(INTERFACE:...)" tracks external system integration, hardware-software boundaries (lines 95-98)

**Pattern:** All frameworks recognize cascading dependencies exist. None solve cross-system impact prediction without human review.

**4. Convergence vs Oscillation Detection**

- **SAM Framework:** Fresh context per phase eliminates error accumulation, but no convergence tracking across iterations
- **Autonomous Refinement Research:** "Is the loop converging or oscillating (fix A breaks B, fix B breaks A)?" (line 37)

**Pattern:** Recursive refinement can spiral. Detecting productive vs degenerative iterations requires state tracking absent from stateless architectures.

### Common Patterns: Machine-Verifiable Conditions Successfully Replace Human Review

**1. Deterministic Backpressure**

- **SAM Framework:** "Always run deterministic checks (tests/linters/static analysis/checklists) and treat failures as ground truth" (README.md, line 153)
- **Plugin-Creator:** Error codes E001-E023 provide deterministic validation without human judgment (plugin-creator/CLAUDE.md, ERROR_CODES.md)
- **Autonomous Refinement Research:** "Cross-reference each finding against the source file with line evidence. False positives have no line evidence." (line 48)

**Success Factor:** When outcomes are binary (pass/fail) with objective evidence (test output, linter errors, file:line references), machines eliminate human review need.

**2. Schema Validation**

- **SAM Framework:** Artifact templates enforce structure (ARTIFACT:DISCOVERY, ARTIFACT:PLAN, ARTIFACT:TASK)
- **Plugin-Creator:** Frontmatter schema validation catches structural errors before execution (plugin-validator.py)
- **Autonomous Refinement Research:** "Diff the plan's 'expected outputs' against actual outputs. Every acceptance criterion in the task file gets a pass/fail." (line 52)

**Success Factor:** Predefined schemas allow automated verification. Human review only needed when schema is ambiguous or incomplete.

**3. Content-Loss Detection**

- **SAM Framework:** Message passing via artifacts creates audit trail (README.md, line 151)
- **Autonomous Refinement Research:** "Before/after token count per skill. Semantic diff — every heading and code fence in the original must appear somewhere in the result." (line 53)

**Success Factor:** Structural preservation can be verified mechanically. Token counts, heading lists, code fence inventories are machine-checkable invariants.

### Agreement: What Makes Autonomous Operation Possible vs Impossible

**Possible When:**

| Condition | Evidence from Documents |
|-----------|------------------------|
| **Complete context provided upfront** | SAM: "Task files contain all answers needed for the task" (README.md, line 155) |
| **Binary pass/fail criteria exist** | SAM: "Deterministic backpressure" (README.md, line 153); Plugin-Creator: ERROR_CODES.md |
| **Scope is constrained** | Process Realignment: "Simple: Single-module, no external interfaces" (line 44) |
| **Verification is structural** | Autonomous Refinement: "Semantic diff — every heading must appear" (line 53) |
| **Dependencies are explicit** | SAM: "ARTIFACT:ARCH-COMPONENT → drives API-SPEC" (Process Realignment, line 159) |

**Impossible When:**

| Condition | Evidence from Documents |
|-----------|------------------------|
| **Goal is ambiguous** | Autonomous Refinement: "Create a meta-skill that assesses any skill" - "requires defining every term" (line 136) |
| **Proportionality requires context** | Autonomous Refinement: "Compare change scope against finding severity" - but who defines severity weights? (line 50) |
| **Downstream impact unknown** | Autonomous Refinement: "Will changes break something downstream?" - requires system knowledge (line 22) |
| **Purpose can drift** | Autonomous Refinement: "Has the skill's original purpose drifted through successive rewrites?" (line 38) |
| **Convergence criteria subjective** | Autonomous Refinement: "Are remaining findings worth fixing?" - diminishing returns judgment (line 38) |

**Critical Insight from Documents:** SAM architecture eliminates many failure modes through structure (stateless agents, externalized memory, verification at boundaries), but the framework assumes human-provided complete task files. The autonomous refinement loop question is: **Can we generate those complete task files automatically?**

---

## 2. Human-Out-of-Loop vs Human-at-End-of-Loop

Classification of all human interaction points identified across documents:

### Eliminable: Replaced by Machine-Verifiable Conditions

| Human Check | Machine-Verifiable Replacement | Source Document | Conditions Required |
|-------------|-------------------------------|-----------------|---------------------|
| **Are findings real?** | Cross-reference each finding against source file with line evidence. False positives have no line evidence. | autonomous-refinement-loop-research.md, line 48 | - Findings must include file:line citations<br>- Source files must be readable<br>- Line evidence must be exact matches |
| **Did implementation match plan?** | Diff the plan's "expected outputs" against actual outputs. Every acceptance criterion in the task file gets a pass/fail. | autonomous-refinement-loop-research.md, line 52 | - Plan must include acceptance criteria<br>- Criteria must be binary (pass/fail)<br>- Outputs must be artifact files |
| **No content loss?** | Before/after token count per skill. Semantic diff — every heading and code fence in the original must appear somewhere in the result. | autonomous-refinement-loop-research.md, line 53 | - Content inventory before changes<br>- Structural elements enumerable<br>- Token counting library (tiktoken) |
| **Is the loop converging?** | Track finding count per iteration. If iteration N has >= findings as iteration N-1, stop. | autonomous-refinement-loop-research.md, line 56 | - State file records findings per iteration<br>- Quantifiable finding count<br>- Stopping threshold defined |
| **Frontmatter valid?** | Schema validation against AgentFrontmatter/SkillFrontmatter Pydantic models. Error codes E001-E023 deterministic. | plugin-creator/CLAUDE.md, plugin-validator.py | - Schema definitions exist<br>- Validation runs pre-commit<br>- Auto-fix capability for common errors |
| **Plugin structure valid?** | `claude plugin validate` checks plugin.json syntax, required fields, file references. | plugin-creator/CLAUDE.md, line 301 | - plugin.json schema defined<br>- All component paths resolvable<br>- Exit code 0/1 deterministic |

### Front-Loadable: Captured Once at Start

| Human Check | What Must Be Captured | Source Document | When Captured | How Used Throughout |
|-------------|----------------------|-----------------|---------------|---------------------|
| **Goal alignment** | Desired outcome (end state/value), Objectives (component outcomes), Acceptance criteria (testable statements) | process_realignment.md, lines 13-17 | Stage 1: Discovery, after user approval (line 32) | - Planner references to prevent scope drift<br>- Final verification checks original goal<br>- Purpose anchor for convergence checks |
| **Proportionality thresholds** | Change scope limits: lines/files touched per severity level. Severity weights: critical/major/minor/info. | autonomous-refinement-loop-research.md, line 50 | Before first iteration, during goal setting | - Findings flagged if scope exceeds severity<br>- Auto-reject over-engineering<br>- Escalate to human if threshold ambiguous |
| **Complexity boundaries** | Artifact selection matrix: Simple/Moderate/Complex/Firmware determines which design docs required. | process_realignment.md, lines 142-151 | Stage 2: Planning, during architecture phase | - Determines depth of design artifacts<br>- Controls verification rigor<br>- Sets quality gate requirements |
| **Downstream dependencies** | Artifact interdependencies: "ARTIFACT:PRD → informs all architecture artifacts". Explicit reference graph. | process_realignment.md, lines 153-161 | Stage 3: Context Integration, after design | - Grep all inbound references before changes<br>- Verify contracts still hold after changes<br>- Block if breaking changes detected |
| **Convergence exit criteria** | - Maximum iteration count<br>- Minimum severity threshold (stop at "info" level)<br>- Score improvement delta (stop if <5% gain) | autonomous-refinement-loop-research.md, line 59 | Before first iteration, during goal setting | - Checked after each iteration<br>- Automatic stop when criteria met<br>- Prevents infinite refinement loops |
| **Purpose invariant** | Skill description at iteration 0. Used as anchor to detect purpose drift. | autonomous-refinement-loop-research.md, line 58 | Stage 1: Discovery, after goal approval | - Compared against description at iteration N<br>- Drift detected if description changed<br>- Flags for human review if drift >threshold |

### Irreducible: Requires Continuous Human Judgment

| Human Check | Why Cannot Be Pre-Captured or Automated | Source Document | Mitigation Strategy |
|-------------|----------------------------------------|-----------------|---------------------|
| **Is the split justified?** | "A new skill must have at least 3 independent trigger scenarios. If it only gets invoked from the parent, it's not a skill — it's a reference file." (line 55) | autonomous-refinement-loop-research.md | **Why irreducible:** Determining "independent trigger scenario" requires understanding user mental models and workflow contexts. Cannot be enumerated upfront because use cases emerge over time.<br><br>**Mitigation:** Post-hoc validation after extraction. Track invocation patterns. If skill only called from one parent after 10 sessions, flag for consolidation. |
| **Will users find the new skill?** | "Will users find and invoke the new skill, or did we just fragment something that worked better as one piece?" (line 33) | autonomous-refinement-loop-research.md | **Why irreducible:** Requires predicting user discovery behavior. Skill discoverability depends on naming intuitiveness, documentation clarity, and user familiarity with domain - all context-dependent.<br><br>**Mitigation:** Generate invocation examples during split. Include cross-references from parent skill. Monitor usage patterns post-split. |
| **Does purpose serve end users?** | "Hard hitting, insightful, well researched, purpose driven. Knowing how and why end users benefit from having the skill." (plugin-creator assessor requirements) | autonomous-refinement-loop-research.md, skill definition | **Why irreducible:** Requires understanding user workflows, pain points, and value perception. End-user benefit is contextual and cannot be algorithmically determined without user feedback.<br><br>**Mitigation:** Capture user benefit statements during Discovery phase. Re-validate against benefit statements after each iteration. Flag if changes don't map to stated benefits. |
| **Are changes proportional to blast radius?** | "Compare change scope (files touched, lines changed) against finding severity. High-scope changes for low-severity findings get flagged." (line 50) - but severity is contextual. | autonomous-refinement-loop-research.md | **Why irreducible:** Severity assessment requires domain knowledge. A typo in user-facing documentation is critical; same typo in internal comment is trivial. Cannot be determined without understanding runtime context and user impact.<br><br>**Mitigation:** Pre-define severity for known issue types during goal setting. Flag unknown issue types for human classification. Build severity knowledge base over time. |
| **Purpose drift detection threshold** | "Compare the skill's description at iteration 0 vs iteration N. If the description changed, the purpose drifted — flag for review." (line 58) - but how much change = drift? | autonomous-refinement-loop-research.md | **Why irreducible:** Natural language comparison requires semantic understanding. Rewording for clarity is not drift; expanding scope is drift. Automated NLP cannot reliably distinguish without domain context.<br><br>**Mitigation:** Use embedding distance as heuristic. If cosine similarity <0.85 between iteration 0 and iteration N descriptions, flag for human review. Threshold tuned over time. |

---

## 3. Prerequisites for Human-Out-of-Loop

What must be **KNOWN** and **MEASURED** before autonomous refinement can operate without human gates.

### Starting State Requirements

#### Dataset Completeness

**What data must be available:**

| Data Type | Specific Requirements | Source Document | Verification Method |
|-----------|----------------------|-----------------|---------------------|
| **Source skill/agent files** | Complete file contents, not excerpts. Line-numbered. Versioned. | SAM README.md, line 155: "Task files contain all answers" | - Read full file (not head/tail)<br>- Store hash for change detection<br>- Record file:line for all citations |
| **Dependency graph** | All inbound references to skill. Cross-plugin references. Invocation patterns. | autonomous-refinement-loop-research.md, line 51 | - Grep all markdown files for skill name<br>- Parse `Skill(command: "...")` calls<br>- Build directed graph: caller → callee |
| **Historical context** | Previous refactoring iterations. Known failure modes. Lessons learned from similar skills. | process_realignment.md, line 13: "Lessons learned" | - State file: `.sam/artifacts/refactor-history.json`<br>- Fields: date, findings, changes, outcomes<br>- Searchable by skill name |
| **Quality baselines** | Token count, heading inventory, code fence count, link graph. Current validation status (pass/fail per validator). | autonomous-refinement-loop-research.md, line 53; plugin-creator plugin-validator.py | - Run plugin-validator.py before iteration 0<br>- Store baseline metrics in artifact<br>- Compare after each iteration |
| **Official reference docs** | Anthropic prompt engineering best practices. Claude Code plugin/skill schema. MCP protocol specifications. | plugin-creator subagent-refactorer agent, line 29: "Researches current Anthropic documentation" | - Pre-fetch URLs during Discovery<br>- Cache in references/ directory<br>- Version timestamp for staleness checks |

**Verification Gate:** RT-ICA (Reverse Thinking - Information Completeness Assessment) from SAM framework runs before Planning stage. Blocks if any required dataset missing.

#### Goal Specification Precision

**Desired outcome must answer:**

- **End state definition:** What does "best-in-class" mean for this specific skill? Measurable attributes (token count, validation pass rate, user satisfaction score).
- **Success criteria:** Binary pass/fail thresholds. Example: "Validation errors = 0, token count <4000, all links resolve, no orphaned references."
- **Non-goals explicit:** What improvements are OUT OF SCOPE? Example: "Do not split skill unless >6400 tokens. Do not change skill purpose. Do not introduce external dependencies."

**Source:** process_realignment.md lines 13-17 (Desired outcome → Objectives → Acceptance criteria structure)

**Captured format:**

```yaml
ARTIFACT:GOAL(SCOPE:skill-name)
desired_outcome: "Skill passes all validators, follows Anthropic best practices, token count under 4000"
objectives:
  - "Frontmatter follows AgentFrontmatter schema"
  - "All internal links resolve"
  - "No orphaned reference files"
  - "Token count <4000"
acceptance_criteria:
  - "plugin-validator.py exit code 0"
  - "All headings in iteration-0 appear in iteration-N"
  - "Cosine similarity between descriptions >0.85"
non_goals:
  - "Do not split unless token count >6400"
  - "Do not change skill purpose"
```

**Verification:** Goal artifact created during Discovery stage. Cannot proceed to Planning without approved goal artifact.

#### Expected vs Acceptable Outcomes Gap

**Questions that must be answered upfront:**

| Question | Why It Matters | Captured Format |
|----------|---------------|-----------------|
| **Ideal outcome vs minimum viable outcome?** | Determines stopping criteria. Iteration stops when "acceptable" reached, not when "perfect" reached. | `expected: "zero warnings", acceptable: "zero errors, <5 warnings"` |
| **What failures are blocking vs advisory?** | Some validators must pass (blocking); others can fail with warnings (advisory). | `blocking_validators: ["schema", "structure"], advisory_validators: ["style", "optimization"]` |
| **When to escalate vs retry?** | If iteration N fails same check as iteration N-1, escalate to human vs retry with different strategy. | `max_retries_per_check: 2, escalation_threshold: "same error 3x"` |

**Source:** SAM framework RT-ICA gate (blocks if prerequisites missing). autonomous-refinement-loop-research.md line 59 (diminishing returns threshold).

**Example:**

```yaml
ARTIFACT:THRESHOLDS(SCOPE:skill-name)
quality_gates:
  - gate: "schema_validation"
    blocking: true
    acceptable: "exit_code == 0"
    expected: "exit_code == 0"
  - gate: "token_count"
    blocking: false
    acceptable: "<6400"
    expected: "<4000"
convergence:
  max_iterations: 5
  min_improvement_delta: 5  # percent
  severity_floor: "info"  # stop when only info-level findings remain
```

#### Caveats and Guardrails

**Safety constraints that prevent destructive changes:**

| Constraint Type | Requirement | Enforcement Method |
|----------------|-------------|-------------------|
| **Immutability constraints** | Fields that must NOT change: skill description (purpose anchor), frontmatter name, user-invocable flag. | Before/after diff. Block commit if changed without explicit --allow-purpose-drift flag. |
| **Dependency preservation** | All inbound references must remain valid. If skill name changes, all callers must be updated atomically. | Grep for references before changes. Re-verify after changes. Block if broken references detected. |
| **Content preservation** | All headings, code fences, examples from iteration 0 must appear in iteration N (possibly reorganized, not deleted). | Structural inventory before/after. Block if any element missing without explicit delete approval. |
| **Scope boundaries** | Changes limited to specific files. Cannot modify files outside artifact SCOPE without approval. | Whitelist: only files in SCOPE can be edited. Bash tool blocked from operating outside SCOPE directory. |

**Source:** SAM framework "Verification at boundaries" (README.md line 152). autonomous-refinement-loop-research.md "content loss detection" (line 53).

**Captured format:**

```yaml
ARTIFACT:GUARDRAILS(SCOPE:skill-name)
immutable_fields:
  - "frontmatter.description"  # purpose anchor
  - "frontmatter.user-invocable"
  - "frontmatter.name"
preserve_structure:
  - "all_headings_from_iteration_0"
  - "all_code_fences_from_iteration_0"
scope_boundaries:
  - "allowed_paths: ['plugins/plugin-name/skills/skill-name/**']"
  - "blocked_paths: ['plugins/**/!(skill-name)']"
dependency_contracts:
  - "inbound_references_must_remain_valid"
  - "if_name_changes_then_update_all_callers"
```

#### Templates and Examples

**Reference patterns that guide implementation:**

| Template Type | What It Provides | Source Document |
|---------------|------------------|-----------------|
| **Skill structure templates** | Progressive disclosure pattern: SKILL.md → references/ → examples/. Frontmatter schema. Section ordering conventions. | plugin-creator claude-skills-overview-2026 skill |
| **Agent structure templates** | Frontmatter fields (name, description, model, tools). Workflow section structure. Quality standards section. | plugin-creator subagent-refactorer agent |
| **Validation templates** | Error code format. Expected output structure. Pass/fail criteria per validator. | plugin-creator ERROR_CODES.md |
| **Architecture artifact templates** | ARTIFACT:DISCOVERY, ARTIFACT:PLAN, ARTIFACT:TASK structures from SAM framework. | stateless-software-engineering-framework.md, Part 3 |

**Captured format:** Reference files in `references/` directory. Agent loads templates during execution. Example:

```
references/
├── skill-structure-template.md
├── agent-frontmatter-schema.yaml
├── validation-output-format.md
└── sam-artifact-templates/
    ├── DISCOVERY.md
    ├── PLAN.md
    └── TASK.md
```

#### Processes/Methodologies/Frameworks

**Workflow structure that governs execution:**

- **SAM 7-stage pipeline:** Discovery → Planning (RT-ICA) → Context Integration → Task Decomposition → Execution → Forensic Review → Final Verification
- **Autonomous refinement 4-phase loop:** Assess → Plan → Implement → Review → Recurse
- **Quality gates:** Validators that run between phases. Exit codes determine proceed/block/escalate.

**Source:** stateless-software-engineering-framework.md (complete pipeline specification)

**Critical requirement:** Framework itself must be artifact-encoded, not instructional. The structure IS the process.

#### Tool Choices

**Decisions that cannot change mid-execution:**

| Decision | Impact | When Decided | Constraints |
|----------|--------|--------------|-------------|
| **Validation toolchain** | Which validators run? plugin-validator.py + validate-skill-structure.sh or consolidated lint-claude-plugin.py? | Before first iteration | Cannot change mid-loop (inconsistent baselines) |
| **Token counting method** | tiktoken library, which encoding (cl100k_base)? Includes/excludes frontmatter? | Before baseline measurement | Must match across all iterations |
| **Refactoring delegation** | Which agents handle which task types? subagent-refactorer for agents, claude-context-optimizer for skills? | Stage 4: Task Decomposition | Agent selection criteria must be deterministic |
| **Parallel vs sequential** | Can tasks run concurrently or must be sequential due to file overlap? | Stage 4: Task Decomposition, after dependency analysis | Git worktrees enable parallelism if no file conflicts |

**Source:** SAM harness architecture (sam-harness.md), plugin-creator agent inventory

**Captured format:**

```yaml
ARTIFACT:TOOLCHAIN(SCOPE:skill-name)
validators:
  - tool: "plugin-validator.py"
    path: "plugins/plugin-creator/scripts/plugin-validator.py"
    flags: "--check --verbose"
  - tool: "validate-skill-structure.sh"
    path: "plugins/plugin-creator/scripts/validate-skill-structure.sh"
complexity_measurement:
  library: "tiktoken"
  encoding: "cl100k_base"
  includes_frontmatter: false
agents:
  AGENT_OPTIMIZE: "subagent-refactorer"
  DOC_IMPROVE: "claude-context-optimizer"
  SKILL_SPLIT: "refactor-skill"
execution_mode: "parallel_if_no_file_conflicts"
```

#### Assumptions Stated

**Explicit declaration of what we believe to be true but cannot verify:**

| Assumption | Risk if Wrong | Mitigation |
|------------|---------------|------------|
| **"Skill description accurately reflects skill purpose"** | Description says one thing, body does another. Assessment optimizes for wrong goal. | Compare description against trigger phrases in examples. Flag if mismatch. |
| **"Token count correlates with comprehension difficulty"** | Model may struggle with 2000 dense tokens more than 5000 verbose tokens. | Track assessment time per skill. If high token count but fast assessment, assumption holds. |
| **"All inbound references found by grep"** | Dynamic skill invocation (user types string, not Skill() call) won't be detected. | Grep for both `Skill(command: "name")` and string literal "name" patterns. Accept false positives. |
| **"Validation pass means quality achieved"** | Validators check structure, not semantic correctness. Skill may pass validation but be useless. | Cannot be fully mitigated. Irreducible human judgment required for usefulness. Front-load user benefit statements during Discovery. |

**Source:** SAM framework acknowledgment that "does not eliminate synthesis/logic errors without verification" (README.md line 156)

**Captured format:**

```yaml
ARTIFACT:ASSUMPTIONS(SCOPE:skill-name)
assumptions:
  - statement: "Skill description accurately reflects purpose"
    risk: "Optimizing for stated goal misses actual user need"
    mitigation: "Compare description vs examples trigger phrases"
    acceptable_if_wrong: false  # escalate to human if mismatch detected
  - statement: "Token count <4000 ensures Claude comprehension"
    risk: "Skill still too complex due to semantic density"
    mitigation: "Track assessment completion time"
    acceptable_if_wrong: true  # continue if validated other ways
```

### Scope-Dependent Complexity

**Critical insight from user:** Scope ambiguity determines feasibility of removing human gates.

#### Constrained Scope Example: "Cross Platform Usage Guide for Astral's uv Tool"

**Characteristics:**

- **Subject matter:** Single, well-defined tool (uv) with official documentation
- **Expected outcome:** Practical guide for cross-platform usage patterns
- **Data sources:** Identifiable (uv docs, GitHub examples, pyproject.toml specs)
- **Success measurement:** Binary (user can install, create project, manage dependencies on Windows/Linux/macOS)
- **Unknowns:** Limited (edge cases around platform-specific paths, shell differences)
- **Precedent:** Strong (many similar tool guides exist, patterns established)

**Human gates eliminable because:**

1. **Complete dataset enumerable:** uv documentation URLs known. Official examples in uv GitHub repository. Platform differences documented in Python packaging standards.
2. **Goal objectively verifiable:** Guide either covers core workflows (install, init, sync, run) or doesn't. Examples either execute successfully on each platform or fail.
3. **No subjective quality judgment:** "Best-in-class" means comprehensive coverage of official uv commands + common workflows. Measurable via checklist.
4. **Proportionality calculable:** Finding "missing --python flag in example" → fix scope is small (add flag). Finding "Windows path handling inconsistent" → fix scope is medium (test all examples on Windows). Severity weights determinable from user impact.

**Required front-loading:**

- List of all uv commands from official docs
- Platform matrix: Windows, Linux, macOS (+ distro variations if relevant)
- Test scenarios: fresh install, existing project, dependency updates, script execution
- Success criteria: All examples in guide execute without error on all platforms
- Reference examples: Existing tool guides as quality benchmarks

**Autonomous loop feasible:** Yes. Assessment → Implementation → Verification cycle can run unattended if:

- Validators test examples on each platform (deterministic pass/fail)
- Content completeness measured against uv command inventory (100% coverage or flag missing)
- User benefit explicit (e.g., "users can migrate from pip/poetry without reading full uv docs")

#### Open-Ended Scope Example: "Meta-Skill that Assesses Any Skill to Best-in-Class in Recursive Self-Improving Loop"

**Characteristics:**

- **Subject matter:** "Meta-skill" undefined. Self-referential (skill that improves skills, including itself).
- **Expected outcome:** "Best-in-class" undefined. "Self-improving" implies no stopping criteria.
- **Data sources:** Unknowable. What is the reference dataset for "best skill design"? Anthropic examples? Community plugins? User feedback?
- **Success measurement:** Subjective. "Best-in-class" varies by use case, user expertise, domain complexity.
- **Unknowns:** Vast. What makes a skill "best"? Speed? Accuracy? Comprehensiveness? Token efficiency? User satisfaction? All of the above with unknown weights?
- **Precedent:** Weak. No established pattern for self-improving meta-skills. Most examples are domain-specific.

**Human gates irreducible because:**

1. **Goal definition infinite regress:** "Best-in-class" requires defining evaluation criteria. Criteria depend on "what matters to users." User priorities emerge from usage, not specification.
2. **No objective stopping criteria:** "Recursive self-improving loop" has no natural end state. Every iteration can find new "improvements" by changing evaluation weights. Requires human to say "this is good enough."
3. **Proportionality judgment subjective:** Is improving token efficiency by 2% worth reorganizing the entire skill structure? Depends on context. Cannot be front-loaded as a threshold.
4. **Purpose drift inevitable:** Each iteration changes the skill based on assessment findings. After N iterations, the skill may optimize for assessor metrics (high scores on rubric) rather than user utility (actually helps users). Human must verify purpose alignment.
5. **Self-reference paradox:** If the meta-skill assesses itself and finds improvements, does it rewrite its own assessment logic? How to prevent assessment bias drift (assessing based on what it's good at detecting vs what actually matters)?

**Why front-loading fails:**

Even if we pre-define:

- Evaluation rubric (comprehensiveness, clarity, examples, references, validation, etc.)
- Success thresholds (score >90/100, zero validation errors, user satisfaction >4.5/5)
- Stopping criteria (max 10 iterations, score improvement <2% per iteration)

...we still cannot eliminate human review because:

- **Rubric weights unknown:** Is comprehensiveness more important than token efficiency? Depends on skill complexity and user expertise. Cannot be pre-specified for "any skill."
- **User satisfaction unknowable:** Cannot measure without deploying skill and gathering feedback. Autonomous loop cannot run unattended without real users.
- **Goal alignment unverifiable:** Each iteration moves toward higher rubric scores. But high scores ≠ useful skill. Human must verify "is this actually better for users?"

**Conclusion:** Open-ended meta-goals require continuous human judgment. Autonomous operation requires collapsing infinite possibility space to bounded, measurable outcomes.

#### Scope Constraint Analysis

**Relationship between scope ambiguity and human-gate eliminability:**

| Scope Clarity | Goal Measurability | Data Source Enumeration | Human Gates Eliminable? |
|--------------|-------------------|------------------------|-------------------------|
| **High** (specific tool, platform, use case) | **High** (binary pass/fail, checklist coverage) | **High** (official docs, known examples) | **Yes** - Autonomous loop feasible |
| **Medium** (domain-specific best practices) | **Medium** (scoring rubric with weights) | **Medium** (reference examples, community patterns) | **Partial** - Autonomous with periodic human checkpoints |
| **Low** (general improvement, meta-goals) | **Low** (subjective quality, emergent criteria) | **Low** (unknown what "complete" means) | **No** - Requires human at each decision point |

**Design implication:** Autonomous refinement skills must either:

1. **Constrain scope:** Only operate on bounded problems with clear success criteria (e.g., "ensure skill passes all validators" not "make skill best-in-class")
2. **Front-load extensively:** Spend discovery phase collapsing ambiguity until scope reaches "High" clarity (may require 50%+ of total effort)
3. **Accept hybrid model:** Autonomous execution within iteration, human review between iterations (human-at-end-of-loop, not human-out-of-loop)

---

## 4. The Front-Loading Pattern

If the design goal is "every point where a human would pivot, decide, review, or quality-check gets asked and clarified at the start," what does that front-loading session look like?

### Structure of Front-Loading Session

**Stage 1: Discovery (SAM Framework)**

This phase runs BEFORE any analysis or planning. Goal: Capture all information needed for autonomous execution.

#### Phase 1A: Goal Definition Interrogation

**Questions that must be answered:**

1. **Desired Outcome:**

   - "What does 'done' look like for this skill?" (End state description)
   - "How will you know it succeeded?" (Observable outcomes)
   - "What value does completion deliver?" (Benefit to users/system)

2. **Objectives Decomposition:**

   - "What are the 3-5 component outcomes that collectively achieve the desired outcome?"
   - "Are these objectives measurable independently?" (Each must have pass/fail criteria)
   - "Are these objectives sufficient? Would achieving all of them guarantee the desired outcome?"

3. **Acceptance Criteria:**

   - For each objective: "What test/check proves this objective is met?"
   - "Are criteria binary (pass/fail) or scored (0-100)?"
   - "Can criteria be automated? If not, who judges and how?"

4. **Non-Goals (Critical - Prevents Scope Creep):**

   - "What improvements are OUT OF SCOPE for this refinement?"
   - "What constraints must NOT be changed?" (e.g., skill purpose, target audience, invocation patterns)
   - "What trade-offs are acceptable?" (e.g., increase token count if needed to improve clarity)

**Example dialogue:**

```
AI: "What does 'done' look like for refactoring the plugin-creator skill?"
User: "All validators pass, token count under 4000, follows Anthropic best practices."
AI: "How will you measure 'follows best practices'?"
User: "Subagent-refactorer agent validates against current Anthropic docs."
AI: "What are the objectives?"
User: "1) Frontmatter valid. 2) Token count <4000. 3) All links resolve. 4) References cited."
AI: "Acceptance criteria for objective 1?"
User: "plugin-validator.py exit code 0."
AI: "What improvements are OUT OF SCOPE?"
User: "Do not change skill purpose. Do not split skill unless token count >6400."
AI: "Acceptable trade-offs?"
User: "Can increase token count slightly if needed for clarity, but hard limit 4800."
```

**Artifact produced:** `ARTIFACT:GOAL(SCOPE:skill-name)` (YAML format shown in section 3)

#### Phase 1B: Threshold and Guardrail Calibration

**Questions that must be answered:**

1. **Quality Gate Thresholds:**

   - "Which validators are blocking (must pass) vs advisory (can warn)?"
   - "For scored criteria, what's acceptable vs expected?" (e.g., "90/100 acceptable, 100/100 expected")
   - "What failures trigger escalation to human?"

2. **Convergence Exit Criteria:**

   - "Maximum iteration count before forcing human review?"
   - "Minimum improvement delta to justify continuing?" (e.g., "stop if score improves <5% per iteration")
   - "Severity floor for continuing refinement?" (e.g., "stop when only info-level findings remain")

3. **Immutability Constraints:**

   - "Which fields/sections must NOT change?" (e.g., skill description = purpose anchor)
   - "If these fields must change, what approval process?"

4. **Content Preservation Rules:**

   - "Must all headings from original appear in final?" (reorganization OK, deletion not OK)
   - "Must all code examples be preserved?" (may be refined, not removed)
   - "Are there sections that can be deleted vs must be preserved?"

**Example dialogue:**

```
AI: "Which validators are blocking?"
User: "Schema validation and structure validation must pass. Token count and style are advisory."
AI: "Maximum iterations before human review?"
User: "5 iterations. If not converged by then, escalate."
AI: "Minimum improvement to justify continuing?"
User: "Each iteration must fix >=2 findings OR improve score >=5%. Otherwise stop."
AI: "What cannot change?"
User: "Skill description (purpose anchor), user-invocable flag, frontmatter name."
AI: "Can headings be deleted?"
User: "No. All headings from iteration 0 must appear in final result, possibly reorganized."
```

**Artifact produced:** `ARTIFACT:THRESHOLDS(SCOPE:skill-name)` and `ARTIFACT:GUARDRAILS(SCOPE:skill-name)`

#### Phase 1C: Context and Dependency Mapping

**Questions that must be answered:**

1. **Dependency Inventory:**

   - "What other skills/agents/files reference this skill?"
   - "Does this skill invoke other skills? If so, which?"
   - "Are there external dependencies (documentation URLs, MCP servers)?"

2. **Historical Context:**

   - "Has this skill been refactored before? If so, what issues arose?"
   - "Are there known failure modes or edge cases?"
   - "What lessons learned from similar skills?"

3. **Reference Standards:**

   - "What are the reference examples of 'best-in-class' for this type of skill?"
   - "Which Anthropic docs are authoritative for this skill's domain?"
   - "Are there community examples we should emulate?"

4. **Blast Radius Assessment:**

   - "If this skill changes, what downstream impacts are possible?"
   - "What are the highest-risk changes (e.g., changing skill name breaks all callers)?"
   - "What safety checks prevent breaking changes?"

**Example dialogue:**

```
AI: "What other skills reference plugin-creator?"
User: "Grep results: refactor-plugin, implement-refactor, ensure-complete all invoke it."
AI: "Does plugin-creator invoke other skills?"
User: "Yes: agent-creator, skill-creator, write-frontmatter-description."
AI: "Has this skill been refactored before?"
User: "Yes, in v2.3.0. Issue: skill split caused broken cross-references. Mitigation: now we validate all links post-refactor."
AI: "What are reference examples of best practices?"
User: "Anthropic's mcp-builder skill, prompt-optimization-claude-45 skill."
AI: "Highest-risk change?"
User: "Changing skill name or removing user-invocable flag. Both would break user workflows."
AI: "Safety check?"
User: "Block commit if name or user-invocable changed without --force flag."
```

**Artifacts produced:**

- `ARTIFACT:DEPENDENCIES(SCOPE:skill-name)` - Inbound/outbound references, invocation graph
- `ARTIFACT:HISTORY(SCOPE:skill-name)` - Previous iterations, lessons learned
- `ARTIFACT:REFERENCES(SCOPE:skill-name)` - URLs to authoritative docs, example skills

#### Phase 1D: Toolchain and Execution Mode Selection

**Questions that must be answered:**

1. **Validation Toolchain:**

   - "Which validators will run?" (plugin-validator.py + validate-skill-structure.sh OR consolidated lint-claude-plugin.py)
   - "In what order do validators run?" (schema → structure → token count → links)
   - "What flags/options for each validator?"

2. **Complexity Measurement:**

   - "How is complexity measured?" (token count via tiktoken, which encoding?)
   - "Does measurement include frontmatter or only body?"
   - "What are warning/error thresholds?"

3. **Agent Delegation:**

   - "Which agents handle which task types?" (subagent-refactorer for agents, claude-context-optimizer for skills)
   - "How are agents selected?" (deterministic mapping or heuristic?)
   - "What context does each agent receive?"

4. **Execution Mode:**

   - "Can tasks run in parallel or must be sequential?" (depends on file overlap)
   - "If parallel, how many concurrent workers?" (git worktree limit, resource constraints)
   - "What happens if a task fails? Retry with different agent or escalate?"

**Example dialogue:**

```
AI: "Which validators should run?"
User: "plugin-validator.py for schema, validate-skill-structure.sh for structure quality."
AI: "Validation order?"
User: "Schema first (blocking). If passes, run structure (advisory). Token count last (advisory)."
AI: "How to measure complexity?"
User: "tiktoken library, cl100k_base encoding, body only (exclude frontmatter)."
AI: "Thresholds?"
User: "Warn at 4000 tokens, error at 6400 tokens."
AI: "Which agents for which task types?"
User: "AGENT_OPTIMIZE → subagent-refactorer. DOC_IMPROVE → claude-context-optimizer. SKILL_SPLIT → refactor-skill."
AI: "Parallel or sequential execution?"
User: "Parallel if tasks touch different files. Sequential if file overlap detected."
```

**Artifact produced:** `ARTIFACT:TOOLCHAIN(SCOPE:skill-name)` - Complete execution configuration

### What Makes Front-Loading Sufficient vs Insufficient

**Front-loading is SUFFICIENT when:**

1. **All decision points captured:** Every question that would cause a human to pause during execution has been answered upfront.
2. **Criteria are binary or scored with thresholds:** No fuzzy "looks good" judgments. Every check returns pass/fail or numeric score compared against threshold.
3. **Scope is constrained:** Problem space is bounded. Complete dataset enumerable. Success measurable.
4. **Guardrails prevent drift:** Immutability constraints block unintended changes. Content preservation rules ensure no data loss.
5. **Escalation triggers defined:** When autonomous loop cannot proceed (ambiguous finding, threshold exceeded, dependency conflict), escalation to human is automatic with clear context.

**Front-loading is INSUFFICIENT when:**

1. **Goal evolves during execution:** User discovers during implementation that original goal was wrong. Requires re-scoping.
2. **Unknowns emerge:** Findings reveal dependencies not captured during discovery. Example: "Skill references deprecated API" - cannot be known without researching API versions.
3. **Proportionality requires runtime context:** Change scope vs severity assessment depends on information only available after implementation attempt.
4. **Subjective quality judgment required:** "Is this wording clearer?" cannot be pre-captured as threshold. Requires human A/B judgment.
5. **Purpose drift undetectable:** Description similarity metrics flag major rewrites but miss subtle scope expansion. Human must validate "is this still the same skill?"

**Design implication:** Autonomous refinement skills must:

1. **Detect insufficiency:** If during execution a decision point arises that wasn't covered in front-loading artifacts, STOP and escalate rather than guessing.
2. **Support re-scoping:** Provide mechanism to pause loop, return to Discovery phase, update artifacts, resume with new context.
3. **Track unknowns:** Maintain list of "questions that arose during execution" for post-mortem review. Feed into next iteration's front-loading phase.

### Artifacts That Must Be Produced

**Minimum viable front-loading produces these artifacts:**

1. **ARTIFACT:GOAL** - Desired outcome, objectives, acceptance criteria, non-goals
2. **ARTIFACT:THRESHOLDS** - Quality gates (blocking/advisory), convergence exit criteria
3. **ARTIFACT:GUARDRAILS** - Immutability constraints, content preservation rules, scope boundaries
4. **ARTIFACT:DEPENDENCIES** - Inbound/outbound references, dependency graph
5. **ARTIFACT:REFERENCES** - Authoritative docs, example skills, templates
6. **ARTIFACT:TOOLCHAIN** - Validators, agents, execution mode, complexity measurement
7. **ARTIFACT:ASSUMPTIONS** - Explicit assumptions, risks if wrong, mitigation strategies

**Format:** YAML files in `.sam/artifacts/` directory. Each artifact is versioned, timestamped, and references the scope (skill/plugin name).

**Usage:** Planning stage reads all artifacts. Task decomposition embeds relevant artifacts into task files. Execution agents receive complete context (stateless). Forensic review validates against artifact constraints.

---

## 5. What the AI Reviewer Must Know

If an AI actor replaces the human reviewer, that AI must be "hard hitting, insightful, well researched, purpose driven, runtime environment and contextually aware, knowing how and why end users benefit from having the skill."

What **concrete information and evaluation frameworks** would give an AI reviewer these qualities?

### "Hard Hitting" - Finds Real Issues, Not False Positives

**Required Inputs:**

| Input Type | Specific Content | How It Enables Hard-Hitting Critique |
|-----------|------------------|-------------------------------------|
| **Source file with line numbers** | Complete skill/agent file, not summary. Every line numbered. | Enables file:line citations. "Line 47: description says 'validates agents' but body only shows skill validation" - specific, verifiable. |
| **Baseline metrics** | Token count, heading inventory, code fence count, link graph from iteration 0. | Enables delta detection. "Iteration 2 added 340 tokens but fixed only 1 finding. Disproportionate." - measurable comparison. |
| **Dependency graph** | All inbound references, invocation patterns, cross-file dependencies. | Enables impact assessment. "Changing skill name on line 12 breaks 7 callers in other plugins. Blocking change." - concrete blast radius. |
| **Validation error logs** | Full output from plugin-validator.py, validate-skill-structure.sh with error codes and line references. | Enables root cause analysis. "E007: Forbidden multiline indicator &#x60;&#x3E;-&#x60; on line 23. Must use single-line quoted string." - specific fix. |
| **Historical failure patterns** | Previous refactoring iterations, what broke, what was reverted. | Enables pattern recognition. "Previous iteration tried splitting skill, caused orphaned references. Current plan similar. Flag for review." - learns from history. |

**Evaluation Framework:**

```yaml
hard_hitting_checklist:
  finding_quality:
    - "Does finding cite specific file:line evidence?"
    - "Can finding be verified objectively (test, validator, grep)?"
    - "Is finding actionable (clear fix vs vague suggestion)?"
  false_positive_prevention:
    - "Is cited line still in file? (source may have changed)"
    - "Does finding still apply after recent changes?"
    - "Is finding duplicate of previously addressed issue?"
  proportionality:
    - "Is change scope proportional to severity?"
    - "If high-scope change (many files/lines), is impact justified?"
    - "Are there lower-scope alternatives?"
```

**Example of hard-hitting review:**

```markdown
FINDING: Schema violation - tools field malformed
LOCATION: plugins/plugin-creator/agents/subagent-refactorer.md, line 8
EVIDENCE: tools: ["Read", "Write"] (YAML array)
EXPECTED: tools: Read, Write (comma-separated string)
ERROR_CODE: E004 (from plugin-validator.py)
SEVERITY: blocking (schema validation must pass)
FIX: Replace line 8 with: tools: Read, Write
VALIDATION: Run plugin-validator.py, verify exit code 0
```

### "Insightful" - Identifies Non-Obvious Issues and Opportunities

**Required Inputs:**

| Input Type | Specific Content | How It Enables Insight |
|-----------|------------------|----------------------|
| **Cross-reference analysis** | Which skills reference this skill? Which skills does this skill reference? Are references balanced (invoked often vs rarely)? | Enables usage pattern insight. "Skill invoked 47 times across plugins but only 2 unique callers. May be over-coupled. Consider splitting." |
| **Semantic similarity metrics** | Embedding distance between skill descriptions. Topic modeling across skill bodies. | Enables redundancy detection. "Skill description 87% similar to existing skill-creator. May be duplicate functionality." |
| **Architectural patterns** | C4 model diagrams, component dependency graphs, interface control documents. | Enables structural insight. "Skill operates at wrong abstraction layer. Currently L3 component, should be L2 container per C4 model." |
| **User workflow traces** | Which skills are invoked in sequence? What are common workflows? Where do users get stuck? | Enables user experience insight. "Users invoke /assessor then manually invoke /implement-refactor. Should be single workflow." |
| **Optimization opportunities** | Token distribution analysis. Which sections are dense vs verbose? Which examples are most cited? | Enables efficiency insight. "Examples section is 40% of tokens but rarely referenced. Move to references/ for progressive disclosure." |

**Evaluation Framework:**

```yaml
insightful_analysis:
  pattern_recognition:
    - "Are there recurring issues across multiple skills/agents?"
    - "Do similar components have similar problems? (suggests systemic issue)"
    - "Are there untapped optimization opportunities?"
  architectural_coherence:
    - "Does skill fit within system architecture?"
    - "Are abstraction boundaries correct?"
    - "Are there coupling issues (too many dependencies)?"
  user_experience:
    - "Are workflows intuitive?"
    - "Are common tasks streamlined?"
    - "Are there friction points in invocation patterns?"
```

**Example of insightful review:**

```markdown
INSIGHT: Workflow fragmentation detected
OBSERVATION: Users invoke /plugin-creator:assessor → review output → manually invoke /plugin-creator:implement-refactor → manually invoke /plugin-creator:ensure-complete
IMPACT: 3-step manual workflow with human gates between each step
OPPORTUNITY: Create unified /plugin-creator:refactor-plugin skill that orchestrates all 3 phases with automated gates
EVIDENCE: 15/20 recent refactoring sessions followed this pattern (75%)
RECOMMENDATION: Implement orchestration skill, delegate to existing skills as sub-tasks
PRECEDENT: SAM framework already defines 7-stage pipeline with automated gates (stateless-software-engineering-framework.md)
```

### "Well Researched" - Grounded in Authoritative Sources

**Required Inputs:**

| Input Type | Specific Content | How It Enables Research Depth |
|-----------|------------------|------------------------------|
| **Official documentation cache** | Anthropic prompt engineering guide, Claude Code plugin/skill schemas, MCP protocol specs. Pre-fetched, timestamped, searchable. | Enables citation. "Per Anthropic docs (accessed 2026-02-13), use positive framing over negative constraints." - authoritative reference. |
| **Community best practices** | GitHub examples, Claude Code marketplace top plugins, forum discussions. Curated, tagged by topic. | Enables pattern emulation. "Top 10 marketplace plugins average 2800 tokens per skill. Current skill 5200 tokens. Above community norm." - benchmarking. |
| **Historical context** | Previous versions of official docs. Changelog of schema updates. Migration guides. | Enables version awareness. "Skill uses deprecated tools array syntax from v1.2 schema. Update to v1.5 comma-separated format." - currency. |
| **Domain-specific references** | For Python skills: PEP standards, packaging guides. For testing skills: testing pyramid, mocking patterns. | Enables domain expertise. "Skill violates PEP 723 inline dependency spec. Must use requires-python and dependencies fields in script block." - correctness. |

**Evaluation Framework:**

```yaml
research_grounding:
  citation_quality:
    - "Are claims cited with specific sources (URL, document, line)?"
    - "Are sources authoritative (official docs > community forums)?"
    - "Are sources current (check publication/access date)?"
  precedent_validation:
    - "Are recommendations supported by existing examples?"
    - "If novel approach, is rationale explained?"
    - "Are there counter-examples that refute recommendation?"
  version_awareness:
    - "Is cited documentation version-matched to current system?"
    - "If schema changed recently, are updates reflected?"
    - "Are deprecated patterns flagged?"
```

**Example of well-researched review:**

```markdown
FINDING: Description field uses multiline indicator (forbidden)
LOCATION: plugins/plugin-creator/skills/assessor/SKILL.md, line 4
EVIDENCE: description: >-
SOURCE: Claude Code Skills Schema v1.5 (https://docs.anthropic.com/en/docs/claude-code/skills.md#frontmatter-schema, accessed 2026-02-13)
SPECIFICATION: "description field must be single-line quoted string. Multiline indicators (>-, |-) not supported due to parser limitations."
COMMUNITY_PATTERN: All 47 marketplace plugins use single-line descriptions (validated via grep across marketplace.json references)
HISTORICAL_CONTEXT: Multiline descriptions worked in v1.2, broke in v1.3 (changelog: 2025-11-04)
FIX: Replace lines 4-6 with: description: "Complete analysis of plugin structure and quality. Creates refactoring task files with validation and context gathering."
VALIDATION: Run plugin-validator.py, verify no FM009 error
```

### "Purpose Driven" - Optimizes for User Value, Not Metrics

**Required Inputs:**

| Input Type | Specific Content | How It Enables Purpose Focus |
|-----------|------------------|----------------------------|
| **User benefit statements** | From Discovery phase: "Users benefit by {concrete outcome}." Example: "Users benefit by reducing 3-step manual workflow to single command." | Enables value validation. "Change improves token count (metric) but removes worked examples (user value). Reject." |
| **Skill purpose anchor** | Original skill description from iteration 0. Used to detect drift. | Enables purpose preservation. "Iteration 3 description now says 'validates and optimizes' vs iteration 0 'analyzes structure.' Scope expanded. Revert or re-scope." |
| **Usage analytics** | Which skills are invoked frequently? Which trigger phrases are used? Where do users abandon workflows? | Enables prioritization. "Optimizing rarely-used advanced feature. Better to optimize common workflow first." |
| **User pain points** | From Discovery: What problems does this skill solve? What frustrations does it eliminate? | Enables problem-solution fit. "Change makes skill more 'elegant' but harder to understand for novices. Violates 'reduce friction' user benefit." |

**Evaluation Framework:**

```yaml
purpose_alignment:
  user_benefit_validation:
    - "Does change serve stated user benefit?"
    - "If change improves metrics but reduces usability, is it justified?"
    - "Are user pain points addressed or ignored?"
  purpose_preservation:
    - "Does skill description still match original purpose?"
    - "If purpose changed, was it intentional (approved) or drift?"
    - "Are trigger phrases still accurate after changes?"
  value_vs_vanity_metrics:
    - "Is optimization for users or for rubric scores?"
    - "If token count reduced, did it sacrifice clarity?"
    - "If validation passes, does skill still help users?"
```

**Example of purpose-driven review:**

```markdown
CONCERN: Optimization degrades user experience
CHANGE: Removed 5 worked examples from SKILL.md to reduce token count from 4200 → 3800
METRIC_IMPACT: Token count now below 4000 threshold (passes quality gate)
USER_IMPACT: Examples section was most-referenced (12/15 users cited examples in feedback)
USER_BENEFIT_STATEMENT: "Users benefit by seeing concrete examples of skill usage without needing to experiment" (from ARTIFACT:GOAL)
PURPOSE_CHECK: Skill description says "provides comprehensive guide with examples" - removing examples violates stated purpose
RECOMMENDATION: REJECT change. Alternative: Move examples to references/examples.md (progressive disclosure), keep 2 core examples inline. Maintains user value, achieves token reduction.
PRECEDENT: Plugin-creator skill uses this pattern successfully (references/templates/ directory)
```

### "Runtime Environment and Contextually Aware" - Understands Execution Context

**Required Inputs:**

| Input Type | Specific Content | How It Enables Context Awareness |
|-----------|------------------|----------------------------------|
| **System architecture** | Claude Code plugin system, skill loading order, agent delegation, MCP server integration. | Enables execution model understanding. "Skill assumes synchronous execution but delegates to MCP server (async). Add await or callback handling." |
| **Tool availability** | Which tools does skill/agent have access to? Which are blocked? What are permission constraints? | Enables feasibility check. "Agent uses Bash tool but permissionMode: strict blocks network access. Script will fail." |
| **Model capabilities** | Target model (Sonnet/Opus/Haiku). Context window size. Tool use patterns. Known limitations. | Enables model-aware design. "Skill targets Haiku but includes 2800 token reference section. Exceeds Haiku attention span. Use Sonnet." |
| **Dependency availability** | External MCP servers, Python packages, system binaries. Are they installed? What versions? | Enables runtime readiness. "Skill invokes pyright-langserver but LSP plugin not in dependencies. Add installation check or remove LSP feature." |
| **User environment** | Project type (Python/JS/Rust), directory structure, git state, existing plugins. | Enables adaptation. "Skill assumes Python project but user may run in JS project. Add language detection or scope check." |

**Evaluation Framework:**

```yaml
runtime_awareness:
  execution_model:
    - "Are async operations handled correctly?"
    - "Are tool permissions sufficient for operations?"
    - "Are resource limits (context window, token count) respected?"
  dependency_validation:
    - "Are all invoked tools/skills/agents available?"
    - "Are external dependencies documented and checked?"
    - "Are version requirements specified?"
  environment_adaptation:
    - "Does skill work in diverse project contexts?"
    - "Are assumptions about directory structure validated?"
    - "Are error messages helpful for diagnosing environment issues?"
```

**Example of context-aware review:**

```markdown
ISSUE: Skill assumes execution environment not guaranteed
LOCATION: plugins/plugin-creator/skills/refactor-plugin/SKILL.md, line 89
OPERATION: Delegates to subagent-refactorer agent with model: sonnet
CONTEXT_CHECK: User invoked skill with --model haiku (override)
PROBLEM: Subagent inherits haiku model (insufficient for refactoring complexity)
RUNTIME_IMPACT: Subagent will fail due to context window limits (Haiku 200K vs Sonnet 500K)
EVIDENCE: Refactoring tasks average 8000 tokens context (stateless-software-engineering-framework.md task decomposition spec)
RECOMMENDATION: Add model requirement validation. If parent model is Haiku, force subagent to Sonnet or block execution with clear error.
PRECEDENT: Plugin-creator agent-creator skill validates model selection before delegation (lines 34-38)
FIX: Add to SKILL.md:
```yaml
hooks:
  - type: "pre-execution"
    script: "./scripts/validate-model.sh"
    # Blocks if model insufficient for task complexity
```
```

### "Knowing How and Why End Users Benefit" - User-Centric Validation

**Required Inputs:**

| Input Type | Specific Content | How It Enables User Focus |
|-----------|------------------|---------------------------|
| **User stories** | "As a {user type}, I want {capability} so that {benefit}." Collected during Discovery. | Enables benefit validation. "Change optimizes internal structure but doesn't address any user story. Low priority." |
| **Workflow traces** | Step-by-step user interactions. Where do users pause? What do they search for? | Enables friction detection. "Users invoke skill, get error, grep for solution in docs. Error message unclear. Fix: add link to troubleshooting guide." |
| **Feedback history** | GitHub issues, user complaints, feature requests. Tagged by skill/agent. | Enables pain point prioritization. "5 users reported 'skill too verbose.' Token reduction directly addresses user feedback." |
| **Outcome metrics** | Does skill achieve stated user benefit? Time saved? Errors prevented? Tasks automated? | Enables impact measurement. "Before skill: 45 min manual validation. After skill: 2 min automated. User benefit delivered." |

**Evaluation Framework:**

```yaml
user_benefit_validation:
  user_story_alignment:
    - "Does change serve a user story?"
    - "If no user story exists, why make change?"
    - "Are user stories still valid after change?"
  friction_reduction:
    - "Does change reduce steps in workflow?"
    - "Does change eliminate manual work?"
    - "Does change prevent common errors?"
  outcome_achievement:
    - "Does skill still deliver stated user benefit?"
    - "Are success metrics still achievable?"
    - "If benefit changes, is it an improvement?"
```

**Example of user-benefit-focused review:**

```markdown
VALIDATION: User benefit assessment
CHANGE: Refactored plugin-creator skill to consolidate 3 sub-skills
USER_STORY: "As a plugin developer, I want to create plugins quickly so that I can focus on implementation, not scaffolding." (from ARTIFACT:GOAL)
BENEFIT_METRICS:
  - Time to create plugin (before): 15 min (manual directory creation, JSON writing, validation)
  - Time to create plugin (after): 3 min (single command, automated scaffolding)
  - Validation errors prevented: 47% (from user testing, 9/19 manual attempts had schema errors vs 0/20 automated)
FEEDBACK_ALIGNMENT:
  - Issue #23: "Too many steps to create plugin" → RESOLVED (consolidated workflow)
  - Issue #31: "Forgot to add .claude-plugin directory" → RESOLVED (automated scaffolding)
  - Issue #45: "Unclear what fields are required in plugin.json" → RESOLVED (guided prompts)
OUTCOME: ✅ Change delivers stated user benefit. Quantifiable improvement.
RESIDUAL_ISSUES: None identified
RECOMMENDATION: APPROVE change. Document time savings in skill description.
```

### Integration: Putting It All Together

**An AI reviewer with all these inputs can:**

1. **Find real issues** (not false positives) because it has source files, baseline metrics, and validation logs.
2. **Provide insights** (not just checklists) because it has cross-reference analysis, usage patterns, and architectural context.
3. **Ground recommendations in research** because it has official docs, community examples, and historical context.
4. **Optimize for user value** (not metrics) because it has user stories, feedback history, and outcome metrics.
5. **Validate runtime feasibility** because it has system architecture, tool availability, and dependency knowledge.
6. **Verify user benefit** because it has workflow traces, friction points, and impact measurements.

**Without these inputs:** AI reviewer becomes shallow. Produces generic advice ("consider splitting skill" without evidence), misses context ("change breaks downstream users" without dependency graph), optimizes for wrong goals ("improve token count" without checking user value).

**Design implication:** Autonomous refinement skills must:

1. **Gather all required inputs during Discovery phase** (front-loading)
2. **Store inputs as artifacts** (stateless agent access)
3. **Provide artifacts to reviewer agent** (complete context)
4. **Validate reviewer output quality** (does it cite sources? provide evidence? align with user goals?)

---

## Summary: From Research to Design

### What Enables Human-Out-of-Loop

**Necessary Conditions (all must be true):**

1. **Constrained scope:** Problem bounded, complete dataset enumerable, success criteria objective
2. **Binary verification:** Pass/fail checks with deterministic outcomes (tests, validators, diffs)
3. **Complete front-loading:** All decision points captured upfront, no runtime ambiguity
4. **Structural preservation:** Guardrails prevent destructive changes, content loss detection mandatory
5. **Escalation triggers:** Clear criteria for when autonomous loop must stop and request human input

### What Forces Human-in-Loop

**Irreducible Judgment Requirements:**

1. **Goal ambiguity:** Open-ended objectives ("best-in-class," "meta-skill") require continuous refinement of success criteria
2. **Proportionality context:** Change scope vs severity assessment depends on domain knowledge not capturable as thresholds
3. **Purpose drift:** Automated metrics can optimize away from original user value without semantic understanding
4. **Downstream impact prediction:** Cross-system effects require knowledge graphs beyond current artifact scope
5. **Diminishing returns judgment:** When to stop refining is subjective trade-off between effort and value

### Design Implications

**For autonomous refinement skills:**

1. **Accept hybrid model:** Human-at-end-of-loop (review after iteration) more feasible than human-out-of-loop (no review ever)
2. **Invest heavily in Discovery phase:** 50%+ of effort spent capturing complete context enables 80%+ of execution to be automated
3. **Detect insufficiency:** If runtime decision point arises not covered in artifacts, STOP rather than guess
4. **Build feedback loops:** Track "questions that arose" during execution → feed into next Discovery phase → improve front-loading over time
5. **Scope constraints matter:** Narrow problems (fix validation errors) autonomizable. Broad problems (make skill best-in-class) require continuous human guidance.

### What This Document Provides

**For implementers of autonomous refinement:**

- **Section 1:** Patterns of where human judgment currently required vs successfully replaced
- **Section 2:** Classification of every human check into eliminable/front-loadable/irreducible
- **Section 3:** Complete checklist of starting state requirements (what must be known)
- **Section 4:** Structure of front-loading session (what questions to ask, what artifacts to produce)
- **Section 5:** Required inputs for AI reviewer to match human review quality

**Next step:** Design autonomous refinement skill using these prerequisites as requirements specification.
