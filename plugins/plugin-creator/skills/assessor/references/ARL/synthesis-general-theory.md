# Synthesis: General Theory of Autonomous Development

A comparative analysis of six frameworks (BMAD-METHOD, Gas Town, GSD, OctoCode, Ralph, SAM) distilling universal patterns, complexity tiers, the autonomy spectrum, best-in-class patterns, shared gaps, and proposed general principles.

**Source documents**: framework-analysis-bmad-method.md, framework-analysis-gastown.md, framework-analysis-gsd.md, framework-analysis-octocode.md, framework-analysis-ralph.md, framework-analysis-sam.md, autonomous-refinement-loop-research.md, human-out-of-loop-prerequisites.md

**Date**: 2026-02-13

---

## 1. Universal Patterns

These patterns appear across most or all frameworks. Each was discovered independently, suggesting they reflect fundamental requirements of AI-driven development rather than borrowed ideas.

### 1.1 Artifact-Based State Management

**Convergent principle**: All state that must survive agent handoffs, session boundaries, or context resets must be externalized to persistent artifacts on disk. Conversation memory is unreliable.

| Framework | Implementation | Source |
|-----------|---------------|--------|
| BMAD | PRD, architecture, sprint-status.yaml, story files on disk. "Always start a fresh chat for each workflow." | framework-analysis-bmad-method.md, Section C |
| Gas Town | Three-layer polecat architecture: Identity (permanent bead) / Sandbox (git worktree) / Session (ephemeral). All in Dolt SQL + git. | framework-analysis-gastown.md, Section C |
| GSD | `.planning/` directory: PROJECT.md, STATE.md, ROADMAP.md, PLAN.md, SUMMARY.md. Each agent reads/writes files. | framework-analysis-gsd.md, Section C |
| OctoCode | plan.md, research.md, context.md, session.json. JSON pipeline artifacts for doc writer: analysis.json -> questions.json -> research.json -> work-assignments.json. | framework-analysis-octocode.md, Section C |
| Ralph | memories.md, tasks.jsonl, event_history.jsonl. "Disk Is State, Git Is Memory" (tenet 4). | framework-analysis-ralph.md, Section C |
| SAM | ARTIFACT:{TYPE}({SCOPE}) tokens backed by filesystem or SQL. Storage-agnostic semantic addressing. | framework-analysis-sam.md, Section C |

**Variation axis**: The frameworks differ in formality of artifact schemas. SAM defines typed semantic tokens; Gas Town uses SQL-backed structured data; GSD uses markdown files with frontmatter; Ralph uses flat files. All converge on "disk, not memory."

### 1.2 Fresh Context Per Stage/Iteration

**Convergent principle**: Each execution unit (stage, iteration, agent session) should start with a clean context window, receiving only the artifacts it needs. Context accumulation degrades quality.

| Framework | Implementation | Source |
|-----------|---------------|--------|
| BMAD | "Always start a fresh chat for each workflow" | framework-analysis-bmad-method.md, Section C (line 329) |
| Gas Town | Polecat session layer cycles on handoff/crash. State survives in git + beads, not in context. | framework-analysis-gastown.md, Section C |
| GSD | Each executor gets "fresh 200k-token context." Orchestrator stays at 10-15% context. Quality degradation curve explicitly modeled. | framework-analysis-gsd.md, Section B |
| OctoCode | "Each action operates with a fresh context window." Grounded in "Lost in the Middle" attention phenomenon. | framework-analysis-octocode.md, Section E.3 |
| Ralph | "Fresh Context Is Reliability" (tenet 1). Each iteration clears context and re-reads everything from disk. Listed as primary error recovery mechanism. | framework-analysis-ralph.md, Section C |
| SAM | "Each agent does exactly one task, then terminates. All state transitions happen through artifacts, not conversation history." | framework-analysis-sam.md, Section C |

**Variation axis**: GSD explicitly models the degradation curve (0-30% peak, 70%+ poor). Ralph treats fresh context as the error recovery mechanism. SAM makes it an architectural constraint. The insight is the same; the emphasis differs.

### 1.3 Quality Gates / Backpressure

