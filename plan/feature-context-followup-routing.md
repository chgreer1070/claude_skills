# Feature Context: Follow-up Task File Routing to Backlog

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: simple_description
- **Source**: GitHub Issue #381 — complete-implementation: route follow-up task files to backlog instead of orphaning
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The complete-implementation skill's code-reviewer phase creates follow-up task files (`plan/tasks-{N}-{slug}-followup-{k}.md`) when it finds gaps. The workflow then expects to recurse with `/implement-feature` on them. Problem: when the orchestrator skips recursion (deferred scope, different priority, session timeout, or context compaction), these files are orphaned -- no backlog item links to them, no one knows they exist. This has happened 3+ times in recent sessions.

Desired outcome: add a routing step between "code reviewer creates follow-up" and "recurse with implement-feature." The routing step should:

1. Search backlog for existing item matching the follow-up scope (by title keywords)
2. If found: attach follow-up as plan via `backlog update --plan`
3. If not found: create new backlog item via `create-backlog-item` with follow-up as plan
4. Only recurse (implement now) if same priority AND same session scope
5. Otherwise: link to backlog only, do not recurse

---

## Core Intent Analysis

### WHO (Target Users)

The orchestrator agent running `/complete-implementation` after all tasks in a feature are marked COMPLETE. Indirectly, the maintainer who relies on the backlog as the single inventory of outstanding work.

### WHAT (Desired Outcome)

Every follow-up task file created by the code-reviewer agent is tracked in the backlog system. No follow-up file exists on disk without a corresponding backlog item linking to it. Recursion (immediate execution of the follow-up) becomes conditional rather than unconditional.

### WHEN (Trigger Conditions)

When Phase 1 (code review) of `/complete-implementation` produces one or more follow-up task files. The routing decision happens after the code-reviewer agent returns its `ARTIFACTS` output listing created task files, and before any recursion into `/implement-feature`.

### WHY (Problem Being Solved)

Follow-up task files are silently orphaned when the orchestrator does not recurse. The files sit in `plan/` with no backlog item referencing them, no GitHub issue tracking them, and no mechanism to rediscover them. This violates the project's accountability principle: every identified issue must be tracked in the backlog.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Backlog Update with Plan Path

- **Location**: `.claude/skills/backlog/scripts/backlog.py:1768-1802`
- **Relevance**: The `update` command already accepts `--plan PATH` to associate a plan file with a backlog item. This is the exact mechanism needed to link a follow-up task file to an existing backlog item.
- **Reusable**: `backlog.py update "{selector}" --plan "{followup_path}"` can be used directly.

#### Pattern 2: Backlog Item Search by Title Substring

- **Location**: `.claude/skills/backlog/scripts/backlog.py:310-333` (`find_item` function)
- **Relevance**: The `find_item` function searches backlog items by case-insensitive title substring. This is the mechanism needed for Step 1 of the routing ("search backlog for existing item matching the follow-up scope").
- **Reusable**: The `backlog.py list --format json` command combined with title substring matching enables programmatic search.

#### Pattern 3: Autonomous Backlog Item Creation

- **Location**: `.claude/skills/create-backlog-item/SKILL.md:31-53` (`--auto` mode)
- **Relevance**: The `create-backlog-item` skill has an `--auto` mode that creates items without interactive prompts, deriving fields from available context. This is the mechanism needed for Step 3 ("if not found, create new backlog item").
- **Reusable**: `Skill(skill="create-backlog-item", args="--auto {followup_title}")` followed by `backlog.py update "{title}" --plan "{followup_path}"`.

#### Pattern 4: Code Reviewer Follow-up Output Format

- **Location**: `plugins/python3-development/agents/code-reviewer.md:240-254` (Output Format)
- **Relevance**: The code-reviewer agent returns a structured `STATUS: DONE` block with an `ARTIFACTS` section listing `Task files: {list of task file paths}`. This is the data source the routing step would consume to know which follow-up files were created.
- **Reusable**: The `Task files:` list in the ARTIFACTS section provides the exact file paths to route.

#### Pattern 5: Unconditional Recursion in complete-implementation

- **Location**: `.claude/skills/complete-implementation/SKILL.md:57-65`
- **Relevance**: This is the section that currently triggers unconditional recursion. It contains no backlog integration, no priority check, and no conditional logic. It is the exact code that needs modification.
- **Reusable**: The recursion pattern itself is still needed for the "implement now" branch.

### Existing Infrastructure

