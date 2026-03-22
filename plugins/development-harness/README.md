<p align="center">
  <img src="./assets/hero.png" alt="Development Harness" width="800" />
</p>

# development-harness

Language-agnostic development process harness implementing the Stateless Agent Methodology
(SAM) 7-stage pipeline with ARL human touchpoint model and Voltron-style language plugin
composition.

## What it does

The primary entry point is the SAM 4-skill workflow:

1. `/dh:add-new-feature` — plan a feature (discovery, analysis, architecture, task decomposition)
2. `/dh:implement-feature` — execute tasks via agent delegation loop
3. `/dh:start-task` — start or complete a specific task
4. `/dh:complete-implementation` — quality gates after all tasks complete

The harness orchestrates feature development through a conceptual 7-stage pipeline (Discovery,
Planning, Context Integration, Task Decomposition, Execution, Forensic Review, Final
Verification). Language plugins snap in by providing a manifest that maps abstract roles to
concrete agents and declares quality gate commands. Without a language manifest the harness
falls back to general-purpose agents. All pipeline artifacts are written to `plan/` for
stateless handoff between stages.

## Skills

**Main orchestration:**

- `development-harness` — Entry point. Detects language, resolves roles, orchestrates S1–S7

**SAM workflow:**

- `add-new-feature` — Plan a feature: discovery, analysis, architecture, task decomposition
- `implement-feature` — Execute tasks from a SAM task file via agent delegation loop
- `start-task` — Start or complete a specific task inside a SAM task file
- `complete-implementation` — Quality gates after all tasks are complete

**Planning tools:**

- `clear-cove-task-design` — Task design methodology for decomposing features into executable units
- `generate-task` — Generate individual task files following SAM conventions
- `planner-rt-ica` — Information completeness analysis applied during planning (RT-ICA)
- `validation-protocol` — Validation patterns and checklists for verifying task completion

**Implementation:**

- `implementation-manager` — Coordinate implementation work across parallel tasks
- `dispatch` — Dispatch tasks to agents using teams-first parallel execution

**Backlog management:**

- `backlog` — Backlog overview and operations reference
- `create-backlog-item` — Create new backlog items
- `work-backlog-item` — Work on a backlog item through its lifecycle
- `groom-backlog-item` — Groom and prioritize backlog items

**Milestone management:**

- `groom-milestone` — Groom milestone issues into dispatch plans
- `work-milestone` — Execute milestone tasks in isolated worktrees

**Workflow stages (subdirectory namespace `dh:workflows:`):**

- `workflows/discovery` — S1 feature and codebase understanding
- `workflows/planning` — S2 plan generation with RT-ICA
- `workflows/context-integration` — S3 plan validation against codebase
- `workflows/task-decomposition` — S4 break plan into executable tasks
- `workflows/execution` — S5 implement tasks with language specialists
- `workflows/forensic-review` — S6 verify task completion
- `workflows/final-verification` — S7 certify feature completion

**Testing (subdirectory namespace `dh:testing:`):**

- `testing/comprehensive-test-review` — Review test coverage and quality
- `testing/analyze-test-failures` — Diagnose and categorize test failures
- `testing/test-failure-mindset` — Systematic approach to understanding test failures

**Other:**

- `interop` — Cross-plugin interoperability
- `dh-meta-docs` — Plugin meta-documentation
- `subagent-contract` — Subagent contract definitions

## Agents

- `swarm-task-planner` — Decomposes features into parallel task streams
- `plan-validator` — Validates plans for completeness and feasibility before execution
- `feature-researcher` — Researches feature requirements and prior art
- `codebase-analyzer` — Analyzes codebase structure and existing patterns
- `ecosystem-researcher` — Researches external dependencies and ecosystem context
- `feature-verifier` — Verifies a feature meets its acceptance criteria
- `integration-checker` — Checks integration points and compatibility between components
- `t0-baseline-capture` — Captures baseline state before implementation (bookend task T0)
- `tn-verification-gate` — Verifies acceptance criteria after implementation (bookend task TN)
- `context-gathering` — Gathers context from codebase and documentation
- `context-refinement` — Refines and validates gathered context before planning
- `doc-drift-auditor` — Detects documentation drift from implementation
- `service-docs-maintainer` — Generates and maintains service-level documentation
- `task-worker` — Executes individual tasks
- `generic-stage-agent` — Generic agent for pipeline stages

## Installation

```bash
/plugin install development-harness@jamie-bitflight-skills
```

## Usage

```text
/dh:development-harness "add JWT authentication to the API"
```

The harness detects the project language, resolves specialist agents from the matching language
plugin, and walks the request through all seven stages. Human escalation is triggered by ARL
constraint analysis, not arbitrary checkpoints.

---

> **The Ancient Woe**
>
> *The mad cook who throws raw flour, unplucked chickens, and unlit coal into a single iron pot, praying to the heavens that a feast will somehow emerge.*

> **The Bard's Decree**
>
> *"Order in the kitchen! First the recipe, then the gathering, then the fire, then the feast! We shall march strictly through the seven gates of preparation before a single dish is served!"*
