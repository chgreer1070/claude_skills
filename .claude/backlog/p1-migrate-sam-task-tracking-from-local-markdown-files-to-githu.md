---
name: Migrate SAM task tracking from local markdown files to GitHub sub-issues via backlog MCP
description: "Currently the SAM workflow splits task tracking across two systems:\n- GitHub Issues (via backlog MCP) for stories/backlog items\n- Local `plan/tasks-*.md` files for task status, with `implementation_manager.py` and `task_status_hook.py` managing state\n\n**Proposed architecture:** Unify everything in GitHub Issues using sub-issues.\n- Stories = GitHub Issues (existing)\n- Tasks within a story = GitHub sub-issues of the story issue\n- Research artifacts = tracked as linked issues or issue comments\n- Backlog MCP = extended to handle sub-issue CRUD, status transitions, and readiness queries\n\n**What needs to change:**\n1. Extend backlog MCP server to support sub-issue creation, status query, and dependency-based readiness logic\n2. Replace `implementation_manager.py` task status queries with MCP calls to GitHub sub-issues\n3. Replace `task_status_hook.py` file edits with GitHub API calls (via MCP or CLI) on `PostToolUse`/`SubagentStop` events\n4. Add research artifact tracking (currently absent) as linked issues on the story\n5. Decide offline/network dependency tradeoff — current system works without GitHub; sub-issues require network on every status check\n\n**Benefits:**\n- Single source of truth — no drift between local files and GitHub state\n- Removes accidental complexity (local markdown task files existed because sub-issues weren't prioritized)\n- Better visibility for collaborators\n- Backlog MCP already does CRUD on issues — extending to sub-issues is natural\n\n**Key risk:** Hook scripts fire frequently (every Write/Edit/Bash in a task session); each hook becoming a GitHub API call adds latency and network dependency."
metadata:
  topic: migrate-sam-task-tracking-from-local-markdown-files-to-githu
  source: Architecture discussion — session 2026-03-06
  added: '2026-03-06'
  priority: P1
  type: Refactor
  status: open
  issue: '#480'
  last_synced: '2026-03-06T06:23:55Z'
  groomed: '2026-03-06'
---

## Fact-Check

**Date**: 2026-03-06
**Claims checked**: 5

| Verdict | Count |
|---------|-------|
| VERIFIED | 4 |
| REFUTED | 1 |
| INCONCLUSIVE | 0 |

### Claim 1: GitHub sub-issues REST API is generally available

