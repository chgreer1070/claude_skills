# Stateless Agent Methodology (SAM)

A constraint-driven development framework that compensates for LLM limitations through architectural structure rather than behavioral instructions.

---

This methodology has companion documentation at:

- <stateless_software_engineering_framework> @stateless-software-engineering-framework.md </stateless_software_engineering_framework>
- <sam_framework_generator> @methodology_development/sam-framework-generator.md </sam_framework_generator>

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

| Limitation                                     | Manifestation                                                                                                                                              | Impact                                  |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **Context window degradation (“context rot”)** | Performance degrades as context length increases (not just retrieval failure): more errors, weaker instruction adherence, and “lost in the middle” effects | Long tasks produce poor results         |
| **Training data staleness (knowledge cutoff)** | Each model has a fixed training cutoff; details can be outdated for fast-moving libraries/APIs unless verified against current sources                     | Incorrect or obsolete solutions         |
| **Training data overconfidence**               | Believes priors over explicit instructions                                                                                                                 | Skips verification, ignores methodology |
| **Completion optimization**                    | Optimized for "appearing helpful" over "being correct"                                                                                                     | Takes shortcuts to show progress        |
| **No self-reflective knowledge gaps**          | Cannot JIT identify what it doesn't know                                                                                                                   | Proceeds with wrong assumptions         |
| **Goal displacement**                          | Optimizes for task metrics, not actual success                                                                                                             | Disables tests, ignores lint rules      |

#### 1.1.1 Context rot: key aspects and mitigations (operational)

**Key aspects of quality reduction in long contexts:**