**Convergent principle**: Autonomous systems need rejection mechanisms -- points where work is evaluated and sent back if insufficient. Prescribing steps is less effective than defining evidence requirements.

| Framework | Implementation | Source |
|-----------|---------------|--------|
| BMAD | Implementation Readiness Check (6-step adversarial), Code Review (must find 3-10 issues), PRD Validation (13-step). | framework-analysis-bmad-method.md, Section C |
| Gas Town | Witness pre-kill verification, Refinery merge queue, structured validation with attribution and quality signals. | framework-analysis-gastown.md, Section C |
| GSD | Plan verification (5 dimensions, up to 3 iterations), Phase verification (goal-backward), UAT (manual). Self-check in executors. | framework-analysis-gsd.md, Section C |
| OctoCode | Gate pattern with Pre-Conditions, Gate Check, FORBIDDEN, ALLOWED, On Failure. Triple Lock pattern. | framework-analysis-octocode.md, Section C |
| Ralph | Backpressure as central design principle. Evidence-based gates (tests pass/fail). "Don't prescribe how; create gates that reject bad work." | framework-analysis-ralph.md, Section C |
| SAM | Four verification levels: Self, Boundary, Forensic, Final. Deterministic backpressure via build/test/lint. | framework-analysis-sam.md, Section C |

**Variation axis**: Ralph is the purest expression -- backpressure IS the design philosophy. BMAD uses adversarial review (must find issues). OctoCode uses explicit FORBIDDEN/ALLOWED lists. SAM separates verification from execution via independent agents. All agree: gates, not instructions.

### 1.4 Adversarial/Independent Verification

**Convergent principle**: The entity that creates work should not be the sole verifier. Some form of adversarial or independent review improves quality beyond self-checking.

| Framework | Implementation | Source |
|-----------|---------------|--------|
| BMAD | "No 'looks good' allowed." Code review must find 3-10 issues. Zero findings = failure mode. | framework-analysis-bmad-method.md, Section C |
| Gas Town | Witness monitors polecats. Refinery reviews merges. Deacon patrols system health. Separation of worker/reviewer roles. | framework-analysis-gastown.md, Section C |
| GSD | Plan-checker verifies planner output (up to 3 iterations). Verifier uses goal-backward analysis independent of executor. | framework-analysis-gsd.md, Section C |
| OctoCode | GAN-inspired Generator/Verifier model. "Verifier tries to find flaws." Suggests cross-model validation. | framework-analysis-octocode.md, Section E.1 |
| Ralph | Reviewer hat re-runs tests to verify builder claims. Confession pattern: builder records shortcuts, confessor audits, handler verifies. | framework-analysis-ralph.md, Section C |
| SAM | Forensic Review Agent (Stage 6) is independent from Execution Agent (Stage 5). Separate context, separate mandate. | framework-analysis-sam.md, Section E.2 |

**Variation axis**: OctoCode frames it as GAN (Generator vs Discriminator). Ralph uses confession (builder reveals weaknesses, auditor exploits them). BMAD forces finding N issues. SAM gives the reviewer completely independent context. The convergent truth: self-verification is necessary but insufficient.

### 1.5 Escalation to Human

**Convergent principle**: Every system needs a mechanism to escalate to human judgment when automated resolution fails. Complete autonomy is not the goal; knowing when to stop is.

| Framework | Implementation | Source |
|-----------|---------------|--------|
| BMAD | Human decision after every template-output (default). YOLO mode as explicit opt-out. | framework-analysis-bmad-method.md, Section B |
| Gas Town | Tiered escalation: Worker -> Deacon -> Mayor -> Overseer (human). Categories: decision, help, blocked, failed, emergency. | framework-analysis-gastown.md, Section C |
| GSD | Deviation Rule 4 (architectural changes): STOP and ask user. Checkpoint protocol for human-verify/decision/human-action. | framework-analysis-gsd.md, Section C |
| OctoCode | Plan approval and implementation approval gates require explicit user consent. FORBIDDEN actions before approval. | framework-analysis-octocode.md, Section B |
| Ralph | RObot Telegram integration: agents emit human.interact events that block the loop. Humans can send proactive guidance. | framework-analysis-ralph.md, Section C |
| SAM | RT-ICA blocks if prerequisites MISSING. Forensic review NEEDS_WORK triggers planner. Final verification against original goals. No explicit mid-execution human gate -- relies on front-loading. | framework-analysis-sam.md, Section C |

