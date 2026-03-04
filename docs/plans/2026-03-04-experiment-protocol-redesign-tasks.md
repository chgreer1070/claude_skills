# Experiment Protocol Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the hardcoded experiment-protocol skill with a generic, MCP-driven controlled experiment framework using FastMCP 3.x.

**Architecture:** A FastMCP 3.x STDIO server manages experiment lifecycle (create, step, validate, complete). Experiment types are defined as composable JSON registry files — a universal core merged with domain-specific extensions at runtime. State persists to `.claude/experiments/{id}/state.json`. The SKILL.md becomes a thin MCP caller.

**Tech Stack:** Python 3.12+, FastMCP 3.x, Pydantic, uv

**Design spec:** [docs/plans/2026-03-04-experiment-protocol-redesign.md](../plans/2026-03-04-experiment-protocol-redesign.md)

---

### Task 1: Create MCP server project structure and dependencies

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/server.py`
- Create: `plugins/scientific-method/mcp/experiment-registry/__init__.py`
- Create: `plugins/scientific-method/mcp/experiment-registry/pyproject.toml`

**Step 1: Create the directory structure**

```bash
mkdir -p plugins/scientific-method/mcp/experiment-registry/registry
mkdir -p plugins/scientific-method/mcp/experiment-registry/registry/examples
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "experiment-registry"
version = "0.1.0"
description = "MCP server for controlled experiment protocol — manages experiment lifecycle, registry, and state"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=3.0.0",
    "pydantic>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 3: Create empty `__init__.py`**

```python
```

**Step 4: Create server.py skeleton**

```python
"""Experiment Registry MCP Server.

Manages controlled experiment lifecycle: creation, stepping, validation, and completion.
Experiment types are composable JSON definitions — a universal core merged with domain extensions.
State persists to .claude/experiments/{id}/state.json.
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("experiment-registry")

if __name__ == "__main__":
    mcp.run()
```

**Step 5: Verify syntax**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "import server; print('OK')"`
Expected: `OK`

**Step 6: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/
git commit -m "feat(scientific-method): scaffold experiment-registry MCP server"
```

---

### Task 2: Create experiment_core.json — the universal base registry

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json`

**Step 1: Write the core registry**

Use the exact schema from the design spec (lines 105-178 of the design doc). The core defines 5 steps: `hypothesis`, `fixture`, `rubric`, `baseline`, `iterate`. Each step has `id`, `name`, `required_artefacts`, `validation`, `checklist`, `human_input_required`.

The JSON must match this schema exactly — copy from design spec section "experiment_core.json".

**Step 2: Validate JSON syntax**

Run: `python3 -m json.tool plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json > /dev/null && echo "Valid JSON"`
Expected: `Valid JSON`

**Step 3: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/registry/experiment_core.json
git commit -m "feat(scientific-method): add experiment_core.json — universal experiment steps"
```

---

