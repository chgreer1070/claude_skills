# Experiment Protocol Redesign — Draft Plan

**Status**: DESIGN COMPLETE — open questions resolved, ready for task plan generation.
**Plugin**: `plugins/scientific-method`
**Skill**: `skills/experiment-protocol`

---

## Problem Statement

The current `experiment-protocol` skill is scoped specifically to testing AI agent and skill instruction changes. File paths are hardcoded to `.claude/agents/tests/` and `.claude/skills/tests/`. All examples use agent/support-ticket scenarios.

The goal is to make it a **generic controlled experiment framework** — domain-agnostic, pluggable, MCP-driven — that can handle any experiment type (AI agent testing, JavaScript debugging, performance regression, etc.) by loading specialist knowledge from a registry.

**Core observation**: AI is bad at running experiments. It jumps to conclusions, changes multiple variables, writes rubrics after seeing output, and skips baselines. This skill must enforce discipline mechanically, not through instruction.

---

## Approved Design Decisions

### 1. Depth: Full methodology (Option B)
Teaches *why* each rule exists, common failure modes, and how to adapt to any domain. Domain-specific steps live in specialist resources, not the core skill.

### 2. Specialist resources: Reference files in `experiment-protocol/references/` (Option A)
The generic skill links to them. Claude loads one on demand when the experiment domain is known.

### 3. Registry: MCP server owns the registry (not markdown files)
The index is a JSON file the MCP loads. The MCP steps through the workflow, tracks state, and surfaces missing artefacts.

### 4. Workflow stepping: Stateful MCP (Option A)
Claude calls `next_step(experiment_id)` and the MCP returns current step, validates prerequisites, and surfaces missing artefacts. Claude is the caller — not the user.

### 5. State persistence: Files (Option A)
`.claude/experiments/{experiment-id}/state.json` — experiments survive session restarts.

### 6. Registry JSON structure: Layered / composable (Option C)
- `experiment_core.json` — universal base, always loaded (minimum essentials)
- Domain JSONs merge on top: `skill_evaluation_experiments.json`, `debugging_javascript.json`, `performance_regression.json`, etc.
- Each domain JSON has: `name`, `description`, `extends`, `step_extensions`, `rubric_templates`, `anti_patterns`
- MCP merges layers at runtime and exposes the combined structure

### 7. Domain selection: Clarify → browse → inspect → extend
Claude clarifies what it's working on from context, calls `list_experiment_types()`, inspects the best match, proposes it. User can confirm or adjust during setup. No user involvement during execution.

### 8. Two-phase model

**Phase 1 — Setup (collaborative)**
- User invokes skill with context (or Claude infers from current task)
- Claude calls `list_experiment_types()`, proposes a match
- May ask one clarifying question if domain is ambiguous
- User can accept, adjust, or extend the base type
- Claude calls `start_experiment(base, context, extensions)` → experiment ID + structure written to disk

**Phase 2 — Execution (mechanical, MCP-driven)**
- Claude calls `get_current_step()` → MCP returns step + checklist + required artefacts
- Claude produces what's required
- Claude calls `complete_step()` → MCP validates, advances or surfaces what's missing
- Loop repeats until all steps pass
- No discussion during execution
- `REQUIRES_HUMAN_INPUT` is a first-class field in checklist items — MCP gates on it when human knowledge is genuinely needed

**User read access**: `/experiment-protocol status {id}` → read-only MCP call, shows current state without interrupting the loop.

---

## Proposed File Structure

```
plugins/scientific-method/
├── skills/experiment-protocol/
│   └── SKILL.md                    ← thin entrypoint, drives MCP interaction
├── mcp/
│   └── experiment-registry/
│       ├── server.py               ← FastMCP server
│       └── registry/
│           ├── experiment_core.json
│           ├── skill_evaluation_experiments.json
│           ├── debugging_javascript.json
│           ├── performance_regression.json
│           └── ai_agent_testing.json
├── agents/
│   └── retrospective-analyst.md   ← unchanged
└── .claude-plugin/plugin.json     ← registers MCP server
```