**Variation axis**: Gas Town has the most sophisticated escalation hierarchy (5 levels). Ralph integrates via messaging platform (Telegram). BMAD defaults to human-at-every-step. SAM tries to eliminate mid-execution escalation entirely through front-loading. The pattern shows a spectrum from "always ask" to "never ask but fail safely."

### 1.6 Scope-Adaptive Planning Depth

**Convergent principle**: The depth of planning should match the complexity of the task. Lightweight tasks need lightweight planning; complex tasks need heavyweight planning. One size does not fit all.

| Framework | Implementation | Source |
|-----------|---------------|--------|
| BMAD | Quick Flow (bug fixes) vs BMad Method (products) vs Enterprise. CSV-driven domain and project type classification. | framework-analysis-bmad-method.md, Section B |
| Gas Town | Scope-agnostic: single bead, convoy, or multi-convoy. Mayor decomposes to appropriate granularity. | framework-analysis-gastown.md, Section B |
| GSD | Quick mode vs Standard vs Comprehensive. Depth config: 3-5 phases / 5-8 phases / 8-12 phases. | framework-analysis-gsd.md, Section B |
| OctoCode | Fast-path evaluation (skip planning for simple lookup) vs Full Planning. Goal classification: RESEARCH_ONLY through REFACTOR. | framework-analysis-octocode.md, Section B |
| Ralph | Direct prompt (small), preset with hats (medium), spec-driven with gap analysis (large), parallel loops (multi-feature). | framework-analysis-ralph.md, Section B |
| SAM | Complexity assessment matrix: Simple / Moderate / Complex / Firmware -- each determines artifact set. | framework-analysis-sam.md, Section B |

**Variation axis**: BMAD uses data-driven classification (CSV lookup). GSD uses user-configured depth. OctoCode uses heuristic fast-path evaluation. SAM uses structural complexity analysis. The convergent truth: planning overhead must be proportional.

---

## 2. Complexity Tiers

How do frameworks handle different levels of task complexity?

### Tier Matrix

| Tier | Definition | BMAD | Gas Town | GSD | OctoCode | Ralph | SAM |
|------|-----------|------|----------|-----|----------|-------|-----|
| **Simple** | Single file, clear fix | Quick Flow: tech-spec + quick-dev (skip phases 1-3) | Single bead, one polecat, one molecule | `/gsd:quick`: planner + executor, skip research/checker | Fast-path: skip planning, direct tool execution | `ralph run -p "..."` with no hats | Simple: PRD + NFR + Component Diagram + ADRs |
| **Moderate** | Multi-file, bounded scope | Quick Flow with spec, or Phase 2-4 with standard depth | Multiple beads in convoy, parallel polecats | Standard: 5-8 phases, 3-5 plans each, wave parallelism | Full planning with sequential strategy. Goal: FEATURE or BUG | Preset with hat pipeline (e.g., TDD, spec-driven) | Moderate: adds Container Diagram, Solution Architecture |
| **Complex** | Multi-system, ambiguous scope | Full BMad Method (Phases 1-4), Enterprise track | Multiple convoys, cross-rig tracking | Comprehensive: 8-12 phases, 5-10 plans, full research suite | Full planning with parallel strategy. Multiple researcher domains | Spec-driven with gap analysis + parallel loops | Complex: adds Context Diagram, ICD, Deployment View |
| **Meta** | Self-referential, unbounded | Not addressed | Not addressed | Not addressed | Prompt optimizer (meta-skill that optimizes other skills) | Confession pattern (self-audit mechanism) | Not addressed directly; human-out-of-loop-prerequisites.md identifies as requiring irreducible human judgment |

**Observations**:

