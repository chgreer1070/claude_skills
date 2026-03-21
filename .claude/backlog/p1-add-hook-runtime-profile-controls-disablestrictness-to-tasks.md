---
name: Add hook runtime profile controls (disable/strictness) to task_status_hook
description: "## Current state\n\nAll hooks defined in SKILL.md frontmatter (`PostToolUse` matcher for Write|Edit|Bash on `start-task`, `SubagentStop` on `implement-feature`) execute unconditionally. There is no mechanism to disable individual hooks, reduce hook frequency (e.g., skip PostToolUse LastActivity updates during high-throughput edits), or set a profile level. If a hook causes performance issues or interferes with debugging, the only option is to edit the SKILL.md frontmatter directly."
metadata:
  topic: add-hook-runtime-profile-controls-disablestrictness-to-tasks
  source: 'Research entry: ./research/agent-frameworks/everything-claude-code.md — pattern: Hook runtime controls (ECC_HOOK_PROFILE, ECC_DISABLED_HOOKS)'
  added: '2026-03-10'
  priority: completed
  type: Feature
  status: done
  issue: '#577'
  last_synced: '2026-03-21T21:46:30Z'
  groomed: '2026-03-21'
  plan: plan/P577-hook-profile-controls.yaml
---

## Story

As a **developer using Claude Code skills**, I want to **add hook runtime profile controls (disable/strictness) to task_status_hook** so that **the tooling becomes more capable and complete**.

## Description

## Current state

All hooks defined in SKILL.md frontmatter (`PostToolUse` matcher for Write|Edit|Bash on `start-task`, `SubagentStop` on `implement-feature`) execute unconditionally. There is no mechanism to disable individual hooks, reduce hook frequency (e.g., skip PostToolUse LastActivity updates during high-throughput edits), or set a profile level. If a hook causes performance issues or interferes with debugging, the only option is to edit the SKILL.md frontmatter directly.

## Target state

`task_status_hook.py` reads environment variables at startup: `CLAUDE_SKILLS_HOOK_PROFILE` (values: `minimal`, `standard`, `strict`; default `standard`) and `CLAUDE_SKILLS_DISABLED_HOOKS` (comma-separated hook IDs like `post:edit:last-activity`). In `minimal` profile, PostToolUse LastActivity updates are skipped (only SubagentStop completion marking runs). In `strict` profile, additional validation checks run (e.g., verify task file exists before writing). Disabled hooks exit immediately with code 0 when their ID matches the environment variable.

## Measurable signal

Set `CLAUDE_SKILLS_HOOK_PROFILE=minimal` and run a task. Verify that `last_activity` is NOT updated on Write/Edit/Bash calls (PostToolUse handler exits early) but SubagentStop still marks the task complete. Set `CLAUDE_SKILLS_DISABLED_HOOKS=post:bash:last-activity` and verify the specific hook is skipped while others run.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Research entry: ./research/agent-frameworks/everything-claude-code.md — pattern: Hook runtime controls (ECC_HOOK_PROFILE, ECC_DISABLED_HOOKS)
- **Priority**: P1
- **Added**: 2026-03-10
- **Research questions**: None

## RT-ICA

<div><sub>2026-03-21T21:46:30Z</sub>

RT-ICA Final: Add hook runtime profile controls
Goal: Add environment-variable-based profile controls to task_status_hook.py so hooks can be disabled, throttled, or run in strict mode without editing SKILL.md frontmatter.
Conditions:
1. task_status_hook.py location and current structure | Snapshot: AVAILABLE → Final: AVAILABLE | Source: item description, confirmed by impact-analyst
2. Hook event types handled (SubagentStop, PostToolUse) | Snapshot: AVAILABLE → Final: AVAILABLE | Source: fact-checker verified both declarations in SKILL.md frontmatter
3. Environment variable naming convention | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: fact-checker confirmed ECC patterns in research entry; item specifies CLAUDE_SKILLS_HOOK_PROFILE / CLAUDE_SKILLS_DISABLED_HOOKS
4. Strict mode validation checks | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: impact-analyst identified task file existence and schema compliance; groomer incorporated into acceptance criteria
5. Hook ID format for DISABLED_HOOKS | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: item description specifies post:edit:last-activity format; groomer acceptance criteria cover this
Changes from snapshot:
- Condition 3: DERIVABLE → AVAILABLE (resolved by fact-checker research entry verification)
- Condition 4: DERIVABLE → AVAILABLE (resolved by impact-analyst systems inventory)
- Condition 5: DERIVABLE → AVAILABLE (resolved from item description + groomer AC)
Decision: APPROVED
</div>