---

## MCP Tools (draft)

| Tool | Purpose |
|------|---------|
| `list_experiment_types()` | Returns all registry JSON names + descriptions |
| `inspect_experiment_type(name)` | Returns full definition of one base — steps, artefacts, checklists, rubric templates |
| `start_experiment(base, context, extensions)` | Merges core + base + extensions. Creates state.json. Returns experiment ID + first step |
| `get_current_step(experiment_id)` | Returns current step, required artefacts, what's missing |
| `complete_step(experiment_id, step_id, artefacts)` | Validates artefacts, advances state, returns next step |
| `list_experiments()` | Lists all in-progress experiments for resuming |
| `resume_experiment(experiment_id)` | Loads state.json, returns current position |

---

## Registry JSON Schema (draft)

### `experiment_core.json`
```json
{
  "name": "experiment_core",
  "description": "Universal controlled experiment protocol — hypothesis, fixture, rubric, baseline, iterate.",
  "steps": [
    {
      "id": "hypothesis",
      "name": "State hypothesis",
      "required_artefacts": ["hypothesis.md"],
      "validation": "contains HYPOTHESIS:, CURRENT BEHAVIOUR:, SUCCESS CRITERION:",
      "checklist": [],
      "human_input_required": false
    },
    {
      "id": "fixture",
      "name": "Build fixture",
      "required_artefacts": ["fixture.md"],
      "validation": "no embedded criteria or model answers",
      "checklist": [
        "Contains only raw input the subject would receive in production",
        "Contains no criteria, hints, or expected outcomes",
        "File is frozen — will not be edited after baseline"
      ],
      "human_input_required": false
    },
    {
      "id": "rubric",
      "name": "Write rubric",
      "required_artefacts": ["rubric.md"],
      "validation": "min 1 binary criterion, written before baseline",
      "checklist": [
        "Each criterion is observable and binary (pass/fail)",
        "Written before baseline run",
        "Rubric file is separate from fixture"
      ],
      "human_input_required": false
    },
    {
      "id": "baseline",
      "name": "Run baseline",
      "required_artefacts": ["output-iter0.md", "log.md"],
      "validation": "log entry for iter0 exists",
      "checklist": [
        "Agent received only task prompt + fixture (not rubric)",
        "All criteria scored for iter0",
        "Log entry complete"
      ],
      "human_input_required": false
    },
    {
      "id": "iterate",
      "name": "Iterate",
      "required_artefacts": ["log.md"],
      "validation": "one change per iter, regressions recorded, all criteria pass in final iter",
      "checklist": [
        "Exactly one thing changed between runs",
        "Predicted effect written before applying change",
        "Regressions recorded explicitly",
        "All criteria pass in this iteration"
      ],
      "human_input_required": false
    }
  ],
  "anti_patterns": [
    "Embedding criteria in the fixture",
    "Changing multiple things between runs",
    "Writing rubric criteria after seeing output",
    "Reporting only passing runs",
    "Changing the task prompt between runs",
    "Eyeballing output instead of scoring rubric criteria",
    "Including model answers in the fixture"
  ],
  "rubric_templates": []
}
```

### Domain extension example — `debugging_javascript.json`
```json
{
  "name": "debugging_javascript",
  "description": "Debugging experiments for JavaScript apps. Extends core with callstack, diff, and dependency graph observations.",
  "extends": "experiment_core",
  "step_extensions": {
    "hypothesis": {
      "additional_artefacts": ["callstack.md", "recent-diffs.md"],
      "checklist": [
        "Does the callstack show the failing frame?",
        "Are recent diffs attached for files in the stack?",
        "Is the dependency graph captured if a module boundary is crossed?"
      ]
    }
  },
  "rubric_templates": [
    {
      "name": "Identifies correct failing frame",
      "observable": "Agent names the specific file and line in the callstack",
      "pass": "Output references exact file:line of the failure",
      "fail": "Output describes the error generally without identifying the frame"
    }
  ]
}
```