1. All frameworks provide a lightweight path for simple tasks. The overhead of full methodology for a bug fix is universally recognized as counterproductive.
2. The transition from moderate to complex varies: BMAD uses domain classification, GSD uses depth configuration, SAM uses artifact set expansion. No consensus on where the boundary lies.
3. Meta-tier tasks (self-referential, self-improving) are addressed only partially. OctoCode's prompt optimizer and Ralph's confession pattern touch this space. human-out-of-loop-prerequisites.md explicitly identifies this as requiring irreducible human judgment.

---

## 3. The Autonomy Spectrum

Each framework occupies a different position on the spectrum from fully human-driven to fully autonomous.

```
Human-Driven                                                        Fully Autonomous
|=========|=========|=========|=========|=========|=========|=========|
          BMAD      OctoCode  GSD       SAM       Ralph     Gas Town
          (human    (check-   (discuss  (front-   (loop     (Mayor
          at every  point     then      load      until     decomp,
          step,     gated,    auto      then      done,     auto
          YOLO      user      execute,  auto      fresh     assign,
          opt-out)  approves  verify    pipeline, context   auto
                    plan)     at end)   forensic  recovery) merge)
                                        review)
```

### Mechanisms That Enable More Autonomy

| Mechanism | Frameworks Using It | How It Increases Autonomy |
|-----------|--------------------|-----------------------------|
| Front-loading decisions into artifacts | SAM, GSD, BMAD | Eliminates mid-execution human gates by capturing all decisions upfront |
| Fresh context per iteration | Ralph, GSD, OctoCode, SAM | Enables error recovery without human diagnosis -- just restart clean |
| Backpressure gates | Ralph, SAM, OctoCode | Replaces human quality judgment with deterministic pass/fail checks |
| Self-cleaning workers | Gas Town | Eliminates human cleanup of stalled/zombie agents |
| Tiered escalation | Gas Town, Ralph | Automated resolution at lower tiers, human only for unresolvable issues |
| Deviation rules | GSD | Auto-fix bugs/blockers (Rules 1-3), only escalate architecture (Rule 4) |
| Loop detection | Ralph | Detects stuck agents automatically (90% similarity threshold), terminates without human |
| Convergence tracking | GSD (finding count), Ralph (completion promise + task exhaustion) | Machine-detectable "done" conditions |

### Mechanisms That Require Human Involvement

| Mechanism | Frameworks Using It | Why Automation Fails |
|-----------|--------------------|-----------------------|
| Goal definition | All 6 | Cannot generate goals from nothing -- requires human intent |
| Proportionality judgment | SAM (front-loaded), GSD (deviation Rule 4) | "Is this change worth its blast radius?" is contextual |
| Purpose drift detection | None solve this well | Automated metrics (embedding distance, description comparison) are insufficient for semantic purpose tracking |
| Split justification | BMAD (none), SAM (none) | "Is this genuinely useful as a separate entity?" requires understanding user mental models |
| Architectural decisions | GSD (Rule 4), Gas Town (escalation) | Cross-system tradeoffs require domain knowledge and organizational context |

### Practical Autonomy Limits

Based on evidence from all 6 frameworks:

1. **Goal definition is irreducibly human.** No framework attempts to generate goals. All start with human intent.
2. **Simple tasks can be fully autonomous.** Every framework provides a lightweight path that runs end-to-end without human intervention for well-scoped work.
3. **Complex tasks converge on "human-at-boundaries."** The successful pattern is: human defines scope and approves plan, then autonomous execution with automated quality gates, then human reviews final result.
4. **Meta-tasks resist automation.** Self-referential improvement loops lack natural stopping criteria (per human-out-of-loop-prerequisites.md, Section 3).
5. **The autonomy ceiling is set by verification quality.** Autonomous systems can only be as autonomous as their ability to detect failure. Current limits: deterministic checks (tests/lint) are reliable; LLM-based quality assessment has blind spots.

---

## 4. Best-in-Class Patterns

For each major concern, which framework has the strongest approach?

### 4.1 Front-Loading

**Best**: SAM (Stateless Agent Methodology)

SAM's RT-ICA gate is the most rigorous front-loading mechanism. It explicitly classifies every prerequisite as AVAILABLE, DERIVABLE, or MISSING, and blocks execution if any are MISSING. The Discovery phase captures goals, anti-goals, NFRs, and references. The Context Integration stage (Stage 3) grounds plans in codebase reality before decomposition.

