# Pipeline Completion-to-Closure Patterns

**Scope**: Current data flow and checkpoint structure for completing features and resolving backlog items.

**Date**: 2026-03-17

---

## 1. Completion Flow (Feature → Resolved)

### 1.1 Task Completion Lifecycle

**Entry point**: `/implement-feature` dispatch loop

**Paths**:
- Task marked `IN PROGRESS` via `sam claim P{N}/{task_id}` (only permitted path)
- Hook `PostToolUse` (Write|Edit|Bash) updates `LastActivity` timestamp
- Hook `SubagentStop` marks status `COMPLETE`, adds `Completed` timestamp
- Context file `.claude/context/active-task-{session_id}.json` stores `{task_file_path, task_id, parent_issue_number}`

**Timestamp responsibilities**:
- `Started`: Agent writes via `/start-task` skill logic
- `Completed`: `task_status_hook.py` (SubagentStop event) writes
- `LastActivity`: `task_status_hook.py` (PostToolUse event) updates

**GitHub sync during task execution** (if `parent_issue_number` known):
- `backlog_core.github.update_task_status()` syncs task status → GitHub sub-issue
- Failure is non-fatal (continue regardless)

---

### 1.2 Acceptance Criteria Verification (Bookend Tasks)

**When invoked**: Task file contains `acceptance-criteria-structured` entries

**T0 (t0-baseline-capture) — Priority 1**:
- No dependencies (runs first)
- Reads each `check_command` from `acceptance-criteria-structured`
- Executes command, captures exit code + stdout + stderr
- Writes `plan/T0-baseline-{slug}.yaml`
- Non-zero exits expected and do NOT fail T0

**TN (tn-verification-gate) — Priority 5**:
- Depends on all non-bookend implementation tasks
- Reads `plan/T0-baseline-{slug}.yaml`
- Re-runs each `check_command`
- Classifies each criterion using 4-cell matrix:
  - T0 pass + TN pass → `status: passed`
  - T0 pass + TN fail → `status: regressed` (BLOCKS completion)
  - T0 fail + TN fail → `status: pre-existing-fail`
  - T0 fail + TN pass → `status: newly-passing`
- Writes `plan/TN-verification-{slug}.yaml` (list of `BookendVerification` records)

**Pre-Phase-1 verification** (in `/complete-implementation`):
- Read `plan/TN-verification-{slug}.yaml`
- Scan all records for `status: regressed`
- If ANY record has `regressed`: STOP, report regressions, block completion
- Else: proceed to Phase 1

---

### 1.3 Quality Gates (`/complete-implementation`)

**Phase sequence**:
1. **Code Review** (`code-reviewer`) → produces follow-up task files if issues found
2. **Feature Verification** (`feature-verifier`) → goal-backward structural check
3. **Integration Check** (`integration-checker`) → integration points
4. **Documentation Drift Audit** (`doc-drift-auditor`) → read-only scan
5. **Documentation Update** (`service-docs-maintainer`) → if drift found (optional)
6. **Context Refinement** (`context-refinement`) → update Context Manifest + plan artifact freshness check

**Outputs**:
- Context Manifest updated with implementation discoveries
- Plan artifacts annotated if divergence found
- `DIVERGENCE_REQUIRING_REVIEW` block if intent-divergence detected
- Follow-up task files created by Phase 1

**Follow-up routing**:
- Extract file paths from `code-reviewer` ARTIFACTS
- Derive search slug from filename (strip prefix/suffix, hyphens → spaces)
- Search backlog via `backlog_list(title="{slug}")` (Strategy 1) then `backlog_list(topic="{slug}")` (Strategy 2)
- Match found: `backlog_update(selector="...", plan="{followup_path}")`
- No match: `create-backlog-item --auto`, then `backlog_update(selector="...", plan="{followup_path}")`
- Recursion gate: BOTH conditions required:
  - Same slug as parent (scope match)
  - `## Priority` section = `High`
- If EITHER fails: defer to backlog (no recursion)

