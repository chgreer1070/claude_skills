# Feature Context: Workflow Architecture Diagram

## Document Metadata

- **Generated**: 2026-03-21
- **Input Type**: simple_description
- **Source**: GitHub Issue #933 — workflow architecture diagram, backlog and SAM publisher-consumer data flow
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

**Feature**: Workflow architecture diagram — backlog and SAM publisher-consumer data flow

**Problem**: `local-workflow.md` documents agent sequencing but not data structure shapes at edges or publisher-consumer relationships. AI agents make incorrect assumptions about available fields when consuming artifacts.

**Deliverables**:
1. Create `.claude/docs/workflow-architecture-diagram.md`
2. Update `.claude/rules/local-workflow.md` with link to new diagram

**7 Acceptance Criteria**:
- AC1: All nodes identified (8 MCP tools, 4 skills, 14 agents, 2 hooks, 5 CLI commands)
- AC2: Data structure shapes at every edge
- AC3: Publisher-consumer table for all artifacts
- AC4: SAM task state lifecycle with actors
- AC5: Cross-system dependency edge (backlog issue → SAM task → context file)
- AC6: Hook trigger conditions documented
- AC7: Mermaid or structured text, renders in GitHub

---

## Core Intent Analysis

### WHO (Target Users)

AI agents in the SAM workflow (feature-researcher, swarm-task-planner, start-task, context-gathering, task_status_hook.py, and orchestrators reading local-workflow.md). Human developers debugging incorrect agent behavior are a secondary audience.

### WHAT (Desired Outcome)

A reference document that tells any agent consuming a workflow artifact exactly what fields are present, what type each field is, and which component wrote them. The document covers the full topology: backlog MCP tools, SAM MCP tools, sam CLI commands, skills, agents, and hooks — with data shapes at every connection point.

### WHEN (Trigger Conditions)

An agent reads `local-workflow.md` before deciding how to handle a workflow artifact and discovers the existing diagram shows sequencing (what runs after what) but not payload shapes (what data is passed). The agent then needs to guess field names.

### WHY (Problem Being Solved)

`local-workflow.md` contains a data flow diagram that names artifacts (`plan/feature-context-{slug}.md`, `TaskAssignment`, `T0-baseline-{slug}.yaml`) but does not show their schemas. Agents consuming these artifacts cannot know from the diagram alone which fields exist. This causes field-name hallucinations (e.g., accessing `verdict` on a TN verification record that has `status` per-criterion instead) and missed required fields (e.g., forgetting `dependencies` must be an empty list for T0, not omitted).

The fix is a separate architecture document that is purely about data shapes at edges and publisher-consumer relationships, linked from `local-workflow.md`.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Authorized Writers Table in TASK_FILE_FORMAT.md

- **Location**: `plugins/development-harness/docs/TASK_FILE_FORMAT.md:186-196`
- **Relevance**: Already defines the publisher-consumer relationship for task fields. Lists field, writer, and mechanism (e.g., `status: in-progress` written by `start-task` skill via `sam claim`). The new document should extend this pattern to cover backlog artifacts and cross-system edges.
- **Reusable**: The table format (Field / Written By / Via) is the right grain for AC3.

#### Pattern 2: Status Values Table in TASK_FILE_FORMAT.md

- **Location**: `plugins/development-harness/docs/TASK_FILE_FORMAT.md:166-175`
- **Relevance**: Defines the SAM task state lifecycle (not-started → in-progress → complete / blocked / deferred / skipped) with the actor that writes each transition. This covers most of AC4 but is buried in a reference doc not linked from the workflow diagram.
- **Reusable**: The Status / Description / Written By columns map directly to the state lifecycle diagram requested in AC4.

#### Pattern 3: Plan Schema and Task Schema in TASK_FILE_FORMAT.md

- **Location**: `plugins/development-harness/docs/TASK_FILE_FORMAT.md:100-178`
- **Relevance**: Defines both plan-level fields (`plan_number`, `slug`, `goal`, `context`, `acceptance_criteria`, `issue`, `feature`, `status`, `tasks`) and task-level required and optional fields with types. These are the data structure shapes for the SAM edges in AC2.
- **Reusable**: Both field tables are complete and sourced from Pydantic models — they are the authoritative shapes for the SAM side.

#### Pattern 4: backlog_add MCP Tool Signature