**Why**: Other frameworks front-load (BMAD's 4-phase pipeline, GSD's deep questioning), but SAM treats incompleteness as a structural blocker rather than a warning. The pipeline physically cannot proceed without complete information.

**Source**: framework-analysis-sam.md, Section D (RT-ICA gate)

### 4.2 Quality Gates

**Best**: Ralph (backpressure model)

Ralph's approach -- "don't prescribe how, create gates that reject bad work" -- is the cleanest separation of concerns. Technical gates (tests, lint, typecheck), behavioral gates (LLM-as-judge), and evidence requirements (events must carry proof) create a layered verification system. The confession pattern adds an adversarial self-audit layer.

**Runner-up**: BMAD's adversarial review ("must find 3-10 issues, zero findings = failure") is a complementary pattern that addresses the "rubber stamp" problem.

**Source**: framework-analysis-ralph.md, Section C (backpressure), framework-analysis-bmad-method.md, Section C (adversarial review)

### 4.3 Convergence Detection

**Best**: Ralph

Ralph has four independent convergence signals: completion promise (agent declares done), task exhaustion (no open tasks), safety limits (iteration/time/cost caps), and loop detection (90% similarity on sliding window). These create redundant detection that catches both genuine completion and stuck states.

**Runner-up**: GSD's goal-backward verification ("task completion != goal achievement") catches the specific failure mode where tasks are marked complete without achieving the actual objective.

**Source**: framework-analysis-ralph.md, Section C (convergence), framework-analysis-gsd.md, Section C (convergence)

### 4.4 State Management

**Best**: Gas Town

Gas Town's three-layer architecture (Identity permanent / Sandbox per-assignment / Session per-step) is the most sophisticated state model. It separates what must persist forever (agent identity, track record), what lives for the duration of an assignment (git worktree, branch), and what cycles frequently (Claude context window). State survives crashes because git commits, molecule state, and hook assignments persist independently of sessions.

**Runner-up**: SAM's storage-agnostic semantic tokens (ARTIFACT:{TYPE}({SCOPE})) are the most portable abstraction.

**Source**: framework-analysis-gastown.md, Section C (three-layer architecture), framework-analysis-sam.md, Section C (semantic tokens)

### 4.5 Error Recovery

**Best**: Ralph (fresh context as recovery)

Ralph's insight is philosophically distinctive: rather than building complex retry logic, simply start each iteration with completely fresh context. This prevents getting stuck in local minima and avoids accumulated confusion. "Complex retry logic" is listed as an anti-pattern.

**Runner-up**: Gas Town's merge conflict recovery (spawn FRESH polecat to re-implement, never send work back) embodies the same principle for a different failure mode.

**Source**: framework-analysis-ralph.md, Section E.3, framework-analysis-gastown.md, Section C (merge conflict recovery)

### 4.6 Parallelism

**Best**: GSD

GSD's wave-based parallelism is the most practical parallel execution model. Plans declare dependencies via frontmatter, gsd-tools.js groups them into waves, plans within a wave execute in parallel (each with fresh 200k context), and waves execute sequentially. The constraint model is simple and deterministic.

**Runner-up**: Gas Town's parallel polecats with git worktree isolation scale to more agents (20-30+), but the coordination overhead is higher. Ralph's parallel loops with shared memories via symlinks are elegant but require a merge-ralph process for conflict resolution.

**Source**: framework-analysis-gsd.md, Section C (parallel execution), framework-analysis-gastown.md, Section B (multi-polecat)

### 4.7 Context Window Management

**Best**: GSD

GSD treats the context window as the fundamental constraint, not an afterthought. The quality degradation curve is explicitly modeled (0-30% peak, 70%+ poor). Plans are sized to complete within ~50% context. Orchestrators stay at 10-15%. Each executor gets fresh 200k. Context budget is a verification dimension in plan checking.

**Source**: framework-analysis-gsd.md, Section E.1

### 4.8 Scope Detection and Adaptation

**Best**: BMAD

