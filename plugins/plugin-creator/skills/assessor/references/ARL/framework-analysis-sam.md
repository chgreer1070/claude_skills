# Framework Analysis: Stateless Agent Methodology (SAM)

**Source Repository**: `/home/ubuntulinuxqa2/repos/claude_skills/methodology_development/`
**Files Analyzed**: `README.md`, `stateless-agent-methodology.md`, `sam-harness.md`, `stateless-software-engineering-framework.md`, `process_realignment.md`
**Date**: 2026-02-13

---

## A. System Overview

### What Is SAM?

SAM is a constraint-driven development framework that compensates for LLM limitations through architectural structure rather than behavioral instructions. It treats Claude as a **stateless computation engine** rather than a knowledge worker.

> "Claude is not a knowledge worker - Claude is a stateless computation engine that happens to have noisy, stale priors baked in."
> -- `README.md`:9

The framework reorganizes AI-driven software development work into discrete pipeline stages, each executed by a purpose-built agent operating in a fresh context with complete information. All state is externalized to artifact files, not held in conversation memory.

### Core Philosophy

SAM operates on the principle that **behavioral instructions cannot override architectural limitations**:

> "Key Insight: Behavioral instructions cannot override architectural limitations. The solution must be structural, not instructional."
> -- `stateless-software-engineering-framework.md`:108

Rather than asking Claude to "be careful" or "verify your work," SAM makes the process itself the enforcement mechanism. The methodology IS the prompt -- it cannot be skipped because it structures the task.

The pure function framing is central:

- **Input**: Complete context (task file with all answers)
- **Output**: Verified result
- **No side effects**: Fresh context each time
- **No memory**: Everything externalized to artifact files

Source: `README.md`:11-17

### Target Audience and Use Case

SAM targets software engineering workflows where LLM agents are used for autonomous or semi-autonomous development. It addresses the gap between what users want (reliable autonomous work) and what LLMs deliver (unreliable work that degrades over long contexts).

The framework is designed for:
- Complex, multi-step feature development
- Tasks requiring multiple agents working in sequence or parallel
- Workflows where quality, correctness, and verification matter more than speed

### Relationship Between Components

The methodology development directory contains several interrelated documents:

| Component | Role | File |
|-----------|------|------|
| **SAM (core methodology)** | Defines the problem, principles, and pipeline architecture | `stateless-agent-methodology.md` |
| **SSE Framework** | Canonical specification with agent specs, artifact templates, theoretical foundations, appendices | `stateless-software-engineering-framework.md` |
| **SAM Harness** | Implementation architecture for SAM as a Claude Code Plugin | `sam-harness.md` |
| **Process Realignment** | User's working notes on desired workflow, artifact types, complexity assessment | `process_realignment.md` |

The `stateless-agent-methodology.md` file is largely a navigation document that points to the SSE framework as the canonical specification. The SSE framework is the most detailed document (1300+ lines with appendices). The SAM Harness describes how to package SAM as a plugin. The Process Realignment document contains the user's evolving vision for the workflow, including detailed architecture artifact specifications.

---

## B. Autonomous Development Model

### Front-Loading Human Effort

SAM front-loads human decision-making into the Discovery and Planning stages, then executes autonomously through the remaining pipeline:

**Human-intensive stages** (Stages 1-2):
- Stage 1 (Discovery): Structured conversation with user to capture requirements, goals, anti-goals, NFRs
- Stage 2 (Planning): RT-ICA gate blocks execution until all prerequisites are verified

**Autonomous stages** (Stages 3-7):
- Context Integration, Task Decomposition, Execution, Forensic Review, Final Verification all proceed without human intervention

> "This framework explicitly avoids tool blocking and approval gates. All approval is frontloaded via explicit agreement on Desired outcome + Objectives + Acceptance criteria."
> -- `stateless-software-engineering-framework.md`:193

### The 7-Stage Pipeline

Source: `README.md`:78-141, `stateless-software-engineering-framework.md`:250-278

| Stage | Name | Agent | Input | Output |
|-------|------|-------|-------|--------|
| 1 | Discovery | Discovery Agent | User request | `ARTIFACT:DISCOVERY(SCOPE:...)` |
| 2 | Planning (RT-ICA) | Planning Agent | Discovery artifacts | `ARTIFACT:PLAN(SCOPE:...)` |
| 3 | Context Integration | Context Integration Agent | Plan + codebase | `ARTIFACT:PLAN(SCOPE:...)` (contextualized) |
| 4 | Task Decomposition | Task Decomposition Agent | Contextualized plan | `ARTIFACT:TASK(TASK:...)` files |
| 5 | Execution | Execution Agent (FRESH SESSION) | Single task file | `ARTIFACT:EXECUTION(TASK:...)` |
| 6 | Forensic Review | Forensic Review Agent (INDEPENDENT) | Execution results + plan | `ARTIFACT:REVIEW(TASK:...)` |
| 7 | Final Verification | Final Verification Agent | All reviews + original goals | `ARTIFACT:VERIFICATION(SCOPE:...)` |