**Final commit**:
- Check `git status` for modified files
- Query backlog for feature issue number: `backlog_list(title="{slug}")`
- If issue found and commit resolves it: append `Fixes #NNN` to commit body
- Stage and commit

---

## 2. Backlog Item Closure (Resolve vs Close)

### 2.1 Close Path (Dismiss without completion — ADR-9)

**Trigger**: `/work-backlog-item close {title}`

**Steps**:
1. Find item via `backlog_view(selector="{title}")`
2. Ask dismissal reason (user chooses):
   - `duplicate` | `out_of_scope` | `superseded` | `wontfix` | `blocked`
3. If `duplicate` or `superseded`: ask for reference (`#N` or title)
4. Optionally ask for comment (free text)
5. Call `backlog_close(selector="...", reason="...", reference="...", comment="...")`
6. **GitHub side effect**: `close_github_issue()` creates comment + closes issue

**Function signatures**:

```python
def close_github_issue(
    issue_ref: str,
    reason: str,
    *,
    reference: str = "",
    comment: str = "",
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> None:
    """Close GitHub issue as dismissed (not completed). ADR-9."""
    # Creates comment: "**Closed** ({reason}).", appends reference & comment, closes issue
```

---

### 2.2 Resolve Path (Mark DONE with evidence trail — ADR-9)

**Trigger**: `/work-backlog-item resolve {title}`

**Checklist phase (9c)**:
- Extract `**Plan**:` field
- Read plan file
- Count `- [ ]` and `- [x]` lines
- If `checked < total`: report incomplete, STOP
- Else: proceed

**Acceptance criteria verification (9d)**:
- Extract `**Acceptance Criteria**:` from per-item file or backlog body
- Spawn verification agent with `subagent_type="general-purpose"`
- Prompt includes: item title, plan path, checklist status (100%), each criterion as "Criterion N: {text}"
- Agent returns per-criterion PASS/FAIL with file:line evidence
- Parse verdict:
  - Overall PASS: proceed to PR check
  - Overall FAIL: report gaps, STOP (do not resolve)

**PR check (9e)**:
- If item has linked GitHub Issue (`#N`):
  - Check git log for `Fixes #N` or `Closes #N` in recent commits
  - If found: PR auto-closes issue on merge
    - Update local status to `in-progress`
    - Report: "GitHub Issue will auto-close on merge"
    - STOP (do not resolve locally)
  - Else: proceed to 9f

**Invoke resolve (9f)**:
- Ask summary: "Summarize what was done (1-2 sentences):" (REQUIRED)
- Optionally gather:
  - `method` — "How was the work done?"
  - `notes` — "Any problems found or surprises?"
  - `follow_ups` — "Follow-up tickets created?" (comma-separated refs)
  - `findings` — "Retrospective learnings?"
- Call `backlog_resolve(selector="...", summary="...", plan="...", method="...", notes="...", follow_ups="...", findings="...")`

**Function signatures**:

```python
def resolve_github_issue(
    issue_ref: str,
    *,
    summary: str,
    method: str = "",
    notes: str = "",
    follow_ups: str = "",
    findings: str = "",
    repo: str = DEFAULT_REPO,
    output: Output | None = None,
) -> None:
    """Close GitHub issue as completed with structured evidence trail. ADR-9."""
    # Creates comment with ## Resolved section containing summary, method, notes, follow-ups, findings
    # Then closes issue
```

---

## 3. GitHub Status Synchronization

### 3.1 In-Progress Status (During Execution)

**Entry point**: Task claimed via `/start-task`

**Function signature**:

```python
def apply_status_in_progress(
    item: BacklogItem,
    repo: str = DEFAULT_REPO,
    output: Output | None = None
) -> None:
    """Set GitHub issue label to status:in-progress."""
    # Adds status:in-progress label
    # Removes status:needs-grooming if present
```

**Data flow**:
- Called during task execution if `parent_issue_number` known and `github_issue` field set
- Checks current labels
- Adds `status:in-progress` if not present
- Removes `status:needs-grooming` if present

