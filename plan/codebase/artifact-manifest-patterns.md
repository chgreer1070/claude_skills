# Plan Artifact Manifest Patterns

**Document Purpose**: Map how plan artifacts are currently created, stored, referenced, and accessed across the SAM workflow. This document describes WHAT EXISTS TODAY — observed patterns, current naming conventions, storage structures, and integration points.

**Analysis Date**: 2026-03-21

---

## 1. Artifact Creation Patterns

### 1.1 Feature Discovery Phase (Phase 1)

Plan artifacts are created by specialized agents during the feature discovery phase, each writing to a specific path pattern.

#### `feature-context-{slug}.md`

**Created by**: `feature-researcher` agent
**Location**: `plan/feature-context-{slug}.md`
**Triggering Skill**: `/add-new-feature`
**Agent File**: `plugins/development-harness/agents/feature-researcher.md` (line 17)

**Content Structure**:
- Core Intent Analysis (WHO, WHAT, WHEN, WHY)
- Questions Requiring Resolution
- Goals (Pending Resolution)
- Similar Patterns Found

**Downstream Consumers**:
- RT-ICA skill (orchestrator) — verifies completeness of WHO/WHAT/WHEN/WHY
- Orchestrator — uses questions section to ask user via AskUserQuestion
- python-cli-design-spec agent — uses resolved goals for architecture
- swarm-task-planner agent — uses resolved requirements to create tasks

**Naming Convention**: Slug derived from feature request (user-provided). Example: `feature-context-redesign-work-milestone-worktree-agents.md`

#### `architect-{slug}.md`

**Created by**: `python-cli-design-spec` agent
**Location**: `plan/architect-{slug}.md`
**Triggering Skill**: `/add-new-feature`
**Agent File**: `plugins/python3-development/agents/python-cli-design-spec.md`

**Content Structure**:
- Architecture specification with component definitions, API design, data models
- Integration points with existing codebase
- Design decisions and rationale

**Downstream Consumers**:
- swarm-task-planner agent — uses architecture to create task dependencies
- codebase-analyzer agent — verifies architecture compliance with existing patterns
- All implementation tasks reference this architecture

**Naming Convention**: `architect-{slug}.md` — same slug as the feature context

#### `plan/codebase/{FOCUS}.md` (Optional)

**Created by**: `codebase-analyzer` agent
**Location**: `plan/codebase/{FOCUS}.md` where FOCUS is one of: PATTERNS, ARCHITECTURE, TESTING, CONVENTIONS, CONCERNS
**Triggering Skill**: `/add-new-feature` (optional, when feature scope requires codebase analysis)
**Agent File**: `plugins/development-harness/agents/codebase-analyzer.md` (line 10-11)

**Focus Areas** (line 20-24):
- `PATTERNS.md` — CLI command patterns and shared utilities
- `ARCHITECTURE.md` — module structure and dependencies
- `TESTING.md` — test patterns and coverage
- `CONVENTIONS.md` — coding conventions and style
- `CONCERNS.md` — technical debt, fragile areas, and issues

**Content Structure** (observational, file path focused, prescriptive):
- Verified patterns with file paths
- Code examples with `file:line` references
- Actionable guidance for downstream agents

**Downstream Consumers**:
- python-cli-architect agent — follows conventions when writing code
- python-pytest-architect agent — matches testing patterns
- python-cli-design-spec agent — uses patterns to design consistent architecture

#### `plan/tasks-{N}-{slug}.md`

**Created by**: `swarm-task-planner` agent
**Location**: `plan/tasks-{N}-{slug}.md` where N is a sequential number (e.g., `plan/tasks-5-redesign-work-milestone.md`)
**Triggering Skill**: `/add-new-feature`
**Agent File**: `plugins/development-harness/agents/swarm-task-planner.md` (line 3)

**YAML Frontmatter Structure**:
```yaml
feature: "{slug}"
version: '1.0'
description: '{brief description}'
goal: '{plan goal}'
context: 'See Context Manifest section below.'
issue: '{github_issue_number}'

tasks:
  - id: T01
    title: 'Task title'
    status: not-started | in-progress | complete | blocked
    agent: plugin-name:agent-name
    priority: 1-5
    complexity: low | medium | high
    skills:
      - skill-name:skill-name
    description: |
      {CLEAR formatted task description}
    acceptance-criteria: |
      {Acceptance criteria list}
    verification-steps: |
      {Verification commands/checks}
    started: '{ISO timestamp}'
    completed: '{ISO timestamp}'
    last-activity: '{ISO timestamp}'
    dependencies:
      - T02
      - T03
```

