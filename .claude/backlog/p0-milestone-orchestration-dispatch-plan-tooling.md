---
name: 'Milestone orchestration: dispatch plan tooling'
description: 'Create tooling to generate and read milestone dispatch plan YAML files (plan/milestone-{N}-dispatch.yaml). The dispatch plan contains: milestone metadata, conflict groups (items with overlapping files), wave assignments (parallel vs sequential grouping), and quality gate commands. Consumed by /work-milestone to orchestrate parallel execution. Extend sam CLI or create a new script.'
metadata:
  topic: milestone-orchestration-dispatch-plan-tooling
  source: Milestone orchestration design — .claude/reports/milestone-orchestration-design-20260320.md
  added: '2026-03-20'
  priority: P0
  type: Feature
  status: open
  issue: '#920'
  last_synced: '2026-03-21T00:44:16Z'
  groomed: '2026-03-21'
  plan: plan/tasks-2-dispatch-plan-tooling.md
---

## Groomed (2026-03-21)

### Acceptance Criteria

<div><sub>2026-03-21T00:42:51Z</sub>

- [ ] Dispatch plan generation produces valid YAML matching the schema (milestone.number, milestone.title, milestone.integration_branch, conflict_groups[], waves[], quality_gates)
- [ ] Conflict groups correctly identify items with overlapping file paths (two items in same group iff Impact Radius paths share a directory prefix)
- [ ] Wave assignments respect dependency ordering (no item depends on an item in a later wave)
- [ ] Wave 1 contains all items with zero dependencies and no conflict group overlap
- [ ] Subsequent waves unblock based on dependency resolution and conflict group serialization
- [ ] Dispatch plan reading returns typed objects (Python dataclass or Pydantic model) with validated schema
- [ ] Reader validates that all items referenced in waves exist in the milestone and are still open on GitHub
- [ ] Reader validates dependency DAG contains no cycles
- [ ] Quality gates commands (pre_merge, post_merge) are correctly read and returned as lists
- [ ] Dispatch plan file written and read successfully in `/groom-milestone` and `/work-milestone` integration tests
- [ ] All YAML parsing/writing uses existing sam_schema patterns (ruamel.yaml with comments preserved)
</div>

### Files

<div><sub>2026-03-21T00:42:58Z</sub>

**Generated artifact** (written by `/groom-milestone` Step 9):
- `plan/milestone-{N}-dispatch.yaml` — dispatch plan YAML file with milestone metadata, conflict groups, wave assignments, and quality gates

**Implementation locations** (to be determined by agent):
- Extend `plugins/development-harness/backlog_core/` with dispatch plan generation module, OR
- Extend sam CLI with new dispatch plan commands (`sam dispatch generate`, `sam dispatch read`), OR
- Create new script in `plugins/development-harness/scripts/` for dispatch plan operations

