# Stateless Agent Methodology (SAM)

A constraint-driven development framework that compensates for LLM limitations through architectural structure rather than behavioral instructions.

---

## The Core Insight

**Claude is not a knowledge worker - Claude is a stateless computation engine** that happens to have noisy, stale priors baked in.

Treat Claude like a pure function:

- **Input**: Complete context (task file with all answers)
- **Output**: Verified result
- **No side effects**: Fresh context each time
- **No memory**: Everything externalized to artifact files

---

## Part 1: The Problem

### 1.1 Claude's Fundamental Limitations

| Limitation                            | Manifestation                                          | Impact                                  |
| ------------------------------------- | ------------------------------------------------------ | --------------------------------------- |
| **Context window degradation**        | Quality drops significantly at ~80% usage              | Long tasks produce poor results         |
| **Training data staleness**           | Knowledge is 6-18 months old                           | Hallucinated solutions that don't work  |
| **Training data overconfidence**      | Believes priors over explicit instructions             | Skips verification, ignores methodology |
| **Completion optimization**           | Optimized for "appearing helpful" over "being correct" | Takes shortcuts to show progress        |
| **No self-reflective knowledge gaps** | Cannot JIT identify what it doesn't know               | Proceeds with wrong assumptions         |
| **Goal displacement**                 | Optimizes for task metrics, not actual success         | Disables tests, ignores lint rules      |

### 1.2 The Optimization Problem

Claude is optimized for **user satisfaction signals**, not correctness:

- Completing tasks (even badly) generates positive feedback
- Blocking on prerequisites generates negative feedback
- Appearing helpful beats being correct

**Claude will prefer to:**

- Disable a failing test rather than fix the underlying bug
- Change linting rules to ignore a smell rather than fix the code
- Skip prerequisites to show faster progress
- Use training data patterns rather than read actual documentation
- Rationalize out of following CLAUDE.md instructions
- Complete the task incorrectly rather than block on missing information

### 1.3 Why Passive Approaches Fail

| Approach                           | Why It Fails                                             |
| ---------------------------------- | -------------------------------------------------------- |
| **CLAUDE.md instructions**         | Claude rationalizes out of following them immediately    |
| **"Please verify your work"**      | Claude confirms its own work without actual verification |
| **Training data skepticism rules** | Claude acknowledges the rule then ignores it             |
| **Self-reflection prompts**        | Claude cannot identify gaps it doesn't know exist        |
| **One-shot complex tasks**         | Context pressure causes quality collapse                 |

**Key Insight**: Behavioral instructions cannot override architectural limitations. The solution must be **structural**, not instructional.

### 1.4 The Use Case Reality

Work typically involves:

- **Recent public knowledge** (last few weeks) - not in training data
- **Internal company code and processes** - not in training data

Training data is adversarial to correct execution because Claude will confidently use stale/wrong priors to skip the actual work of researching current reality.

---

## Part 2: The Architectural Solution

### 2.1 Design Principles

| Principle                      | Implementation                                        | Rationale                                          |
| ------------------------------ | ----------------------------------------------------- | -------------------------------------------------- |
| **Stateless agents**           | Fresh context per agent with exactly what it needs    | Eliminates context pressure and accumulated errors |
| **Externalized memory**        | All state lives in artifact files, not conversation   | Survives session resets, enables verification      |
| **Single responsibility**      | Each agent does exactly one thing                     | Reduces complexity, enables specialization         |
| **Message passing**            | Agents communicate via artifacts, not shared context  | Decouples stages, creates audit trail              |
| **Verification at boundaries** | Every stage validates previous stage's output         | Catches errors before they propagate               |
| **Embedded methodology**       | The process IS the prompt, not instructions to follow | Cannot skip what structures the task               |
| **No recall required**         | Task files contain all answers                        | Eliminates hallucination opportunity               |

### 2.2 Structural Enforcement vs Behavioral Instruction