### Domain extension example — `performance_regression.json`
```json
{
  "name": "performance_regression",
  "description": "Performance regression experiments. Extends core with baseline metrics, regression window, and hot path analysis.",
  "extends": "experiment_core",
  "step_extensions": {
    "baseline": {
      "additional_artefacts": ["baseline-metrics.md"],
      "checklist": [
        "Are baseline metrics captured before any change?",
        "Is the regression window defined (commit range or date range)?",
        "Is the hot path identified and profiled?"
      ],
      "human_input_required": true,
      "human_input_description": "Baseline metrics require running the profiler against the current codebase. Provide the profiler output."
    }
  }
}
```

---

## State File Schema

`.claude/experiments/{experiment-id}/state.json`:

```json
{
  "id": "exp-2026-03-04-001",
  "base": "debugging_javascript",
  "extensions": [],
  "merged_steps": ["...fully merged step definitions..."],
  "current_step": "fixture",
  "completed_steps": ["hypothesis"],
  "artefacts": {
    "hypothesis": ".claude/experiments/exp-2026-03-04-001/hypothesis.md",
    "callstack": ".claude/experiments/exp-2026-03-04-001/callstack.md"
  },
  "context": "Debugging failing Jest test in packages/auth — stack shows jwt.verify frame",
  "created": "2026-03-04T10:00:00Z",
  "last_updated": "2026-03-04T10:15:00Z"
}
```

---

## What the Redesigned SKILL.md Does

1. Brief description of the generic protocol (no domain-specific content)
2. Invocation: calls `list_experiment_types()` to orient
3. Context gathering: reads current task/files/error from session context
4. Type selection: calls `inspect_experiment_type(name)` on best match
5. Setup confirmation: proposes base type to user, allows adjustment
6. Execution loop: drives MCP autonomously — `get_current_step()` → produce artefact → `complete_step()`
7. Surfaces `REQUIRES_HUMAN_INPUT` items to user when genuinely needed
8. Completes when MCP confirms all steps pass

The `ai_agent_testing.json` domain file contains what currently lives in the skill body — domain file locations, worked examples (the current `<eg>` blocks rewritten as proper JSON rubric templates).

---

## Resolved Design Questions

1. **REQUIRES_HUMAN_INPUT gating** — **Blocking.** `complete_step()` rejects step completion if required human input artefacts are missing. Claude surfaces the question, waits for response, then submits.
2. **Extension mechanism** — **Both.** `start_experiment()` accepts inline `extensions` parameter for one-off checklist additions. New JSON files for reusable, named experiment types. MCP merges inline extensions into step definitions at runtime.
3. **Iteration limit** — **Yes, default 10.** Configurable per-experiment at `start_experiment()` time. After limit reached, MCP returns `inconclusive` status. Only the `iterate` step is repeatable.
4. **Retrospective integration** — **Analyst reads files directly.** New `get_experiment_summary(experiment_id)` tool returns file paths and final status for discovery. No coupling between MCP and agent format.
5. **Domain JSON files at launch** — **2 production + examples.** Launch: `ai_agent_testing.json`, `skill_evaluation_experiments.json`. Examples dir: `debugging_javascript.json`, `performance_regression.json` as templates.
6. **MCP server implementation** — **FastMCP 3.x (Python).** Decorator-based tools, Pydantic validation, STDIO transport, file-based state management.

---

## Current State of `plugins/scientific-method`

- 3 skills: `scientific-thinking`, `evidence-first-debugging`, `experiment-protocol`
- 1 agent: `retrospective-analyst`
- Shared content in `shared/` (evidence-rules, causality-check, investigation-template, investigation-workflow, extensions/)
- Validator: exit 0, score 82/100, no errors
- 5 pending fixes from assessment (unrelated to this redesign — tracked in `.claude/plan/tasks-refactor-scientific-method.md`)

---

## Next Steps

1. ~~Resume this plan in a new session~~ DONE
2. ~~Answer open questions above~~ DONE — all 6 resolved
3. Generate executable task plan via `/superpowers:writing-plans`