**Existing patterns to follow**:
- `plugins/development-harness/backlog_core/` — existing backlog YAML operations module
- `sam_schema/` — existing YAML handling patterns using ruamel.yaml
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` — reference for task metadata structure and format utilities

**Testing locations**:
- Test fixtures: `plan/` directory in test milestone (created as part of `/groom-milestone` test)
- Test runner: `/work-milestone` Step 1 validation confirms dispatch plan exists and is readable
</div>

### Dependencies

<div><sub>2026-03-21T00:43:05Z</sub>

**Hard dependencies** (must exist before this work starts):
- Backlog MCP server (`backlog_list_issues`, `backlog_view`) — reads groomed items and Impact Radius
- sam CLI (`sam status`, `sam read`) — already exists for task file operations; can be reused or extended
- ruamel.yaml library — existing dependency in project (used in sam_schema/)
- Python 3.11+ (project standard)

**Soft dependencies** (nice to have, not blocking):
- Pydantic v2 — if used for dispatch plan validation model (not required; can use dataclass)
- Existing conflict group algorithm from gastown research — informs the implementation approach but no code dependency

**Downstream dependencies** (this work unblocks):
- `/groom-milestone` skill — depends on dispatch plan generation (Step 9)
- `/work-milestone` skill — depends on dispatch plan reading and validation (Step 1)
- Wave-based parallel execution — depends on correct wave assignment in dispatch plan

**Not dependent on**:
- Integration branch lifecycle tooling — separate backlog item, `/work-milestone` calls those operations independently
- Quality gate execution — `/work-milestone` calls gate commands directly from dispatch plan
</div>

### Effort

<div><sub>2026-03-21T00:43:14Z</sub>

**Estimated complexity**: Medium (algorithms exist, integration is straightforward)

**Effort breakdown**:

1. **Schema definition and types** (2 hours): Define Python dataclass or Pydantic model matching the dispatch plan YAML schema. Include validation constraints (no cycles in dependencies, all items exist, conflict groups are consistent).

2. **Conflict group algorithm** (3 hours): Implement file overlap detection. Read Impact Radius from all items. Build overlap matrix. Group items by shared directory prefixes. Validate groups are minimal (no unnecessary serialization).

3. **Wave assignment algorithm** (4 hours): Implement topological sort of dependency DAG. Assign items to waves based on: dependency constraints (no item before its dependencies), priority ordering (P0 > P1 > P2 within each wave), and conflict serialization (items in same conflict group cannot be in same wave unless dependencies allow).

4. **YAML generation** (2 hours): Populate dispatch plan object. Write to YAML using ruamel.yaml (preserve comments and structure). Call from `/groom-milestone` Step 9. Write metadata fields (milestone number, title, integration_branch name).

5. **YAML reading and validation** (2 hours): Parse YAML into typed objects. Validate schema, item existence on GitHub, dependency DAG integrity. Provide accessor methods for `/work-milestone` wave iteration and item lookup.

6. **Integration and testing** (3 hours): Wire generation into `/groom-milestone`. Wire reading into `/work-milestone`. Create test fixtures with 3+ items across different conflict groups. End-to-end test with a real milestone.

**Total estimate**: 16 hours, can be parallelized (algorithms 1–3 independent, testing can run on generated outputs)
</div>

### Impact Radius

<div><sub>2026-03-21T00:44:03Z</sub>

### Architecture Decision
New module `plugins/development-harness/dispatch_schema/` parallel to `sam_schema/`. Separation of concerns: individual task plans (sam) vs milestone-level dispatch plans.

### Code — New Module
- `plugins/development-harness/dispatch_schema/__init__.py` — exports
- `plugins/development-harness/dispatch_schema/models.py` — Pydantic models (DispatchPlan, ConflictGroup, Wave, WaveItem, QualityGates)
- `plugins/development-harness/dispatch_schema/reader.py` — load_dispatch_plan() from YAML
- `plugins/development-harness/dispatch_schema/writer.py` — write_dispatch_plan() to YAML
- `plugins/development-harness/dispatch_schema/validator.py` — validate dispatch plan integrity
- `plugins/development-harness/tests/test_dispatch_schema.py` — tests

### Code — Modifications
- `plugins/development-harness/backlog_core/operations.py` — add analyze_impact_radius_conflicts() to build conflict matrix from Impact Radius sections

### Generated Artifacts
- `plan/milestone-{N}-dispatch.yaml` — dispatch plan files written by /groom-milestone

### Consumers
- `/groom-milestone` skill (to be created) — writes dispatch plan
- `/work-milestone` skill (to be created) — reads dispatch plan

### No Breaking Changes
All new artifacts and modules. No existing interfaces modified.
</div>

## RT-ICA

<div><sub>2026-03-21T00:44:16Z</sub>

**RT-ICA Final**: Milestone orchestration: dispatch plan tooling

**Goal**: Create tooling to generate and read milestone dispatch plan YAML files

**Conditions**:
1. Dispatch plan YAML schema | Snapshot: AVAILABLE → Final: AVAILABLE | design doc has full schema
2. Where to place tooling | Snapshot: DERIVABLE → Final: AVAILABLE | impact analyst: new dispatch_schema/ module
3. Existing YAML patterns | Snapshot: DERIVABLE → Final: AVAILABLE | sam_schema/ uses ruamel.yaml + Pydantic models
4. Consumer interface | Snapshot: AVAILABLE → Final: AVAILABLE | /groom-milestone writes, /work-milestone reads
5. Conflict group definition | Snapshot: AVAILABLE → Final: AVAILABLE | file overlap from Impact Radius
6. Wave assignment algorithm | Snapshot: AVAILABLE → Final: AVAILABLE | priority + dependency ordering

**Changes from snapshot**: Condition 2 resolved (new dispatch_schema/ module), Condition 3 resolved (ruamel.yaml + Pydantic)
**Decision**: APPROVED
</div>