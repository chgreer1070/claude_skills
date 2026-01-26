# Stateless Agent Methodology (SAM) Documentation

## Overview

This directory contains comprehensive documentation for the **Stateless Agent Methodology (SAM)**, a constraint-driven development framework designed to compensate for LLM limitations through architectural structure rather than behavioral instructions.

### Core Insight

**Claude is not a knowledge worker—Claude is a stateless computation engine** that happens to have noisy, stale priors baked in.

Instead of trying to make Claude "smarter," SAM treats Claude like a pure function:

- **Input**: Complete context (task file with all answers)
- **Output**: Verified result
- **No side effects**: Fresh context each time
- **No memory**: Everything externalized to artifact files

---

## Quick Navigation

### Core Documents

**[stateless-agent-methodology.md](./stateless-agent-methodology.md)** — The foundational methodology document

- The problem: Claude's fundamental limitations (context degradation, training data staleness, completion optimization)
- The architectural solution: Stateless agents, externalized memory, verification at boundaries
- The pipeline architecture (stages + orchestration loop) with detailed specifications
- Why this works: Failure mode elimination, structural enforcement
- Theoretical foundations and success metrics

**[stateless-software-engineering-framework.md](./stateless-software-engineering-framework.md)** — Expanded framework with complete specifications

- Detailed agent specifications (Discovery, Planning, Context Integration, Task Decomposition, Execution, Forensic Review, Final Verification)
- Artifact templates and output formats
- Mapping to formal methods, systems engineering, and manufacturing patterns
- Implementation roadmap with 5 phases
- Naming candidates and comparison with GSD

### Comparison Documents

These documents compare SAM to established frameworks and methodologies, identifying complementary strengths and integration opportunities.

| Document                                                                                  | Compares To                                | Focus                                                           |
| ----------------------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------- |
| [vs Task Master](./stateless-agent-methodology-vs-taskmaster.md)                          | Task Master (npm task management tool)     | Cognitive framework vs task tooling; integration potential      |
| [vs Get Shit Done](./stateless-agent-methodology-vs-get-shit-done.md)                     | GSD (Claude Code workflow)                 | Theory vs practice; shared architecture; combining strengths    |
| [vs Ralph Loop Orchestrator](./stateless-agent-methodology-vs-ralph-loop-orchestrator.md) | Ralph (orchestration framework)            | Phase decomposition vs emergent gates; different control models |
| [vs Gas Town](./stateless-agent-methodology-vs-gastown.md)                                | Gas Town (pipeline framework)              | Message passing patterns; artifact vs shared context            |
| [vs OctoCode](./stateless-agent-methodology-vs-octocode.md)                               | Octocode RDD + octocode-mcp (research platform) | Workflow reliability vs research-driven development + toolchain |
| [vs V-Model](./stateless-agent-methodology-vs-v-model.md)                                 | SDLC V-Model (systems engineering)         | Mapping to traditional verification patterns                    |
| [vs SuperClaude](./stateless-agent-methodology-vs-superclaude.md)                         | SuperClaude (cognitive framework)          | Constraint-driven vs capability-driven approaches               |
| [vs cc-sessions](./stateless-agent-methodology-vs-cc-sessions.md)                         | cc-sessions (session management framework) | Stateless execution vs session-aware architecture               |

---

## Core Concepts

### The Problem: Why LLM Agents Fail

Claude exhibits fundamental limitations that prevent reliable autonomous work:

| Limitation                       | Manifestation                              | Impact                                  |
| -------------------------------- | ------------------------------------------ | --------------------------------------- |
| **Context window degradation (“context rot”)** | Performance can degrade as context length increases (including “lost in the middle” effects) | Long tasks produce poor results         |
| **Training data staleness (knowledge cutoff)** | Facts/APIs can be outdated; priors can be stale even before formal cutoffs | Incorrect or obsolete solutions         |
| **Training data overconfidence** | Believes priors over explicit instructions | Skips verification, ignores methodology |
| **Completion optimization**      | Optimized for "appearing helpful"          | Takes shortcuts to show progress        |
| **No self-assessment**           | Cannot JIT identify knowledge gaps         | Proceeds with wrong assumptions         |
| **Goal displacement**            | Optimizes for task metrics, not success    | Disables tests, ignores lint rules      |

