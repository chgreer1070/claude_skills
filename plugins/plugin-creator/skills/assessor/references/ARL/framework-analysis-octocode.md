# Framework Analysis: OctoCode MCP - Research Driven Development

**Repository**: `/home/ubuntulinuxqa2/repos/octocode-mcp/`
**Primary Documents Analyzed**: MANIFEST.md, AGENTS.md, README.md, all SKILL.md files (8 skills), docs/DEVELOPMENT_GUIDE.md, docs/CONFIGURATION_REFERENCE.md, packages/octocode-shared/docs/SESSION_PERSISTENCE.md
**Analysis Date**: 2026-02-13

---

## A. System Overview

### What Is This System?

OctoCode is a methodology, MCP server, and skill ecosystem that transforms how AI agents interact with codebases. It implements **Research Driven Development (RDD)** -- a formalized approach that forces AI to gather evidence and validate context before writing any code.

The system has three layers:

1. **OctoCode MCP Server** (`packages/octocode-mcp/`) -- An MCP server providing GitHub API tools, local filesystem tools, and LSP (Language Server Protocol) intelligence. This is the "eyes and hands" that give AI semantic understanding of code.

2. **OctoCode Skills** (`skills/`, `packages/octocode-cli/skills/`) -- Markdown-based instruction sets that turn AI agents into specialized roles (researcher, planner, implementer, reviewer, etc.). Eight skills total.

3. **OctoCode CLI** (`packages/octocode-cli/`) -- A command-line installer and skills marketplace for setting up the MCP server and distributing skills.

Source: README.md:16 -- "Octocode is not just a tool; it's a methodology and a platform that transforms how AI interacts with code."

### Core Philosophy

> "Code is Truth, but Context is the Map."
> -- MANIFEST.md:16

RDD prioritizes **evidence gathering** and **context validation** before any code is written. The core equation:

```
RDD = (Static Context + Dynamic Context) x Validation x epsilon
```

Where:
- **Static Context** = the actual code on disk (local tools, LSP)
- **Dynamic Context** = external knowledge, patterns, history (GitHub API)
- **Validation** = cross-referencing against reality
- **epsilon** = a quality factor

Source: MANIFEST.md:29-34

### Target Audience and Use Case

AI agents working on codebases -- particularly Claude Code, Cursor, and similar AI development environments. The system is designed to prevent AI "guessing" based on training data by forcing it to research actual code before acting.

---

## B. Autonomous Development Model

### How It Front-Loads Human Effort

OctoCode uses a **checkpoint-gated** model rather than requiring upfront specification documents. The human effort is front-loaded at specific decision points:

1. **Initial request** -- the user states what they want
2. **Plan approval** -- user reviews the research plan before execution
3. **Implementation approval** -- user approves the plan before coding begins
4. **Fix selection** -- user picks which issues to address (in review/roast flows)

Between checkpoints, the system operates autonomously. The key insight is that OctoCode front-loads *research*, not human specification. The human provides direction; the AI does the investigation work.

Source: `skills/octocode-plan/SKILL.md:202-205` -- "Triple Lock: MUST wait for explicit user approval before Phase 3 / FORBIDDEN: Proceeding to Implement without approval / REQUIRED: Verify user approved plan before any code edits"

### The Workflow Pipeline

OctoCode defines a GAN-inspired adversarial workflow with 6 stages, drawn from MANIFEST.md:39-81:

```
Stage 0: INIT RESEARCH    (Researcher agent gathers initial context)
Stage 1: PLAN              (Planner/Generator creates plan.md)
Stage 2: VERIFY PLAN       (Verifier/Discriminator critiques the plan)
Stage 3: RESEARCH          (Researcher gathers implementation context)
Stage 4: VALIDATE RESEARCH (Verifier ensures evidence is sufficient)
Stage 5: IMPLEMENT         (Coder executes using plan + research)
Stage 6: VALIDATE CODE     (Verifier runs tests, checks against research)
```