**Key Fields** (from `plugins/development-harness/agents/swarm-task-planner.md`):
- `feature`: slug identifying the plan
- `goal`: human-readable goal statement
- `issue`: GitHub issue number (optional, links to backlog)
- `context`: Reference to Context Manifest section
- `tasks`: array of individual task objects
- Per-task: status, agent, priority, complexity, skills, dependencies, acceptance-criteria, verification-steps

**Task Format Options** (from `.claude/rules/local-workflow.md` line 79-87):
- **Legacy markdown**: Monolithic file with `## Task {ID}: {Name}` headers
- **YAML frontmatter**: Individual `.md` files with `---` delimited metadata per task
- **Single file**: All tasks in one `plan/tasks-{N}-{slug}.md`
- **Directory structure**: One task per `.md` file in `plan/tasks-{slug}/` directory

**Naming Convention**: Sequential numbering with slug — `plan/tasks-5-backlog-yaml-migration.yaml`

**Current Observed Plans**:
- `plan/P006-enhance-skill-research-process.yaml`
- `plan/P970-redesign-work-milestone-worktree-agents.yaml`
- `plan/P975-migrate-backlog-github-rest-to-graphql-followup-2.yaml`
- Plans stored as `.yaml` files in root `plan/` directory with `P{NNN}` prefix

### 1.2 Acceptance Criteria and Verification Phase (Phase 2)

#### `plan/T0-baseline-{slug}.yaml`

**Created by**: `t0-baseline-capture` agent
**Location**: `plan/T0-baseline-{slug}.yaml`
**Trigger**: Runs first when `acceptance-criteria-structured` is non-empty in the task plan
**Agent File**: `plugins/development-harness/agents/t0-baseline-capture.md` (line 3, 21)

**Schema** (from `t0-baseline-capture.md` lines 70-91):
```yaml
feature: "{slug}"
captured_at: "2026-03-15T10:00:00Z"
plan_path: "plan/tasks-5-{slug}.md"
criteria_count: 2
results:
  - criterion-id: AC-1
    check-command: "uv run pytest tests/test_conversion.py::test_body_preserved -v"
    exit-code: 1
    stdout: |
      FAILED tests/test_conversion.py::test_body_preserved - AssertionError
    stderr: ""
    timestamp: "2026-03-15T10:00:01Z"
    duration-seconds: 2.3
  - criterion-id: AC-2
    check-command: "uv run pytest tests/test_roundtrip.py -v"
    exit-code: 0
    stdout: |
      PASSED tests/test_roundtrip.py - 3 passed
    stderr: ""
    timestamp: "2026-03-15T10:00:04Z"
    duration-seconds: 1.8
```

**Field Definitions** (from agent documentation):
- `feature`: Plan's feature slug
- `captured_at`: ISO 8601 UTC timestamp when T0 agent ran
- `plan_path`: Relative path to the plan file
- `criteria_count`: Number of criteria executed
- `results`: List of execution results
  - `criterion-id`: Identifier from plan
  - `check-command`: Exact command string executed
  - `exit-code`: 0 or non-zero
  - `stdout` / `stderr`: Full, untruncated output
  - `timestamp`: When command started
  - `duration-seconds`: Elapsed time

**Purpose**: Captures baseline state before implementation begins. Non-zero exits are expected and do NOT indicate failure. This provides the comparison point for `TN` verification.

#### `plan/TN-verification-{slug}.yaml`

**Created by**: `tn-verification-gate` agent
**Location**: `plan/TN-verification-{slug}.yaml`
**Trigger**: Runs last after all implementation tasks complete (Priority 5, depends on all non-bookend tasks)
**Agent File**: `plugins/development-harness/agents/tn-verification-gate.md` (line 3, 21)

**Schema** (from `tn-verification-gate.md` lines 82-100+):
```yaml
feature: "{slug}"
verified_at: "2026-03-15T14:00:00Z"
plan_path: "plan/tasks-5-{slug}.md"
t0_baseline_path: "plan/T0-baseline-{slug}.yaml"
verdict: "PASS"  # or "FAIL"
criteria_count: 2
regressions: 0
newly_passing: 1
results:
  - criterion-id: AC-1
    check-command: "uv run pytest tests/test_conversion.py::test_body_preserved -v"
    t0-exit-code: 1
    tn-exit-code: 0
    status: newly-passing  # or passed | regressed | pre-existing-fail
    stdout-diff-summary: "Was FAILED, now PASSED (3 tests passed)"
  - criterion-id: AC-2
    check-command: "uv run pytest tests/test_roundtrip.py -v"
    t0-exit-code: 0
    tn-exit-code: 0
    status: passed
    stdout-diff-summary: "No change from T0"
```

