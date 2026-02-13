# Framework Analysis: Get-Shit-Done (GSD)

Repository: `/home/ubuntulinuxqa2/repos/get-shit-done/`
Analyzed: 2026-02-13
Source: GitHub — glittercowboy/get-shit-done (MIT License)

---

## A. System Overview

### What This System Is

GSD is a meta-prompting and context engineering system for Claude Code (also supporting OpenCode and Gemini CLI). It packages slash commands, agent definitions, workflow scripts, templates, and a Node.js CLI tool into a coherent development pipeline.

> "A light-weight and powerful meta-prompting, context engineering and spec-driven development system for Claude Code"
> — `README.md:5`

The system positions itself as the antithesis of enterprise project management. It targets solo developers and small teams who use AI coding assistants as their primary implementer.

> "Other spec-driven development tools exist; BMAD, Speckit... But they all seem to make things way more complicated than they need to be (sprint ceremonies, story points, stakeholder syncs, retrospectives, Jira workflows)"
> — `README.md:51`

### Core Problem: Context Rot

GSD's primary innovation is solving **context rot** — the quality degradation that happens as Claude fills its context window. The README states this explicitly at line 8:

> "Solves context rot — the quality degradation that happens as Claude fills its context window."

The solution is to keep the orchestrator lean (10-15% context usage) and give each executor agent a fresh 200k-token context window. This is documented in the planner agent's philosophy:

> "Plans should complete within ~50% context. More plans, smaller scope, consistent quality. Each plan: 2-3 tasks max."
> — `agents/gsd-planner.md:83`

The quality degradation curve is explicitly modeled:

| Context Usage | Quality | Claude's State |
|---|---|---|
| 0-30% | PEAK | Thorough, comprehensive |
| 30-50% | GOOD | Confident, solid work |
| 50-70% | DEGRADING | Efficiency mode begins |
| 70%+ | POOR | Rushed, minimal |

Source: `agents/gsd-planner.md:77-83`

### Target Audience

Solo developers and small teams who describe what they want built and expect AI to implement it. The philosophy is explicit:

> "User = visionary/product owner, Claude = builder"
> — `agents/gsd-planner.md:63`

---

## B. Autonomous Development Model

### How It Front-Loads Human Effort

GSD front-loads human effort at two points:

1. **Project initialization** (`/gsd:new-project`) — Deep questioning to capture vision, research, requirements, and roadmap
2. **Phase discussion** (`/gsd:discuss-phase`) — Gray area identification and decision capture before each phase

After these points, execution is designed to be autonomous (with optional verification checkpoints).

The new-project workflow at `workflows/new-project.md:89-130` conducts deep questioning:

> "Based on what they said, ask follow-up questions that dig into their response. Use AskUserQuestion with options that probe what they mentioned — interpretations, clarifications, concrete examples."

> "Keep following threads. Each answer opens new threads to explore. Ask about: What excited them, What problem sparked this, What they mean by vague terms, What it would actually look like, What's already decided"

### The Pipeline: Stages, Phases, Gates

GSD operates on a **milestone > phase > plan > task** hierarchy:

```
Milestone (e.g., v1.0 MVP)
  └── Phase 1: Authentication
  │     ├── Plan 01-01: Login endpoint (Wave 1)
  │     │     ├── Task 1: Create route handler
  │     │     ├── Task 2: Add JWT generation
  │     │     └── Task 3: Write tests
  │     └── Plan 01-02: Registration (Wave 1, parallel)
  │           ├── Task 1: Create signup endpoint
  │           └── Task 2: Email verification
  └── Phase 2: Core Features
        └── ...
```

The core loop is: **discuss -> plan -> execute -> verify** per phase.

Source: `README.md:291-308`

**Full command pipeline with artifacts:**