Each stage uses a **fresh context window** -- the output of one stage becomes the input for the next. This is explicitly designed to prevent context pollution.

Source: MANIFEST.md:244-249 -- "Each flow (Plan, Research, Implement) is executed by a separate agent or session to adhere to this principle."

### Concrete Skill Flows

Each skill implements a subset of this pipeline:

| Skill | Flow | Source |
|-------|------|--------|
| `octocode-research` | INIT → CONTEXT → FAST-PATH → PLAN → RESEARCH → OUTPUT | `skills/octocode-research/SKILL.md:21-30` |
| `octocode-plan` | UNDERSTAND → RESEARCH → PLAN → IMPLEMENT → VERIFY | `skills/octocode-plan/SKILL.md:9` |
| `octocode-implement` | SPEC → SPEC_VALIDATE → CONTEXT → PLAN → RESEARCH → IMPLEMENT → VALIDATE | `packages/octocode-cli/skills/octocode-implement/SKILL.md:9` |
| `octocode-pr-review` | GUIDELINES → CONTEXT → CHECKPOINT → ANALYSIS → FINALIZE → REPORT | `skills/octocode-pull-request-reviewer/SKILL.md:232-250` |
| `octocode-documentation-writer` | DISCOVERY → QUESTIONS → RESEARCH → ORCHESTRATE → WRITE → QA | `skills/octocode-documentation-writer/SKILL.md:8` |
| `octocode-local-search` | DISCOVER → PLAN → EXECUTE → VERIFY → OUTPUT | `skills/octocode-local-search/SKILL.md:9` |

### Human Decision Points vs Automated Decision Points

**Human decision points** (explicit user approval required):
- Plan approval before research execution (`octocode-research/SKILL.md:324-327`)
- Plan approval before implementation (`octocode-plan/SKILL.md:202-205`)
- Focus area selection during PR review (`octocode-pull-request-reviewer/SKILL.md:440-443`)
- Fix selection during roast (`octocode-roast/SKILL.md:210-237`)
- Scope/depth/focus during local search (`octocode-local-search/SKILL.md:244-252`)

**Automated decision points** (agent decides without user):
- Fast-path evaluation (simple lookup vs full planning) (`octocode-research/SKILL.md:236-259`)
- Parallel vs sequential execution based on domain count (`octocode-research/SKILL.md:336-350`)
- Tool selection based on hints from previous tool results
- Error recovery strategy (broaden, retry, backtrack)
- Review mode selection (Quick vs Full) based on file count and risk (`octocode-pull-request-reviewer/SKILL.md:46-53`)

### Scope Handling

OctoCode handles scope through a combination of:

1. **Fast-path evaluation** -- Simple queries (single-point lookup, unambiguous target) skip the planning phase entirely. Source: `octocode-research/SKILL.md:240-259`

2. **Goal classification** -- The plan skill classifies tasks as RESEARCH_ONLY, ANALYSIS, CREATION, FEATURE, BUG, or REFACTOR, determining how much of the pipeline to execute. Source: `octocode-plan/SKILL.md:139-142`

3. **Dynamic scaling** -- The documentation writer scales agent count based on question volume (1-8 parallel writers). Source: `octocode-documentation-writer/SKILL.md:248-252`

4. **Complexity assessment** -- Quick, Medium, or Thorough classification at the start of planning. Source: `octocode-plan/SKILL.md:143`

---

## C. Key Concepts and Mechanisms

### Named Concepts

**Agents/Roles** (from MANIFEST.md:56-81):
- **Researcher** -- Gathers context using MCP tools. The "eyes" of the system.
- **Planner (Generator)** -- Creates plans based on research. One half of the GAN pair.
- **Verifier (Discriminator)** -- Critiques outputs adversarially. The other half.
- **Coder** -- Implements based on plan + research artifacts.
- **Orchestrator** -- Coordinates parallel agents and assigns file ownership (documentation writer flow).