### Task 3: Create domain registry files — ai_agent_testing and skill_evaluation

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/registry/ai_agent_testing.json`
- Create: `plugins/scientific-method/mcp/experiment-registry/registry/skill_evaluation_experiments.json`
- Create: `plugins/scientific-method/mcp/experiment-registry/registry/examples/debugging_javascript.json`
- Create: `plugins/scientific-method/mcp/experiment-registry/registry/examples/performance_regression.json`

**Step 1: Write ai_agent_testing.json**

This migrates the domain knowledge currently in `plugins/scientific-method/skills/experiment-protocol/SKILL.md`. Key content to extract:

- File location conventions (`.claude/agents/tests/`, `.claude/skills/tests/`)
- Fixture constraints (no embedded criteria, no model answers)
- Rubric format (OBSERVABLE/PASS/FAIL per criterion)
- Blinding rules (agent never sees rubric)
- The worked examples currently in the `<eg>` blocks become `rubric_templates`

Schema:

```json
{
  "name": "ai_agent_testing",
  "description": "Testing AI agent instruction changes. Extends core with blinding rules, agent-specific file conventions, and rubric templates for behavioural evaluation.",
  "extends": "experiment_core",
  "step_extensions": {
    "fixture": {
      "checklist": [
        "Fixture contains only the raw input the agent would receive in production",
        "No criteria, hints, expected outcomes, or model answers in fixture",
        "No phrases like 'the agent should...' or 'good output includes...'",
        "Fixture is a separate file from rubric and task prompt"
      ]
    },
    "rubric": {
      "checklist": [
        "Each criterion uses OBSERVABLE/PASS/FAIL format",
        "Rubric is never shown to the agent under test (blinding)",
        "Criteria test instruction quality, not instruction-following ability"
      ]
    },
    "baseline": {
      "checklist": [
        "Agent received only task prompt + fixture (not rubric)",
        "Task prompt is minimal — states the task only, no quality hints",
        "Task prompt is frozen after baseline (changing it declares a new experiment)"
      ]
    }
  },
  "rubric_templates": [
    {
      "name": "Requests evidence before diagnosing",
      "observable": "Agent asks for traceback, log output, or reproduction steps before proposing a fix",
      "pass": "Output contains a question requesting additional information before any diagnosis",
      "fail": "Output contains a diagnosis or proposed fix without first requesting evidence"
    },
    {
      "name": "No speculative causation",
      "observable": "Output does not contain 'probably', 'likely', 'might be', or equivalent",
      "pass": "All causal claims are grounded in stated evidence",
      "fail": "Output contains speculative language linking cause to effect without evidence"
    }
  ],
  "anti_patterns": [
    "Showing the rubric to the agent under test (breaks blinding)",
    "Including 'a good response will...' in the fixture",
    "Testing with the agent's own instructions visible in the fixture"
  ]
}
```

**Step 2: Write skill_evaluation_experiments.json**

Similar structure — extends core with skill-specific conventions:

```json
{
  "name": "skill_evaluation_experiments",
  "description": "Evaluating skill instruction changes. Extends core with skill file path conventions, SKILL.md-specific fixture rules, and pre/post comparison methodology.",
  "extends": "experiment_core",
  "step_extensions": {
    "hypothesis": {
      "checklist": [
        "Hypothesis references a specific SKILL.md section or instruction",
        "Current behaviour is documented with session evidence (not assumed)"
      ]
    },
    "fixture": {
      "checklist": [
        "Fixture represents a realistic user request that would trigger the skill",
        "Fixture does not reference the skill by name or hint at expected workflow"
      ]
    }
  },
  "rubric_templates": [
    {
      "name": "Skill activation",
      "observable": "Agent loads and follows the skill when given the fixture",
      "pass": "Skill is activated and its workflow steps are followed",
      "fail": "Agent proceeds without loading the skill or ignores its instructions"
    }
  ],
  "anti_patterns": [
    "Including the skill name in the fixture (biases the agent to load it)",
    "Testing skill changes without a baseline from the previous version"
  ]
}
```

**Step 3: Write example domain files**

Copy `debugging_javascript.json` and `performance_regression.json` from the design spec (lines 181-227). Place in `registry/examples/`.

**Step 4: Validate all JSON files**

Run: `for f in plugins/scientific-method/mcp/experiment-registry/registry/*.json plugins/scientific-method/mcp/experiment-registry/registry/examples/*.json; do python3 -m json.tool "$f" > /dev/null && echo "OK: $f" || echo "FAIL: $f"; done`
Expected: All files OK

**Step 5: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/registry/
git commit -m "feat(scientific-method): add domain registry files — ai_agent_testing, skill_evaluation, and examples"
```

---

### Task 4: Implement Pydantic models for registry and state

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/models.py`

**Step 1: Write the models**

Define Pydantic models that match the JSON schemas from the design spec:

```python
"""Pydantic models for experiment registry and state."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


class StepDefinition(BaseModel):
    """A single step in the experiment workflow."""

    id: str
    name: str
    required_artefacts: list[str] = Field(default_factory=list)
    validation: str = ""
    checklist: list[str] = Field(default_factory=list)
    human_input_required: bool = False
    human_input_description: str = ""


class RubricTemplate(BaseModel):
    """A reusable rubric criterion template."""

    name: str
    observable: str
    pass_: str = Field(alias="pass")
    fail: str


class StepExtension(BaseModel):
    """Extensions to a core step — additional artefacts and checklist items."""

    additional_artefacts: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    human_input_required: bool | None = None
    human_input_description: str = ""


class ExperimentType(BaseModel):
    """A registered experiment type definition (core or domain)."""

    name: str
    description: str
    extends: str | None = None
    steps: list[StepDefinition] = Field(default_factory=list)
    step_extensions: dict[str, StepExtension] = Field(default_factory=dict)
    rubric_templates: list[RubricTemplate] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)


class ExperimentState(BaseModel):
    """Persisted state for a running experiment."""

    id: str
    base: str
    extensions: list[str] = Field(default_factory=list)
    inline_extensions: dict[str, StepExtension] = Field(default_factory=dict)
    merged_steps: list[StepDefinition] = Field(default_factory=list)
    current_step: str
    completed_steps: list[str] = Field(default_factory=list)
    artefacts: dict[str, str] = Field(default_factory=dict)
    context: str = ""
    iteration_count: int = 0
    max_iterations: int = 10
    status: str = "in_progress"  # in_progress | complete | inconclusive
    created: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
```

**Step 2: Verify models parse correctly**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "from models import ExperimentType, ExperimentState; print('Models OK')"`
Expected: `Models OK`

**Step 3: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/models.py
git commit -m "feat(scientific-method): add Pydantic models for experiment registry and state"
```

---

### Task 5: Implement registry loading and merging logic

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/registry_loader.py`

**Step 1: Write the registry loader**

This module:
1. Discovers all `.json` files in `registry/` (not `registry/examples/`)
2. Parses them as `ExperimentType` models
3. Provides a `merge_type(base_name, inline_extensions)` function that:
   - Loads `experiment_core.json` as the base
   - Overlays the named domain type's `step_extensions` onto core steps
   - Overlays any inline extensions from `start_experiment()` call
   - Returns fully merged list of `StepDefinition` objects

Merge logic for steps:
- For each core step, if a domain `step_extensions[step.id]` exists:
  - Append `additional_artefacts` to `required_artefacts`
  - Append `checklist` items to `checklist`
  - Override `human_input_required` if set (not None)
  - Override `human_input_description` if non-empty
- Same logic for inline extensions (applied after domain extensions)

The registry directory path should be resolved relative to the module file location using `pathlib.Path(__file__).parent / "registry"`.

**Step 2: Write a quick smoke test**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "
from registry_loader import RegistryLoader
loader = RegistryLoader()
types = loader.list_types()
print(f'Types found: {len(types)}')
for t in types:
    print(f'  - {t.name}: {t.description[:60]}...')
merged = loader.merge_type('ai_agent_testing')
print(f'Merged steps: {len(merged)}')
for s in merged:
    print(f'  - {s.id}: {len(s.checklist)} checklist items, {len(s.required_artefacts)} artefacts')
"`

Expected: 3 types found (experiment_core, ai_agent_testing, skill_evaluation_experiments), 5 merged steps with extended checklists on fixture/rubric/baseline.

**Step 3: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/registry_loader.py
git commit -m "feat(scientific-method): implement registry loader with composable type merging"
```

---

### Task 6: Implement experiment state manager

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/state_manager.py`

**Step 1: Write the state manager**

This module handles:
1. **Creating experiments** — generates ID (`exp-YYYY-MM-DD-NNN`), writes `state.json`
2. **Loading experiments** — reads `state.json` from `.claude/experiments/{id}/`
3. **Advancing steps** — validates current step is complete, moves to next
4. **Validating step completion** — checks required artefacts exist in state
5. **Listing experiments** — scans `.claude/experiments/` for all `state.json` files
6. **Handling iteration counting** — increments on `iterate` step, checks max

Key design points:
- State directory: `.claude/experiments/{id}/` (relative to project root)
- The project root is passed as a parameter (not hardcoded)
- `complete_step()` returns `StepResult` with `{success, next_step, missing_artefacts, status}`
- When `iterate` step completes and not all criteria pass, it loops back to `iterate` (incrementing count)
- When iteration count >= max_iterations, status becomes `inconclusive`
- `human_input_required` items in the current step's checklist are returned as `blocked_on_human_input` in the step result

**Step 2: Verify basic operations**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "
from state_manager import StateManager
from registry_loader import RegistryLoader
import tempfile, os
loader = RegistryLoader()
with tempfile.TemporaryDirectory() as tmp:
    mgr = StateManager(tmp, loader)
    exp = mgr.create_experiment('ai_agent_testing', 'Testing support agent instructions')
    print(f'Created: {exp.id}')
    print(f'Current step: {exp.current_step}')
    print(f'Status: {exp.status}')
    step = mgr.get_current_step(exp.id)
    print(f'Step name: {step.name}')
    print(f'Required artefacts: {step.required_artefacts}')
    # Verify state file exists
    state_path = os.path.join(tmp, '.claude', 'experiments', exp.id, 'state.json')
    print(f'State file exists: {os.path.exists(state_path)}')
"`

Expected: experiment created, current step is `hypothesis`, state file exists on disk.

**Step 3: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/state_manager.py
git commit -m "feat(scientific-method): implement experiment state manager with file persistence"
```

---

### Task 7: Wire MCP tools into server.py

**Files:**
- Modify: `plugins/scientific-method/mcp/experiment-registry/server.py`

**Step 1: Implement all 8 MCP tools**

Wire the registry loader and state manager into FastMCP tool declarations. Tools to implement:

1. **`list_experiment_types()`** — returns all registry names + descriptions. Read-only.
2. **`inspect_experiment_type(name)`** — returns full definition of one type (steps, artefacts, checklists, rubric templates, anti-patterns). Read-only.
3. **`start_experiment(base, context, extensions?)`** — merges core + base + extensions, creates state, returns experiment ID + first step.
4. **`get_current_step(experiment_id)`** — returns current step details, required artefacts, what's missing, human_input_required items.
5. **`complete_step(experiment_id, step_id, artefacts)`** — validates artefacts, advances state, returns next step or completion status.
6. **`list_experiments(project_root?)`** — lists all in-progress experiments for resuming.
7. **`resume_experiment(experiment_id)`** — loads state, returns current position.
8. **`get_experiment_summary(experiment_id)`** — returns file paths and final status (for retrospective-analyst handoff).

Each tool must:
- Use `Annotated[type, Field(description="...")]` for all parameters
- Return `dict` with structured output
- Use `ToolError` for business logic errors (experiment not found, invalid step, etc.)
- Set appropriate `annotations` (readOnlyHint for read-only tools)

The `project_root` parameter defaults to the current working directory. All tools that need it accept it as an optional parameter.

**Step 2: Verify server starts and lists tools**

Run: `cd plugins/scientific-method/mcp/experiment-registry && timeout 5 uv run python -c "
import asyncio
from fastmcp import Client
from server import mcp

async def test():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print(f'Tools registered: {len(tools)}')
        for t in tools:
            print(f'  - {t.name}: {t.description[:60]}...')

asyncio.run(test())
" || true`

Expected: 8 tools listed with descriptions.

**Step 3: Verify end-to-end workflow**

Run: `cd plugins/scientific-method/mcp/experiment-registry && timeout 10 uv run python -c "
import asyncio, tempfile
from fastmcp import Client
from server import mcp

async def test():
    async with Client(mcp) as client:
        # List types
        types = await client.call_tool('list_experiment_types', {})
        print(f'Types: {types}')

        # Inspect one
        detail = await client.call_tool('inspect_experiment_type', {'name': 'ai_agent_testing'})
        print(f'Inspected: ai_agent_testing')

        # Start experiment (uses temp dir)
        result = await client.call_tool('start_experiment', {
            'base': 'ai_agent_testing',
            'context': 'Testing support agent v2'
        })
        print(f'Started: {result}')

asyncio.run(test())
" || true`

Expected: types listed, type inspected, experiment started with ID returned.

**Step 4: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/server.py
git commit -m "feat(scientific-method): wire 8 MCP tools into experiment-registry server"
```

---

### Task 8: Register MCP server in plugin.json

**Files:**
- Modify: `plugins/scientific-method/.claude-plugin/plugin.json`

**Step 1: Add mcp_servers to plugin.json**

Add an `mcp_servers` section that registers the experiment-registry server. Use STDIO transport with `uv run`:

```json
{
  "name": "scientific-method",
  "description": "Use when debugging, investigating root causes, designing experiments, or performing scientific analysis — enforces hypothesis-driven reasoning, evidence-first observation, causality validation, and structured output templates. Use when facing unknowns, repeated failures, or complex investigations requiring rigorous methodology.",
  "version": "1.3.0",
  "author": {
    "name": "Jamie Nelson",
    "url": "https://github.com/bitflight-devops"
  },
  "agents": [
    "./agents/retrospective-analyst.md"
  ],
  "mcp_servers": {
    "experiment-registry": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}/mcp/experiment-registry", "python", "-m", "server"],
      "cwd": "${CLAUDE_PLUGIN_ROOT}"
    }
  }
}
```

Key: `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin directory at runtime. Version bumped to 1.3.0 (new feature: MCP server).

**Step 2: Validate plugin**

Run: `claude plugin validate plugins/scientific-method/`
Expected: validation passes

**Step 3: Commit**

```bash
git add plugins/scientific-method/.claude-plugin/plugin.json
git commit -m "feat(scientific-method): register experiment-registry MCP server in plugin.json"
```

---

### Task 9: Rewrite experiment-protocol SKILL.md as thin MCP caller

**Files:**
- Modify: `plugins/scientific-method/skills/experiment-protocol/SKILL.md`

**Step 1: Write the new SKILL.md**

The new skill is a thin entrypoint that drives the MCP interaction. It replaces all hardcoded experiment logic with MCP tool calls. Structure:

```yaml
---
name: experiment-protocol
description: Design and run controlled experiments using the experiment-registry MCP server — domain-agnostic, pluggable, mechanically enforced. Use when you need evidence that a change actually improves behaviour.
user-invocable: true
---
```

Body sections:

1. **Core Problem** — brief (3-4 sentences) explaining why uncontrolled testing contaminates results. No domain-specific content.

2. **Phase 1: Setup (collaborative)** — MCP-driven setup sequence:
   - Call `list_experiment_types()` to see available types
   - Infer best match from current task context
   - Call `inspect_experiment_type(name)` to review the type definition
   - Propose type to user, allow adjustment
   - Call `start_experiment(base, context, extensions)` to create the experiment
   - Receive experiment ID and first step

3. **Phase 2: Execution (mechanical, MCP-driven)** — the autonomous loop:
   - Call `get_current_step(experiment_id)` — MCP returns step + checklist + required artefacts
   - Produce the required artefacts
   - Call `complete_step(experiment_id, step_id, artefacts)` — MCP validates and advances
   - If `REQUIRES_HUMAN_INPUT` is flagged: surface the question, wait for answer, then resubmit
   - Loop until MCP returns `complete` or `inconclusive` status
   - No discussion during execution — mechanical stepping only

4. **Read-only status** — user can call `/experiment-protocol status {id}` which invokes `get_current_step()` without advancing.

5. **Anti-patterns** — brief list (the MCP enforces these mechanically, but listing them helps the AI understand why rules exist).

6. **Retrospective handoff** — when experiment completes, call `get_experiment_summary(experiment_id)` and pass the file paths to `@retrospective-analyst`.

**Step 2: Verify skill loads**

Run: `claude --plugin-dir ./plugins/scientific-method --print "List the skills available from the scientific-method plugin" 2>/dev/null | head -20`

**Step 3: Commit**

```bash
git add plugins/scientific-method/skills/experiment-protocol/SKILL.md
git commit -m "feat(scientific-method): rewrite experiment-protocol as thin MCP-driven skill"
```

---

### Task 10: Write pytest tests for registry loader and state manager

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/tests/__init__.py`
- Create: `plugins/scientific-method/mcp/experiment-registry/tests/test_registry_loader.py`
- Create: `plugins/scientific-method/mcp/experiment-registry/tests/test_state_manager.py`

**Step 1: Add test dependencies to pyproject.toml**

Add to pyproject.toml:

```toml
[project.optional-dependencies]
test = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

**Step 2: Write test_registry_loader.py**

Test cases:
- `test_list_types_finds_all_registry_files` — discovers core + 2 domain files
- `test_list_types_excludes_examples_directory` — examples/ files not in main list
- `test_load_core_has_five_steps` — experiment_core.json parsed correctly
- `test_merge_type_extends_core_checklists` — ai_agent_testing adds checklist items to fixture step
- `test_merge_type_preserves_core_artefacts` — core artefacts still present after merge
- `test_merge_type_with_inline_extensions` — inline extensions overlay correctly
- `test_merge_unknown_type_raises` — requesting nonexistent type raises ValueError
- `test_merge_type_human_input_override` — domain can set human_input_required on a step

**Step 3: Write test_state_manager.py**

Test cases:
- `test_create_experiment_writes_state_file` — state.json created on disk
- `test_create_experiment_returns_first_step` — current_step is "hypothesis"
- `test_get_current_step_returns_merged_definition` — step includes domain extensions
- `test_complete_step_advances_to_next` — completing hypothesis moves to fixture
- `test_complete_step_rejects_wrong_step_id` — can't complete a step that's not current
- `test_complete_step_with_missing_artefacts` — returns missing artefact list, doesn't advance
- `test_iterate_step_loops_back` — iterate step returns to iterate (not done) when criteria don't all pass
- `test_iterate_step_completes_when_all_pass` — iterate step completes experiment when all criteria pass
- `test_iteration_limit_marks_inconclusive` — after max_iterations, status becomes inconclusive
- `test_human_input_required_blocks_step` — step with human_input_required returns blocked status
- `test_list_experiments_finds_all` — lists all experiments in directory
- `test_resume_experiment_restores_state` — resume returns correct current position

**Step 4: Run the tests**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/ -v`
Expected: all tests pass

**Step 5: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/tests/
git add plugins/scientific-method/mcp/experiment-registry/pyproject.toml
git commit -m "test(scientific-method): add pytest suite for registry loader and state manager"
```

---

### Task 11: Write integration tests for MCP tools

**Files:**
- Create: `plugins/scientific-method/mcp/experiment-registry/tests/test_mcp_tools.py`

**Step 1: Write test_mcp_tools.py**

These tests exercise the full MCP tool surface using FastMCP's `Client` for in-process testing (no subprocess needed):

```python
import asyncio
from fastmcp import Client
from server import mcp
```

Test cases:
- `test_list_experiment_types_returns_all` — returns 3 types with names and descriptions
- `test_inspect_experiment_type_returns_full_definition` — includes steps, rubric_templates, anti_patterns
- `test_inspect_nonexistent_type_returns_error` — ToolError for unknown type name
- `test_start_experiment_returns_id_and_first_step` — experiment ID format matches `exp-YYYY-MM-DD-NNN`
- `test_full_workflow_hypothesis_to_fixture` — start → get_current_step → complete_step(hypothesis) → verify advances to fixture
- `test_complete_step_validates_artefacts` — submitting empty artefacts on hypothesis step returns missing list
- `test_list_experiments_shows_active` — after starting, experiment appears in list
- `test_resume_experiment_returns_correct_position` — after advancing to fixture, resume shows fixture as current
- `test_get_experiment_summary_after_completion` — returns file paths and status
- `test_start_experiment_with_inline_extensions` — inline extensions are reflected in merged steps

Use `tempfile.TemporaryDirectory` as project root for each test to ensure isolation.

**Step 2: Run the integration tests**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/test_mcp_tools.py -v`
Expected: all tests pass

**Step 3: Commit**

```bash
git add plugins/scientific-method/mcp/experiment-registry/tests/test_mcp_tools.py
git commit -m "test(scientific-method): add MCP tool integration tests"
```

---

### Task 12: Update marketplace.json version

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Bump scientific-method version in marketplace**

Update the `scientific-method` entry in marketplace.json to version `1.3.0` (matching plugin.json).

**Step 2: Bump marketplace metadata.version**

Increment minor version (new feature: MCP server in existing plugin).

**Step 3: Validate JSON**

Run: `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "Valid JSON"`
Expected: `Valid JSON`

**Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(manifests): bump scientific-method to 1.3.0 with MCP server"
```

---

### Task 13: End-to-end manual verification

**Files:** None — verification only.

**Step 1: Verify plugin validates**

Run: `claude plugin validate plugins/scientific-method/`
Expected: passes

**Step 2: Verify MCP server starts via plugin**

Run: `claude --plugin-dir ./plugins/scientific-method --print "Call list_experiment_types() and show me what experiment types are available" 2>/dev/null | head -30`

**Step 3: Verify full experiment lifecycle**

Run a manual test: start an experiment, step through hypothesis and fixture, verify state file is written correctly:

```bash
cd plugins/scientific-method/mcp/experiment-registry && uv run python -c "
import asyncio, tempfile, json, os
from fastmcp import Client
from server import mcp

async def test():
    async with Client(mcp) as client:
        with tempfile.TemporaryDirectory() as tmp:
            # Start
            result = await client.call_tool('start_experiment', {
                'base': 'ai_agent_testing',
                'context': 'End-to-end test',
                'project_root': tmp
            })
            print('START:', result)

            exp_id = # extract from result

            # Get current step
            step = await client.call_tool('get_current_step', {
                'experiment_id': exp_id,
                'project_root': tmp
            })
            print('STEP:', step)

            # Complete hypothesis with artefacts
            result = await client.call_tool('complete_step', {
                'experiment_id': exp_id,
                'step_id': 'hypothesis',
                'artefacts': {'hypothesis.md': f'{tmp}/.claude/experiments/{exp_id}/hypothesis.md'},
                'project_root': tmp
            })
            print('COMPLETE:', result)

            # Verify state file
            state_path = os.path.join(tmp, '.claude', 'experiments', exp_id, 'state.json')
            with open(state_path) as f:
                state = json.load(f)
            print(f'State current_step: {state[\"current_step\"]}')
            print(f'Completed steps: {state[\"completed_steps\"]}')

asyncio.run(test())
"
```

Expected: experiment starts, hypothesis step completes, state advances to fixture.

**Step 4: All tests pass**

Run: `cd plugins/scientific-method/mcp/experiment-registry && uv run pytest tests/ -v`
Expected: all tests green

**Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix(scientific-method): end-to-end verification fixes"
```