| Stage | Command | Creates | Human Decision Point |
|---|---|---|---|
| Initialize | `/gsd:new-project` | PROJECT.md, config.json, research/, REQUIREMENTS.md, ROADMAP.md, STATE.md | Idea description, feature scoping, roadmap approval |
| Discuss | `/gsd:discuss-phase N` | {phase}-CONTEXT.md | Gray area decisions, scope boundaries |
| Plan | `/gsd:plan-phase N` | {phase}-RESEARCH.md, {phase}-N-PLAN.md | None (auto, with optional checker loop) |
| Execute | `/gsd:execute-phase N` | Code + commits, {phase}-N-SUMMARY.md, {phase}-VERIFICATION.md | Checkpoint tasks only |
| Verify | `/gsd:verify-work N` | {phase}-UAT.md, fix plans | Pass/fail per test item |
| Complete | `/gsd:complete-milestone` | Milestone archive, git tag | Confirmation |

### Human vs Automated Decision Points

**Human decisions required at:**
- Project initialization (what to build, feature scoping, roadmap approval)
- Phase discussion (implementation preferences, gray areas)
- Checkpoint tasks during execution (visual verification, auth credentials, architectural decisions)
- User acceptance testing (does the feature actually work as expected)

**Automated decisions (no human involvement):**
- Research (spawns 4 parallel researchers)
- Planning (spawns planner, plan-checker iterates up to 3 times)
- Execution (spawns executor agents per plan, wave-based parallelism)
- Verification (spawns verifier agent, checks code against goals)
- Deviation handling (Rules 1-3 auto-fix bugs, missing critical functionality, blockers)
- Gap diagnosis (spawns parallel debug agents)
- Gap closure planning (spawns planner in gaps mode)

### Scope Handling: Small Tasks to Large Projects

GSD handles scope through two mechanisms:

**Full pipeline** (large scope): `/gsd:new-project` -> discuss -> plan -> execute -> verify per phase, then `/gsd:complete-milestone` -> `/gsd:new-milestone` for next version.

**Quick mode** (small scope): `/gsd:quick` provides the same guarantees (atomic commits, state tracking) with a shorter path — spawns planner + executor, skips research/checker/verifier. Quick tasks live in `.planning/quick/` separate from planned phases.

Source: `commands/gsd/quick.md:16-23`, `workflows/quick.md:1-3`

**Depth configuration** controls planning granularity (`config.json`):
- `quick`: 3-5 phases, 1-3 plans each
- `standard`: 5-8 phases, 3-5 plans each
- `comprehensive`: 8-12 phases, 5-10 plans each

Source: `workflows/new-project.md:237-241`

### Milestones and Progress Tracking

State is maintained in `STATE.md` — a living file kept under 100 lines that serves as project memory:

> "STATE.md is the project's short-term memory spanning all phases and sessions."
> — `templates/state.md:78`

Progress tracking includes:
- Visual progress bar: `Progress: [████░░░░░░] 40%`
- Performance metrics (total plans completed, average duration, per-phase breakdown, trend)
- Session continuity (last session timestamp, stopped-at description, resume file path)

Source: `templates/state.md:17-74`

Milestone completion (`/gsd:complete-milestone`) archives the milestone to `.planning/milestones/`, tags the git release, clears REQUIREMENTS.md for the next milestone, and performs a full PROJECT.md evolution review.

Source: `workflows/complete-milestone.md:1-35`

---

## C. Key Concepts and Mechanisms

### Named Concepts

**Agents** (11 total, defined in `agents/`):

| Agent | Role | Spawned By |
|---|---|---|
| `gsd-planner` | Creates executable PLAN.md files with task breakdown, dependency analysis, goal-backward verification | `/gsd:plan-phase` |
| `gsd-executor` | Executes plans with atomic commits, deviation handling, checkpoint protocols | `/gsd:execute-phase` |
| `gsd-verifier` | Goal-backward verification — checks codebase delivers what phase promised | `/gsd:execute-phase` |
| `gsd-plan-checker` | Verifies plans will achieve phase goal before execution | `/gsd:plan-phase` |
| `gsd-phase-researcher` | Researches phase implementation domain, produces RESEARCH.md | `/gsd:plan-phase` |
| `gsd-project-researcher` | Researches project domain (stack, features, architecture, pitfalls) | `/gsd:new-project` |
| `gsd-research-synthesizer` | Synthesizes research outputs into SUMMARY.md | `/gsd:new-project` |
| `gsd-roadmapper` | Creates roadmaps with phase breakdown and requirement mapping | `/gsd:new-project` |
| `gsd-codebase-mapper` | Explores existing codebase and writes analysis documents | `/gsd:map-codebase` |
| `gsd-debugger` | Systematic debugging with persistent state | `/gsd:debug`, verify-work diagnosis |
| `gsd-integration-checker` | Checks integration between components | Execution verification |