**Artifacts**:
- `plan.md` -- Implementation plan with research questions (output of planning stage)
- `research.md` -- Evidence-backed findings with file:line citations (output of research stage)
- `context.md` -- User preferences and project context (persistent across sessions)
- `session.json` -- Session state including checkpoints (output of state management)
- `analysis.json`, `questions.json`, `research.json`, `work-assignments.json` -- Pipeline artifacts in the documentation writer flow

**Stages**: The 6-stage adversarial pipeline (see Section B above).

**Key Technical Concepts**:
- **Vibe-Research** -- The intuitive flow state where AI researches code seamlessly. Source: MANIFEST.md:19
- **Smart Research** -- Automated evidence-based forensics. Source: MANIFEST.md:22-23
- **Context Pillars** -- Static (code on disk) + Dynamic (external knowledge) + RDD Data (session artifacts). Source: MANIFEST.md:198-211
- **Hints** -- Tool responses include `hints` arrays that guide the agent to the next action. Following hints is mandatory. Source: `octocode-research/SKILL.md:438-450`

### State Management Across Agent Handoffs

OctoCode manages state through **file-based artifact passing**:

1. Each stage writes its output to a file (plan.md, research.md, etc.)
2. The next stage reads those files as input
3. Context windows are intentionally kept fresh -- each agent/session gets minimal context

For the documentation writer pipeline, this is formalized with JSON artifacts:
```
analysis.json → questions.json → research.json → work-assignments.json → documentation/*.md
```

Source: `octocode-documentation-writer/SKILL.md:72`

For parallel agent coordination, agents write to domain-specific files:
```
.octocode/research/{session-id}/domain-{DOMAIN_NAME}.md
```

Source: `skills/octocode-research/references/PARALLEL_AGENT_PROTOCOL.md:38`

Session persistence is handled by `octocode-shared`'s session module with deferred writes, in-memory caching, and atomic file operations. Source: `packages/octocode-shared/docs/SESSION_PERSISTENCE.md:7-8`

### Quality Gates and Verification

OctoCode uses a **gate pattern** throughout all skills. Every phase transition has:

1. **Pre-Conditions** -- Checklist of what must be true before entering
2. **Gate Check** -- Verification checklist before proceeding to next phase
3. **FORBIDDEN** -- Explicit list of prohibited actions at this stage
4. **ALLOWED** -- Explicit list of permitted actions
5. **On Failure** -- IF/THEN recovery rules

Example from `octocode-research/SKILL.md:141-163`:
```
<context_gate>
**STOP. DO NOT call any research tools yet.**

### Pre-Conditions
- [ ] Server returned "ok" in Phase 1

### Context Loading Checklist (MANDATORY - Complete ALL steps)
...
### FORBIDDEN Until Context Loaded
- Any research tools

### ALLOWED During Context Loading
- `curl` commands to localhost:1987
...
</context_gate>
```

The **Triple Lock** pattern is used for critical rules:
1. STATE: "You MUST X"
2. FORBID: "FORBIDDEN: Not doing X"
3. REQUIRE: "REQUIRED: Verify X complete"

Source: `octocode-prompt-optimizer/SKILL.md:303-308`

### Convergence (Knowing When "Done")

The research skill defines explicit **completion triggers** with precedence:

| Priority | Trigger | Evidence |
|----------|---------|----------|
| 1 (highest) | Goal achieved | Answer found with file:line refs |
| 2 | User satisfied | User says "enough" or "looks good" |
| 3 | Scope complete | All planned domains/files explored |
| 4 (lowest) | Stuck (exhausted) | Multiple recovery attempts failed |

Source: `octocode-research/SKILL.md:519-533`

For implementation, convergence is defined by validation gates:
- TypeScript compiles
- Linter passes
- Tests pass
- Each spec requirement verified with code evidence

Source: `octocode-implement/SKILL.md:136-139`