## Fact-Check

<div><sub>2026-03-21T21:44:32Z</sub>

## Fact-Check Results

**Claims verified**: 5 of 5

---

### Claim 1: "All hooks execute unconditionally"
**Status**: VERIFIED

**Evidence**:
- `start-task/SKILL.md` (lines 6-11): PostToolUse hook with matcher `Write|Edit|Bash` — executes on all Write, Edit, and Bash calls, no skip conditions
- `implement-feature/SKILL.md` (lines 9-13): SubagentStop hook — executes when sub-agent finishes, no conditions
- Both hooks are declared but neither contains conditional logic (no `if`, `when`, `enabled`, or `skip` fields in YAML)

**Conclusion**: Hooks fire every time their trigger conditions are met. No environment variable or flag can currently disable them.

---

### Claim 2: "PostToolUse matcher for Write|Edit|Bash on start-task"
**Status**: VERIFIED

**Evidence**:
- `start-task/SKILL.md` lines 6-8:
  ```yaml
  hooks:
    PostToolUse:
    - matcher: Write|Edit|Bash
  ```
- Exact syntax confirmed. Hook fires on any Write, Edit, or Bash call during task implementation.

---

### Claim 3: "SubagentStop on implement-feature"
**Status**: VERIFIED

**Evidence**:
- `implement-feature/SKILL.md` lines 9-13:
  ```yaml
  hooks:
    SubagentStop:
    - hooks:
      - type: command
        command: python3 "${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py"
  ```
- Hook declaration confirmed. Fires when sub-agent finishes and marks task complete.

---

### Claim 4: "The only option is to edit the SKILL.md frontmatter directly"
**Status**: VERIFIED

**Evidence**:
- No built-in Claude Code hook disable mechanism found in official docs
- No environment variable pattern in SKILL.md that controls hook execution (e.g., `$DISABLE_HOOKS`)
- Command-type hooks have no conditional fields in current YAML schema (no `when:`, `enabled:`, or `skip:` support)
- To prevent hook execution, the SKILL.md frontmatter must be edited to remove or comment out the hook declaration

**Conclusion**: Editing SKILL.md is the only current method. No runtime controls exist in Claude Code's hook system.

---

### Claim 5: "ECC_HOOK_PROFILE, ECC_DISABLED_HOOKS pattern from research"
**Status**: VERIFIED

**Evidence**:
- File exists: `/home/ubuntulinuxqa2/repos/claude_skills/research/agent-frameworks/everything-claude-code.md`
- Exact source: Lines 158-160:
  ```
  Runtime controls:
  - `ECC_HOOK_PROFILE` — Hook strictness (minimal, standard, strict)
  - `ECC_DISABLED_HOOKS` — Disable specific hooks by ID
  ```
- Source confirmed: Everything Claude Code (external project, not this repo)

**Conclusion**: Pattern exists in external framework. Could be adapted for claude_skills hooks if adopted.

---

## Summary

- **Total claims checked**: 5
- **Verified**: 5
- **Refuted**: 0
- **Inconclusive**: 0

All claims in #577 are accurate based on primary sources (SKILL.md files, hook declarations, and research document). No counter-evidence found.
</div>

## Groomed (2026-03-21)


### Impact

<div><sub>2026-03-10T00:00:00Z</sub>

<div><sub>2026-03-21T21:44:59Z</sub>
</div>

<div><sub>2026-03-21T21:45:43Z</sub>

**Who**: Developers running `/implement-feature` and `/start-task` workflows, especially during iteration and testing.

**What's affected**:
- task_status_hook.py hook execution cost (PostToolUse fires on every Write/Edit/Bash)
- Task file artifact noise (timestamps update even for trivial operations)
- Hook performance testing (no way to isolate behavioral validation from timestamp updates)

**What's blocked**: Performance optimization and testing workflows; no workaround exists to disable timestamp-only updates without disabling all hooks.
</div>