**Key Artifacts:**

| Artifact | Purpose | Size Constraint |
|---|---|---|
| `PROJECT.md` | Project vision, requirements, decisions — always loaded | None specified |
| `STATE.md` | Living project memory, position tracking | Under 100 lines |
| `ROADMAP.md` | Phase structure with requirement mappings and success criteria | Constant-size (archives old milestones) |
| `REQUIREMENTS.md` | Scoped requirements with REQ-IDs and traceability | Milestone-scoped (cleared per milestone) |
| `CONTEXT.md` | Per-phase user decisions from discuss-phase | Per phase |
| `RESEARCH.md` | Per-phase research findings | Per phase |
| `PLAN.md` | Executable plan with XML-structured tasks | 2-3 tasks per plan (targets <50% context) |
| `SUMMARY.md` | Post-execution report with deviations and metrics | Per plan |
| `VERIFICATION.md` | Goal-backward verification results | Per phase |
| `UAT.md` | User acceptance test results with gap tracking | Per phase |
| `config.json` | Workflow preferences (mode, depth, model profile, agents) | Static |

**Workflows** (31 files in `workflows/`): Detailed step-by-step orchestration scripts that commands reference via `@~/.claude/get-shit-done/workflows/`.

**gsd-tools.js** (161KB, `get-shit-done/bin/gsd-tools.js`): Central Node.js CLI utility replacing repetitive bash patterns. Handles config parsing, model resolution, phase lookup, git commits, summary verification, frontmatter CRUD, scaffolding, state management, and validation.

### State Management Across Agent Handoffs

GSD manages state through **file-based persistence** — every agent reads from and writes to `.planning/` files. The handoff chain works as follows:

1. **Orchestrator loads state** via `gsd-tools.js init <command>` which returns JSON with all context
2. **Orchestrator passes context to agent** as inline text in the Task prompt (not file references, since `@` syntax doesn't work across Task boundaries)
3. **Agent reads additional files** as needed (plans, research, etc.)
4. **Agent writes results** to `.planning/` files (PLAN.md, SUMMARY.md, etc.)
5. **Agent updates STATE.md** via `gsd-tools.js state` commands
6. **Orchestrator reads results** from files after agent completes

Source: `workflows/plan-phase.md:135-146` (explicit note about `@` syntax limitation)

For mid-plan interruptions, GSD uses `.continue-here.md` files that capture exact position, completed work, remaining work, decisions, blockers, and mental context.

Source: `workflows/pause-work.md:37-83`

### Quality Gates and Verification

GSD implements verification at three levels:

**1. Plan verification (pre-execution):**
The `gsd-plan-checker` agent verifies plans will achieve phase goals across 5 dimensions:
- Requirement coverage
- Task completeness (Files + Action + Verify + Done)
- Dependency correctness
- Context compliance (honoring CONTEXT.md decisions)
- Context budget (will plans complete within ~50% context)

Iterates with planner up to 3 times: plan -> check -> revise -> check -> revise -> check.

Source: `agents/gsd-plan-checker.md:42-61`, `workflows/plan-phase.md:269-319`

**2. Phase verification (post-execution):**
The `gsd-verifier` agent uses goal-backward analysis:

> "Task completion =/= Goal achievement. A task 'create chat component' can be marked complete when the component is a placeholder."
> — `agents/gsd-verifier.md:17-19`

Three-level verification:
1. **Truths** — What must be TRUE for the goal to be achieved?
2. **Artifacts** — What must EXIST for those truths to hold?
3. **Key links** — What must be WIRED for those artifacts to function?

Source: `agents/gsd-verifier.md:22-27`

**3. User acceptance testing (manual):**
`/gsd:verify-work` presents testable deliverables one at a time, records pass/fail/issues, infers severity, and if issues found: spawns parallel debug agents -> diagnoses root causes -> creates fix plans -> verifies fix plans.

Source: `workflows/verify-work.md:1-570`

### Convergence: Knowing When "Done"

GSD defines "done" through goal-backward verification at multiple levels:

- **Task done**: Explicit `<done>` criteria in PLAN.md (e.g., "Valid credentials return 200 + JWT cookie, invalid credentials return 401")
- **Plan done**: All tasks complete + verification checks pass + SUMMARY.md created with self-check
- **Phase done**: Verifier confirms phase goal achieved (not just tasks completed) + optional UAT passes
- **Milestone done**: All phases complete + `/gsd:audit-milestone` passes + `/gsd:complete-milestone` archives

The self-check mechanism in executors verifies claims:

> "After writing SUMMARY.md, verify claims before proceeding. Check created files exist. Check commits exist. Append result: ## Self-Check: PASSED or ## Self-Check: FAILED"
> — `agents/gsd-executor.md:307-323`

### Error, Failure, and Recovery Handling

**Deviation rules** (during execution) are tiered by severity:

| Rule | Trigger | Action | Permission |
|---|---|---|---|
| Rule 1: Bug | Broken behavior, errors, type errors | Fix inline, test, track | Auto |
| Rule 2: Missing Critical | Missing error handling, validation, auth | Add, test, track | Auto |
| Rule 3: Blocking | Missing deps, wrong types, broken imports | Fix blocker, track | Auto |
| Rule 4: Architectural | New DB table, schema change, switching libs | STOP, present decision | Ask user |

Source: `agents/gsd-executor.md:84-139`, `workflows/execute-plan.md:171-201`

**Execution failure handling:**
- Agent fails mid-plan: Report, ask user "Retry?" or "Continue with remaining waves?"
- Dependency chain breaks: Wave 1 fails -> Wave 2 dependents likely fail -> user chooses
- All agents in wave fail: Systemic issue -> stop, report for investigation

Source: `workflows/execute-phase.md:326-332`

**Known Claude Code bug handling:**
GSD explicitly handles the `classifyHandoffIfNeeded` bug where agents report "failed" but the work was actually completed. Spot-checks (SUMMARY exists, commits present) determine real vs false failure.

Source: `workflows/execute-phase.md:165`, `workflows/execute-plan.md:115-116`

**Session recovery:**
- `/gsd:pause-work` creates `.continue-here.md` with full state
- `/gsd:resume-work` loads state and incomplete work, offers resume or restart
- Re-running `/gsd:execute-phase` discovers completed SUMMARYs and skips them

Source: `workflows/pause-work.md`, `workflows/resume-project.md`, `workflows/execute-phase.md:334-338`

### Parallel Execution of Tasks

GSD uses **wave-based parallelism**:

1. Plans declare dependencies via `depends_on` in frontmatter
2. `gsd-tools.js phase-plan-index` groups plans into waves
3. Plans within a wave execute in parallel (each spawned as a separate Task with fresh context)
4. Waves execute sequentially (Wave 2 depends on Wave 1 completing)

Source: `workflows/execute-phase.md:56-72`

Configuration controls:
- `parallelization.enabled`: true/false
- `parallelization.max_concurrent_agents`: 3 (default)
- `parallelization.min_plans_for_parallel`: 2

Source: `templates/config.json:13-19`

---

## D. Front-Loading Pattern

### Information Captured Upfront

**During `/gsd:new-project`:**

1. **Deep questioning** — Freeform conversation about the idea, goals, constraints, tech preferences, edge cases. Uses techniques from `references/questioning.md` to challenge vagueness, make abstract concrete, surface assumptions.

2. **Workflow configuration** — Mode (yolo/interactive), depth (quick/standard/comprehensive), parallelization, git tracking, model profile, workflow agents (research/plan-checker/verifier).

3. **Domain research** — 4 parallel researchers investigate stack, features, architecture, pitfalls. Produces research files in `.planning/research/`.

4. **Requirement scoping** — Features categorized as table stakes vs differentiators, scoped into v1/v2/out-of-scope with REQ-IDs.

5. **Roadmap** — Phases derived from requirements, 100% coverage validated, success criteria derived via goal-backward thinking.

**During `/gsd:discuss-phase`:**

Domain-specific gray areas identified and resolved. The system analyzes what kind of thing is being built and generates phase-specific questions:

> "Something users SEE -> layout, density, interactions, states. Something users CALL -> responses, errors, auth, versioning. Something users RUN -> output format, flags, modes, error handling."
> — `commands/gsd/discuss-phase.md:58-62`

Captured decisions are classified as:
- **Locked** (from `## Decisions`) — Non-negotiable, must be implemented exactly
- **Claude's Discretion** — Freedom areas for the AI to choose approach
- **Deferred Ideas** — Out of scope, captured but not acted on

Source: `workflows/discuss-phase.md:28-47`

### Artifacts Produced During Planning

| Phase | Artifacts | Purpose |
|---|---|---|
| Initialization | `PROJECT.md` | Full project context, vision, constraints |
| Initialization | `config.json` | Workflow preferences |
| Initialization | `research/STACK.md` | Technology stack recommendations |
| Initialization | `research/FEATURES.md` | Feature categorization (table stakes/differentiators) |
| Initialization | `research/ARCHITECTURE.md` | System structure patterns |
| Initialization | `research/PITFALLS.md` | Common mistakes and prevention |
| Initialization | `research/SUMMARY.md` | Synthesized key findings |
| Initialization | `REQUIREMENTS.md` | Scoped v1/v2 requirements with REQ-IDs |
| Initialization | `ROADMAP.md` | Phase structure with requirement mappings |
| Initialization | `STATE.md` | Project memory |
| Per-Phase | `{phase}-CONTEXT.md` | User decisions from discuss-phase |
| Per-Phase | `{phase}-RESEARCH.md` | Phase-specific research findings |
| Per-Phase | `{phase}-N-PLAN.md` | Executable plans with XML tasks |

### Planning Completion Criteria

Planning is "complete enough" when:

1. The planner has created PLAN.md files with valid frontmatter, XML tasks, verification criteria, and must_haves
2. The plan-checker has verified plans against 5 dimensions and returned `VERIFICATION PASSED` (or user overrides after max 3 iterations)
3. Every phase requirement has covering tasks
4. Dependencies are correctly identified and waves assigned

The plan-checker acts as the gate. If it finds issues, plans loop back to the planner for revision. After 3 iterations, the user decides: force proceed, provide guidance, or abandon.

Source: `workflows/plan-phase.md:269-319`

### The New-Project -> Plan-Phase -> Execute-Phase Pipeline

**Step 1: `/gsd:new-project`**
1. Brownfield detection (existing code -> offer `/gsd:map-codebase`)
2. Deep questioning until PROJECT.md can be written
3. Workflow preferences (8 questions across 2 rounds)
4. Optional domain research (4 parallel agents)
5. Requirement scoping (per-category multi-select)
6. Roadmap creation (spawns `gsd-roadmapper` agent)
7. User approval of roadmap

Source: `workflows/new-project.md:36-958`

**Step 2: `/gsd:discuss-phase N` (optional but recommended)**
1. Analyze phase to identify gray areas
2. Present gray areas for user selection
3. Deep-dive each selected area (4 questions per area)
4. Write CONTEXT.md with locked decisions, discretion areas, deferred ideas

Source: `workflows/discuss-phase.md`

**Step 3: `/gsd:plan-phase N`**
1. Initialize and parse arguments
2. Phase research (spawns `gsd-phase-researcher`)
3. Planning (spawns `gsd-planner`)
4. Verification loop (spawns `gsd-plan-checker`, up to 3 iterations)

Source: `workflows/plan-phase.md`

**Step 4: `/gsd:execute-phase N`**
1. Discover plans, analyze dependencies, group into waves
2. Execute waves (parallel within wave, sequential across waves)
3. Each plan gets a fresh executor agent with 200k context
4. Handle checkpoints (human-verify, decision, human-action)
5. Phase verification (spawns `gsd-verifier`)
6. Update roadmap and state

Source: `workflows/execute-phase.md`

---

## E. Unique Innovations

### 1. Context Window as First-Class Constraint

GSD treats the context window as the fundamental constraint of AI development, not just a technical limitation. Every design decision flows from this:

- Plans are sized to complete within ~50% context
- Orchestrators stay at 10-15% context
- Each executor gets fresh 200k context
- The quality degradation curve is explicitly modeled and referenced
- Context budget is a verification dimension in plan checking

This is not an afterthought — it is the core design principle.

### 2. Plans-As-Prompts

PLAN.md files are not documents that get converted into prompts — they ARE the prompts. XML-structured tasks with explicit files, actions, verification criteria, and done conditions:

```xml
<task type="auto">
  <name>Create login endpoint</name>
  <files>src/app/api/auth/login/route.ts</files>
  <action>
    Use jose for JWT (not jsonwebtoken - CommonJS issues).
    Validate credentials against users table.
    Return httpOnly cookie on success.
  </action>
  <verify>curl -X POST localhost:3000/api/auth/login returns 200 + Set-Cookie</verify>
  <done>Valid credentials return cookie, invalid return 401</done>
</task>
```

Source: `README.md:363-374`

This eliminates the interpretation step between planning and execution.

### 3. Goal-Backward Verification

Both the plan-checker (pre-execution) and verifier (post-execution) use goal-backward analysis rather than task-forward checking:

> "Task completion =/= Goal achievement"
> — `agents/gsd-verifier.md:17`

The methodology works backwards from the desired outcome:
1. What must be TRUE for the goal to be achieved?
2. What must EXIST for those truths to hold?
3. What must be WIRED for those artifacts to function?

This catches stub implementations that technically complete tasks without achieving goals.

### 4. Tiered Deviation Rules

Rather than treating all unexpected situations as errors, GSD categorizes them into 4 tiers with different authority levels (3 auto-fix, 1 requires human). This enables autonomous execution while preventing architectural drift.

Source: `agents/gsd-executor.md:84-139`

### 5. Discuss-Phase as Decision Capture

The `/gsd:discuss-phase` command creates a structured contract between human and AI:
- **Locked decisions** — AI must implement exactly as specified
- **Claude's Discretion** — AI chooses approach
- **Deferred ideas** — Explicitly out of scope (captured, not lost)

This prevents the common failure mode where AI second-guesses user preferences or adds unrequested features.

### 6. Brownfield Support via Codebase Mapping

`/gsd:map-codebase` spawns 4 parallel agents to analyze existing codebases across tech stack, architecture, conventions, and concerns. This produces 7 analysis documents consumed by planners and executors, enabling GSD to work on existing projects — not just greenfield.

Source: `agents/gsd-codebase-mapper.md:1-51`

### 7. gsd-tools.js as Centralized State Engine

A single 161KB Node.js CLI replaces repetitive bash patterns across ~50 files. Handles config parsing, model resolution, phase lookup, git commits, summary verification, frontmatter CRUD, scaffolding, state management, and validation. This centralizes all state operations and ensures consistency.

Source: `get-shit-done/bin/gsd-tools.js:1-79`

### 8. Checkpoint Protocol

GSD formalizes three types of human interaction during autonomous execution:

| Type | Frequency | Purpose |
|---|---|---|
| human-verify (90%) | Most common | Visual/functional verification after automation |
| decision (9%) | Occasional | Implementation choice needed |
| human-action (1%) | Rare | Truly unavoidable manual step (email link, 2FA) |

The golden rule: "If Claude can run it, Claude runs it." Users only do what requires human judgment.

Source: `references/checkpoints.md:1-11`

### 9. Self-Check in Executors

After writing SUMMARY.md, executors verify their own claims by checking that created files exist on disk and commits exist in git history. This catches hallucinated completion.

Source: `agents/gsd-executor.md:307-323`

### 10. Configurable Model Profiles

Three profiles control which Claude model each agent uses:

| Profile | Planning | Execution | Verification |
|---|---|---|---|
| quality | Opus | Opus | Sonnet |
| balanced | Opus | Sonnet | Sonnet |
| budget | Sonnet | Sonnet | Haiku |

Source: `README.md:496-501`

### Known Limitations and Gaps

1. **No inter-plan communication during execution** — Plans within a wave execute in parallel but cannot coordinate in real-time. If Plan A discovers something Plan B needs, it can only communicate via committed files that Wave 2 reads.

2. **Context CONTEXT.md is only for discuss-phase output** — There is no equivalent mechanism for capturing runtime decisions or discoveries during execution (beyond deviation tracking in SUMMARY.md).

3. **No rollback mechanism** — If execution produces broken code, there is no automated rollback. The approach is gap closure (diagnose -> plan fix -> execute fix), not revert.

4. **Checkpoint handling requires fresh agent spawn** — When an executor hits a checkpoint, it cannot be resumed. A fresh continuation agent is spawned with explicit state. This works but adds overhead.

   > "Why fresh agent, not resume: Resume relies on internal serialization that breaks with parallel tool calls."
   > — `workflows/execute-phase.md:201`

5. **STATE.md size constraint (100 lines)** creates information loss for complex projects — decisions, blockers, and context must be aggressively pruned.

6. **No automated testing integration** — While TDD is supported as a plan type, there is no test runner integration that would catch regressions across phases. Verification is per-phase, not cumulative.

7. **Single-user model** — The entire system assumes one human and one AI. There is no mechanism for multiple humans collaborating through the system, or multiple AI instances coordinating beyond the wave-based parallelism.

---

## Architecture Summary

```
User
  │
  ├── /gsd:new-project ──────── Deep questioning ──── Research (4 parallel) ──── Requirements ──── Roadmap
  │                                                                                                  │
  ├── /gsd:discuss-phase N ──── Gray areas ──── CONTEXT.md                                          │
  │                                                  │                                               │
  ├── /gsd:plan-phase N ──────── Research ──── Planner ←──→ Checker (max 3 iterations)              │
  │                                                  │                                               │
  ├── /gsd:execute-phase N ──── Wave 1: [Plan A, Plan B] parallel ──── Wave 2: [Plan C] ───────────│
  │                               │                                       │                          │
  │                        gsd-executor (fresh 200k)              gsd-executor (fresh 200k)          │
  │                               │                                       │                          │
  │                        Atomic commits per task              Atomic commits per task               │
  │                               │                                       │                          │
  │                        SUMMARY.md + self-check              SUMMARY.md + self-check              │
  │                                                                                                  │
  │                        gsd-verifier ──── VERIFICATION.md                                         │
  │                                                                                                  │
  ├── /gsd:verify-work N ──────── UAT (one test at a time) ──── Diagnosis ──── Fix plans            │
  │                                                                                                  │
  ├── /gsd:complete-milestone ── Archive ──── Git tag                                                │
  │                                                                                                  │
  └── /gsd:new-milestone ──────── Next version ─────────────────────────────────────────────────────┘
```

**Key design principle**: The orchestrator never does heavy lifting. It spawns agents, waits, integrates results. Context stays lean, quality stays high.

---

## File Inventory

| Category | Count | Key Files |
|---|---|---|
| Commands | 29 | `commands/gsd/*.md` |
| Agents | 11 | `agents/gsd-*.md` |
| Workflows | 31 | `get-shit-done/workflows/*.md` |
| Templates | 25+ | `get-shit-done/templates/*.md` |
| References | 13 | `get-shit-done/references/*.md` |
| CLI Tool | 1 | `get-shit-done/bin/gsd-tools.js` (161KB) |
| Hooks | 2 | `hooks/gsd-statusline.js`, `hooks/gsd-check-update.js` |
| Installer | 1 | `bin/install.js` |