- **Performance degradation**: capability can drop materially as input length grows, even when the relevant evidence is present and retrievable. Source: [Context Length Alone Hurts LLM Performance Despite Perfect Retrieval (Findings EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.1264/) (accessed 2026-01-26).
- **“Lost in the Middle”**: performance is often highest when relevant info is at the beginning/end, and degrades when the relevant info is in the middle of long contexts. Source: [Lost in the Middle (arXiv:2307.03172)](https://arxiv.org/abs/2307.03172) (accessed 2026-01-26).
- **Noise / distractors**: adding irrelevant material can further reduce accuracy, but note the stronger finding above: length alone can hurt performance even without “meaningful” distractors. Source: [Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.1264/) (accessed 2026-01-26).
- **Context compaction issues (tooling)**: agentic harnesses may compact/summarize long conversations; if the compaction drops nuance/constraints, downstream work can drift. Claude Code explicitly warns that as the context window fills, Claude may “start forgetting earlier instructions or making more mistakes,” and discusses automatic compaction. Source: [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices.md) (accessed 2026-01-26). Evidence status: **PARTIAL** (tool behavior described; still validate in your own logs).

**Mitigation strategies (how SAM responds):**

- **Be concise**: prefer targeted prompts over dumping large, weakly relevant context.
- **Modularize content**: decompose work into small tasks with minimal context (“stateless function”).
- **Manage conversation state**: do not rely on long conversations; externalize state to artifacts.
- **Use tools wisely**: prefer durable artifacts, explicit gates, and deterministic backpressure over adding more “guidance text” to the context.

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
- **Closed-source codebases** - _never_ in training data
- **Rapidly evolving technologies** (month-by-month releases) - often too new to be reliably represented in training data, even before a model’s formal cutoff

Training data is adversarial to correct execution because Claude will confidently use stale/wrong priors to skip the actual work of researching current reality.

**Knowledge cutoff reference**: Anthropic publishes per-model training cutoffs; if you’re relying on post-cutoff facts, you must ground them via current sources/tools. Source: [How up-to-date is Claude's training data? (Anthropic Help Center)](https://support.anthropic.com/en/articles/8114494-how-up-to-date-is-claude-s-training-data) (accessed 2026-01-26).

**Operational implication**: In this environment, you must assume the model will “cargo-cult” training patterns (plausible defaults and familiar idioms) unless you force grounding and verification. Therefore SAM treats **linters, tests, checklists, and authoritative reference documentation** as first-class control surfaces: they are the backpressure that corrects hallucinated or cargo-cult content.

---

## Part 2: The Architectural Solution

### 2.1 Design Principles

| Principle                      | Implementation                                                                                                                                                | Rationale                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Stateless agents**           | Fresh context per agent with exactly what it needs                                                                                                            | Eliminates context pressure and accumulated errors                                                    |
| **Externalized memory**        | All state lives in artifact files, not conversation                                                                                                           | Survives session resets, enables verification                                                         |
| **Single responsibility**      | Each agent does exactly one thing                                                                                                                             | Reduces complexity, enables specialization                                                            |
| **Message passing**            | Agents communicate via artifacts, not shared context                                                                                                          | Decouples stages, creates audit trail                                                                 |
| **Verification at boundaries** | Every stage validates previous stage's output                                                                                                                 | Catches errors before they propagate                                                                  |
| **Deterministic backpressure** | Always run deterministic checks (tests, linters, static analysis, checklists) and treat failures as ground truth; iterate until passing or explicitly BLOCKED | Counters cargo-cult priors and hallucinated content with objective feedback                           |
| **Embedded methodology**       | The process IS the prompt, not instructions to follow                                                                                                         | Cannot skip what structures the task                                                                  |
| **No recall required**         | Task files contain all answers needed for the task (plus verification steps)                                                                                  | Reduces reliance on unverified recall; does not eliminate synthesis/logic errors without verification |

#### 2.1.1 Storage-agnostic semantic tokens (artifact IDs, not file paths)

SAM is intentionally storage-agnostic. Any concrete filename/path (e.g. `design-guide.md`, `task-{N}.md`, `PLAN.md`) is an example implementation, not the canonical representation. The canonical representation is a semantic identifier that can be backed by files, a database, a queue, etc.

**Core token pattern**:

```text
ARTIFACT:{TYPE}({SCOPE_OR_ID})
```

**Minimal starting set (recommended)**:

```text
SCOPE:{scope_id}

ARTIFACT:DISCOVERY(SCOPE:...)
ARTIFACT:PRD(SCOPE:...)
ARTIFACT:NFR(SCOPE:...)
ARTIFACT:ARCH(SCOPE:...)
ARTIFACT:ADR(DECISION:...)
ARTIFACT:PLAN(SCOPE:...)
ARTIFACT:TASK(TASK:...)
ARTIFACT:EXECUTION(TASK:...)
ARTIFACT:REVIEW(TASK:...)
ARTIFACT:VERIFICATION(SCOPE:...)

# Optional (often useful in practice)
ARTIFACT:FEATURE_REGISTRY(SCOPE:project)
ARTIFACT:STATE(SCOPE:...)
ARTIFACT:CONTEXT(SCOPE:...)
```

**Disambiguators (recommended)**:

```text
CTX:WINDOW | CTX:CODEBASE | CTX:CONVERSATION | CTX:INTEGRATION
PREREQ:AVAILABLE | PREREQ:DERIVABLE | PREREQ:MISSING | PREREQ:CONFIDENCE(0.0-1.0)
EXEC:SEQUENTIAL | EXEC:PARALLEL | EXEC:WAVE
VERIFY:SELF | VERIFY:BOUNDARY | VERIFY:FORENSIC | VERIFY:FINAL
```

**Workflow stance (approval + tool use)**:

- SAM avoids tool blocking and approval gates. All approval is frontloaded via explicit agreement on desired outcome + objectives + acceptance criteria. After that, progress is gated only by prerequisite completeness (`PREREQ:*`) and check outcomes (`VERIFY:*`), not by “permission to use tools”.
- For example token→filesystem/SQL mappings, see the companion framework doc: @stateless-software-engineering-framework.md

**Agent taxonomy**:

- An **agent** is any AI instance doing work and capable of using tools.
- The **assistant** is the interactive agent in the main conversation.
- A **sub-agent** is an agent invoked via the built-in `Task()` tool (isolated context, returns findings).

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
│ ARTIFACT:DISCOVERY  │  Feature requirements, NFRs, goals, references
│ (e.g. discovery-    │
│ output.md)          │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ ARTIFACT:PLAN       │  RT-ICA assessment, solution design, success criteria
│ (e.g. design-       │
│ guide.md)           │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ ARTIFACT:PLAN       │  Plan + existing code references, conflicts resolved,
│ (contextualized)    │  utilities identified, file paths mapped
│ (e.g. contextualized│
│ -plan.md)           │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ ARTIFACT:TASK       │  Atomic task with ALL context embedded:
│                     │  - Constraints, files, style, methodology
│                     │  - Self-verification steps, Definition of Done
│ (e.g. task-{N}-     │
│ {name}.md)          │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ ARTIFACT:EXECUTION  │  Implementation results, verification output
│ (e.g. execution-    │
│ results-{N}.md)     │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ ARTIFACT:REVIEW     │  Forensic findings, verdict, issues
│ (e.g. review-report-│
│ {N}.md)             │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ ARTIFACT:VERIFICATION│ Final certification against original goals
│ (e.g. feature-      │
│ certification.md)   │
└─────────────────────┘
```

---

## Part 4: Input Constraints

### 4.1 Input Identification and Uniqueness

**Constraint**: All SAM workflows MUST handle input identification with deduplication and context reuse detection.

#### Name Generation Rules

1. **If name provided explicitly**: Use as-is (must be globally unique within project)
2. **If name not provided**: Auto-generate slug from description
   - Convert to lowercase
   - Replace spaces with hyphens
   - Remove special characters (keep alphanumeric and hyphens)
   - Maximum 40 characters
   - Example: "Add Health Check Dashboard" → "add-health-check-dashboard"

#### Similarity Detection Protocol (Discovery Stage)

Before proceeding with full workflow, the Discovery Agent MUST:

**Step 1: Generate Candidate Name**

- Generate slug from description (if not provided)
- This becomes the working identifier

**Step 2: Search Existing Artifacts**
Search for similar features/goals:

- Query existing artifacts (implementation-dependent):
  - `ARTIFACT:FEATURE_REGISTRY(SCOPE:project)` (e.g. `PLAN.md`, `.claude/feature-registry.json`)
  - `ARTIFACT:ARCH(SCOPE:...)` (e.g. `architecture.md`, `plan/architect-*.md`)
  - `ARTIFACT:TASK(TASK:...)` (e.g. `plan/tasks-*.md`)

**Step 3: Assess Similarity**
For each existing artifact found:

- Compare descriptions semantically
- Check for name/slug overlap
- Identify domain concept matches (e.g., "health check" vs "health monitoring")
- Calculate similarity score (0-100%)

**Step 4: If Similarity > 70% Detected**
MUST ask clarifying questions using AskUserQuestion:

```
I found existing feature '{existing-name}' that seems similar to your request.

Existing feature includes:
- {bullet point summary of existing scope}

Questions:
1. Is your request related to the existing '{existing-name}' feature?
   Options:
   - Yes, extend it (add new capabilities to existing feature)
   - No, separate feature (independent implementation)
   - Use as reference only (learn from structure, but independent)

2. If extending:
   - Should I modify the existing architecture spec?
   - Should I create a new feature that depends on it?
```

**Step 5: Handle User Response**

| Response             | Action                                                                                                                                                                                                                                               |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Extend existing**  | Load existing artifacts as input context:<br/>- Read existing architecture spec<br/>- Read existing task files<br/>- Plan incremental changes<br/>- Update artifacts (don't create new ones)<br/>- Add note in discovery: "Extends: {existing-name}" |
| **Use as reference** | Proceed with new feature:<br/>- Note reference in Feature Requirements<br/>- Copy applicable patterns<br/>- Ensure name uniqueness<br/>- Add note: "References: {existing-name}"                                                                     |
| **Separate feature** | Proceed independently:<br/>- Ensure name uniqueness (append suffix if needed)<br/>- No explicit linkage<br/>- Add note: "Similarity noted but confirmed separate"                                                                                    |

#### Uniqueness Enforcement

- Names MUST be unique within project scope
- If conflict detected after similarity check:
  - Append numeric suffix: `{base-name}-2`, `{base-name}-3`
  - Warn user: "Name conflict detected. Using '{resolved-name}' instead."
- Track all names in a central registry (recommended: `ARTIFACT:FEATURE_REGISTRY(SCOPE:project)` (e.g. `PLAN.md`, `.claude/feature-registry.json`))

#### Discovery Output Extension

The `ARTIFACT:DISCOVERY(SCOPE:...)` MUST include (e.g. `discovery-output.md`):

```markdown
## Feature Identification

- **Name**: {unique-slug}
- **Description**: {full description}
- **Similarity Assessment**:
  - Similar features checked: {count}
  - Matches found: {list of similar features with scores}
  - User decision: {extend | reference | separate}

## Related Features

- **Extends**: {feature-name} (if extending existing)
  - Existing artifacts loaded: {list}
  - Incremental changes planned: {summary}

- **References**: {feature-name} (if using as reference)
  - Patterns to follow: {list}
  - Structure to emulate: {summary}

- **None** (if confirmed separate)
  - Uniqueness verified: Yes
  - Name conflicts resolved: {if any}
```

---

## Part 5: Stage Specifications

### Stage 1: Discovery

**Purpose**: Gather complete information through structured discussion with user, with similarity detection and deduplication.

**Agent**: Discovery Agent

**Input**: User's initial request or problem statement (with optional explicit name)

**Process**:

1. **Generate/validate name** (see Input Constraints 4.1)
2. **Search for similar existing features** (similarity detection protocol)
3. **Ask clarifying questions** (including similarity resolution if needed)
4. Identify the problem domain
5. Gather references and examples
6. Document non-functional requirements
7. Capture explicit goals and anti-goals (out of scope)

**Output**: `ARTIFACT:DISCOVERY(SCOPE:...)` (e.g. `discovery-output.md`)

- Feature identification (name, description, similarity assessment)
- Related features (extends/references/none)
- Feature requirements
- Non-functional requirements
- Goals and anti-goals
- References and examples
- Resolved questions

**Success Criteria**:

- User confirms document accurately captures their intent
- Name uniqueness verified
- Similarity assessment complete (if applicable)

---

### Stage 2: Planning (RT-ICA)

**Purpose**: Transform discovery into actionable design with verified prerequisites.

**Agent**: Planning Agent

**Input**: `ARTIFACT:DISCOVERY(SCOPE:...)` (e.g. `discovery-output.md`)

**Process**:

1. **RT-ICA Assessment** (Reverse Thinking - Information Completeness Assessment):
   - List all prerequisites for success
   - Mark each: AVAILABLE | DERIVABLE | MISSING
   - **If MISSING: BLOCK and request information**
   - If all AVAILABLE/DERIVABLE: PROCEED
2. Solution design with success criteria
3. Risk assessment

**Output**: `ARTIFACT:PLAN(SCOPE:...)` (e.g. `design-guide.md`)

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

**Input**: `ARTIFACT:PLAN(SCOPE:...)` + codebase access (e.g. `design-guide.md`)

**Process**:

1. Review plan against existing codebase
2. Identify what already exists (NEW | MODIFY | COMPLETE)
3. Find conflicts, contradictions, technical constraints
4. Map existing systems, methodologies, utilities to reuse
5. Add concrete file/URL references to plan

**Output**: `ARTIFACT:PLAN(SCOPE:...)` (e.g. `contextualized-plan.md`)

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

**Input**: `ARTIFACT:PLAN(SCOPE:...)` (e.g. `contextualized-plan.md`)

**Process**:

1. Decompose into atomic tasks (15-60 min each)
2. Order by TDD pattern:
   - Interface tasks first
   - Test tasks second
   - Implementation tasks third
   - Integration tasks last
3. Embed ALL context into each task file

**Output**: `ARTIFACT:TASK(TASK:...)` for each task (e.g. `task-{N}-{name}.md`)

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

**Input**: Single `ARTIFACT:TASK(TASK:...)` (AS THE COMPLETE PROMPT) (e.g. `task-{N}-{name}.md`)

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

**Output**: Implementation + `ARTIFACT:EXECUTION(TASK:...)` (e.g. `execution-results-{N}.md`)

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

- `ARTIFACT:EXECUTION(TASK:...)` (e.g. `execution-results-{N}.md`)
- `ARTIFACT:TASK(TASK:...)` (e.g. `task-{N}-{name}.md`)
- `ARTIFACT:PLAN(SCOPE:...)` (e.g. `contextualized-plan.md`)

**Process**:

1. Completion verification (results vs requirements)
2. Quality assessment (standards, patterns, tests)
3. Fact-check (verify claims, confirm file changes)
4. Determination: COMPLETE or NEEDS_WORK

**Output**: `ARTIFACT:REVIEW(TASK:...)` (e.g. `review-report-{N}.md`)

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

- `ARTIFACT:DISCOVERY(SCOPE:...)` (original goals) (e.g. `discovery-output.md`)
- All `ARTIFACT:REVIEW(TASK:...)` artifacts (e.g. `review-report-{N}.md`)
- `ARTIFACT:PLAN(SCOPE:...)` (e.g. `contextualized-plan.md`)

**Process**:

1. Each original goal → evidence of completion
2. Each acceptance criterion → test result
3. Feature-level Definition of Done → verification

**Output**: `ARTIFACT:VERIFICATION(SCOPE:...)` (e.g. `feature-certification.md`)

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

| Anti-Pattern                  | Why It Fails                                            | SAM Approach                  |
| ----------------------------- | ------------------------------------------------------- | ----------------------------- |
| **One agent does everything** | Context pressure, no verification                       | Pipeline with specialists     |
| **Trust Claude's memory**     | Memory is unreliable                                    | Externalize to artifact files |
| **Behavioral instructions**   | Claude rationalizes out                                 | Structural enforcement        |
| **Self-verification only**    | Confirmation bias                                       | Independent forensic review   |
| **Skip prerequisites**        | Garbage in, garbage out                                 | RT-ICA gate blocks            |
| **Large context tasks**       | Long-context degradation / “lost in the middle” effects | Small, focused tasks          |
| **Implicit methodology**      | Gets skipped                                            | Methodology IS the prompt     |
| **Assume training data**      | Stale, wrong, hallucinated                              | Provide all context in task   |

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
