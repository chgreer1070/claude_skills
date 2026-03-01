# Task Plan: SAM Task Skills Context Propagation

Fixes #338

**Feature**: SAM Task Skills Context Propagation
**Architecture Spec**: [architect-sam-task-skills-context.md](./architect-sam-task-skills-context.md)
**Feature Context**: [feature-context-sam-task-skills-context.md](./feature-context-sam-task-skills-context.md)

---

## Task 1.1: Add `skills:` Field to TASK_FILE_FORMAT.md

**Status**: NOT STARTED
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose

### Context

The task YAML schema in `.claude/docs/TASK_FILE_FORMAT.md` defines all recognized frontmatter fields for SAM task files. The `skills` field does not exist in the schema, the JSON schema definition, the optional fields table, or the template. Without it, planners have no slot to declare which skills a sub-agent needs, and parsers have no basis for extracting or validating the field.

### Objective

Add the `skills` field to every relevant section of TASK_FILE_FORMAT.md so that the field is schema-defined, documented, and included in examples and templates.

### Requirements

1. Add `skills` to the JSON Schema `properties` object (after `parallelize-with`), typed as `array` of `string` with default `[]`
2. Add `skills` row to the Optional Fields table with type `array`, description, and example
3. Add `skills:` to the YAML template in the Template File section with an inline comment
4. Add `skills` to the Conversion Example showing legacy format `**Skills**: skill1, skill2` mapped to YAML `skills: [skill1, skill2]`
5. Add `skills` to the Field Mapping table (Old Format `**Skills**: skill1, skill2` to New Format `skills: [skill1, skill2]`)

### Acceptance Criteria

- [ ] JSON schema at lines 264-345 contains a `"skills"` property with `type: array`, `items: {type: string}`, `default: []`
- [ ] Optional Fields table includes a `skills` row with type `array` and example `["fastmcp-python-tests", "python3-development"]`
- [ ] Template file section includes `skills: []` with comment `# OPTIONAL: Skills for sub-agent to load`
- [ ] Legacy format example shows `**Skills**: fastmcp-python-tests, python3-development`
- [ ] Field Mapping table includes the `skills` conversion row

### Verification Steps

1. Read `.claude/docs/TASK_FILE_FORMAT.md` and confirm the JSON schema `properties` object contains the `skills` property with correct type, items, and default
2. Confirm the Optional Fields table has a `skills` row between `parallelize-with` and the end of the table
3. Confirm the template section includes `skills: []` with the OPTIONAL comment

### File

- `.claude/docs/TASK_FILE_FORMAT.md`

---

## Task 2.1: Add Skills Mapping and `skills:` Generation to python3-development Swarm-Task-Planner

**Status**: NOT STARTED
**Dependencies**: Task 1.1
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose

### Context

The swarm-task-planner agent at `plugins/python3-development/agents/swarm-task-planner.md` generates task YAML frontmatter during Phase 4 of `/add-new-feature`. Its current template (lines 250-263) does not include a `skills:` field, and its Agent Assignment Rules table (lines 315-325) maps task types to agents but has no column for associated skills. The architecture spec (Section 2) defines a keyword-to-skill mapping table and template update.

### Objective

Add the skills mapping table, update the task YAML template to include `skills:`, and add a validation step so the planner auto-populates skills based on task content.

### Requirements

1. Add a "Skills Mapping Table" section after the Agent Assignment Rules section, containing the mapping from architecture spec Section 2.1
2. Update the task YAML frontmatter template to include `skills: []` between `accuracy-risk` and `parallelize-with`
3. Add rules for: (a) architecture spec override, (b) union of multiple matches, (c) empty list when no pattern matches, (d) extensibility note
4. Add validation step 10 to Phase 5 (Plan Validation): skills field check verifying every task has `skills` in frontmatter, values are valid skill activation names, and architecture-prescribed skills are present

### Acceptance Criteria