1. **Backlog CLI** (`backlog.py`): Full CRUD with `add`, `update --plan`, `list --format json`, and `find_item` by title substring. All infrastructure needed for search-and-link is present.
2. **Create-backlog-item skill** (`--auto` mode): Autonomous item creation without user interaction. Can create a backlog item and then immediately attach a plan to it.
3. **Code-reviewer output format**: Structured ARTIFACTS section with task file paths. The routing step has a reliable data source.
4. **No follow-up files currently exist**: Glob for `**/tasks-*followup*` returned zero results, meaning either follow-ups have been cleaned up or were never created in practice (contradicted by the issue report of 3+ orphaned instances, suggesting they were cleaned up or existed in prior branches).

### Code References

- `.claude/skills/complete-implementation/SKILL.md:57-65` -- Recursive Follow-up Handling section (the section to be modified)
- `.claude/skills/complete-implementation/SKILL.md:21-23` -- Phase 1 launches code-reviewer
- `plugins/python3-development/agents/code-reviewer.md:176-189` -- Follow-up task file naming convention
- `plugins/python3-development/agents/code-reviewer.md:240-254` -- Output format with ARTIFACTS listing task files
- `.claude/skills/backlog/scripts/backlog.py:310-333` -- `find_item` function for title-based search
- `.claude/skills/backlog/scripts/backlog.py:1768-1802` -- `update` command with `--plan` flag
- `.claude/skills/backlog/scripts/backlog.py:856-902` -- `add` command for creating new items
- `.claude/skills/create-backlog-item/SKILL.md:31-53` -- `--auto` mode for autonomous creation
- `.claude/skills/implement-feature/SKILL.md:84-91` -- Completion Gate (calls complete-implementation)
- `.claude/rules/local-workflow.md:239-244` -- Documentation of the recursive pattern

---

## Use Scenarios

### Scenario 1: Follow-up matches existing backlog item

**Actor**: Orchestrator running `/complete-implementation`
**Trigger**: Code-reviewer creates `plan/tasks-8-data-validation-followup-1.md` for "missing input validation tests." A backlog item titled "SAM: Input Validation Test Coverage" already exists.
**Goal**: Link the follow-up task file to the existing backlog item as its plan.
**Expected Outcome**: The existing backlog item's `plan` field is updated to point to the follow-up task file. No duplicate backlog item is created. No immediate recursion occurs (different scope than the current session).

### Scenario 2: Follow-up has no matching backlog item

**Actor**: Orchestrator running `/complete-implementation`
**Trigger**: Code-reviewer creates `plan/tasks-8-data-validation-followup-2.md` for "missing error handling in service layer." No backlog item matches this scope.
**Goal**: Create a new backlog item and attach the follow-up as its plan.
**Expected Outcome**: A new backlog item is created with the follow-up's title/description. The follow-up task file is attached as the item's plan. The item is tracked in `.claude/backlog/` (and optionally as a GitHub Issue for P0/P1).

### Scenario 3: Follow-up is same priority and scope -- recurse immediately

**Actor**: Orchestrator running `/complete-implementation`
**Trigger**: Code-reviewer creates a critical follow-up that is the same priority as the current feature and within the current session's scope.
**Goal**: Execute the follow-up immediately (current recursive behavior) AND track it in the backlog.
**Expected Outcome**: Backlog item created/linked first, then recursion proceeds. If recursion completes, the backlog item can be closed. If recursion fails or is interrupted, the backlog item persists.

### Scenario 4: Session ends before recursion

**Actor**: Orchestrator running `/complete-implementation` near session timeout
**Trigger**: Code-reviewer creates follow-up files. The orchestrator recognizes it cannot recurse (context budget, session ending).
**Goal**: Ensure follow-up files are tracked even though recursion will not happen.
**Expected Outcome**: All follow-up files are linked to backlog items. No orphaned files. The next session can pick up the work via `/work-backlog-item`.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | What constitutes "same priority" for the recurse-now decision? Is it the priority of the parent feature's backlog item, the priority assigned to the follow-up task file, or something else? | Determines whether recursion happens or is deferred to backlog |
| 2 | Scope | What constitutes "same session scope"? Is this a user-defined boundary, a context budget threshold, or based on the feature slug? | Controls the recurse vs. defer decision |
| 3 | Behavior | How should the routing step extract a meaningful title/description from the follow-up task file for backlog item creation? The code-reviewer output has `Task files: {paths}` but the title comes from reading the file. | Determines quality of auto-created backlog items |
| 4 | Behavior | If `backlog.py find_item` returns multiple matches for a follow-up's keywords, which item should receive the plan? The first match? The closest match? | Prevents wrong backlog item linkage |
| 5 | Integration | Should the routing step live in the `/complete-implementation` SKILL.md (orchestrator instructions), or as a separate script/function? | Affects where the change is made |
| 6 | Integration | The code-reviewer agent creates follow-up files and returns paths in its ARTIFACTS. Does the routing step consume those paths from the agent output, or does it independently glob for `*-followup-*` files? | Reliability of follow-up detection |
| 7 | Behavior | When a follow-up is linked to a backlog item and recursion is deferred, should the follow-up task file's status be set to something specific (e.g., "DEFERRED" or "BACKLOGGED")? | Prevents confusion about task file state |