For the documentation writer, convergence is a QA score:
- Excellent (>=90), Good (>=75), Fair (>=60), Needs Improvement (<60)

Source: `octocode-documentation-writer/SKILL.md:493-494`

### Error Handling, Failures, and Recovery

Every skill includes explicit error recovery tables. Common patterns:

| Error Type | Recovery | Source |
|------------|----------|--------|
| Empty results | Broaden pattern, try semantic variants | `octocode-research/SKILL.md:473` |
| Timeout | Reduce scope/depth | `octocode-research/SKILL.md:474` |
| Rate limit | Back off, batch fewer queries | `octocode-research/SKILL.md:475` |
| Dead end | Backtrack, try alternate approach | `octocode-research/SKILL.md:476` |
| Looping | STOP, re-read hints, ask user | `octocode-research/SKILL.md:477` |
| Conflicting sources | Find authoritative source, ask user | `octocode-plan/SKILL.md:297` |
| Build fails | Fix error, re-verify loop | `octocode-plan/SKILL.md:298` |
| Blocked >2 attempts | Summarize attempts, ask user | `octocode-plan/SKILL.md:300` |

The documentation writer has a retry system with partial data preservation:
- Retry config per phase (2-3 max attempts with exponential backoff)
- Partial results saved to `partials/<phase>/<task_id>.json`
- Atomic writes using temp file + rename pattern
- Failed parallel agents retried individually
- State preserved via `state.json` for resume capability

Source: `octocode-documentation-writer/SKILL.md:604-793`

---

## D. Front-Loading Pattern

### Information Captured Upfront

Before autonomous execution, OctoCode captures:

1. **User intent** -- What the user wants to accomplish (natural language request)
2. **Project context** -- `.octocode/context/context.md` with user preferences (checked at start of every skill)
3. **Tool schemas** -- The `initContext` endpoint returns all available tool schemas, which the agent must parse before any tool call
4. **Prompt selection** -- Based on user intent, a specific prompt template is loaded (research, research_local, reviewPR, plan, roast)
5. **Scope classification** -- Goal type, complexity level, risk assessment
6. **Existing state** -- Resume from previous session if state.json exists

Source: `octocode-research/SKILL.md:149-153`, `octocode-plan/SKILL.md:132-149`

### Artifacts Produced During Planning

| Artifact | Content | When Produced |
|----------|---------|---------------|
| Research plan | Structured plan with tool → goal mapping | Phase 3 of research skill |
| Task list | TaskCreate entries tracking each research question | During planning |
| `plan.md` | Implementation plan with steps, file paths, risk areas | Plan skill Phase 2 |
| `research.md` | Evidence-backed findings from research skills | Plan skill Phase 1 |
| `context.md` | User preferences and project conventions | Persistent, updated per session |

The plan must follow a specific format:
```
## Research Plan
**Goal:** [User's question]
**Strategy:** [Sequential / Parallel]
**Steps:**
1. [Tool] → [Specific Goal]
2. [Tool] → [Specific Goal]
...
**Estimated scope:** [files/repos to explore]

Proceed? (yes/no)
```

Source: `octocode-research/SKILL.md:296-306`

### When Planning is "Complete Enough"

OctoCode defines two paths:

1. **Fast-Path** -- Planning is skipped entirely when ALL criteria are true:
   - Single-point lookup
   - One file/location expected
   - Few tool calls needed
   - Target is unambiguous

   Source: `octocode-research/SKILL.md:244-248`

2. **Full Planning** -- Planning is complete when:
   - User explicitly approves the plan (mandatory gate)
   - All research domains identified
   - Parallel vs sequential strategy determined
   - Tasks created via TaskCreate

   Source: `octocode-research/SKILL.md:320-331`

The plan skill adds additional completion criteria:
- All questions answered with confidence levels documented
- References complete
- Research findings presented to user in TL;DR format