- [ ] A "Skills Mapping Table" section exists in the agent prompt with at least 6 pattern rows matching the architecture spec
- [ ] The YAML template includes `skills: []` in the correct position
- [ ] Rules 1-4 from architecture spec Section 2.1 are documented below the table
- [ ] Phase 5 validation includes step 10 checking skills field presence, value format, and architecture spec compliance

### Verification Steps

1. Read `plugins/python3-development/agents/swarm-task-planner.md` and confirm the Skills Mapping Table section exists after Agent Assignment Rules
2. Confirm the YAML template between the `---` delimiters includes `skills: []`
3. Confirm Phase 5 validation includes a step numbered 10 with skills field checks

### File

- `plugins/python3-development/agents/swarm-task-planner.md`

### Can Parallelize With

Task 2.2 (same structure, different file)

---

## Task 2.2: Add Skills Mapping and `skills:` Generation to development-harness Swarm-Task-Planner

**Status**: NOT STARTED
**Dependencies**: Task 1.1
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose

### Context

The development-harness swarm-task-planner at `plugins/development-harness/agents/swarm-task-planner.md` uses the same template structure as the python3-development version but uses `role:` instead of `agent:`. The same skills gap exists: no `skills:` field in the template, no mapping table, no validation step.

### Objective

Add the skills mapping table, update the task YAML template to include `skills:`, and add a validation step, mirroring the changes in Task 2.1 but preserving the `role:` convention.

### Requirements

1. Add a "Skills Mapping Table" section after the Agent Assignment Rules section, containing the same mapping from architecture spec Section 2.1
2. Update the task YAML frontmatter template to include `skills: []` between `accuracy-risk` and `parallelize-with`, keeping `role:` (not `agent:`)
3. Add rules for: (a) architecture spec override, (b) union of multiple matches, (c) empty list when no pattern matches, (d) extensibility note
4. Add validation step 10 to Phase 5 (Plan Validation): skills field check

### Acceptance Criteria

- [ ] A "Skills Mapping Table" section exists in the agent prompt with at least 6 pattern rows
- [ ] The YAML template includes `skills: []` and uses `role:` (not `agent:`)
- [ ] Rules 1-4 are documented below the mapping table
- [ ] Phase 5 validation includes step 10 with skills field checks

### Verification Steps

1. Read `plugins/development-harness/agents/swarm-task-planner.md` and confirm the Skills Mapping Table section exists
2. Confirm the YAML template includes both `role:` and `skills: []`
3. Confirm Phase 5 validation includes step 10

### File

- `plugins/development-harness/agents/swarm-task-planner.md`

### Can Parallelize With

Task 2.1 (same structure, different file)

---

## Task 2.3: Add `skills` Field to implementation_manager.py Data Model

**Status**: NOT STARTED
**Dependencies**: Task 1.1
**Priority**: 2
**Complexity**: Medium
**Agent**: python-cli-architect

### Context

- **File**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
- **Architecture Spec**: Section 5 (Data Model Changes)

### Objective

Add `skills` support to the implementation_manager.py data model so the `ready-tasks` command output includes the `skills` array for each task. Without this, implement-feature cannot read task-level skills from the ready-tasks JSON.

### Requirements

1. Add `skills: list[str] = field(default_factory=list)` to the `Task` dataclass
2. Add `skills` key to `TaskDict` TypedDict
3. Add `skills` to the `to_dict()` method
4. Add skills extraction to `parse_task_from_frontmatter()` — read `skills` from YAML frontmatter
5. Update `ready-tasks` command output to include `skills` array per task
6. Add `**Skills**:` line parsing to legacy markdown parser

### Acceptance Criteria

- [ ] `Task` dataclass has `skills: list[str]` field with empty list default
- [ ] `parse_task_from_frontmatter()` extracts `skills` from YAML and populates the field
- [ ] `ready-tasks` JSON output includes `"skills": [...]` for each task
- [ ] Legacy markdown parser handles `**Skills**: skill1, skill2` format
- [ ] Existing task files without `skills:` field parse without errors (backward compat)