### Pipeline Control Flow

The pipeline is not purely linear. After Stage 6, a decision point routes work:

- **COMPLETE**: Proceed to Stage 7 (Final Verification)
- **NEEDS_WORK**: Route to a Planner Agent that creates new tasks, which loop back through Stage 5

Source: `stateless-software-engineering-framework.md`:274-277

An Orchestrator agent coordinates the overall flow. It is explicitly a **thin orchestrator** that reads status, dispatches agents, and does not do work itself.

Source: `stateless-software-engineering-framework.md`:743

### Handling Scope

The `process_realignment.md` document defines a complexity assessment matrix:

| Complexity | Characteristics | Artifact Set |
|------------|----------------|--------------|
| Simple | Single-module, no external interfaces | PRD, NFR, Component Diagram, ADRs |
| Moderate | Multi-module, internal APIs, config | Adds Container Diagram, Solution Architecture |
| Complex | Cross-system, infrastructure, hardware | Adds Context Diagram, ICD, Deployment View |
| Firmware | Hardware interaction | Adds HAL Specification |

Source: `process_realignment.md`:43-48, 142-149

This allows SAM to scale from small single-module changes to complex cross-system projects by adjusting which architecture artifacts are produced.

### Human Decision Points vs Automated Decision Points

| Decision Type | Stage | Who Decides |
|---------------|-------|-------------|
| Feature requirements and goals | Stage 1 | Human (via structured conversation) |
| Approval of discovery document | Stage 1 exit | Human |
| Prerequisite availability (RT-ICA) | Stage 2 | Automated (with human escalation for MISSING items) |
| Plan approval | Stage 2 exit | Frontloaded via acceptance criteria agreement |
| Codebase conflict resolution | Stage 3 | Automated (agent-driven) |
| Task ordering and parallelism | Stage 4 | Automated |
| Task execution | Stage 5 | Automated (fresh session) |
| Quality verdict (COMPLETE/NEEDS_WORK) | Stage 6 | Automated (independent agent) |
| Feature certification | Stage 7 | Automated (against original goals) |

---

## C. Key Concepts and Mechanisms

### Named Concepts

**Agents**: Purpose-specific AI instances, each doing exactly one task then terminating. The framework specifies 9 agent roles:
1. Discovery Agent
2. Planning Agent
3. Context Integration Agent
4. Task Decomposition Agent
5. Execution Agent
6. Forensic Review Agent
7. Planner Agent (Iteration)
8. Orchestrator
9. Final Verification Agent

Source: `stateless-software-engineering-framework.md`:298-798

**Artifacts**: Externalized state tokens following the pattern `ARTIFACT:{TYPE}({SCOPE_OR_ID})`. These are storage-agnostic semantic identifiers that can be backed by files, databases, queues, or git notes.

Source: `stateless-software-engineering-framework.md`:148-157

**RT-ICA**: Real-Time Information Completeness Assessment. A prerequisite verification gate in Stage 2 that blocks execution if required information is missing. Each prerequisite is classified as AVAILABLE, DERIVABLE, or MISSING.

Source: `stateless-software-engineering-framework.md`:373-378

**Deterministic Backpressure**: Gating progress on deterministic checks (build/tests/lint/security scans) rather than prompts or behavioral instructions.

Source: `stateless-software-engineering-framework.md`:124

### Managing State Across Agent Handoffs (Stateless Architecture)

The core mechanism is **artifact-based message passing**:

> "The execution context from one agent session is NOT passed to another session or agent. Each agent does exactly one task, then terminates. All state transitions happen through artifacts, not through conversation history or shared context."
> -- `stateless-software-engineering-framework.md`:21

What this eliminates:
- Guessing from incomplete information
- Relying on training data priors
- Carrying forward errors from earlier context
- Context window degradation across tasks

Source: `stateless-software-engineering-framework.md`:23-28

### Quality Gates and Verification

SAM implements verification at four levels:

1. **Self-verification** (Stage 5): Embedded in each task file as steps the execution agent must follow. Augmented by deterministic checks (lint, tests, build).

