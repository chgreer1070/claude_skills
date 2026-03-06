# Comparison Analysis: GitHub Task Dependency Options for SAM Workflow

## Metadata

- **Generated**: 2026-03-06
- **Research Mode**: Comparison Analysis
- **Options**: Issue-body cross-references vs GitHub Sub-issues + body deps vs Projects v2 custom fields
- **Decision Context**: Replacing local markdown task files with GitHub Issues as task storage, while preserving SAM dependency resolution (`get_ready_tasks` logic)
- **Status**: COMPARISON_COMPLETE

---

## MCP Tool Availability Notice

Claims sourced from:

- **Installed PyGitHub source** at `.venv/lib/python3.11/site-packages/github/Issue.py` — HIGH confidence (copyright 2025)
- **Local codebase files** (implementation_manager.py, task_format.py, github.py) — HIGH confidence
- **Training data** about GitHub Projects v2 and GraphQL API — tagged UNVERIFIED; check URLs in Open Questions section before implementing

---

## Executive Summary

**Recommendation**: Option B (GitHub Sub-issues + structured issue body for dep list).

The SAM dependency model is a DAG resolved locally from a complete task list. `get_ready_tasks()` loads ALL tasks into memory and resolves deps in O(N). This maps cleanly to a local file cache of GitHub Issues — the same pattern the backlog MCP already uses. No option requires a server-side dep query at runtime; readiness is always a local computation over a synced cache.

---

## Current SAM Dependency Model

**Source**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (read 2026-03-06)

### Task dataclass (lines 95-141) — HIGH confidence

- `id: str` — task identifier, e.g. "T1", "1.1", "T15"
- `status: TaskStatus` — NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED | DEFERRED | SKIPPED
- `dependencies: list[str]` — list of task ID strings, e.g. `["T1", "T2"]`

### Readiness logic (lines 770-799) — HIGH confidence

```python
_TERMINAL_STATUSES = frozenset({TaskStatus.COMPLETE, TaskStatus.DEFERRED, TaskStatus.SKIPPED})

def get_ready_tasks(tasks: list[Task]) -> list[Task]:
    status_by_id = {task.id: task.status for task in tasks}
    ready = []
    for task in tasks:
        if task.status != TaskStatus.NOT_STARTED:
            continue
        deps_satisfied = all(
            status_by_id.get(dep_id) in _TERMINAL_STATUSES
            for dep_id in task.dependencies
        )
        if deps_satisfied:
            ready.append(task)
    return ready
```

A task is ready when: status is NOT_STARTED AND all listed dependency IDs resolve to a terminal status.

### Dependencies field format — HIGH confidence

YAML format: `dependencies: [T1, T2]` or `dependencies: "T1, T2"`. Both forms parsed to `list[str]`.

### Current github.py state — HIGH confidence

`.claude/skills/backlog/backlog_core/github.py` has no calls to `get_sub_issues`, `add_sub_issue`, `prioritize_sub_issue`, or `remove_sub_issue`. Sub-issues are not currently used.

---

## PyGitHub Sub-Issue API (Installed Version)

**Source**: `.venv/lib/python3.11/site-packages/github/Issue.py` (read 2026-03-06, copyright 2025)

### Available methods — HIGH confidence

| Method | REST Endpoint | Purpose |
|--------|--------------|---------|
| `issue.get_sub_issues()` | `GET /repos/{owner}/{repo}/issues/{number}/sub_issues` | Returns `PaginatedList[SubIssue]` |
| `issue.add_sub_issue(sub_issue)` | `POST /repos/{owner}/{repo}/issues/{number}/sub_issues` | Adds a sub-issue; accepts int (`.id`) or `Issue` object |
| `issue.remove_sub_issue(sub_issue)` | `DELETE /repos/{owner}/{repo}/issues/{number}/sub_issue` | Removes a sub-issue |
| `issue.prioritize_sub_issue(sub_issue, after_sub_issue)` | `PATCH /repos/{owner}/{repo}/issues/{number}/sub_issues/priority` | Reorders; `after_sub_issue=None` moves to front |

### SubIssue attributes — HIGH confidence

Inherits all `Issue` fields plus:

- `parent_issue: Issue` — back-reference to parent
- `priority_position: int` — ordinal position in the parent's sub-issue list

### Critical `.id` vs `.number` requirement — HIGH confidence (Issue.py line 588)

`add_sub_issue()` requires the issue's `.id` (GraphQL node ID integer), NOT `.number` (human-visible `#N`). The docstring at line 588 states: "Note: Use sub_issue.id, not sub_issue.number". Implementation at line 595 confirms.