### Verification Steps

1. Run `uv run python -m pytest` on implementation_manager tests to verify no regressions
2. Create a test task file with `skills: [fastmcp-python-tests]` and verify `ready-tasks` output includes it
3. Create a test task file WITHOUT `skills:` and verify it parses with `skills: []` default

### Can Parallelize With

Task 2.1, Task 2.2 (independent files)

---

## Task 3.1: Update implement-feature to Read `skills:` and Include in Delegation Prompt

**Status**: NOT STARTED
**Dependencies**: Task 1.1, Task 2.3
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose

### Context

The `/implement-feature` skill at `.claude/skills/implement-feature/SKILL.md` orchestrates the execution loop. Its step 3 delegates to sub-agents using `Skill(skill="start-task", args="{task_file_path} --task {task_id}")`. The ready-tasks JSON output (after implementation_manager.py changes, which are out of scope for this task plan) will include a `skills` array per task. The orchestrator must read this field and include skill-loading instructions in the delegation prompt so the sub-agent loads domain-specific context.

### Objective

Update the implement-feature SKILL.md execution loop to read the `skills` field from ready-tasks output and include skill-loading instructions in the delegation prompt sent to each sub-agent.

### Requirements

1. Update step 3 (delegation step) to check for a non-empty `skills` list in the ready task data
2. When `skills` is non-empty, add to the delegation prompt: instructions for the sub-agent to call `Skill(skill="{skill-name}")` for each skill before starting work
3. When `skills` is empty or missing, do not add skill-loading instructions (backward compatible)
4. Document that skill-loading instructions are additive to the agent's default skills

### Acceptance Criteria

- [ ] Step 3 of the execution loop includes conditional logic for non-empty `skills` list
- [ ] The delegation prompt template includes the skill-loading instruction format: `Skill(skill="{skill-name}")`
- [ ] Backward compatibility is preserved: empty or missing `skills` produces no skill-loading instructions
- [ ] A note documents that task-level skills supplement (not replace) agent-level skills

### Verification Steps

1. Read `.claude/skills/implement-feature/SKILL.md` and confirm step 3 references the `skills` field from ready-tasks output
2. Confirm the delegation prompt includes the `Skill(skill="{skill-name}")` instruction pattern
3. Confirm a conditional check for non-empty `skills` is present (not unconditional)

### File

- `.claude/skills/implement-feature/SKILL.md`

### Can Parallelize With

Task 3.2 (same dependency, different file)

---

## Task 3.2: Update start-task to Load Skills from Task Metadata at Execution Start

**Status**: NOT STARTED
**Dependencies**: Task 1.1
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose

### Context

The `/start-task` skill at `.claude/skills/start-task/SKILL.md` runs inside a sub-agent for a single task. It reads the task file, selects the task, updates status, and implements against acceptance criteria. It does not read or act on a `skills:` field. The architecture spec (Section 4) defines a step 2a that reads the `skills:` field and loads each skill via `Skill()` calls. This provides redundant safety: even if the orchestrator did not pass skill-loading instructions, the sub-agent loads skills directly from the task metadata.

### Objective

Add a step 2a to the "Starting a Task" section that reads the `skills:` field from YAML frontmatter (or `**Skills**:` from legacy format) and invokes `Skill(skill="{name}")` for each.

### Requirements

1. Add step 2a between step 2 (Select the task) and step 3 (Update status to in-progress)
2. Step 2a reads `skills:` from the task's YAML frontmatter or `**Skills**:` from legacy bold-field format
3. For each skill name in the list, invoke `Skill(skill="{skill-name}")`
4. If a skill fails to load (not found), log a warning and continue with remaining skills
5. Document that this is intentional redundancy with the orchestrator's skill-loading instructions

### Acceptance Criteria