**Verdict Logic** (from agent documentation):
- `verdict: FAIL` if ANY criterion has `status: regressed`
- `verdict: PASS` otherwise

**Status Classification** (4-cell matrix from agent):
| T0 exit | TN exit | Status |
|---------|---------|--------|
| 0 | 0 | `passed` |
| 0 | non-zero | `regressed` (blocks) |
| non-zero | non-zero | `pre-existing-fail` |
| non-zero | 0 | `newly-passing` |

---

## 2. Artifact Storage

### 2.1 Directory Structure

```
plan/
├── P001-followup-routing.yaml
├── P002-validator-ux-coverage.yaml
├── P006-enhance-skill-research-process.yaml
├── ...
├── P970-redesign-work-milestone-worktree-agents.yaml
├── P975-migrate-backlog-github-rest-to-graphql-followup-2.yaml
├── architect-add-status-field-to-backlogitem-model.md
├── architect-audit-tests-limitation-patterns.md
├── architect-backlog-cli-dedup.md
├── ...
├── codebase/
│   └── {FOCUS}.md  (PATTERNS.md, ARCHITECTURE.md, TESTING.md, CONCERNS.md, CONVENTIONS.md)
├── feature-context-redesign-work-milestone-worktree-agents.md
├── feature-context-*.md  (other feature contexts)
├── T0-baseline-{slug}.yaml
├── TN-verification-{slug}.yaml
└── tasks-{N}-{slug}.md
```

### 2.2 Naming Conventions

#### P{NNN} Plan Files

**Pattern**: `P{NNN}-{slug}.yaml` or `.md`
**Examples Observed**:
- `P001-followup-routing.yaml`
- `P006-enhance-skill-research-process.yaml`
- `P970-redesign-work-milestone-worktree-agents.yaml`
- `P975-migrate-backlog-github-rest-to-graphql-followup-2.yaml`

**Numbering Scheme**: Sequential positive integers, starting at 001. The P{NNN} is NOT manually assigned — it is generated by `sam_create` MCP tool based on the next available number.

**File Format**: Can be `.yaml` (structured YAML frontmatter + task array) or `.md` (markdown with Task headers). YAML is the canonical format for new plans.

#### Feature Artifact Naming

All feature artifacts share the same `{slug}`:
- `feature-context-{slug}.md`
- `architect-{slug}.md`
- `plan/tasks-{N}-{slug}.md`
- `plan/T0-baseline-{slug}.yaml`
- `plan/TN-verification-{slug}.yaml`

**Slug Examples**:
- `redesign-work-milestone-worktree-agents`
- `backlog-yaml-migration`
- `add-status-field-to-backlogitem-model`

Slugs are derived from the feature request and remain consistent across all artifacts in a feature's lifecycle.

### 2.3 Creation Responsibility Matrix

| Artifact | Created By | Format | Path Pattern | Status Field |
|----------|-----------|--------|--------------|--------------|
| feature-context | feature-researcher agent | Markdown | `plan/feature-context-{slug}.md` | N/A (document) |
| architect | python-cli-design-spec agent | Markdown | `plan/architect-{slug}.md` | N/A (document) |
| codebase analysis | codebase-analyzer agent | Markdown | `plan/codebase/{FOCUS}.md` | N/A (document) |
| tasks | swarm-task-planner agent | YAML frontmatter | `plan/tasks-{N}-{slug}.yaml` | task.status field |
| T0 baseline | t0-baseline-capture agent | YAML | `plan/T0-baseline-{slug}.yaml` | captured_at timestamp |
| TN verification | tn-verification-gate agent | YAML | `plan/TN-verification-{slug}.yaml` | verdict field (PASS/FAIL) |

---

## 3. Artifact Linking

### 3.1 GitHub Issue Integration

#### Issue Number in Plan Frontmatter

**Location**: `plan/tasks-{N}-{slug}.yaml` frontmatter
**Field**: `issue: '{github_issue_number}'`
**Example**: `issue: '970'` (from P970-redesign-work-milestone-worktree-agents.yaml line 7)