### Reproducibility

<div><sub>2026-03-21T21:45:38Z</sub>

1. Start a task via `/start-task` that produces at least one Write or Edit operation
2. Monitor the task file and observe the `**LastActivity**` timestamp in the task section
3. Run multiple Write/Edit/Bash operations during the task
4. Verify that `**LastActivity**` is updated on every operation without exception
5. Current behavior: no way to suppress these timestamp updates (they always fire)
</div>

### Priority

<div><sub>2026-03-21T21:45:41Z</sub>

**Numeric**: 2 (should-have, enables better dev ergonomics but not blocking)

**Rationale**: This is a developer quality-of-life feature that reduces noise in task artifacts and allows faster iteration without hook-related slowdowns. Not a correctness issue (hooks work as designed). Ranked below bug fixes and critical feature work, above refactorings and optimizations.
</div>

### Benefits

<div><sub>2026-03-21T21:45:46Z</sub>

- Faster iteration: developers can disable non-critical updates during testing without removing hooks entirely
- Cleaner artifacts: minimal profile reduces timestamp noise when only validation is needed
- Diagnostic capability: strict profile enables additional validation checks for troubleshooting
- Hook-by-hook control: individual hooks can be disabled by ID, allowing fine-grained testing
- Zero breaking changes: default behavior remains unchanged (standard profile)
</div>

### Expected Behavior

<div><sub>2026-03-21T21:45:49Z</sub>

**With CLAUDE_SKILLS_HOOK_PROFILE=minimal**:
PostToolUse hook runs validation checks but skips LastActivity timestamp updates. SubagentStop hook runs normally (marks task COMPLETE and adds Completed timestamp). Task file remains smaller, operations are faster.

**With CLAUDE_SKILLS_HOOK_PROFILE=strict**:
Both hooks run; additional validation checks execute (stricter argument validation, deeper error classification). Useful for pre-commit testing and problem diagnosis.

**With CLAUDE_SKILLS_DISABLED_HOOKS=hook1,hook2,...**:
Named hooks skip execution entirely. Allows isolating specific hook effects for testing or performance measurement.

**Default (no env vars)**:
CLAUDE_SKILLS_HOOK_PROFILE=standard. All hooks run with baseline validation. Backward compatible with current behavior.
</div>

### Acceptance Criteria

<div><sub>2026-03-21T21:45:51Z</sub>

1. **Profile parsing**: CLAUDE_SKILLS_HOOK_PROFILE env var is read; valid values are minimal/standard/strict; invalid values trigger clear warning and default to standard
2. **Hook disabling**: CLAUDE_SKILLS_DISABLED_HOOKS env var (comma-separated hook IDs) is parsed; hooks matching those IDs skip execution entirely and log a skip message
3. **Minimal profile**: When set to minimal, PostToolUse hook skips LastActivity timestamp updates but still validates context file existence and sync status
4. **Strict profile**: When set to strict, both hooks run; no breaking changes to existing behavior, but additional validation checks execute
5. **Backward compatibility**: Default behavior (no env vars set) is unchanged; all existing tests pass without modification
6. **Documentation**: SKILL.md hook declarations and task_status_hook.py docstring document all three profiles and disable mechanism with examples
7. **Test coverage**: New test cases cover each profile, disabled-hooks combinations, and invalid values
</div>

### Files

<div><sub>2026-03-21T21:45:54Z</sub>

**Primary change**:
- plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py

**Documentation**:
- .claude/skills/implement-feature/SKILL.md (hook declarations)
- .claude/skills/start-task/SKILL.md (hook declarations)
- plugins/development-harness/skills/implementation-manager/SKILL.md
- plugins/development-harness/docs/task-status-hook-profiles.md (new)

**Tests**:
- plugins/development-harness/tests/test_task_status_hook.py
- plugins/development-harness/tests/test_hook_profiles.py (new)
</div>

### Resources

<div><sub>2026-03-21T21:45:56Z</sub>

| Type | Item |
|------|------|
| Skill | `/python3-development:python-cli-architect` for implementation |
| Skill | `/plugin-creator:hook-creator` for SKILL.md hook syntax validation |
| Agent | `@python3-development:python-pytest-architect` for test suite |
| Reference | plugins/development-harness/docs/workflow-architecture-diagram.md |
| Reference | plugins/development-harness/agents/t0-baseline-capture.md (hook context) |
| Prior Work | session 2026-03-17 hook investigation and ECC pattern validation
</div>