Source: `octocode-plan/SKILL.md:283-287`

---

## E. Unique Innovations

### 1. GAN-Inspired Adversarial Validation

The most distinctive mechanism is borrowing from Generative Adversarial Networks:

> "Similar to a GAN, the Verifier (Discriminator) tries to find flaws in the Generator's output. Generator's Goal: Produce output so good the Verifier cannot find faults. Verifier's Goal: Find any discrepancy between the output and the 'Truth' (Codebase/Context). This tension forces quality up without manual user intervention at every micro-step."
> -- MANIFEST.md:117-120

The framework even suggests **cross-model validation** (using different LLMs for Generator vs Discriminator to eliminate shared blind spots). Source: MANIFEST.md:123

**Assessment**: This is described in the MANIFEST but only partially implemented in the skills. The skills define Generator-side flows (plan, research, implement) with user-as-verifier checkpoints. A dedicated Verifier skill that adversarially reviews plans and research does not exist as a separate skill in the repository. The verification is instead built into phase gates within each skill.

### 2. Hint-Driven Tool Chaining

OctoCode tools return `hints` arrays that tell the agent what to do next. Following hints is mandatory:

> "MANDATORY: You MUST understand hints and think how they can help with research."
> -- `octocode-research/SKILL.md:439`

This creates a feedback loop where the tooling itself guides the agent's research path, rather than the agent deciding independently. The hint system includes:
- Next tool suggestions
- Pagination guidance
- Refinement needs
- Error recovery guidance

Source: `octocode-research/SKILL.md:438-450`

### 3. Fresh Context Window Per Stage

Each stage operates with a deliberately clean context window. The output of one stage is a file artifact that becomes the only input for the next stage:

> "Each action operates with a fresh context window, utilizing only the output of the previous action as its input."
> -- MANIFEST.md:343

This prevents "context pollution" where irrelevant information from previous attempts confuses the model. It is grounded in the observation that transformers have a "Lost in the Middle" attention phenomenon.

Source: MANIFEST.md:295-298

### 4. LSP-First Research Flow with Mandatory lineHint

OctoCode enforces a strict tool ordering for code navigation:

```
localSearchCode (get lineHint) → lspGotoDefinition → lspFindReferences/lspCallHierarchy → localGetFileContent (LAST)
```

The `lineHint` parameter is REQUIRED for all LSP tools, and it can only come from `localSearchCode` results. This prevents the agent from guessing code locations.

Source: `octocode-local-search/SKILL.md:146-152` -- "Triple Lock: 1. STATE: You MUST call localSearchCode first to obtain lineHint before any LSP tool / 2. FORBIDDEN: Calling lspGotoDefinition, lspFindReferences, or lspCallHierarchy without lineHint / 3. REQUIRED: Verify lineHint present before every LSP call"

### 5. Exclusive File Ownership for Parallel Agents

The documentation writer solves parallel write conflicts by assigning exclusive file ownership:

> "Each writer owns EXCLUSIVE files - no conflicts possible"
> -- `octocode-documentation-writer/SKILL.md:255`

The Orchestrator agent (Phase 4) groups questions by file target and assigns ownership, so multiple writer agents can run in parallel without race conditions.

### 6. FORBIDDEN Thinking Pattern

Several skills include "Red Flags" sections that prohibit specific thought patterns:

| Forbidden thought | Required action | Source |
|-------------------|-----------------|--------|
| "I assume it works like..." | MUST find evidence in code | `octocode-local-search/SKILL.md:423` |
| "It's probably in src/utils..." | MUST search first | `octocode-local-search/SKILL.md:424` |
| "I'll call lspGotoDefinition directly..." | MUST call localSearchCode first | `octocode-local-search/SKILL.md:425` |
| "I'll read the file to understand..." | MUST use LSP tools first | `octocode-local-search/SKILL.md:426` |
| "I'll just use grep..." | MUST use localSearchCode | `octocode-local-search/SKILL.md:427` |