**Task status update** (on GitHub sub-issues):

```python
def update_task_status(
    repo: Repository,
    issue_number: int,
    new_status: str,
    output: Output | None = None
) -> bool:
    """Update status field inside <!-- sam:task ... --> block of task issue body."""
    # Reads current body, patches YAML block's status value, writes back
    # Returns: True if updated, False if no-op or error
```

---

### 3.2 Local Cache Refresh (`refresh_local_cache_from_github`)

**Purpose**: Pull GitHub issue state into local per-item files

**Data fetched**:
- Open issues only (filters closed, PRs)
- Per issue: `number`, `title`, `state`, `body`, `labels`, `milestone`
- Status extracted from `status:*` labels
- Priority extracted from `priority:*` labels

**Function signature** (inferred from usage):

```python
def batch_fetch_statuses(
    items: list[BacklogItem],
    repo: str = DEFAULT_REPO
) -> dict[int, IssueStatus]:
    """Batch fetch status and milestone from GH for all items with issue numbers."""
    # Returns: Dict mapping issue_number -> IssueStatus(status, milestone)
```

**State parameter logic** (referenced in workflow):
- When called with `state="open"`: fetches only open issues
- Repository object's `get_issues(state="open")` used for batch fetch
- Filters out pull requests: `if issue.pull_request is None`

---

## 4. Completion Checkpoints and Data Integrity

### 4.1 What Checks Exist

**Task completion**:
- ✓ Task claimed (prevents duplicate dispatch)
- ✓ Status: `NOT STARTED` → `IN PROGRESS` (via `sam claim`)
- ✓ Status: `IN PROGRESS` → `COMPLETE` (via hook only, no direct edit)
- ✓ Timestamps: `Started`, `Completed`, `LastActivity` recorded

**Acceptance criteria verification**:
- ✓ T0 baseline captured before implementation
- ✓ TN verification gates on regression (blocks if any criterion regressed)
- ✓ 4-cell matrix classification (passed/regressed/pre-existing-fail/newly-passing)

**Quality gates** (before resolve):
- ✓ Code review (Phase 1)
- ✓ Feature verification (Phase 2)
- ✓ Integration check (Phase 3)
- ✓ Documentation drift audit (Phase 4)
- ✓ Context refinement + plan artifact freshness (Phase 6)

**Resolve preconditions**:
- ✓ Checklist 100% complete (if plan attached)
- ✓ Acceptance criteria pass (if defined)
- ✓ No open PR already closing the issue
- ✓ Summary provided (required)

**GitHub sync gates**:
- ✓ Issue created before any GitHub write (backlog_add or backlog_sync with create_issue=True)
- ✓ Status labels applied atomically (add new + remove old in same operation)
- ✓ Groomed content synced to issue before label removal (status:needs-grooming)

---

### 4.2 What Checks Are Missing

**Pre-resolve verification**:
- ✗ No verification that implementation files exist
- ✗ No verification that commits reference the issue
- ✗ No verification that feature branch exists or has changes
- ✗ No cross-check: "is the feature actually merged into main?"

**Acceptance criteria**:
- ✗ No verification that T0 baseline file exists before TN runs
- ✗ No recovery if T0 baseline is corrupted or stale
- ✗ No per-criterion detail in TN output (only top-level verdict)

**Follow-up routing**:
- ✗ No validation that follow-up task files are well-formed
- ✗ No check that derived slug matches actual filename pattern
- ✗ No fallback if both backlog search strategies fail (creates item but no verification it was created)

**GitHub issue closure**:
- ✗ No pre-check that issue is not already in a terminal state (closed, archived)
- ✗ No guard against closing same issue twice (from different backlog paths)
- ✗ No verification that `Fixes #N` commit exists before reporting "auto-closes on merge"

**Label management**:
- ✗ No atomic transaction wrapping status label add + remove (separate API calls)
- ✗ No verification that labels exist before attempting to add/remove
- ✗ No recovery if label operation fails mid-operation

---

## 5. Data Flow Diagram (Completion → Closure)