### Dependencies

<div><sub>2026-03-21T21:45:59Z</sub>

**Depends on**:
- task_status_hook.py current structure (stable)
- Python 3.11+ os module for env var reading (stdlib)

**Unblocks**:
- Performance testing workflows (developers can disable timestamps to measure pure validation overhead)
- Hook diagnostic tooling (strict profile enables targeted validation)
- Potential future: hook profiling and performance optimization
</div>

### Effort

<div><sub>2026-03-21T21:46:02Z</sub>

**Estimate**: Medium (6-8 hours)

**Rationale**:
- Core feature is straightforward (env var parsing + conditional execution blocks) — ~2 hours implementation
- Documentation updates (4 files, hook syntax, profiles guide) — ~2 hours
- Test coverage (existing suite + new profile cases) — ~2 hours
- Integration verification (run full workflow with each profile) — ~1 hour

No architectural changes or dependency additions required. Risk is low; testing is the main effort.
</div>


## Systems Inventory

### Code — Producers (Write to task_status_hook.py output)

**Files that invoke task_status_hook.py:**

1. `plugins/development-harness/skills/implement-feature/SKILL.md` (lines 9-13)
   - Hook Event: SubagentStop
   - Invokes: `python3 "${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py"`
   - Purpose: Mark task COMPLETE + add Completed timestamp
   - Status: Will remain unchanged by env var controls; script still runs on SubagentStop

2. `plugins/development-harness/skills/start-task/SKILL.md` (lines 6-11)
   - Hook Event: PostToolUse (matcher: Write|Edit|Bash)
   - Invokes: `python3 "${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py"`
   - Purpose: Update LastActivity timestamp on Write/Edit/Bash
   - Status: Will be affected by env var controls — minimal profile skips PostToolUse

**Hook Configuration Changes Required:**

- No changes to SKILL.md hook declarations needed — env var filtering happens inside task_status_hook.py
- Hook will still be invoked; script will check env vars and exit early if disabled

### Code — Consumers (Code that assumes hooks always run)

**Files that depend on hook side effects:**

1. `plugins/development-harness/skills/implementation-manager/SKILL.md` (lines 164-198)
   - Documents hook behavior and timestamp responsibilities
   - **Impact**: Section "Hook Integration" describes unconditional behavior
   - **Change needed**: Update table and description to note env var behavior
   - **Severity**: Documentation drift — agents/users could expect behavior that doesn't occur in minimal profile

2. `.claude/rules/local-workflow.md` (lines 164-198, 201-209)
   - Phase 2 "Execution Loop" describes hook operations for task status tracking
   - Phase 2a "Task Execution" describes hook configuration
   - **Impact**: Describes unconditional LastActivity updates
   - **Change needed**: Add note that PostToolUse updates are profile-dependent
   - **Severity**: High — this is the canonical workflow documentation

3. `plugins/development-harness/docs/TASK_FILE_FORMAT.md`
   - Likely documents task fields including timestamps
   - **Change needed**: Verify if it describes hook behavior; if so, update with profile notes

4. `plugins/development-harness/docs/workflow-architecture-diagram.md`
   - Data flow diagrams may show hook operations
   - **Change needed**: Verify if diagrams assume unconditional hook execution

5. `plugins/development-harness/docs/plan-artifact-lifecycle.md`
   - Describes artifact mutability and task file lifecycle
   - **Change needed**: Verify if it assumes hooks always update LastActivity for "freshness"

### Configuration/CI

**No direct CI configuration changes** — hooks are declarative in SKILL.md; env vars are runtime-only.

### Tests

**Test files that assume hook behavior:**

1. `plugins/python3-development/skills/implementation-manager/tests/test_task_status_hook/test_subagent_stop_integration.py`
   - **Impact**: Tests SubagentStop completion marking; will still work (SubagentStop not skipped in any profile)
   - **Change needed**: Add test cases for env var profile selection

2. `plugins/python3-development/skills/implementation-manager/tests/test_task_status_hook/test_github_sync.py`
   - **Impact**: Tests GitHub sync on completion; should still work
   - **Change needed**: Add test cases for env var behavior; test disabled hooks