- [ ] Step 2a exists in the "Starting a Task" section between steps 2 and 3
- [ ] Step 2a reads both YAML frontmatter `skills:` and legacy `**Skills**:` format
- [ ] Each skill triggers a `Skill(skill="{name}")` call
- [ ] Failure handling is documented: warn and continue, not abort
- [ ] A note explains the redundancy rationale (manual invocation, older orchestrator)

### Verification Steps

1. Read `.claude/skills/start-task/SKILL.md` and confirm step 2a exists between steps 2 and 3
2. Confirm step 2a mentions both YAML and legacy format parsing
3. Confirm the error handling instruction says to warn and continue, not abort

### File

- `.claude/skills/start-task/SKILL.md`

### Can Parallelize With

Task 3.1 (same dependency, different file)

---

## Task 4.1: Update local-workflow.md to Document `skills:` Field in SAM Pipeline Documentation

**Status**: NOT STARTED
**Dependencies**: Task 1.1, Task 2.1, Task 2.2, Task 2.3, Task 3.1, Task 3.2
**Priority**: 3
**Complexity**: Low
**Agent**: general-purpose

### Context

The SAM workflow reference at `.claude/rules/local-workflow.md` documents the full pipeline from planning through execution to quality gates. It does not mention the `skills:` field anywhere. After the preceding tasks add skills support to the schema, planners, orchestrator, and executor, the workflow documentation must reflect the new field so that agents and humans consulting this reference understand the skills propagation mechanism.

### Objective

Update local-workflow.md to document the `skills:` field at each relevant stage of the SAM pipeline: task file format, planner output, execution loop, and start-task actions.

### Requirements

1. In the "Task File Format" section (under "Key fields per task"), add `**Skills**`: list of skill names for the sub-agent
2. In the "Execution Loop" section, add a sub-step noting that `skills` from ready-tasks output is included in the delegation prompt
3. In the "Phase 2a: Task Execution" actions list, add the step 2a for loading skills from task metadata
4. In the "Data Flow Diagram", add a line showing skills propagation from task file through orchestrator to sub-agent

### Acceptance Criteria

- [ ] The "Key fields per task" list includes `**Skills**`
- [ ] The execution loop section mentions reading `skills` from ready-tasks output
- [ ] The Phase 2a actions list includes the skills-loading step
- [ ] The data flow diagram includes at least one line referencing skills propagation

### Verification Steps

1. Read `.claude/rules/local-workflow.md` and search for "skills" to confirm all four required additions are present
2. Confirm the data flow diagram shows skills flowing from task file through the orchestrator to the sub-agent
3. Confirm no existing content was removed or broken by the additions

### File

- `.claude/rules/local-workflow.md`

---

## Task 4.2: Validate by Dry-Running the Planner on an Example Test-Writing Feature

**Status**: NOT STARTED
**Dependencies**: Task 1.1, Task 2.1, Task 2.2, Task 3.1, Task 3.2, Task 4.1
**Priority**: 3
**Complexity**: Low
**Agent**: general-purpose

### Context

All preceding tasks modify agent prompts, skill definitions, and documentation. The changes are to instruction text, not executable code. Validation requires confirming that the modified planner prompt, when given a test-writing feature request, would produce task YAML that includes the `skills:` field with appropriate values. This is a manual review / dry-run validation, not an automated test.

### Objective

Verify end-to-end correctness by reading the modified planner prompt and confirming it would produce correct `skills:` output for a representative test-writing scenario.

### Requirements

1. Read the updated `plugins/python3-development/agents/swarm-task-planner.md` and confirm the skills mapping table maps test-related keywords to `fastmcp-python-tests` and `python3-development`
2. Read the updated `plugins/development-harness/agents/swarm-task-planner.md` and confirm the same mapping exists
3. Read the updated `.claude/skills/implement-feature/SKILL.md` and confirm the delegation prompt includes skill-loading instructions
4. Read the updated `.claude/skills/start-task/SKILL.md` and confirm step 2a reads `skills:` and loads each skill
5. Read the updated `.claude/docs/TASK_FILE_FORMAT.md` and confirm the JSON schema includes the `skills` property
6. Construct a hypothetical task YAML for "Create pytest integration tests for FastMCP server" and verify the planner's mapping table would produce `skills: [fastmcp-python-tests, python3-development]`