**Purpose**: Links the plan to a GitHub Issue (backlog item). This enables GitHub-aware tooling to sync task status to the issue.

**Linkage Mechanism**:
1. Backlog item has `issue_number` (GitHub Issue #970)
2. Plan file has `issue: '970'` in frontmatter
3. Task status hook reads this and syncs completion to GitHub sub-issue
4. MCP tools (`backlog_get_ready_sam_tasks`) use the issue number to fetch ready tasks

#### Backlog Item Plan Field

**Location**: Backlog item (`.claude/backlog/` per-item file or GitHub Issue)
**Field**: `plan` (optional)
**Structure**: Single path or reference to a plan file
**Tool Access**: `backlog_view` returns `{"plan": "..."}`, `backlog_update(selector=..., plan="...")` sets it

**From SKILL.md** (`plugins/development-harness/skills/backlog/SKILL.md` line 51, 66, 109):
- `backlog_list` returns items with `plan` field
- `backlog_view` returns `{title, priority, issue, plan, file_path, body, groomed}`
- `backlog_update(selector=..., plan="path/to/plan/file")` attaches a plan

**Purpose**: Tracks which plan file (if any) is associated with a backlog item. Multiple backlog items can reference the same plan (not typical), or one backlog item can reference one plan.

### 3.2 Task Status Synchronization

#### Task Status Hook

**Script**: `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py`
**Trigger Events**:
- `SubagentStop` (when `/implement-feature` finishes a sub-agent)
- `PostToolUse` (when `/start-task` calls Write, Edit, or Bash)

**Actions** (from `.claude/rules/local-workflow.md` line 236-239):

| Event | Action |
|-------|--------|
| SubagentStop | Parse prompt, extract task file + task ID, set status to COMPLETE, add Completed timestamp, delete context file, sync to GitHub |
| PostToolUse | Read active-task context file, update LastActivity timestamp |

**Timestamp Responsibility** (from local-workflow.md line 241-247):
- `Started`: Written by agent (via `/start-task` skill logic)
- `Completed`: Written by hook (SubagentStop in task_status_hook.py)
- `LastActivity`: Updated by hook (PostToolUse in task_status_hook.py)

#### Task Context File

**Location**: `.claude/context/active-task-{CLAUDE_SESSION_ID}.json`
**Created by**: `/start-task` skill (Phase 2a, line 208-214)
**Content**:
```json
{
  "task_file_path": "plan/tasks-5-{slug}.md",
  "task_id": "T01",
  "parent_issue_number": 970
}
```

**Consumed by**: `task_status_hook.py` (PostToolUse handler) — reads to know which task is active
**Lifetime**: Deleted by SubagentStop hook when task completes

### 3.3 Context Manifest

**Location**: Section within `plan/tasks-{N}-{slug}.yaml` under `Context Manifest`
**Created by**: `context-gathering` agent (Phase 1, Step 6)
**Purpose**: Maps the plan to supporting documentation and codebase context
**Content Structure**:
- Links to related issues, discussions
- References to architecture specs, design documents
- Key files and modules affected
- Related backlog items

**Updated by**: `context-refinement` agent (Phase 3, Step 6) — refreshes context to reflect actual implementation changes

---

## 4. Artifact Access in Worktrees

### 4.1 Worktree Isolation

**Mechanism**: `/work-milestone` skill spawns agents with `Agent(isolation: "worktree")`
**Worktree Location**: `.claude/worktrees/{worktree_name}/`
**Parent Worktree**: Root repository (original branch)

### 4.2 Plan File Access from Worktree

**Current Behavior**: Worktree agents can read plan files from the root repository via relative paths.

**Path Resolution**:
- Worktree inherits same CWD offset as parent session
- Reading `plan/tasks-5-{slug}.md` from a worktree resolves to the **root repository's plan file**
- This is because `.claude/worktrees/` is a git worktree linked to the same repo, sharing the same `.git` directory

**Limitations**:
- Worktree agents cannot modify root repo plan files (different working directory)
- Plan files are read-only from worktree perspective
- Task status updates require writing back to root repository

**Related Code**:
- Worktree dispatch: `plugins/development-harness/skills/work-milestone/SKILL.md`
- Task reading: Phase 2a (`/start-task`) reads task file from prompt-provided path

---

## 5. GitHub Integration

### 5.1 GitHub Issue as Source of Truth

**Authority Model** (from `plugins/development-harness/skills/backlog/SKILL.md` line 9):
- GitHub Issues are the **source of truth**
- `.claude/backlog/` per-item files are the **local cache**
- All backlog CRUD goes through MCP tools (no direct file edits)

### 5.2 MCP Backlog Tools for Artifact Linking

#### `backlog_update(selector=..., plan=...)`

**From**: `plugins/development-harness/skills/backlog/SKILL.md` (line 119-138)

**Signature**:
```
mcp__plugin_dh_backlog__backlog_update(
  selector: str,          # title substring, #N, bare number, or GitHub issue URL
  plan: str | None,       # Path to a plan file to attach
  status: str | None,     # Set item status
  create_issue: bool,     # Create GitHub issue if lacking one
  groomed_content: str,   # Full groomed content (replaces entire section)
  section: str,           # Section name for incremental update
  content: str,           # Content for the named section
  title: str,             # New title
  description: str,       # New description
  verified: bool          # Apply status:verified label
)
```

**Returns**: `{title, changes, messages, warnings}`

**Plan Field Semantics**:
- Attaches a plan file path to the backlog item
- Single value (not array) — one item, one plan
- Stored in backlog item metadata (`.claude/backlog/item.md` or GitHub issue body)
- Used to trace which plan (if any) relates to the backlog item

#### `backlog_get_ready_sam_tasks(parent_issue_number=N)`

**From**: `plugins/development-harness/skills/backlog/SKILL.md` and `.claude/rules/local-workflow.md` (line 139-142)

**Purpose**: Query GitHub Issues for a parent story issue, fetch sub-issues (SAM tasks), determine readiness

**Returns**: `{feature: "...", ready_tasks: [...], count: N}`

**Each ready_task includes**:
- Task ID
- Title
- Agent name
- Skills list
- Dependencies
- Status

**Fallback**: If GitHub unavailable, falls back to local `.claude/backlog/` cache

### 5.3 GitHub Issue Body Sections

**Managed Programmatically**:
- Task status synchronized to GitHub sub-issue (task-level GitHub Issues)
- Backlog item grooming content synced to issue body
- Plan field stored in backlog item frontmatter or body

**Not Managed by SAM Tools**:
- Custom GitHub Projects V2 fields (not currently used in observed patterns)
- Custom labels beyond `status:*` conventions
- Milestones (separate from plan linkage)

---

## 6. Existing Abstractions and Extension Points

### 6.1 SAM Schema Package

**Location**: Python package (referenced in `task_status_hook.py` line 47-52)
**Models**: Defined in `sam_schema.core.models`
**Query Functions**:
- `get_task(task_file_path, task_id)` — read task
- `update_plan_fields(...)` — update plan
- `update_status(...)` — update task status

**Purpose**: Canonical abstraction for task/plan I/O. All SAM operations route through this package (not direct file I/O).

**Extension Point**: Adding new artifact types or fields would extend this schema via new model classes.

### 6.2 SAM MCP Server

**Tools Available** (from `.claude/rules/local-workflow.md` line 310-327):
- `sam_list` — enumerate plans with search and pagination
- `sam_status` — get plan-level progress summary
- `sam_ready` — list tasks ready for dispatch
- `sam_read` — read plan or task fields
- `sam_claim` — mark task in-progress (prevents duplicate dispatch)
- `sam_state` — update task status
- `sam_update` — update plan/task fields or append sections
- `sam_create` — create new plan from YAML task definitions

**CLI Fallback** (when MCP unavailable):
```bash
uv run sam list
uv run sam status P{N}
uv run sam ready P{N}
uv run sam read P{N}
uv run sam claim P{N} {task_id}
uv run sam update P{N} --context "..."
```

**Extension Point**: Adding new query or update operations would extend the MCP server and CLI simultaneously.

### 6.3 Hook Configuration

**Location**: SKILL.md frontmatter (`hooks:` section)
**Current Hooks**:
- `/implement-feature`: `SubagentStop` → calls `task_status_hook.py`
- `/start-task`: `PostToolUse` (Write|Edit|Bash) → calls `task_status_hook.py`

**Environment Variable Controls** (from `task_status_hook.py` lines 65-268):
- `CLAUDE_SKILLS_HOOK_PROFILE` — profile selection (minimal, standard, strict)
- `CLAUDE_SKILLS_DISABLED_HOOKS` — comma-separated hook IDs to disable

**Extension Point**: New hooks can be added to SKILL.md frontmatter. Hook script can be extended with new event handlers.

### 6.4 Plan Artifact Lifecycle Policy

**Location**: `.claude/docs/plan-artifact-lifecycle.md` (referenced in `.claude/rules/local-workflow.md` line 102-103)
**Categories**:
- **Human-decision artifacts** (immutable) — backlog items, grooming output, interview transcripts
- **Generated artifacts** (mutable but intent-bound) — feature context, architecture spec, task plan, codebase analysis

**Annotation Format**: Agents can append annotations to generated artifacts when they discover divergence, but cannot silently rewrite.

**Divergence Detection**: During Phase 6 (`/complete-implementation`), `context-refinement` agent performs plan artifact freshness check and flags `DIVERGENCE_REQUIRING_REVIEW` for human review.

---

## 7. Key Observations

### 7.1 Central Plan Directory

The `plan/` directory serves as the hub for all feature-related artifacts:
- All discovery artifacts (feature-context, architect, codebase analysis)
- All task plans (tasks-{N}-{slug})
- All verification artifacts (T0-baseline, TN-verification)
- All follow-up task files created by quality gates

### 7.2 Slug as Cross-Artifact Identity

The `{slug}` is the unique identifier across all artifacts for a single feature:
- Same slug appears in: feature-context, architect, tasks, T0-baseline, TN-verification
- Slug links all artifacts to a cohesive feature lifecycle
- SAM plan's `feature` field stores the slug in frontmatter

### 7.3 GitHub Issue Number as Backlog Link

The `issue` field in plan frontmatter (`issue: '970'`) is the primary link to GitHub:
- Enables task status sync to GitHub sub-issues
- Enables `backlog_get_ready_sam_tasks()` query by parent issue number
- Optional but recommended for tracked feature work

### 7.4 P{NNN} is Plan Registry

The `P{NNN}` prefix is auto-generated by `sam_create`, providing:
- Sequential registry of all plans ever created
- Unique identifier for reports and artifacts
- Stable reference for GitHub workflow artifacts (e.g., `.claude/reports/P700-code-review.md`)

### 7.5 Timestamp-Based Status Tracking

Task status is tracked via three timestamps:
- `started`: When work began (agent-set)
- `completed`: When work finished (hook-set)
- `last-activity`: Most recent work timestamp (hook-updated on every Write/Edit/Bash)

These timestamps enable progress reporting and detect stalled tasks.

### 7.6 Minimal Centralized State

SAM tooling maintains minimal centralized state:
- Plan files are the source of truth (not a database)
- Task status is recorded IN the plan file (not external)
- GitHub Issues mirror backlog items (but backlog MCP tools are primary interface)
- Context files are ephemeral (deleted on completion)

This design minimizes synchronization complexity and keeps state decentralized.

---

## 8. Files and Code References

### Agent Implementations
- Feature researcher: `plugins/development-harness/agents/feature-researcher.md`
- Codebase analyzer: `plugins/development-harness/agents/codebase-analyzer.md`
- Swarm task planner: `plugins/development-harness/agents/swarm-task-planner.md`
- T0 baseline capture: `plugins/development-harness/agents/t0-baseline-capture.md`
- TN verification gate: `plugins/development-harness/agents/tn-verification-gate.md`
- Context refinement: `plugins/development-harness/agents/context-refinement.md`

### Skills
- Backlog: `plugins/development-harness/skills/backlog/SKILL.md`
- Implementation manager: `plugins/development-harness/skills/implementation-manager/SKILL.md`
- Work milestone: `plugins/development-harness/skills/work-milestone/SKILL.md`
- Add new feature: `.claude/skills/add-new-feature/SKILL.md`
- Implement feature: `.claude/skills/implement-feature/SKILL.md`
- Complete implementation: `.claude/skills/complete-implementation/SKILL.md`

### Hooks
- Task status hook: `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py`
- Get task context: `plugins/development-harness/skills/implementation-manager/scripts/get_task_context.py`

### Documentation
- SAM workflow: `.claude/rules/local-workflow.md`
- Plan artifact lifecycle: `.claude/docs/plan-artifact-lifecycle.md`

### Observed Plans
- Root plan directory: `plan/` (contains ~100+ artifacts)
- P-numbered plans: `plan/P001-*.yaml` through `plan/P975-*.yaml`
- Feature context files: `plan/feature-context-*.md`
- Architect specs: `plan/architect-*.md`
- Codebase analysis: `plan/codebase/*.md`
- Verification outputs: `plan/T0-baseline-*.yaml`, `plan/TN-verification-*.yaml`