3. Unit tests in `plugins/development-harness/tests_sam/` and `plugins/development-harness/tests/`
   - Files: `test_cli.py`, `test_cli_create.py`, `test_backlog_core_operations.py`
   - **Impact**: May create tasks and expect hook behavior; should verify profile handling

### Agent Instructions

**Agents that may assume unconditional hook behavior:**

1. `plugins/development-harness/agents/context-refinement.md`
   - May rely on LastActivity field freshness when analyzing task state
   - **Change needed**: No change required (env var behavior transparent to agent)

2. `plugins/development-harness/agents/t0-baseline-capture.md` and `tn-verification-gate.md`
   - Bookend tasks capture baseline and verification state
   - **Change needed**: No change required (these tasks not affected by PostToolUse updates)

### Agent Files That Reference Hook Context

**Files created during task execution that may reference hooks:**

1. `.claude/context/active-task-{CLAUDE_SESSION_ID}.json`
   - Written by `/start-task` SKILL.md step 4 (line 95)
   - Read by PostToolUse hook
   - **Impact**: File creation NOT affected by env vars; hook reads it regardless
   - **Change needed**: None

### Shared Utilities

**Python modules used by task_status_hook.py:**

1. `plugins/development-harness/sam_schema/` — SAM task file parsing
   - Used by hook to read/write task state
   - **Impact**: No changes needed; hook will use regardless of profile
   - **Change needed**: None (transparent to hook users)

### Ecosystem Completeness Checklist

- [x] Hook declarations in SKILL.md identified (implement-feature, start-task)
- [x] Hook invocation points found (2 files)
- [x] Consumer code identified (skills, agents, tests)
- [x] Documentation files that describe hook behavior found (5 files)
- [x] Test coverage for hook behavior identified (2 test suites)
- [x] Shared utilities located (sam_schema)
- [x] Backlog items referencing hooks found (5+ items reference hook behavior)
- [x] Context files that hooks read identified (active-task-*.json)

## Impact Analysis by Profile

**minimal profile (PostToolUse skipped):**
- LastActivity timestamps will NOT be updated during task execution
- SubagentStop completion still marks task COMPLETE
- Test assertions that check LastActivity != Started will fail
- Agent state inference based on LastActivity will see stale timestamps

**standard profile (current behavior):**
- No changes to behavior
- All tests pass as-is

**strict profile (validation added):**
- PostToolUse validation checks may fail on malformed task files
- May cause unexpected hook exits if task file is corrupted
- SubagentStop may also gain validation checks

## Breaking Changes

1. **In minimal profile**: Tests asserting LastActivity updates will need profile-aware assertions
2. **In strict profile**: Tests may see hook validation errors on edge case task files
3. **API expectations**: Code assuming LastActivity reflects wall-clock time will get stale values in minimal profile

## Files Requiring Changes

**Code:**
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — add env var logic (primary change)

**Documentation (MUST UPDATE):**
1. `.claude/rules/local-workflow.md` — Update Phase 2a to note profile-dependent behavior
2. `plugins/development-harness/skills/implementation-manager/SKILL.md` — Update "Hook Integration" section
3. `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — Add profile behavior note
4. `plugins/development-harness/docs/workflow-architecture-diagram.md` — Verify diagram accuracy

**Tests (MUST ADD):**
1. `plugins/python3-development/skills/implementation-manager/tests/test_task_status_hook/` — Add profile selection tests
2. Environment variable behavior tests for each profile
3. Disabled hooks (CLAUDE_SKILLS_DISABLED_HOOKS) functionality tests

**Backlog items affected by this change:**
- #526 (SubagentStop hook does not mark SAM tasks complete)
- #527 (SubagentStop hook should capture structured summary)
- #530 (Stall detection for subagent tasks)
- #561 (Enforce single-authority task state)
- Multiple other items reference hook timestamp behavior

## Notes

- Hook declarations in SKILL.md do NOT need syntax changes; env var filtering is internal to task_status_hook.py
- No changes to SAM MCP server needed; hook is client-side script
- Orchestrator discipline (who calls hooks) remains unchanged
- Profile selection is entirely runtime; no code generation or conditional skill loading needed
</div>