BMAD's CSV-driven domain complexity detection (15 domains) and project type detection (11 types) provide data-driven planning depth adjustment. This is extensible (edit CSV, not code), covers diverse domains (healthcare, fintech, govtech, aerospace), and automatically adjusts required knowledge areas, key concerns, and special document sections.

**Source**: framework-analysis-bmad-method.md, Section E.1

---

## 5. Gaps Across All Frameworks

Problems that no framework solves well. These are open research questions.

### 5.1 Purpose Drift Detection

No framework reliably detects when iterative refinement shifts a component away from its original purpose. human-out-of-loop-prerequisites.md identifies this as irreducible: "Natural language comparison requires semantic understanding. Rewording for clarity is not drift; expanding scope is drift. Automated NLP cannot reliably distinguish."

**Current approaches**: Embedding distance comparison (SAM suggests cosine similarity <0.85 threshold), description text diffing (autonomous-refinement-loop-research.md). Neither is reliable for semantic purpose preservation.

### 5.2 Proportionality Judgment

No framework automatically determines whether a proposed change is proportional to the issue it addresses. A typo fix touching 15 files is disproportionate; a security fix touching 15 files is not. This requires domain-specific severity weights that none of the frameworks define automatically.

**Current approaches**: GSD's deviation rules (tiered severity), BMAD's domain complexity classification. These help but don't solve the general case.

### 5.3 Cross-Session Learning

No framework learns from past failures in a generalizable way. Ralph's memory system comes closest (pattern, decision, fix, context memories injected at iteration start), but memories are per-project, not cross-project. No framework builds a knowledge base of "this type of change tends to cause this type of problem" across codebases.

**Current approaches**: Ralph's memories (project-scoped). Gas Town's CV chain (agent-scoped track record). Neither generalizes.

### 5.4 Inter-Agent Real-Time Coordination

All frameworks that support parallelism (GSD, Gas Town, Ralph) use file-based coordination. No framework supports real-time message passing between concurrent agents during execution. If Agent A discovers something Agent B needs, it can only communicate via committed files that a later stage reads.

**Current approaches**: Gas Town's nudge system (`gt nudge`) and event bus come closest but operate at the orchestration layer, not between concurrent workers on related tasks.

### 5.5 Automated Stopping Criteria for Open-Ended Tasks

No framework has a reliable mechanism for deciding "this is good enough" for tasks without binary pass/fail criteria. human-out-of-loop-prerequisites.md identifies this as a fundamental limitation: "Open-ended meta-goals require continuous human judgment. Autonomous operation requires collapsing infinite possibility space to bounded, measurable outcomes."

**Current approaches**: Ralph's safety limits (max iterations, max cost). GSD's severity floor ("stop when only info-level findings remain"). These are heuristics, not principled stopping criteria.

### 5.6 Verification of Verification

No framework verifies that its quality gates are actually catching real problems. A test suite that passes does not prove the tests are meaningful. An adversarial review that finds 5 issues does not prove they are the right 5 issues. This meta-verification problem is unaddressed.

**Current approaches**: SAM's evidence ledger (Appendix D) audits the methodology's own claims, but this is a one-time analysis, not continuous verification-of-verification.

---

## 6. Proposed General Principles

Based on evidence from all six frameworks and two research documents. Each principle cites evidence from at least two frameworks.

### Principle 1: Externalize All State to Persistent Artifacts

**Statement**: Every piece of information that must survive beyond a single agent execution must be written to a persistent artifact. Conversation memory, in-context state, and session variables are unreliable and must not be trusted for handoff.

**Evidence**: SAM ("All state transitions happen through artifacts, not conversation history" -- framework-analysis-sam.md, Section C). Ralph ("Disk Is State, Git Is Memory" -- framework-analysis-ralph.md, tenet 4). GSD (file-based `.planning/` directory -- framework-analysis-gsd.md, Section C). Gas Town (three-layer architecture with git-backed everything -- framework-analysis-gastown.md, Section C).

### Principle 2: Each Execution Unit Gets Fresh Context

**Statement**: Each agent, iteration, or workflow step should begin with a clean context window loaded only with the artifacts relevant to its task. Context accumulation degrades output quality.