```
Feature Execution
  │
  ├─ T0: t0-baseline-capture (Priority 1)
  │  └─ Runs check_commands, writes plan/T0-baseline-{slug}.yaml
  │
  ├─ T1..TN-1: Implementation tasks
  │  ├─ sam claim P{N}/T{M} → status: IN PROGRESS
  │  ├─ PostToolUse hook updates LastActivity
  │  └─ SubagentStop hook → status: COMPLETE + Completed timestamp
  │
  └─ TN: tn-verification-gate (Priority 5)
     ├─ Reads T0 baseline
     ├─ Re-runs check_commands
     ├─ Writes plan/TN-verification-{slug}.yaml
     └─ If any regressed: STOP (blocks complete-implementation)
       │
       └─ /complete-implementation
          ├─ Pre-Phase 1: Read TN verification → STOP if regressed
          │
          ├─ Phase 1: code-reviewer
          │  └─ Produces follow-up task files (if issues found)
          │
          ├─ Phase 2: feature-verifier (goal-backward check)
          ├─ Phase 3: integration-checker
          ├─ Phase 4: doc-drift-auditor
          ├─ Phase 5: service-docs-maintainer (if drift found)
          ├─ Phase 6: context-refinement (plan artifact freshness)
          │
          ├─ Follow-up routing
          │  ├─ Search backlog (Strategy 1: title, Strategy 2: topic)
          │  ├─ Link or create backlog item
          │  └─ Gate: same slug + High priority → recurse | else defer
          │
          └─ Final commit + push
             └─ Issue number lookup: backlog_list(title="{slug}")
                └─ If issue found: append Fixes #NNN

Backlog Item Resolve
  │
  ├─ backlog_view(selector="{title}") → find item
  │
  ├─ If close path:
  │  ├─ Ask dismissal reason
  │  ├─ backlog_close() → local status update
  │  └─ close_github_issue() → comment + close
  │     └─ Creates: "**Closed** ({reason})." with reference & comment
  │
  └─ If resolve path:
     ├─ Checklist verification (if plan attached)
     │  └─ STOP if checked < total
     │
     ├─ Acceptance criteria verification (if criteria defined)
     │  ├─ Spawn general-purpose agent
     │  └─ STOP if overall FAIL
     │
     ├─ PR check (if GitHub issue linked)
     │  ├─ git log --grep "Fixes #N"
     │  └─ If found: report "auto-closes on merge", STOP (no local resolve)
     │
     └─ backlog_resolve()
        ├─ Ask summary (required)
        ├─ Optionally gather: method, notes, follow-ups, findings
        └─ resolve_github_issue()
           └─ Creates: ## Resolved section with evidence trail + closes issue
```

---

## 6. External Interface Points

### 6.1 GitHub API Calls

**Issue creation**:
- `Repository.create_issue(title, body, labels)` → creates new issue

**Issue closure**:
- `Issue.create_comment(body)` → posts comment (used for dismissal reason, evidence trail)
- `Issue.edit(state="closed")` → closes issue

**Status management**:
- `Issue.add_to_labels(label_object)` → adds status:in-progress
- `Issue.remove_from_labels(label_object)` → removes status:needs-grooming
- `Repository.get_label(name)` → fetches label object

**Issue body updates**:
- `Issue.edit(body=new_body)` → overwrites issue body (groomed content sync)

**Sub-issue operations**:
- `Issue.add_sub_issue(task_issue)` → links task issue to parent story
- `Issue.get_sub_issues()` → fetches task issues, ordered by `priority_position`

**Task status sync**:
- `Issue.body` → read (extracts `<!-- sam:task ... -->` YAML block)
- `Issue.edit(body=updated_body)` → write (patches `status:` field inside block)

---

### 6.2 Local File Operations