**Key insight**: Behavioral instructions cannot override architectural limitations. The solution must be structural, not instructional.

### The Solution: Pipeline Stages + Orchestration Loop

SAM reorganizes work into discrete stages, each with a specific agent, complete context, and independent verification:

```
┌─────────────────────────────────────────────────────┐
│  STAGE 1: DISCOVERY                                  │
│  Gather complete information through structured     │
│  discussion with user                                │
│  Output: Feature requirements, NFRs, goals          │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 2: PLANNING (RT-ICA)                          │
│  Verify prerequisites, identify gaps, design solution│
│  BLOCKS if prerequisites missing                    │
│  Output: Design guide with verified prerequisites   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 3: CONTEXT INTEGRATION                        │
│  Map plan to existing codebase, resolve conflicts   │
│  Output: Contextualized plan with file references   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 4: TASK DECOMPOSITION                         │
│  Create atomic tasks with ALL context embedded      │
│  Output: Task files (15-60 min each)                │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 5: EXECUTION (FRESH SESSION)                 │
│  Implement single task with embedded verification   │
│  Output: Implementation + verification results      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 6: FORENSIC REVIEW (INDEPENDENT)             │
│  Verify task completion independently               │
│  COMPLETE or NEEDS_WORK                             │
│  Output: Findings and verdict                       │
└─────────────────────────────────────────────────────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
              ┌─────────┐ ┌────────┐
              │COMPLETE │ │ ISSUES │
              └────┬────┘ └───┬────┘
                   │          │
                   │          ▼
                   │    Planner creates
                   │    new tasks
                   │          │
                   │          ▼
                   │    (loop back)
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 7: FINAL VERIFICATION                         │
│  Verify feature achieves original goals             │
│  Output: Feature certification                      │
└─────────────────────────────────────────────────────┘
```

### Key Design Principles

| Principle                      | Implementation                                        | Rationale                                          |
| ------------------------------ | ----------------------------------------------------- | -------------------------------------------------- |
| **Stateless agents**           | Fresh context per agent with exactly what it needs    | Eliminates context pressure and accumulated errors |
| **Externalized memory**        | All state lives in artifact files, not conversation   | Survives session resets, enables verification      |
| **Single responsibility**      | Each agent does exactly one thing                     | Reduces complexity, enables specialization         |
| **Message passing**            | Agents communicate via artifacts, not shared context  | Decouples stages, creates audit trail              |
| **Verification at boundaries** | Every stage validates previous stage's output         | Catches errors before they propagate               |
| **Deterministic backpressure** | Always run deterministic checks (tests/linters/static analysis/checklists) and treat failures as ground truth | Counters stale priors and hallucinated content with objective feedback |
| **Embedded methodology**       | The process IS the prompt, not instructions to follow | Cannot skip what structures the task               |
| **No recall required**         | Task files contain all answers needed for the task (plus verification steps) | Reduces reliance on unverified recall; does not eliminate synthesis/logic errors without verification |

### Pure Function Framing

SAM treats agents like pure functions:

```
Task File ───▶ [Stateless Agent] ───▶ Verified Result
(complete       (pure function)
 context)
  │                    │
  └────────────────────┴─── No side effects
                             No memory required
                             No training data needed
```

---

## Comparison Matrix: SAM vs Other Frameworks

Quick reference for what distinguishes SAM from other approaches:

| Framework         | Problem Addressed             | Primary Focus             | Key Differentiator                           |
| ----------------- | ----------------------------- | ------------------------- | -------------------------------------------- |
| **Task Master**   | Task management               | Tooling & persistence     | Ready-to-use CLI/MCP vs conceptual framework |
| **Get Shit Done** | Context rot & completion bias | Production workflow       | Theory vs practice; parallelism              |
| **Ralph Loop**    | Apparent completion           | Backpressure gates        | Phase decomposition vs emergent gates        |
| **Gas Town**      | Pipeline failures             | Message passing           | Complete artifact context vs shared memory   |
| **OctoCode**      | Guess-driven coding           | Research-first workflows  | RDD methodology + tools vs staged reliability constraints |
| **V-Model**       | Systems engineering           | Requirements verification | Stateless execution vs sequential phases     |
| **SuperClaude**   | Cognitive limitations         | Capability expansion      | Constraints vs capabilities                  |
| **cc-sessions**   | Session management            | Context persistence       | Stateless design vs session awareness        |

---

## Document Structure

### Core Methodology Files

1. **stateless-agent-methodology.md** (main document)

   - Problem analysis (Part 1)
   - Architectural solution (Part 2)
   - Pipeline overview (Part 3)
   - Stage specifications (Part 4)
   - Theoretical foundations (Part 6)

2. **stateless-software-engineering-framework.md** (expanded framework)
   - Executive summary
   - Problem statement with observed failures
   - Design principles and pipeline architecture
   - Detailed agent specifications with output templates
   - Mapping to formal methods and engineering disciplines
   - Implementation roadmap (5 phases)

### Comparison Documents (8 files)

Each comparison document includes:

- Executive summary with quick reference table
- Architecture comparison (stage mapping, data structures)
- Key differences between approaches
- Failure mode coverage
- Complementary strengths
- When to use each approach
- Integration recommendations

---

## Status

This is work-in-progress methodology documentation being refined and expanded. The core framework is stable; implementation details are evolving based on practical application.

### Maturity Levels

- **Core Concepts**: Stable
- **Pipeline Architecture**: Stable
- **Stage Specifications**: Refined
- **Formal Mappings**: Stable
- **Implementation Details**: Evolving
- **Comparison Analysis**: Growing
- **Integration Patterns**: Developing

---

## Key Takeaways

1. **Claude is a stateless function, not a stateful agent** — Treat it accordingly with complete context per execution unit

2. **Structure enforces methodology** — The process IS the task, not instructions to follow

3. **Externalize assessment** — Use separate agents for discovery, planning, execution, and verification

4. **Verify at boundaries** — Each stage validates the previous stage's output

5. **Fresh context per phase** — Reduces long-context degradation pressure and accumulated drift

6. **Task files contain all answers** — No recall from training data required

7. **Independent verification** — Separate forensic agent, not self-review

---

## Related Resources

For implementation patterns and practical application of these principles:

- **CLAUDE.md** in the parent repository implements some SAM patterns (verification at boundaries, structured methodology enforcement, artifact passing)
- **Get Shit Done (GSD)** provides production-ready implementation of SAM concepts
- **Ralph Loop Orchestrator** shows alternative control model using emergent gates instead of phase decomposition
- **Task Master** provides task management tooling that can work with SAM principles

---

## How to Use This Documentation

**To understand SAM concepts:**

1. Start with [stateless-agent-methodology.md](./stateless-agent-methodology.md) — read Part 1-2 for problem and solution
2. Review the pipeline overview (Part 3) and stage specifications (Part 4)

**To compare SAM to your current workflow:**

1. Find the relevant comparison document in the matrix above
2. Review "Key Differences" section
3. Check "When to Use Each" section for applicability

**To implement SAM patterns:**

1. Start with [stateless-software-engineering-framework.md](./stateless-software-engineering-framework.md)
2. Review agent specifications and output templates
3. Consult "Implementation Roadmap" section for phased approach

**To integrate SAM with existing systems:**

1. Read the relevant comparison document
2. Review "Integration Potential" or "Complementary Strengths" sections
3. Check "Recommendations" for combining both approaches

---

## Questions & Exploration

This methodology is designed to be questioned and refined. Consider:

- How do these principles apply to your current LLM workflows?
- Which failure modes are you experiencing that SAM addresses?
- How might you adapt SAM patterns to your existing tools?
- What would a hybrid approach combining SAM with your current methodology look like?

See the comparison documents for specific integration proposals with established frameworks.