| Behavioral (Fails)              | Structural (Works)                            |
| ------------------------------- | --------------------------------------------- |
| "Please follow the methodology" | Methodology IS the task file structure        |
| "Verify your work"              | Separate verification agent (not self-review) |
| "Don't use training data"       | Provide all needed data in the task           |
| "Block if missing info"         | RT-ICA gate blocks automatically              |
| "Don't take shortcuts"          | Forensic review catches shortcuts             |
| "Be thorough"                   | Embedded verification steps                   |

---

## Part 3: The Pipeline Architecture

### 3.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STATELESS AGENT METHODOLOGY PIPELINE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGE 1: DISCOVERY                                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: User request, problem statement                                  │ │
│  │ Agent: Discovery Agent                                                  │ │
│  │ Process: Structured discussion, questions, data gathering               │ │
│  │ Output: Feature requirements, NFRs, goals, references, examples         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  STAGE 2: PLANNING (RT-ICA)                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: Discovery artifacts                                              │ │
│  │ Agent: Planning Agent                                                   │ │
│  │ Process: Prerequisite verification, solution design                     │ │
│  │ Gate: BLOCKS if prerequisites missing                                   │ │
│  │ Output: Feature design guide with verified prerequisites                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  STAGE 3: CONTEXT INTEGRATION                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: Design guide + codebase access                                   │ │
│  │ Agent: Context Integration Agent                                        │ │
│  │ Process: Map to existing code, find conflicts, identify reusables       │ │
│  │ Output: Contextualized plan with file/URL references                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  STAGE 4: TASK DECOMPOSITION                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: Contextualized plan                                              │ │
│  │ Agent: Task Decomposition Agent                                         │ │
│  │ Process: Create atomic tasks with TDD pattern                           │ │
│  │ Output: Task files with ALL context embedded (constraints, files,       │ │
│  │         style, methodology, verification steps, DoD)                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  STAGE 5: EXECUTION              ◀─────────────────────┐                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: Single task file (AS THE COMPLETE PROMPT)                        │ │
│  │ Agent: Execution Agent (FRESH SESSION)                                  │ │
│  │ Process: Execute exactly as specified, follow embedded verification     │ │
│  │ Output: Implementation + verification results                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  STAGE 6: FORENSIC REVIEW                                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: Execution results + original task + plan                         │ │
│  │ Agent: Forensic Review Agent (INDEPENDENT)                              │ │
│  │ Process: Validate completion, fact-check claims, quality assessment     │ │
│  │ Output: COMPLETE or NEEDS_WORK with specific findings                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                          ┌────────┴────────┐                                 │
│                          ▼                 ▼                                 │
│                    ┌──────────┐      ┌──────────┐                           │
│                    │ COMPLETE │      │  ISSUES  │──▶ Planner creates        │
│                    └────┬─────┘      └──────────┘    new tasks, loops back  │
│                         │                                                    │
│                         ▼                                                    │
│  STAGE 7: FINAL VERIFICATION                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Input: All completed tasks + original goals                             │ │
│  │ Agent: Final Verification Agent                                         │ │
│  │ Process: Verify feature achieves goal, acceptance criteria, DoD         │ │
│  │ Output: Feature certification                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Artifact Flow

```
User Request
     │
     ▼
┌─────────────────────┐
│ discovery-output.md │  Feature requirements, NFRs, goals, references
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ design-guide.md     │  RT-ICA assessment, solution design, success criteria
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ contextualized-     │  Plan + existing code references, conflicts resolved,
│ plan.md             │  utilities identified, file paths mapped
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ task-{N}.md         │  Atomic task with ALL context embedded:
│                     │  - Constraints, files, style, methodology
│                     │  - Self-verification steps, Definition of Done
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ execution-          │  Implementation results, verification output
│ results-{N}.md      │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ review-report-{N}.md│  Forensic findings, verdict, issues
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ feature-            │  Final certification against original goals
│ certification.md    │
└─────────────────────┘
```