**Evidence**: GSD (explicit quality degradation curve: 0-30% peak, 70%+ poor -- framework-analysis-gsd.md, Section B). Ralph ("Fresh Context Is Reliability" -- framework-analysis-ralph.md, tenet 1). OctoCode ("Lost in the Middle" attention phenomenon as theoretical basis -- framework-analysis-octocode.md, Section E.3). SAM ("Each agent does exactly one task, then terminates" -- framework-analysis-sam.md, Section C).

### Principle 3: Define Gates, Not Steps

**Statement**: Prescribe what evidence must exist (backpressure gates) rather than how to produce it. The AI agent chooses the method; the system validates the result.

**Evidence**: Ralph ("Backpressure Over Prescription" -- framework-analysis-ralph.md, tenet 2). SAM (deterministic backpressure via build/test/lint as first-class principle -- framework-analysis-sam.md, Section E.4). OctoCode (FORBIDDEN/ALLOWED lists at phase transitions -- framework-analysis-octocode.md, Section C).

### Principle 4: Separate Execution from Verification

**Statement**: The agent that produces work should not be the sole judge of its quality. Use independent agents, adversarial review, or deterministic checks to verify.

**Evidence**: SAM (Forensic Review Agent independent from Execution Agent -- framework-analysis-sam.md, Section E.2). BMAD (adversarial review: "must find 3-10 issues, zero findings = failure" -- framework-analysis-bmad-method.md, Section C). Ralph (confession pattern: builder records shortcuts, confessor audits -- framework-analysis-ralph.md, Section E.2). GSD (goal-backward verification: "task completion != goal achievement" -- framework-analysis-gsd.md, Section C).

### Principle 5: Planning Depth Must Be Proportional to Complexity

**Statement**: A single planning methodology applied uniformly wastes effort on simple tasks and underserves complex ones. Systems must detect complexity and adapt planning depth.

**Evidence**: BMAD (Quick Flow vs BMad Method vs Enterprise, CSV-driven domain classification -- framework-analysis-bmad-method.md, Section E.1). GSD (quick/standard/comprehensive depth configuration -- framework-analysis-gsd.md, Section B). OctoCode (fast-path evaluation for simple lookups -- framework-analysis-octocode.md, Section B). Ralph (direct prompt vs preset vs spec-driven vs parallel loops -- framework-analysis-ralph.md, Section B).

### Principle 6: Front-Load Ambiguity Resolution

**Statement**: All questions that would cause a human to pause during execution should be answered before execution begins. Runtime ambiguity forces either suboptimal autonomous decisions or expensive human interrupts.

**Evidence**: SAM (RT-ICA gate blocks if prerequisites MISSING -- framework-analysis-sam.md, Section D). GSD (discuss-phase captures locked decisions, discretion areas, deferred ideas before planning -- framework-analysis-gsd.md, Section E.5). human-out-of-loop-prerequisites.md (Section 4: "every point where a human would pivot, decide, review, or quality-check gets asked and clarified at the start").

### Principle 7: Provide Structured Escalation When Automation Fails

**Statement**: Autonomous systems must have explicit paths to human judgment when they encounter situations they cannot resolve. Failing silently or guessing is worse than stopping.

**Evidence**: Gas Town (tiered escalation: Worker -> Deacon -> Mayor -> Overseer with categories -- framework-analysis-gastown.md, Section C). GSD (deviation Rule 4: STOP for architectural decisions -- framework-analysis-gsd.md, Section C). Ralph (RObot: blocking human.interact events -- framework-analysis-ralph.md, Section C). SAM (RT-ICA BLOCK for missing prerequisites -- framework-analysis-sam.md, Section D).

### Principle 8: Detect and Terminate Non-Convergent Loops

**Statement**: Iterative systems must monitor whether successive iterations are making progress. If they are not, the loop must terminate or escalate rather than continue indefinitely.

**Evidence**: Ralph (loop detection via 90% fuzzy similarity on sliding window, plus safety limits -- framework-analysis-ralph.md, Section C). GSD (finding count tracking: "if iteration N >= iteration N-1, stop" -- referenced in autonomous-refinement-loop-research.md, line 56). Ralph (consecutive failure tracking: 5 failures = termination -- framework-analysis-ralph.md, Section C).