---

## Questions Requiring Resolution

### Q1: What determines "same priority"?

- **Category**: Behavior
- **Gap**: The request says "only recurse if same priority." Priority of what compared to what?
- **Question**: Does "same priority" mean the follow-up task file's priority matches the parent feature's backlog item priority? Or does it mean the follow-up is P0/P1 (high enough to warrant immediate action)?
- **Options**:
  - A) Follow-up priority matches parent feature's backlog item priority
  - B) Follow-up is P0 or P1 regardless of parent
  - C) Follow-up priority is explicitly marked "Critical" or "High" in the task file
- **Why It Matters**: Determines the threshold for immediate recursion vs. backlog deferral
- **Resolution**: _pending_

### Q2: What determines "same session scope"?

- **Category**: Behavior
- **Gap**: The request says "only recurse if same session scope." Session scope is not a defined concept in the current workflow.
- **Question**: How should the routing step determine whether a follow-up is "in scope" for the current session? Is this based on the feature slug, a user-declared boundary, or the orchestrator's remaining context budget?
- **Options**:
  - A) Same feature slug (follow-up is part of the same feature being completed)
  - B) Orchestrator decides based on remaining context budget
  - C) Always defer to backlog (never auto-recurse)
  - D) User configurable via a flag on `/complete-implementation`
- **Why It Matters**: This is the core routing decision -- when to recurse vs. when to defer
- **Resolution**: _pending_

### Q3: Should backlog item creation happen before or independent of recursion?

- **Category**: Scope
- **Gap**: If the routing step creates a backlog item AND then recurses, the backlog item exists even if recursion succeeds. Should the backlog item be closed automatically after successful recursion?
- **Question**: When recursion succeeds (follow-up fully implemented), should the backlog item created by the routing step be automatically closed, or left open for manual verification?
- **Options**:
  - A) Auto-close after successful recursion (add to `/complete-implementation` recursion logic)
  - B) Leave open -- user closes via `/work-backlog-item close` after review
  - C) Always create backlog item but only for the defer path (no backlog item for recurse-now path)
- **Why It Matters**: Determines whether backlog items accumulate for already-completed work
- **Resolution**: _pending_

### Q4: Where should the routing logic live?

- **Category**: Integration
- **Gap**: The routing step could be added to the `/complete-implementation` SKILL.md as orchestrator instructions, or extracted into a script/skill.
- **Question**: Should this be orchestrator-level instructions in the SKILL.md (matching the current pattern), or a new script that programmatically handles the routing?
- **Options**:
  - A) Orchestrator instructions in `/complete-implementation` SKILL.md (replace lines 57-65)
  - B) New script invoked by the SKILL.md (e.g., `route_followups.py`)
  - C) New skill (e.g., `/route-followup`)
- **Why It Matters**: Scripts are more reliable than orchestrator instructions for multi-step logic. But adding a script changes the architecture pattern.
- **Resolution**: _pending_

### Q5: How should follow-up files be detected?

- **Category**: Integration
- **Gap**: Two detection methods are possible -- parsing the code-reviewer's ARTIFACTS output, or globbing for `*-followup-*` files.
- **Question**: Should the routing step rely on the code-reviewer's output (ARTIFACTS section listing task files), or independently scan for follow-up files via glob?
- **Options**:
  - A) Parse ARTIFACTS from code-reviewer output (available in the orchestrator's context)
  - B) Glob for `plan/tasks-*-{slug}-followup-*.md` after Phase 1 completes
  - C) Both -- use ARTIFACTS as primary, glob as fallback
- **Why It Matters**: ARTIFACTS parsing is fragile (depends on output format). Globbing is independent but could pick up stale files from prior sessions.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Every follow-up task file created by the code-reviewer is linked to a backlog item (new or existing)
2. Follow-up files are never orphaned on disk without backlog tracking
3. Recursion into `/implement-feature` for follow-ups is conditional, not unconditional
4. The routing decision (recurse now vs. defer to backlog) is deterministic and based on defined criteria
5. The routing step integrates with existing backlog infrastructure (`backlog.py` commands)
6. Documentation in `local-workflow.md` is updated to reflect the new routing behavior

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