This is a meta-cognitive enforcement pattern -- it attempts to catch and redirect the agent's reasoning before it takes incorrect action.

### 7. Prompt Optimizer as a Meta-Skill

The `octocode-prompt-optimizer` skill is unique -- it is a skill that optimizes other skills. It uses a gated 6-step flow (READ → UNDERSTAND → RATE → FIX → VALIDATE → OUTPUT) with:
- Weak word detection and replacement
- Command strength hierarchy (NEVER/ALWAYS/MUST > STOP/HALT > REQUIRED > should/prefer)
- Triple Lock pattern enforcement
- Bloat prevention (<10% line count increase required)

Source: `octocode-prompt-optimizer/SKILL.md:1-607`

### 8. Structural Code Vision

OctoCode encourages agents to "think like a parser" -- visualizing the AST rather than reading code linearly:

> "See the Tree: Visualize AST. Root (Entry) → Nodes (Funcs/Classes) → Edges (Imports/Calls)"
> -- `octocode-local-search/SKILL.md:195`

This is paired with the "Text narrows → Symbols identify → Graphs explain" golden rule for research flow.

Source: `octocode-local-search/SKILL.md:141`

### Known Limitations and Gaps

1. **Verifier skill not implemented as standalone** -- The GAN-inspired adversarial model describes a Verifier agent, but verification is embedded in phase gates rather than being a separate adversarial agent. Cross-model validation is proposed but not implemented.

2. **No persistent learning across sessions** -- While session.json tracks statistics, there is no mechanism for the system to learn from previous research sessions or improve its approach over time. Each session starts fresh except for user preferences in context.md.

3. **MCP server dependency** -- The research and local-search skills depend on the OctoCode MCP server being running on localhost:1987. Without it, no research tools are available. Source: `octocode-research/SKILL.md:62-63`

4. **No automated testing of skills** -- Skills are markdown instruction sets without automated verification that they produce correct behavior. The prompt optimizer provides manual optimization, but there is no CI/CD-like testing of skill quality.

5. **Latency vs Quality tradeoff acknowledged but incompletely solved** -- MANIFEST.md:43-48 describes Fast-Path and Deep-Research modes, but the determination of which path to use relies on heuristic criteria evaluated by the agent itself, which could lead to inconsistent path selection.

6. **Parallel agent coordination is file-based** -- No message-passing or event system between parallel agents. They write to files and are merged after completion. This limits real-time coordination and error propagation.

7. **Documentation writer is the most complex skill** (~830 lines of SKILL.md) and approaches the limits of what can be reliably followed as a prompt instruction set. The retry logic and state management are described in pseudocode within the skill file.

---

## Summary of Key Patterns for Autonomous Refinement

| Pattern | OctoCode Implementation | Applicability to ARL |
|---------|------------------------|---------------------|
| Adversarial validation | GAN-inspired Generator/Verifier | Core pattern for quality assessment loops |
| Fresh context windows | Artifact-based stage handoff | Prevents context pollution in multi-stage refinement |
| Hint-driven tool chaining | Tool responses guide next action | Could drive assessment criteria selection |
| Mandatory evidence | file:line citations required for all claims | Assessment criteria must cite specific evidence |
| Phase gates with FORBIDDEN/ALLOWED | Triple Lock on critical transitions | Prevents premature advancement in refinement loop |
| Completion triggers with precedence | Goal achieved > User satisfied > Scope complete > Stuck | Defines when refinement loop should terminate |
| Fast-path evaluation | Skip planning for simple tasks | Scope-appropriate refinement depth |
| Exclusive file ownership | Parallel agents assigned non-overlapping domains | Prevents conflicts in parallel assessment |
| FORBIDDEN thinking | Meta-cognitive pattern interception | Could prevent assessment shortcuts |
| Prompt optimization meta-skill | Skill that optimizes other skills | Self-improving assessment criteria |