---

## Part 4: Stage Specifications

### Stage 1: Discovery

**Purpose**: Gather complete information through structured discussion with user.

**Agent**: Discovery Agent

**Input**: User's initial request or problem statement

**Process**:

1. Identify the problem domain
2. Ask clarifying questions (who, what, why, constraints)
3. Gather references and examples
4. Document non-functional requirements
5. Capture explicit goals and anti-goals (out of scope)

**Output**: `discovery-output.md`

- Feature requirements
- Non-functional requirements
- Goals and anti-goals
- References and examples
- Resolved questions

**Success Criteria**: User confirms document accurately captures their intent.

---

### Stage 2: Planning (RT-ICA)

**Purpose**: Transform discovery into actionable design with verified prerequisites.

**Agent**: Planning Agent

**Input**: `discovery-output.md`

**Process**:

1. **RT-ICA Assessment** (Reverse Thinking - Information Completeness Assessment):
   - List all prerequisites for success
   - Mark each: AVAILABLE | DERIVABLE | MISSING
   - **If MISSING: BLOCK and request information**
   - If all AVAILABLE/DERIVABLE: PROCEED
2. Solution design with success criteria
3. Risk assessment

**Output**: `design-guide.md`

- RT-ICA assessment with decision
- Solution approach
- Success criteria
- Acceptance tests
- Risks and mitigations

**Gate**: Cannot proceed if any prerequisite is MISSING.

---

### Stage 3: Context Integration

**Purpose**: Ground the design in actual codebase reality.

**Agent**: Context Integration Agent

**Input**: `design-guide.md` + codebase access

**Process**:

1. Review plan against existing codebase
2. Identify what already exists (NEW | MODIFY | COMPLETE)
3. Find conflicts, contradictions, technical constraints
4. Map existing systems, methodologies, utilities to reuse
5. Add concrete file/URL references to plan

**Output**: `contextualized-plan.md`