### Acceptance Criteria

- [ ] Both planner agents have consistent skills mapping tables with test-related keywords
- [ ] The implement-feature delegation prompt references `skills` from ready-tasks output
- [ ] The start-task skill includes step 2a with `Skill()` invocations for each skill
- [ ] The TASK_FILE_FORMAT.md JSON schema includes `skills` with correct type
- [ ] A hypothetical test-writing task would receive `skills: [fastmcp-python-tests, python3-development]` based on the mapping table

### Verification Steps

1. Read all 5 modified files and confirm changes are present and consistent
2. Trace the data flow: planner generates `skills:` -> task file stores it -> implement-feature reads it from ready-tasks -> delegation prompt includes it -> start-task loads it
3. Confirm no conflicts or inconsistencies between the files

### Files

- `plugins/python3-development/agents/swarm-task-planner.md`
- `plugins/development-harness/agents/swarm-task-planner.md`
- `.claude/skills/implement-feature/SKILL.md`
- `.claude/skills/start-task/SKILL.md`
- `.claude/docs/TASK_FILE_FORMAT.md`
- `.claude/rules/local-workflow.md`

---

## Context Manifest

### How the SAM Skills Propagation Pipeline Currently Works

When a user invokes `/add-new-feature`, the orchestrator runs Phase 4 which delegates to the `swarm-task-planner` agent. This agent reads the architecture spec and generates task YAML frontmatter for each task. The current YAML template in the python3-development planner (lines 250-263 of `plugins/python3-development/agents/swarm-task-planner.md`) produces fields like `task`, `title`, `status`, `agent`, `dependencies`, `priority`, `complexity`, `accuracy-risk`, `parallelize-with`, `reason`, and `handoff`. The development-harness variant (lines 249-262) is identical except it uses `role:` instead of `agent:`. Neither planner generates a `skills:` field because the field does not exist in the schema and has no mapping table to drive population.

Once the task file is written, the user invokes `/implement-feature`. This skill runs a progress loop: it queries `implementation_manager.py ready-tasks` which returns JSON containing `id`, `name`, and `agent` per ready task (line 1031 of `implementation_manager.py`). The `Task` dataclass (lines 89-113) has no `skills` field, so the ready-tasks output cannot include skills even if the task file contained them. The orchestrator then delegates each task to a sub-agent using `Skill(skill="start-task", args="{task_file_path} --task {task_id}")` (lines 58-65 of `implement-feature/SKILL.md`). No skill-loading instructions are included in the delegation prompt.

Inside the sub-agent, `/start-task` reads the task file, selects the target task, updates status to `in-progress`, writes the active-task context file, and implements against acceptance criteria (lines 65-88 of `start-task/SKILL.md`). It never reads a `skills:` field from the task metadata and never invokes `Skill()` to load domain-specific context. The sub-agent operates only with skills declared in the agent definition file's frontmatter, which are static per agent type and do not vary per task.

The task YAML schema at `.claude/docs/TASK_FILE_FORMAT.md` defines JSON schema properties (lines 264-345) for `task`, `title`, `status`, `agent`, `dependencies`, `priority`, `complexity`, `created`, `started`, `completed`, `blocked-by`, and `parallelize-with`. There is no `skills` property. The Optional Fields table (lines 138-149), the YAML template (lines 617-631), the Conversion Example (lines 456-491), and the Field Mapping table (lines 494-503) all lack any mention of skills.

### What This Task Plan Changes

This task plan closes the three broken links in the skills propagation chain identified in the feature context document:

1. **Task 1.1** adds the `skills` field to the TASK_FILE_FORMAT.md schema (JSON schema, Optional Fields table, template, conversion example, field mapping).
2. **Tasks 2.1 and 2.2** add a Skills Mapping Table to both swarm-task-planner agents so they auto-populate `skills:` during task generation, plus update the YAML template and add validation step 10 to Phase 5.
3. **Task 3.1** updates `/implement-feature` to read `skills` from ready-tasks JSON output and include skill-loading instructions in the delegation prompt.
4. **Task 3.2** updates `/start-task` to read `skills:` from task frontmatter and invoke `Skill()` for each (redundant safety for manual invocation or older orchestrators).
5. **Task 4.1** updates `.claude/rules/local-workflow.md` to document skills propagation at every relevant stage.
6. **Task 4.2** performs end-to-end dry-run validation by reading all modified files.

The architecture spec also prescribes changes to `implementation_manager.py` (Section 5: add `skills` to `Task` dataclass, `TaskDict`, `to_dict()`, `parse_task_from_frontmatter()`, and ready-tasks output). Those data model changes are explicitly out of scope for this task plan. Tasks 3.1 and 3.2 assume the ready-tasks output will eventually include `skills` but their changes are written to be backward compatible (conditional on non-empty `skills`).

### Files Directly Modified by Tasks

| Path | Purpose |
|------|---------|
| `.claude/docs/TASK_FILE_FORMAT.md` | Task YAML schema definition. Task 1.1 adds `skills` to: JSON schema `properties` (after `parallelize-with`, lines 335-343), Optional Fields table (lines 138-149), YAML template (lines 617-631), Conversion Example (lines 456-491), Field Mapping table (lines 494-503). Task 4.2 reads for validation. |
| `plugins/python3-development/agents/swarm-task-planner.md` | python3-development swarm-task-planner agent prompt. Task 2.1 adds: Skills Mapping Table section (after Agent Assignment Rules at line 325), `skills: []` to YAML template (between `accuracy-risk` and `parallelize-with` at lines 259-260), validation step 10 to Phase 5 (after step 9 at line 484). Task 4.2 reads for validation. |
| `plugins/development-harness/agents/swarm-task-planner.md` | development-harness swarm-task-planner agent prompt. Task 2.2 mirrors Task 2.1 changes, preserving `role:` convention (line 254). Skills Mapping Table after Agent Assignment Rules (line 326), `skills: []` to template (between `accuracy-risk` and `parallelize-with` at lines 258-259), validation step 10 to Phase 5 (after step 9 at line 484). Task 4.2 reads for validation. |
| `.claude/skills/implement-feature/SKILL.md` | SAM execution loop orchestrator skill. Task 3.1 updates step 3 (lines 58-65) to check for non-empty `skills` in ready-tasks output and add skill-loading instructions (`Skill(skill="{skill-name}")`) to the delegation prompt. Backward compatible: empty or missing `skills` produces no instructions. Task 4.2 reads for validation. |
| `.claude/skills/start-task/SKILL.md` | Sub-agent task execution skill. Task 3.2 inserts step 2a between step 2 (Select task, line 69) and step 3 (Update status, line 72): read `skills:` from YAML frontmatter or `**Skills**:` from legacy format, invoke `Skill(skill="{name}")` for each, warn and continue on load failure. Task 4.2 reads for validation. |
| `.claude/rules/local-workflow.md` | SAM workflow reference documentation. Task 4.1 adds: `**Skills**` to Key fields per task (line 72), skills reading note to Execution Loop (lines 117-120), step 2a to Phase 2a actions (lines 158-170), skills propagation line to Data Flow Diagram (lines 289-339). Task 4.2 reads for validation. |

### Planning and Architecture References (Read-Only)