- **Location**: `plugins/development-harness/backlog_core/server.py:69-79`
- **Relevance**: Shows the backlog item fields at creation: `title`, `priority` (P0/P1/P2/Ideas), `description`, `source`, `type_` (Feature/Bug/Refactor/Docs/Chore), `create_issue`, `force`. This is the data shape for the backlog-side edges in AC2.
- **Reusable**: The parameter set documents the backlog item schema at the MCP tool boundary.

#### Pattern 5: Data Flow Diagram in local-workflow.md

- **Location**: `.claude/rules/local-workflow.md` (Data Flow Diagram section)
- **Relevance**: The existing diagram names all nodes (agents, skills, artifacts) but uses only artifact file paths as edge labels — no field shapes. The new document supplements this by adding payload schemas to each labeled edge.
- **Reusable**: The node inventory in the existing diagram is the starting point for AC1.

### Existing Infrastructure

- `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — complete task schema, authorized writers table, status lifecycle. The new document can cross-reference this rather than duplicate it.
- `plugins/development-harness/backlog_core/models.py` — Pydantic models for backlog items; path `.claude/backlog/*.md` per-item files are the local cache; GitHub Issues are the source of truth.
- `plugins/development-harness/backlog_core/server.py` — all 8 backlog MCP tool signatures with annotated parameter types.
- `.claude/docs/` directory — existing location for workflow reference documents; the new file belongs here.

### Code References

- `plugins/development-harness/backlog_core/server.py:69-79` — `backlog_add` tool signature (backlog item creation fields)
- `plugins/development-harness/backlog_core/models.py:42` — `BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"` (storage location)
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:100-130` — Plan schema (plan-level fields)
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:131-178` — Task schema (task-level required and optional fields)
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:166-175` — Status values with writers
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md:186-196` — Authorized writers table
- `.claude/rules/local-workflow.md` — existing data flow diagram (node inventory for AC1)

---

## Use Scenarios

### Scenario 1: Agent reading TaskAssignment before implementing a task

**Actor**: `start-task` skill (or any agent delegated a task)
**Trigger**: Orchestrator sends a task ID; agent calls `sam read P{N}/T{M} --format json`
**Goal**: Know which fields in the returned `TaskAssignment` are safe to read, especially whether `context`, `skills`, `dependencies`, and `body` are always present or optional
**Expected Outcome**: The diagram document shows the `sam_read` → agent edge with the `TaskAssignment` schema, listing required vs optional fields so the agent knows `skills` may be absent and `dependencies` is always a list (possibly empty)

### Scenario 2: swarm-task-planner creating a new plan

**Actor**: `swarm-task-planner` agent
**Trigger**: Receives architecture spec and feature context; must call `sam create` to write the plan
**Goal**: Know what fields are required in the YAML passed to `sam create` and how the `acceptance-criteria-structured` flag triggers T0/TN bookend task generation
**Expected Outcome**: The diagram shows the `swarm-task-planner` → `sam create` edge with the YAML schema and the conditional T0/TN node with the triggering condition

### Scenario 3: Hook script updating task status on SubagentStop

**Actor**: `task_status_hook.py` SubagentStop handler
**Trigger**: A sub-agent finishes; hook reads `.claude/context/active-task-{session_id}.json`
**Goal**: Know the exact shape of the context file (fields: `task_file_path`, `task_id`, `parent_issue_number`) and what happens when `parent_issue_number` is absent
**Expected Outcome**: AC6 documents the trigger condition (SubagentStop event) and the context file schema the hook expects, including the optional `parent_issue_number` field and its effect on GitHub sync

### Scenario 4: Orchestrator linking a backlog item to a SAM plan

**Actor**: Orchestrator running `/add-new-feature`
**Trigger**: `swarm-task-planner` produces `plan/tasks-{N}-{slug}.md`; orchestrator needs to attach it to the backlog item via `backlog_update`
**Goal**: Know the exact `backlog_update` call signature — which parameter receives the plan file path (`plan=`), what the selector is
**Expected Outcome**: AC5 cross-system edge shows backlog item (GitHub issue number) → SAM plan (`issue:` field in plan YAML) → context file with the field names at each link

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | AC1 says "8 MCP tools, 4 skills, 14 agents, 2 hooks, 5 CLI commands" — these counts need verification against the actual codebase before the diagram can claim completeness | Diagram could miscount nodes; implementer must audit all components |
| 2 | Behavior | The backlog item schema (fields present in `.claude/backlog/*.md` files) is not fully captured in the server.py read so far — only creation fields are confirmed | AC2 edge shapes for backlog-read operations (backlog_view, backlog_list) may be incomplete |
| 3 | Behavior | `sam_ready` returns a list — the exact shape of each item in `ready_tasks` (does it include `skills`, `agent`, `dependencies`?) is referenced in local-workflow.md but not verified against the actual sam_schema models | Orchestrator agents may misread the ready-task payload |
| 4 | Scope | The document lives at `.claude/docs/workflow-architecture-diagram.md` but the link from `local-workflow.md` is unspecified — where exactly in `local-workflow.md` the link should appear is not stated | Implementer must decide placement (near Data Flow Diagram section, or at top) |
| 5 | Integration | The `context file` (`.claude/context/active-task-{session_id}.json`) is a runtime artifact not currently mentioned in `local-workflow.md`'s node list — it is only documented in the hook section | AC5 cross-system edge requires this to be treated as a first-class node |

---

## Questions Requiring Resolution

### Q1: Backlog item full schema

- **Category**: Behavior
- **Gap**: The `backlog_add` tool signature covers creation fields. The full per-item file schema (what fields exist in `.claude/backlog/*.md` and what `backlog_view` returns) is not confirmed from the files read.
- **Question**: Is the full backlog item schema documented somewhere (e.g., a Pydantic model in `backlog_core/models.py` beyond what was read, or a schema JSON file)? Or should the implementer read `models.py` fully to extract it?
- **Options**:
  - A) A `BacklogItem` Pydantic model in `models.py` defines all fields — implementer reads it
  - B) The schema is implicit from the per-item markdown template — implementer inspects a sample `.claude/backlog/*.md` file
- **Why It Matters**: AC2 requires data shapes at every edge; backlog-read edges are undefined without this
- **Resolution**: _pending_

### Q2: Exact node count verification

- **Category**: Scope
- **Gap**: AC1 specifies exact counts: 8 MCP tools, 4 skills, 14 agents, 2 hooks, 5 CLI commands. These counts were not verified against the codebase in this research pass.
- **Question**: Are these counts pre-verified by the requester (from GitHub issue #933), or should the implementer audit and potentially correct them?
- **Options**:
  - A) Counts are pre-verified — implementer should match them exactly
  - B) Counts are approximate — implementer should audit and report actual counts
- **Why It Matters**: If the implementer discovers 9 MCP tools, they need to know whether to update AC1 or flag a discrepancy
- **Resolution**: _pending_

### Q3: `sam_ready` payload shape

- **Category**: Behavior
- **Gap**: `local-workflow.md` states the ready JSON includes `skills` per task, but the actual `sam_ready` return shape is not confirmed from the sam_schema models.
- **Question**: Does `sam_ready` return the full task object or a subset? Specifically, are `agent`, `skills`, `dependencies`, `priority`, and `complexity` all present in each ready-task entry?
- **Why It Matters**: AC2 requires the data shape on the `sam_ready` → orchestrator edge to be documented accurately
- **Resolution**: _pending_

### Q4: Link placement in local-workflow.md

- **Category**: Integration
- **Gap**: Deliverable 2 says "update local-workflow.md with link to new diagram" but does not specify where.
- **Question**: Should the link appear (A) at the top of the Data Flow Diagram section, (B) in the Supporting Scripts table, or (C) as a new "Architecture Reference" section at the top of the file?
- **Options**:
  - A) Top of the existing "Data Flow Diagram" section
  - B) New standalone section near the top of the file
  - C) Inline reference in each agent step that produces or consumes a documented artifact
- **Why It Matters**: Placement determines how discoverable the diagram is to agents parsing the file
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Produce `.claude/docs/workflow-architecture-diagram.md` documenting all workflow nodes (backlog MCP tools, SAM MCP tools, sam CLI commands, skills, agents, hooks) with data structure shapes at every inter-node edge.
2. Document the publisher-consumer relationship for every workflow artifact (who writes each field, who reads it, via what interface).
3. Document the SAM task state machine (states, valid transitions, actor that writes each transition) in a format that renders in GitHub.
4. Document the cross-system linkage chain: backlog item (GitHub issue number) → SAM plan (`issue:` field) → active-task context file (`parent_issue_number` field) → GitHub sub-issue sync.
5. Document hook trigger conditions and the input data shapes each hook expects.
6. Add a link from `.claude/rules/local-workflow.md` to the new diagram file.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