2. **Boundary verification** (every stage transition): Each stage validates the previous stage's output before proceeding.

3. **Forensic review** (Stage 6): An independent agent verifies task completion by comparing results against the original plan, fact-checking claims, and assessing quality.

4. **Final verification** (Stage 7): Validates the complete feature against the original goals and acceptance criteria from Discovery.

Source: `stateless-software-engineering-framework.md`:116-126

The disambiguation tokens clarify verification types:

```text
VERIFY:SELF | VERIFY:BOUNDARY | VERIFY:FORENSIC | VERIFY:FINAL
```

Source: `stateless-software-engineering-framework.md`:185

### Convergence (Knowing When "Done")

Convergence is determined through the pipeline's iteration loop:

1. Stage 6 (Forensic Review) produces a verdict: COMPLETE or NEEDS_WORK
2. If NEEDS_WORK: Planner creates new tasks addressing the specific issues
3. New tasks loop back through Execution (Stage 5) and Forensic Review (Stage 6)
4. Loop continues until all tasks pass forensic review
5. Stage 7 (Final Verification) certifies the feature against original goals

The target metrics from the framework:

| Metric | Target |
|--------|--------|
| Hallucination rate | <5% |
| Methodology compliance | 100% |
| Rework rate | <20% |
| Context usage per agent | <50% |
| Goal achievement | >95% |
| First-pass success | >70% |

Source: `stateless-software-engineering-framework.md`:963-973

### Error, Failure, and Recovery

**RT-ICA blocking**: If prerequisites are MISSING at Stage 2, the pipeline blocks and requests information. It does not proceed with incomplete data.

**Execution failures**: If a task cannot be completed, the Execution Agent reports BLOCKED status with specific blockers listed.

**Forensic review failures**: NEEDS_WORK triggers the Planner Agent to create corrective tasks that loop back through execution.

**Deterministic backpressure**: Build/test/lint failures in the inner execution loop are treated as ground truth. The agent must repair until checks pass or explicitly block.

> "Treat 'run deterministic checks' as a mandatory self-verification step in Stage 5 (Execution). If checks fail, the next loop iteration must incorporate the tool output as ground truth and repair until the checks pass or the task is explicitly blocked."
> -- `stateless-software-engineering-framework.md`:146

### Externalized Memory

All state lives in artifact files, not in conversation history or agent memory. The framework defines a token-based addressing system:

```text
ARTIFACT:DISCOVERY(SCOPE:...)
ARTIFACT:PLAN(SCOPE:...)
ARTIFACT:TASK(TASK:...)
ARTIFACT:EXECUTION(TASK:...)
ARTIFACT:REVIEW(TASK:...)
ARTIFACT:VERIFICATION(SCOPE:...)
```

These tokens are storage-agnostic. Two example backends are specified:

**A) Filesystem-backed**: Artifacts stored as markdown files in `.sam/artifacts/`
**B) SQL-backed**: Artifacts stored in a relational database with token, type, scope_id, task_id, content, and timestamps

Source: `stateless-software-engineering-framework.md`:201-247

The SAM Harness (`sam-harness.md`) specifies an MCP server as the artifact management layer with CRUD operations, versioning, and query interfaces.

Source: `sam-harness.md`:82-104

---

## D. Front-Loading Pattern

### Information Captured Upfront

Stage 1 (Discovery) captures:
- Problem statement
- User identification
- Goals and anti-goals (explicit out-of-scope items)
- Functional requirements
- Non-functional requirements (performance, security, compatibility)
- References and examples
- Open questions (resolved with user)
- Additional contextual notes

Source: `stateless-software-engineering-framework.md`:323-357

The `process_realignment.md` extends this with a structured goal hierarchy:

> "Desired outcome (end state/value) -> Objectives (component outcomes) -> Acceptance criteria (verification)"
> -- `process_realignment.md`:14-17

Discovery includes dispatching researcher sub-agents for:
- Online research
- Local repository discovery
- Git analysis
- Remote repository reference gathering
- Package/version documentation verification

Source: `process_realignment.md`:26-31

### Artifacts Produced During Planning

The planning phases produce a cascade of artifacts:

| Artifact | Stage | Content |
|----------|-------|---------|
| `ARTIFACT:DISCOVERY(SCOPE:...)` | Stage 1 | Requirements, NFRs, goals, references |
| `ARTIFACT:PRD(SCOPE:...)` | Stage 2 | Project requirements documentation |
| `ARTIFACT:NFR(SCOPE:...)` | Stage 2 | Non-functional requirements |
| `ARTIFACT:ARCH-CONTEXT(SCOPE:...)` | Stage 2 | System context diagram (C4 L1) |
| `ARTIFACT:ARCH-CONTAINER(SCOPE:...)` | Stage 2 | Container diagram (C4 L2) |
| `ARTIFACT:ARCH-COMPONENT(SCOPE:...)` | Stage 2 | Component diagram (C4 L3) |
| `ARTIFACT:ADR(DECISION:...)` | Stage 2 | Architecture decision records |
| `ARTIFACT:PLAN(SCOPE:...)` | Stage 2 | Design guide with success criteria |
| `ARTIFACT:PLAN(SCOPE:...)` (contextualized) | Stage 3 | Plan grounded in codebase reality |
| `ARTIFACT:TASK(TASK:...)` | Stage 4 | Atomic task files with embedded context |

Source: `process_realignment.md`:49-161, `stateless-software-engineering-framework.md`:280-295

The `process_realignment.md` document specifies artifact interdependencies:

> "ARTIFACT:PRD informs all architecture artifacts; ARTIFACT:NFR constrains Solutions and Systems architecture; ARTIFACT:ARCH-CONTEXT defines scope for ARCH-CONTAINER; ARTIFACT:ARCH-CONTAINER defines boundaries for ARCH-COMPONENT; ARTIFACT:ARCH-COMPONENT drives API-SPEC and MODULE-DESIGN; All architecture artifacts referenced by ADRs for decision rationale"
> -- `process_realignment.md`:155-161

### Planning "Complete Enough" for Execution

Planning completeness is determined by the RT-ICA gate:

1. List all prerequisites for success
2. Mark each as: AVAILABLE | DERIVABLE | MISSING
3. If any are MISSING: BLOCK and request information
4. If all AVAILABLE or DERIVABLE: PROCEED

Source: `stateless-software-engineering-framework.md`:373-378

The Context Integration stage (Stage 3) further validates completeness by grounding the plan in codebase reality -- marking scope items as NEW, MODIFY, or COMPLETE and resolving conflicts before decomposition begins.

### RT-ICA Gate Mechanism

RT-ICA (Real-Time Information Completeness Assessment) is the primary quality gate between planning and execution. It operates as a precondition verification step:

```markdown
### RT-ICA Assessment
| Prerequisite | Status | Source |
|--------------|--------|--------|
| {prereq} | AVAILABLE | {where it comes from} |

Decision: APPROVED / BLOCKED
```

Source: `stateless-software-engineering-framework.md`:397-402

The gate is deterministic: if any prerequisite is MISSING, the pipeline blocks. There is no override mechanism built into the methodology -- the information must be obtained before proceeding. This is an explicit design choice to prevent the common LLM failure mode of "completing the task incorrectly rather than blocking on missing information."

Source: `stateless-software-engineering-framework.md`:94

---

## E. Unique Innovations

### 1. Stateless Agent Architecture as an LLM Failure Mode Countermeasure

SAM's central innovation is treating LLM limitations not as bugs to be fixed but as architectural constraints to be designed around. The framework explicitly maps each LLM failure mode to a structural countermeasure:

| Failure Mode | Structural Countermeasure |
|--------------|--------------------------|
| Fabrication | Grounding via artifacts + evidence requirements + permitted abstention |
| Long-context degradation | Bounded context per agent |
| Methodology skipping | Methodology IS the prompt |
| Shortcut-taking | Embedded verification (preferring external/deterministic checks) |
| Goal displacement | Forensic review validates against original goals |
| Self-confirmation bias | Independent verification agent |

Source: `stateless-software-engineering-framework.md`:848-857

This contrasts with most LLM frameworks that attempt to improve behavior through better instructions. SAM's position is that behavioral instructions are fundamentally unreliable:

> "Claude rationalizes out of following them immediately"
> -- `stateless-software-engineering-framework.md`:102 (on CLAUDE.md instructions)

### 2. Separation of Verification from Execution

Many AI coding frameworks rely on self-verification (the agent checks its own work). SAM explicitly separates execution (Stage 5) from verification (Stage 6) using independent agents with independent context. The forensic review agent does not share context with the execution agent -- it receives the execution results, the original task specification, and the plan, and performs independent fact-checking.

Source: `stateless-software-engineering-framework.md`:640-710

### 3. Storage-Agnostic Semantic Tokens

Rather than coupling to filesystem paths, SAM defines a semantic token system (`ARTIFACT:{TYPE}({SCOPE_OR_ID})`) that can be backed by any storage:

> "Any concrete filename or path should be treated as an example implementation, not the canonical representation."
> -- `stateless-software-engineering-framework.md`:150

This enables the same methodology to work with filesystem artifacts during development, SQL databases in production, or MCP servers for tool-integrated workflows.

### 4. Deterministic Backpressure as a First-Class Principle

SAM elevates the concept of running deterministic checks (build, tests, lint, security scans) from a best practice to a core architectural principle. The framework explicitly distinguishes between:

- **Outer loop**: CI, pre-commit, server-side hooks, PR checks
- **Inner loop**: The agent's local generate-check-repair cycle

Source: `stateless-software-engineering-framework.md`:128-146

The framework cites research and field perspectives supporting this distinction:

> "Rules in the context window (Cursor rules / AGENTS.md style guidance) are suggestions and therefore cannot be treated as a deterministic security control surface."
> -- `stateless-software-engineering-framework.md`:137 (citing Huntley 2025)

### 5. Comprehensive Evidence Ledger (Appendix D)

The SSE framework document includes an unusual self-auditing feature: Appendix D catalogs every empirical claim made in the document and tracks its evidence status (EMPIRICAL CLAIM / DESIGN CHOICE / TERMINOLOGY) with verification paths and external references.

This includes 26 tracked claims (A1-A26), each with:
- The exact statement
- Whether evidence is provided (YES / NO / PARTIAL)
- What would make the claim accurate
- Suggested resources to consult

Source: `stateless-software-engineering-framework.md`:976-1012

This is an explicit acknowledgment that the methodology itself must be held to the same verification standards it imposes on agents.

### 6. Community Observation Integration (Appendix F)

The framework systematically converts community observations (Reddit threads, blog posts, field reports) into structured operational claims with:
- Human-relatable explanation
- Operational claim (measurable)
- Mitigation primitive (what to do)
- Evidence links (research/benchmarks)

Source: `stateless-software-engineering-framework.md`:1038-1155

### 7. Input Deduplication and Similarity Detection

Appendix H defines a protocol for detecting when a new feature request overlaps with existing work. The Discovery Agent must:
1. Generate a candidate name/slug
2. Search existing artifacts for similar features
3. Assess semantic similarity (>70% threshold triggers user clarification)
4. Handle responses: extend existing, use as reference, or confirm separate

Source: `stateless-software-engineering-framework.md`:1220-1325

### Known Limitations and Gaps

**Noted in the framework itself**:

- Success metrics (Appendix C) are targets, not measured baselines. The framework acknowledges many claims lack quantitative evidence (Appendix D).
- The "15-60 minutes per task" heuristic is marked as a design choice requiring time-tracking validation (`stateless-software-engineering-framework.md`:997).
- Self-verification limitations are acknowledged: the forensic review mitigates but does not eliminate confirmation bias, since another LLM instance performs the review.

**From SAM Harness open questions** (`sam-harness.md`:243-252):

- Naming not finalized
- Storage backend not decided (filesystem vs SQL)
- Orchestrator design open (pure Python vs hybrid Claude orchestration)
- Task file structure not fully defined
- Parallel execution limits not specified
- Error handling for RT-ICA blocks not fully specified
- Resume/checkpoint capability not defined

**Structural limitations**:

- The pipeline assumes feature development workflows. Debugging, exploratory research, and documentation tasks may not map cleanly to the 7-stage structure.
- The framework does not specify how to handle conflicting forensic review findings (e.g., reviewer disagrees with the plan itself).
- Parallelism in execution (git worktrees) is described but the coordination mechanisms are not fully specified.
- The framework status is "Design Document" -- it has not been empirically validated at scale (`stateless-software-engineering-framework.md`:4).

---

## Summary for Autonomous Refinement System Design

SAM provides several patterns directly applicable to autonomous refinement:

1. **Front-loaded specification**: All ambiguity resolved before autonomous execution begins
2. **Artifact-based state**: Enables restart, resume, and independent verification without session continuity
3. **Independent verification loop**: Stage 6 forensic review -> Planner -> Stage 5 execution creates a convergence mechanism
4. **Deterministic backpressure**: External tool checks (tests, lint, build) provide ground truth that LLM-based review alone cannot
5. **Stateless execution**: Fresh context per task prevents error accumulation and context degradation
6. **Explicit convergence criteria**: Target metrics and Definition of Done provide measurable termination conditions

The framework's primary gap for autonomous refinement is the lack of empirical validation data and the open questions around orchestration mechanics (parallelism limits, checkpoint granularity, failure recovery protocols).