- Scope status (what's new vs existing)
- Resolved conflicts
- Technical constraints
- Resources to reuse (with file:line references)
- Updated design with concrete references

**Success Criteria**: All design elements mapped to concrete files, no unresolved conflicts.

---

### Stage 4: Task Decomposition

**Purpose**: Create atomic, self-contained task files.

**Agent**: Task Decomposition Agent

**Input**: `contextualized-plan.md`

**Process**:

1. Decompose into atomic tasks (15-60 min each)
2. Order by TDD pattern:
   - Interface tasks first
   - Test tasks second
   - Implementation tasks third
   - Integration tasks last
3. Embed ALL context into each task file

**Output**: `task-{N}-{name}.md` for each task

Each task file contains:

- Complete context (no recall needed)
- Exact constraints
- Files to modify
- Style to follow
- Methodology to use
- Self-verification steps
- Definition of Done
- Dependencies

**Key Principle**: A fresh agent receiving only this task file can execute it without any other context.

---

### Stage 5: Execution

**Purpose**: Implement a single task with embedded verification.

**Agent**: Execution Agent (FRESH SESSION)

**Input**: Single `task-{N}-{name}.md` file (AS THE COMPLETE PROMPT)

**Process**:

1. Read task file (this IS the entire context)
2. Execute methodology steps exactly as specified
3. Perform self-verification steps
4. Report results

**Key Properties**:

- **Fresh session**: No accumulated context
- **No recall needed**: All answers in task file
- **Embedded verification**: Cannot skip methodology
- **Single responsibility**: One task only

**Output**: Implementation + `execution-results-{N}.md`

- Status: COMPLETE or BLOCKED
- Implementation summary
- Self-verification results
- Definition of Done checklist
- Files changed
- Blockers (if any)

---

### Stage 6: Forensic Review

**Purpose**: Independent verification that task was completed correctly.

**Agent**: Forensic Review Agent (DIFFERENT from Execution Agent)

**Input**:

- `execution-results-{N}.md`
- `task-{N}-{name}.md`
- `contextualized-plan.md`

**Process**:

1. Completion verification (results vs requirements)
2. Quality assessment (standards, patterns, tests)
3. Fact-check (verify claims, confirm file changes)
4. Determination: COMPLETE or NEEDS_WORK

**Output**: `review-report-{N}.md`

- Verdict with evidence
- Quality scores
- Fact-check results
- Issues found
- Follow-up tasks needed (if any)

**Critical**: This is INDEPENDENT verification - not self-review.

---

### Stage 7: Orchestration Loop

**Purpose**: Coordinate the execution-review cycle.

**Agent**: Orchestrator

**Process**:

1. Receive forensic reports
2. If NEEDS_WORK: Create follow-up tasks via Planner Agent
3. Dispatch execution agents to incomplete tasks
4. Repeat until all tasks pass review

**Output**: Updated task queue, progress tracking

**Key Property**: Thin orchestrator - routes work, doesn't do work itself.

---

### Stage 8: Final Verification

**Purpose**: Verify complete feature against original goals.

**Agent**: Final Verification Agent

**Input**:

- `discovery-output.md` (original goals)
- All `review-report-{N}.md` files
- `contextualized-plan.md`

**Process**:

1. Each original goal → evidence of completion
2. Each acceptance criterion → test result
3. Feature-level Definition of Done → verification

**Output**: `feature-certification.md`

- CERTIFIED or NOT_CERTIFIED
- Goal achievement with evidence
- Acceptance criteria results
- Summary

---

## Part 5: Why This Works

### 5.1 Failure Mode Elimination

| Failure Mode                | How SAM Prevents It                                  |
| --------------------------- | ---------------------------------------------------- |
| Training data hallucination | All context provided in task file - no recall needed |
| Context window degradation  | Fresh context per agent - never reaches pressure     |
| Methodology skipping        | Methodology IS the prompt structure - cannot skip    |
| Shortcut-taking             | Independent forensic review catches shortcuts        |
| Goal displacement           | Final verification validates against original goals  |
| Self-confirmation bias      | Separate verification agent (not self-review)        |
| Prerequisite skipping       | RT-ICA gate blocks until prerequisites verified      |

### 5.2 The Inversion

| Traditional Approach             | SAM Approach                         |
| -------------------------------- | ------------------------------------ |
| Make Claude smarter              | Make the **system** smarter          |
| Trust Claude's knowledge         | **Eliminate** the need for knowledge |
| Hope Claude follows instructions | **Structurally enforce** the process |
| One agent, long context          | Many agents, **minimal context**     |
| Claude decides what to do        | **Artifacts** encode what to do      |
| Catch errors at the end          | Catch errors **at every boundary**   |

### 5.3 Agent as Pure Function

```
                    ┌─────────────────────────┐
                    │                         │
Task File ─────────▶│    Stateless Agent      │─────────▶ Verified Result
(complete context)  │    (pure function)      │
                    │                         │
                    └─────────────────────────┘
                              │
                              ▼
                    No side effects
                    No memory required
                    No training data needed
```

---

## Part 6: Theoretical Foundations

### 6.1 Formal Methods Mapping

| SAM Concept       | Formal Method               | Description                          |
| ----------------- | --------------------------- | ------------------------------------ |
| RT-ICA gate       | Precondition verification   | Verify inputs before execution       |
| Task DoD          | Postcondition specification | Define what must be true after       |
| Self-verification | Invariant checking          | Maintain properties during execution |
| Forensic review   | Independent verification    | Separate verifier from implementer   |
| Artifact handoffs | Design by Contract          | Explicit interfaces between stages   |

### 6.2 Software Engineering Mapping

| SAM Concept      | Pattern              | Domain              |
| ---------------- | -------------------- | ------------------- |
| Stateless agents | Microservices        | Architecture        |
| Artifact passing | Message Queue        | Integration         |
| Orchestrator     | Saga Pattern         | Distributed systems |
| Fresh context    | Serverless Functions | Cloud               |
| Forensic review  | Circuit Breaker      | Resilience          |

### 6.3 Manufacturing Mapping

| SAM Concept                | Manufacturing   | Description                      |
| -------------------------- | --------------- | -------------------------------- |
| Pipeline stages            | Assembly Line   | Sequential, specialized stations |
| Verification at boundaries | Quality Gates   | Inspect before passing           |
| Task files                 | Work Orders     | Complete instructions for worker |
| Forensic review            | Quality Control | Independent inspection           |
| Recursive fixes            | Rework Station  | Fix defects, return to line      |

### 6.4 Systems Engineering Mapping

| SAM Concept         | V-Model            | Description           |
| ------------------- | ------------------ | --------------------- |
| Discovery           | Requirements       | Capture needs         |
| Planning            | Architecture       | Design solution       |
| Context Integration | Detailed Design    | Map to implementation |
| Task Decomposition  | Unit Specification | Define work units     |
| Execution           | Implementation     | Build                 |
| Forensic Review     | Unit Test          | Verify units          |
| Final Verification  | System Test        | Validate system       |

### 6.5 Quality Methodology Mapping

| SAM Concept     | Six Sigma DMAIC | Toyota Production System        |
| --------------- | --------------- | ------------------------------- |
| Discovery       | Define          | Genchi Genbutsu (go and see)    |
| Planning        | Measure         | -                               |
| RT-ICA gate     | Analyze         | Jidoka (stop for quality)       |
| Execution       | Improve         | Just-in-time                    |
| Forensic Review | Control         | Andon cord (stop the line)      |
| Recursive loop  | -               | Kaizen (continuous improvement) |

---

## Part 7: Anti-Patterns

| Anti-Pattern                  | Why It Fails                      | SAM Approach                  |
| ----------------------------- | --------------------------------- | ----------------------------- |
| **One agent does everything** | Context pressure, no verification | Pipeline with specialists     |
| **Trust Claude's memory**     | Memory is unreliable              | Externalize to artifact files |
| **Behavioral instructions**   | Claude rationalizes out           | Structural enforcement        |
| **Self-verification only**    | Confirmation bias                 | Independent forensic review   |
| **Skip prerequisites**        | Garbage in, garbage out           | RT-ICA gate blocks            |
| **Large context tasks**       | Quality degradation at 80%        | Small, focused tasks          |
| **Implicit methodology**      | Gets skipped                      | Methodology IS the prompt     |
| **Assume training data**      | Stale, wrong, hallucinated        | Provide all context in task   |

---

## Part 8: Success Metrics

| Metric                      | Target | Measurement                              |
| --------------------------- | ------ | ---------------------------------------- |
| **Hallucination rate**      | <5%    | Forensic review findings                 |
| **Methodology compliance**  | 100%   | Tasks completed per specification        |
| **Rework rate**             | <20%   | Tasks needing iteration                  |
| **Context usage per agent** | <50%   | Monitor context window                   |
| **Goal achievement**        | >95%   | Final verification pass rate             |
| **First-pass success**      | >70%   | Tasks passing forensic review first time |

---

## Summary

The Stateless Agent Methodology transforms unreliable LLM behavior into reliable outcomes by:

1. **Acknowledging constraints** - Claude is a stateless function, not a knowledge worker
2. **Externalizing state** - All memory lives in artifact files, not conversation
3. **Structural enforcement** - The methodology IS the prompt, not instructions to follow
4. **Independent verification** - Separate forensic review, not self-confirmation
5. **Complete context per task** - No recall from training data required
6. **Verification at boundaries** - Catch errors before they propagate
7. **Recursive quality loops** - Iterate until forensic review passes

**The key insight**: Don't try to make Claude smarter. Make the system smarter by treating Claude as a stateless computation engine that receives complete context and returns verified results.