| Path | Purpose |
|------|---------|
| `plan/architect-sam-task-skills-context.md` | Architecture spec defining all changes across 8 sections: schema changes, planner changes (keyword-to-skill mapping table with 6 pattern rows, template update, validation step), orchestrator changes (modified ready-tasks JSON shape, delegation prompt with skill-loading), start-task changes (step 2a, redundancy rationale), data model changes (out of scope), backward compatibility guarantees, file change summary, data flow diagram. Referenced by all tasks. |
| `plan/feature-context-sam-task-skills-context.md` | Feature discovery document with evidence inventory. Documents the three broken links (no `skills:` in schema, `start-task` ignores fields, `implement-feature` lacks skill context). Lists current state with line-number references for every claim. Defines desired state and constraints (backward compatibility, schema consistency, dual-format support, no breaking changes to agent definitions). Open questions resolved by architecture spec. Referenced by all tasks for problem context. |

### Data Model and Parsing Scripts (Not Modified by This Plan)

| Path | Purpose |
|------|---------|
| `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` | CLI for task status queries. `Task` dataclass (lines 89-113) lacks `skills`. `TaskDict` (lines 175-190) and `TaskData` (lines 157-172) TypedDicts lack `skills`. `to_dict()` (lines 115-131) does not serialize `skills`. `parse_task_from_frontmatter()` (line 352) does not extract `skills`. `ready-tasks` output (line 1031) returns `id`, `name`, `agent` without `skills`. Architecture spec Section 5 prescribes adding `skills` to all of these; those changes are out of scope for this task plan but Tasks 3.1 and 3.2 reference the expected future output format. |
| `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` | Shared YAML frontmatter utilities. Field-agnostic functions (`has_yaml_frontmatter`, `normalize_status`, `parse_yaml_frontmatter`, `update_yaml_field`). No changes needed for `skills` field. |
| `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` | Hook script for `SubagentStop` and `PostToolUse` events. Handles status and timestamps only. No `skills` relevance. No changes needed. |
| `plugins/python3-development/scripts/split_task_file.py` | Splits monolithic task files into per-task files. Preserves all frontmatter fields generically. No changes needed. |
| `plugins/python3-development/scripts/migrate_task_format.py` | Migrates legacy markdown to YAML frontmatter. Missing `skills` defaults to empty list. No changes needed. |
| `plugins/python3-development/templates/sam-task-template.md` | Task YAML template for new task creation. Currently lacks `skills:` field. May need updating in a follow-up (not in this plan's scope). |

### Workflow and Pipeline References (Read-Only Context)

| Path | Purpose |
|------|---------|
| `.claude/skills/add-new-feature/SKILL.md` | Planning skill that invokes swarm-task-planner in Phase 4. Planner changes in Tasks 2.1/2.2 affect output generated during this phase. |
| `.claude/skills/implementation-manager/SKILL.md` | Skill providing `status` and `ready-tasks` CLI commands consumed by `/implement-feature`. |
| `.claude/skills/complete-implementation/SKILL.md` | Quality gates skill invoked after all tasks complete. Next step in pipeline after `/implement-feature`. Not modified by this plan. |
| `plugins/python3-development/skills/implementation-manager/scripts/get_task_context.py` | Dynamic context injection for implementation-manager skill. Not modified. |

---

## Parallelization Summary

```text
Group 1: Task 1.1 (no dependencies)
           |
     +-----+-----+
     |             |
Group 2: Task 2.1  Task 2.2  (parallel, both depend on 1.1)
     |             |
     +-----+-----+
           |
     +-----+-----+
     |             |
Group 3: Task 3.1  Task 3.2  (parallel, both depend on 1.1)
     |             |
     +-----+-----+
           |
Group 4: Task 4.1 (depends on 1.1, 2.1, 2.2, 3.1, 3.2)
           |
         Task 4.2 (depends on all prior)
```

**Note**: Groups 2 and 3 can also run in parallel with each other since they share only the Task 1.1 dependency. The critical path is: 1.1 -> (2.1 || 2.2 || 3.1 || 3.2) -> 4.1 -> 4.2.