**VERDICT**: REFUTED
**Source**: GitHub Changelog Dec 2024, Sep 2025; docs.github.com/en/rest/issues/sub-issues (accessed 2026-03-06)
**Evidence**: Dec 2024 announcement explicitly states "available in public preview". No GA announcement found through Mar 2026.
**Citation**: [GitHub Changelog - REST API for sub-issues (Dec 2024)](https://github.blog/changelog/2024-12-12-github-issues-projects-close-issue-as-a-duplicate-rest-api-for-sub-issues-and-more/)

### Claim 2: PyGitHub venv has `get_sub_issues()` / `add_sub_issue()` methods

**VERDICT**: VERIFIED
**Source**: `.venv/lib/python3.11/site-packages/github/Issue.py` lines 572–602 (accessed 2026-03-06)
**Evidence**: Both methods present; `add_sub_issue()` uses `sub_issue.id` (not `.number`).

### Claim 3: `implementation_manager.py` uses local files only (no GitHub API calls)

**VERDICT**: VERIFIED
**Source**: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` (accessed 2026-03-06)
**Evidence**: No GitHub imports; all status operations parse local `plan/tasks-*.md` files via `Path`.

### Claim 4: `task_status_hook.py` edits local markdown files only (no GitHub calls)

**VERDICT**: VERIFIED
**Source**: `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` (accessed 2026-03-06)
**Evidence**: No GitHub imports; all mutations via `Path.write_text()` on local files.

### Claim 5: Backlog MCP `github.py` has CRUD but zero sub-issue methods

**VERDICT**: VERIFIED
**Source**: `.claude/skills/backlog/backlog_core/github.py` (accessed 2026-03-06)
**Evidence**: PyGitHub CRUD confirmed (create, close, resolve, labels). No `sub_issue` methods present.

## RT-ICA

**Decision**: BLOCKED

**Goal**: Eliminate local `plan/tasks-*.md` files by making GitHub sub-issues the single source of truth for SAM task state, managed through the backlog MCP.

| # | Condition | Status | Notes |
|---|-----------|--------|-------|
| 1 | GitHub sub-issues REST API is production-stable | MISSING | REFUTED by fact-check — still public preview as of 2026-03-06. Preview APIs can break without deprecation notice. |
| 2 | PyGitHub library supports sub-issue methods | AVAILABLE | VERIFIED — `get_sub_issues()`, `add_sub_issue()` present in installed venv |
| 3 | Backlog MCP has PyGitHub integration to extend | AVAILABLE | VERIFIED — `github.py` uses PyGitHub, ready to add new methods |
| 4 | `implementation_manager.py` is the only task-status query layer | AVAILABLE | VERIFIED — isolated, no GitHub calls, clean replacement target |
| 5 | `task_status_hook.py` is the only status-write layer | AVAILABLE | VERIFIED — isolated, no GitHub calls, clean replacement target |
| 6 | Hook latency budget for GitHub API calls | DERIVABLE | Hooks fire on every Write/Edit/Bash. API round-trip adds ~100–500ms per hook event. Impact unknown without measurement. |
| 7 | Offline/network-degraded operation strategy | MISSING | No fallback design exists. Current system works without network; replacement would not. |
| 8 | Sub-issue dependency graph maps to current task dependency model | DERIVABLE | GitHub sub-issues express parent-child but not arbitrary task→task dependency. Current model allows `Task 1.1, Task 2.3` as deps. Needs design. |

**Missing inputs that prevent full planning**:
1. Preview API risk decision — choose: (a) accept preview risk and build now, (b) wait for GA, (c) hybrid approach (GitHub Issues as display layer, local files as execution state)
2. Offline strategy — define behavior when GitHub is unreachable during hook execution
3. Dependency model mapping — define how `Task A depends on Task B, C` maps to GitHub sub-issue structure

## Groomed (2026-03-06)

### Issue Classification

**Type**: unbounded-design
**Scenario-target**: Architectural migration — two valid designs (full GitHub-native vs hybrid) with unresolved tradeoffs on API stability, latency, and offline behavior.
**Analysis method**: design-framing (no RCA needed — not a defect or recurring pattern)

### Reproducibility

**Current state** (observable by reading the files below):

1. Run `uv run plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py status . <slug>` — returns JSON parsed from local `plan/tasks-*.md` files. No GitHub API calls. All I/O via `Path.read_text()` / `Path.write_text()`.
2. Trigger a `SubagentStop` or `PostToolUse` hook event — `task_status_hook.py` updates YAML frontmatter fields (`status`, `completed`, `last_activity`) directly in the local task file. No GitHub API calls. Uses `Path.write_text()`.
3. Inspect `.claude/skills/backlog/backlog_core/github.py` — PyGitHub CRUD present for story-level issues (create, close, resolve, label, fetch body). Zero `sub_issue` methods in this file.
4. Inspect `.venv/lib/python3.11/site-packages/github/Issue.py` lines 572–606 — `get_sub_issues()` and `add_sub_issue()` methods present; `add_sub_issue()` uses `sub_issue.id` (numeric GitHub node ID), not `sub_issue.number`.

**Proposed state** (what done looks like, observable from outside):

- `implementation_manager.py status . <slug>` returns task counts derived from GitHub sub-issues on the parent story issue, not from local markdown files.
- `task_status_hook.py` SubagentStop and PostToolUse events call GitHub API (via MCP or PyGitHub) to update sub-issue state rather than writing local files.
- `backlog_core/github.py` exposes `list_sub_issues()`, `add_sub_issue()`, `update_sub_issue_status()` returning structured dicts.
- `plan/tasks-*.md` files are either absent or demoted to read-only reference artifacts — they are no longer the execution source of truth.

### Priority

5/10 — Architecturally valuable but blocked on unresolved design decisions (preview API risk, offline behavior, dependency model). Current system works; this is a quality-of-life and single-source-of-truth improvement, not a defect fix. Cannot begin planning until the three MISSING RT-ICA conditions are resolved by human decision.

### Impact

- Blocks: Nothing is blocked on this today — existing system functions.
- Bottleneck: The split-system problem causes drift: task status in local markdown can diverge from the GitHub story issue, making it impossible to know task progress from GitHub alone. Collaborators (and future agents) who see only GitHub Issues see no task-level state.
- Hook latency risk: `task_status_hook.py` fires on every Write/Edit/Bash in a task session. Replacing file writes with GitHub API calls adds ~100–500ms per hook event and creates a hard network dependency in the hot path of every agent operation.

### Benefits

- GitHub becomes the single source of truth for both story and task state — no drift possible.
- Task progress visible to collaborators without access to local `plan/` files.
- Backlog MCP already manages issues — sub-issue support is a natural extension of existing PyGitHub integration.
- Eliminates the `plan/tasks-*.md` file format as an operational concern — agents no longer need to parse YAML frontmatter to query task state.
- Enables future task querying by any MCP client, not just the local orchestrator.