```python
# Wrong — silently sends wrong value:
parent.add_sub_issue(child.number)

# Correct — pass the Issue object; library extracts .id:
parent.add_sub_issue(child)
```

Always pass the `Issue` object, never extract `.id` manually — both `.id` and `.number` are integers, confusing them produces no type error.

### Sub-issue ordering — HIGH confidence

`get_sub_issues()` passes no server-side ordering parameter. `SubIssue.priority_position` is returned by the API. `prioritize_sub_issue(sub_issue, after_sub_issue=None)` sends `{"after_id": null}` = "move to front".

---

## Option A: Issue Body Cross-References with Local Dep Parse

### How it works

Each task issue body contains a structured section listing `#N` issue numbers:

```markdown
## SAM Dependencies
Depends on: #42, #43
```

On sync, parse the body to extract issue numbers. Store as `dependencies: [42, 43]` in local cache. Readiness check reads cache, uses existing O(N) logic.

### GitHub cross-reference behavior — UNVERIFIED

When `#42` appears in an issue body, GitHub creates a "mentioned in" timeline event in issue #42 (`CrossReferencedEvent`). This is a display feature, not a queryable dep field. Reverse-dep queries require GraphQL `timelineItems(itemTypes: [CROSS_REFERENCED_EVENT])`.

Verify at: <https://docs.github.com/en/graphql/reference/objects#issue>

### Readiness query

Local cache read only — no API call at execution time.

### Offline support

Full offline support.

### Complexity: **Simple**

1. Define machine-parseable body format for dep section
2. Parse section in sync path, store issue numbers in local cache
3. No changes to `implementation_manager.py`

### Limitations

- Body format must be machine-parseable; human edits can break parsing silently
- No GitHub-native dep relationship — text convention only
- No hierarchy grouping — task issues appear as flat standalone issues

---

## Option B: GitHub Sub-Issues for Tasks + Body-Parsed Dep List

### How it works

The parent story issue gets sub-issues, one per SAM task. Each task issue body includes a "Dependencies" section (same parsing as Option A). The sub-issue relationship adds:

- Hierarchical grouping: parent shows sub-issue checklist with completion status
- Progress indicator on parent issue
- `get_sub_issues()` retrieves all tasks under a story without knowing issue numbers in advance

Dep graph is still expressed in issue bodies and resolved locally.

### Task creation flow

```python
# Create task issue
task_issue = repo.create_issue(
    title=f"[{task_id}] {task_name}",
    body=build_task_body(task),  # SAM metadata + ## SAM Dependencies section
    labels=["sam-task", f"priority:{priority}"]
)

# Link as sub-issue — pass Issue object to avoid .id/.number confusion
parent_story.add_sub_issue(task_issue)

# Optional: set display order
parent_story.prioritize_sub_issue(task_issue, after_sub_issue=prev_task)
```

### Readiness query

```python
sub_issues = load_cached_sub_issues(story_issue_number)
tasks = [parse_task_from_issue(si) for si in sub_issues]
ready = get_ready_tasks(tasks)  # existing logic, unchanged
```

### Offline support

Full offline support. Same caching pattern as existing backlog MCP.

### Complexity: **Medium**

1. `create_task_issue()` — creates issue + links as sub-issue
2. `get_task_issues()` — wraps `get_sub_issues()` with caching
3. `update_task_status()` — edits issue body Status section or label
4. `sync_tasks_from_github()` — pulls sub-issues, parses body, writes local cache
5. Body format schema for all SAM task fields

### Limitations

- Sub-issues are a 2024/2025 GitHub feature. Plan availability UNVERIFIED.
- `.id` vs `.number` confusion mitigated by passing `Issue` object, but must be documented
- Two-API-call creation (create issue + link) — partial failure needs error handling
- No server-side ordering control — order reflects `priority_position` from explicit calls

---

## Option C: GitHub Projects v2 Custom Fields for Dependency Metadata

### How it works

Tasks are GitHub Issues added to a Projects v2 board. A custom "Depends On" text field stores the dep list. Status is a Projects v2 field. Readiness computed locally from synced cache of project item field values.

### Projects v2 field types — UNVERIFIED

Training data indicates: Text, Number, Date, Single select, Iteration, Milestone. **No native "blocked by" or "depends on" field type exists.** Deps expressed via a Text custom field.

Verify at: <https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields>

### Projects v2 is GraphQL-only — UNVERIFIED