### Principle 9: Workers Own Their Cleanup

**Statement**: Agents that complete work should clean up their own resources (branches, sessions, temporary state). Do not rely on external supervision for routine cleanup.

**Evidence**: Gas Town (self-cleaning model: polecat runs `gt done`, pushes branch, submits to merge queue, nukes own sandbox, exits -- framework-analysis-gastown.md, Section E.3). Ralph (LOOP_COMPLETE terminates the loop; no idle state -- framework-analysis-ralph.md, Section C).

### Principle 10: Verify Goals, Not Just Tasks

**Statement**: Task completion does not guarantee goal achievement. Verification must check whether the original objective is satisfied, not just whether the checklist items are done.

**Evidence**: GSD ("Task completion != Goal achievement. A task 'create chat component' can be marked complete when the component is a placeholder." -- framework-analysis-gsd.md, Section C). SAM (Final Verification Agent validates against original goals from Discovery -- framework-analysis-sam.md, Section C). BMAD (Implementation Readiness Check validates cross-document alignment -- framework-analysis-bmad-method.md, Section C).

### Principle 11: Treat Plans as Disposable

**Statement**: If a plan fails or becomes stale, regenerate it rather than patching it. In iterative systems, plan regeneration is cheap; plan repair introduces accumulated errors.

**Evidence**: Ralph ("The Plan Is Disposable. Regeneration costs one planning loop. Cheap. Never fight to save a plan." -- framework-analysis-ralph.md, tenet 3). GSD (plan-checker iterates up to 3 times, then user decides; plans are not sacred -- framework-analysis-gsd.md, Section C).

### Principle 12: Attribute Every Action to an Actor

**Statement**: In multi-agent systems, every action (commit, decision, artifact creation) must be attributed to a specific agent identity. Attribution enables quality measurement, routing decisions, and accountability.

**Evidence**: Gas Town (BD_ACTOR: every git commit, bead record, and event log attributed -- framework-analysis-gastown.md, Section E.6). SAM (artifact tokens include scope and type identification -- framework-analysis-sam.md, Section E.3).

### Principle 13: Use Deterministic Checks as Ground Truth

**Statement**: When deterministic checks (tests, linters, type checkers, build systems) disagree with AI judgment, the deterministic check wins. AI-generated assessments of code quality are supplements, not replacements.

**Evidence**: SAM ("Treat deterministic checks as ground truth. Rules in the context window are suggestions and cannot be treated as a deterministic security control surface." -- framework-analysis-sam.md, Section E.4). Ralph (backpressure gates: evidence-based, not claim-based -- framework-analysis-ralph.md, Section C). GSD (self-check: executors verify their own claims against filesystem and git -- framework-analysis-gsd.md, Section E.9).

### Principle 14: Make Error Recovery Structural, Not Instructional

**Statement**: Error recovery should be built into the system architecture (fresh context, artifact-based state, idempotent operations) rather than relying on behavioral instructions ("if an error occurs, try again").

**Evidence**: SAM ("Behavioral instructions cannot override architectural limitations. The solution must be structural, not instructional." -- framework-analysis-sam.md, Section A). Ralph (fresh context as primary recovery, "Complex retry logic" listed as anti-pattern -- framework-analysis-ralph.md, Section E.3). Gas Town (nondeterministic idempotence: any worker can continue any molecule, steps are atomic checkpoints -- framework-analysis-gastown.md, Section C).

---

## Summary

### Universal Truths Discovered Independently

1. Disk state outlasts conversation state
2. Fresh context beats accumulated context
3. Gates beat prescriptions
4. Independent review catches what self-review misses
5. Planning depth must match task complexity
6. Escalation paths to humans are necessary

### The Autonomy Ceiling

The practical limit of autonomous AI development is determined by the intersection of:
- **Verification quality** (can we detect failure?)
- **Scope clarity** (is the problem well-defined?)
- **Front-loading completeness** (were all decisions captured?)

When all three are high, full autonomy for bounded tasks is achievable. When any is low, human involvement becomes necessary. No framework has found a way around this constraint; the best frameworks accept it and optimize the boundaries.
