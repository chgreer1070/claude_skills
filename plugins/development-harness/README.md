<p align="center">
  <img src="./assets/hero.png" alt="Development Harness" width="800" />
</p>

# development-harness

Language-agnostic development process harness implementing the Stateless Agent Methodology
(SAM) 7-stage pipeline with ARL human touchpoint model and Voltron-style language plugin
composition.

## What it does

Orchestrates feature development through a structured 7-stage pipeline: Discovery, Planning,
Context Integration, Task Decomposition, Execution, Forensic Review, and Final Verification.
Language plugins snap in by providing a manifest that maps abstract roles to concrete agents
and declares quality gate commands. Without a language manifest the harness falls back to
general-purpose agents. All pipeline artifacts are written to `.planning/harness/` for
stateless handoff between stages.

## Skills

- `development-harness` — Entry point. Detects language, resolves roles, orchestrates S1–S7
- `clear-cove-task-design` — Task design methodology for decomposing features into executable units
- `generate-task` — Generate individual task files following SAM conventions
- `implementation-manager` — Coordinate implementation work across parallel tasks
- `planner-rt-ica` — Information completeness analysis applied during planning (RT-ICA)
- `testing` — Test design and coverage methodology
- `validation-protocol` — Validation patterns and checklists for verifying task completion
- `workflows` — Workflow orchestration patterns for the harness pipeline

## Agents

- `swarm-task-planner` — Decomposes features into parallel task streams
- `plan-validator` — Validates plans for completeness and feasibility before execution
- `feature-researcher` — Researches feature requirements and prior art
- `codebase-analyzer` — Analyzes codebase structure and existing patterns
- `ecosystem-researcher` — Researches external dependencies and ecosystem context
- `feature-verifier` — Verifies a feature meets its acceptance criteria
- `integration-checker` — Checks integration points and compatibility between components
- `context-gathering` — Gathers context from codebase and documentation
- `context-refinement` — Refines and validates gathered context before planning
- `doc-drift-auditor` — Detects documentation drift from implementation
- `service-docs-maintainer` — Generates and maintains service-level documentation

## Installation

```bash
/plugin install development-harness@jamie-bitflight-skills
```

## Usage

```text
/development-harness "add JWT authentication to the API"
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