All field creation, item addition, and field value mutations require GraphQL. PyGitHub REST client does not directly support Projects v2 GraphQL mutations. Raw HTTP calls needed.

Verify at: <https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects>

### Offline support

Requires local cache. Sync more complex due to GraphQL pagination and opaque field IDs.

### Complexity: **Complex**

1. GraphQL client setup — outside PyGitHub REST
2. Project ID discovery — opaque GraphQL node IDs
3. `add_item_to_project()` — GraphQL mutation
4. `set_field_value()` — GraphQL mutation per field, field IDs discovered separately
5. `sync_project_items()` — GraphQL pagination with field values
6. Field ID caching

### Limitations

- GraphQL-only — significant complexity vs REST
- Projects v2 as a hard dependency — project must be set up
- Plan availability for automation features UNVERIFIED
- PyGitHub Projects v2 coverage not checked

Check: `grep -rn "ProjectV2" .venv/lib/python3.11/site-packages/github/`

---

## Comparison Matrix

| Criterion | A: Body Cross-refs | B: Sub-issues + Body Deps | C: Projects v2 Fields |
|-----------|--------------------|---------------------------|------------------------|
| Dep graph expression | Text in body | Text in body | Custom text field |
| GitHub UI hierarchy | None — flat issues | Sub-issue checklist on parent | Board grouping |
| Readiness query | Local cache | Local cache | Local cache |
| Dep enforcement | None | None | None |
| Offline support | Full | Full | Full (with cache) |
| PyGitHub support | HIGH — REST | HIGH — verified in source | LOW — GraphQL only |
| Impl complexity | Simple | Medium | Complex |
| `.id`/`.number` footgun | No | Yes (mitigated by object passing) | Yes (GraphQL node IDs) |
| Feature availability risk | Low | Medium (new feature) | High (plan limits, GraphQL) |
| Pattern consistency w/ backlog MCP | Partial | High | Low |

---

## Key Invariant Across All Options

None of the three options provide native GitHub dep enforcement. GitHub has no "blocked by" or "depends on" issue relationship type (as of training data cutoff August 2025 — UNVERIFIED for current state). The dep list is always expressed as a text field and resolved by parsing.

This means:

- `get_ready_tasks()` is unchanged in all options
- Local cache stores `dependencies: list[int]` parsed from text
- The difference between options is structural metadata (hierarchy, board grouping) and API surface, not dep resolution

---

## Recommendation

**Option B** (sub-issues + body dep list).

1. Sub-issues provide the story-to-task hierarchy matching the SAM mental model — visible in GitHub UI as a completion checklist
2. `get_sub_issues()` is verified in the installed PyGitHub (copyright 2025, lines 572-578)
3. Dep resolution stays local and unchanged
4. Consistent with the existing backlog MCP caching pattern
5. `prioritize_sub_issue()` reflects execution priority in the UI

**Fallback**: If sub-issues are unavailable on the repo's plan, use Option A. Readiness logic is identical; only the GitHub UI hierarchy is lost.

**Confidence**: MEDIUM — all PyGitHub API facts HIGH from installed source; sub-issue plan availability and ordering behavior are UNVERIFIED.

---

## Open Questions Requiring Verification Before Implementation

1. Sub-issue plan availability — <https://docs.github.com/en/rest/issues/sub-issues>
2. `get_sub_issues()` ordering guarantee (by `priority_position`?) — same URL
3. CrossReferencedEvent GraphQL query — <https://docs.github.com/en/graphql/reference/objects#issue>
4. Native Projects v2 dep field after August 2025? — <https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields>
5. PyGitHub Projects v2 coverage — run: `grep -rn "ProjectV2" .venv/lib/python3.11/site-packages/github/`

---

## Sources

1. `LOCAL: .venv/lib/python3.11/site-packages/github/Issue.py` (read 2026-03-06, copyright 2025) — sub-issue methods lines 572–655, SubIssue class lines 822–861, `.id` requirement line 588/595
2. `LOCAL: plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (read 2026-03-06) — Task dataclass lines 95–141, `get_ready_tasks` lines 770–799, `_TERMINAL_STATUSES` line 78
3. `LOCAL: plugins/python3-development/skills/implementation-manager/scripts/task_format.py` (read 2026-03-06) — YAML dep parsing lines 318–335
4. `LOCAL: .claude/skills/backlog/backlog_core/github.py` (read 2026-03-06) — confirms no sub-issue methods; establishes existing REST caching pattern
5. Training data (cutoff August 2025) — GitHub Projects v2 field types, GraphQL API patterns — all tagged UNVERIFIED