**Per-item file structure**:
```yaml
---
name: {title}
description: {description}
source: {source}
added: {ISO date}
priority: {P0|P1|P2}
type: {Feature|Bug|Refactor|Docs|Chore}
status: {open|in-progress|done|...}
issue: #{N} or blank
plan: {path/to/plan/file} or blank
metadata:
  groomed: {ISO date}
  last_synced: {ISO timestamp}
---

## Description

{Free-form text}

## Groomed ({ISO date})

{Entry blocks with timestamps}

## Acceptance Criteria

- {criterion 1}
- {criterion 2}
```

**Frontmatter updates**:
- `update_item_metadata(filepath, {updates}, set_synced=bool)` → patches metadata

**Content sync**:
- `_write_groomed_to_item_file(filepath, content, section_name, entry_id, replace_section, reason)` → adds/updates Groomed section with entry blocks

**Body replacement**:
- `_overwrite_body_from_github(filepath, issue_body)` → pulls GitHub issue body into cache

---

## 7. Known Risks and Edge Cases

**Risk: PR-based auto-close collides with local resolve**

- Pattern: Item linked to issue, PR with `Fixes #N` exists and is open
- Current behavior: `/work-backlog-item resolve` detects PR, stops, reports "will auto-close on merge"
- Risk: If PR is stale or abandoned, issue never closes
- Mitigation: Resolve workflow asks user to clean up stale PRs first

**Risk: Regressed acceptance criteria blocks all completion**

- Pattern: TN verification finds `status: regressed` on any criterion
- Current behavior: `/complete-implementation` stops before Phase 1
- Risk: User must re-run implementation tasks even if other criteria passed
- Mitigation: TN output should list only regressed criteria (not blocking all)

**Risk: Follow-up routing silent failure**

- Pattern: `create-backlog-item --auto` creates item, `backlog_update` search fails
- Current behavior: Error logged, continues to next follow-up
- Risk: Follow-up not linked to backlog item (orphaned task file)
- Mitigation: Fallback: retry search on most recently created item

**Risk: Status label atomicity**

- Pattern: `apply_status_in_progress()` calls add + remove separately
- Current behavior: If remove fails after add, label is in inconsistent state
- Mitigation: Wrap both in transaction or add idempotent guard (check state before each call)

---

## 8. Validation Summary

| Component | Check | Status | Missing |
|-----------|-------|--------|---------|
| Task completion | Status path enforcement | ✓ via `sam claim` | Verification: does commit exist? |
| Acceptance criteria | T0 baseline capture | ✓ (`t0-baseline-capture`) | Recovery: if baseline corrupted |
| Acceptance criteria | TN regression detection | ✓ (4-cell matrix) | Detail: per-criterion output |
| Quality gates | Phase 1-6 sequence | ✓ (code-reviewer..context-refinement) | Guard: prevent out-of-order execution |
| Follow-up routing | Backlog search | ✓ (2-strategy fallback) | Validation: slug matches filename |
| GitHub sync | Status labels | ✓ (add/remove) | Atomicity: no transaction wrapping |
| GitHub sync | Issue closure | ✓ (comment + close) | Guard: check not already closed |
| Resolve preconditions | Checklist check | ✓ (count [ ] vs [x]) | Sync: verify against GitHub state |
| Resolve preconditions | Criteria verification | ✓ (general-purpose agent) | Evidence: store verdict history |
| Resolve preconditions | PR check | ✓ (git log --grep) | Validation: confirm commit is merged |

---

## References

- `.claude/skills/backlog/backlog_core/github.py` — GitHub API operations (signatures, label management, issue closure)
- `.claude/skills/backlog/backlog_core/operations.py` — CRUD operations (metadata updates, groomed content sync, file I/O)
- `plugins/python3-development/skills/complete-implementation/SKILL.md` — Quality gates workflow (phases 1-6, follow-up routing, commit step)
- `plugins/python3-development/skills/start-task/SKILL.md` — Task execution (claim, context file, divergence notes)
- `.claude/rules/local-workflow.md` — SAM workflow (execution loop, hook configuration, bookend tasks)
- `.claude/skills/work-backlog-item/references/close-resolve-procedure.md` — Resolve/close checklist (steps 9a-9f, preconditions, evidence trail)

