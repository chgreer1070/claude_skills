---
name: 'fetch_gitlab_mr.py: replace subprocess glab call with python-gitlab library'
description: "fetch_gitlab_mr.py shells out to the 'glab' binary (lines 105-114) to fetch MR data. The script already has PyGithub as a dependency and the codebase uses python-gitlab elsewhere. Subprocess call to glab: (1) requires glab binary on PATH, (2) bypasses token auth handled by libraries, (3) triggered S607 linting error that was patched with shutil.which instead of fixed architecturally. Fix: replace subprocess.run(['glab', ...]) with python-gitlab equivalent API call. This eliminates the binary dependency entirely."
metadata:
  topic: fetchgitlabmrpy-replace-subprocess-glab-call-with-python-git
  source: Not specified
  added: '2026-03-01'
  priority: P2
  type: Feature
  status: open
  issue: '#368'
  last_synced: '2026-03-02T02:53:43Z'
  groomed: '2026-03-02'
  plan: plan/tasks-17-replace-glab-subprocess.md
---

## Story

As a **developer using Claude Code skills**, I want to **fetch_gitlab_mr.py: replace subprocess glab call with python-gitlab library** so that **the tooling becomes more capable and complete**.

## Description

fetch_gitlab_mr.py shells out to the 'glab' binary (lines 105-114) to fetch MR data. The script already has PyGithub as a dependency and the codebase uses python-gitlab elsewhere. Subprocess call to glab: (1) requires glab binary on PATH, (2) bypasses token auth handled by libraries, (3) triggered S607 linting error that was patched with shutil.which instead of fixed architecturally. Fix: replace subprocess.run(['glab', ...]) with python-gitlab equivalent API call. This eliminates the binary dependency entirely.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Not specified
- **Priority**: P2
- **Added**: 2026-03-01
- **Research questions**: None

## Fact-Check

**Date**: 2026-03-02
**Claims checked**: 5

| Claim | Verdict | Evidence |
|-------|---------|----------|
| shells out to glab at lines 105-114 | VERIFIED | Lines 105-114: shutil.which("glab") + subprocess.run() |
| Script has PyGithub dependency | REFUTED | Line 4: deps are python-gitlab, gitpython, typer — NOT PyGithub |
| Codebase uses python-gitlab elsewhere | VERIFIED | 13 files match; gitlab_context.py, pyproject.toml |
| Subprocess triggered S607 linting error | VERIFIED | p2-fix-pre-existing-linting backlog item references same pattern |
| S607 patched with shutil.which | VERIFIED | Line 105: shutil.which("glab") resolves path, subprocess remains |

**Summary**: VERIFIED: 4 | REFUTED: 1 | INCONCLUSIVE: 0
**Correction**: Item description says "PyGithub" — actual dependency is python-gitlab and gitpython. PyGithub is a GitHub library, not GitLab.

## RT-ICA

**Decision**: APPROVED
**Goal**: Eliminate glab binary dependency from _resolve_token() by using python-gitlab config/auth mechanisms
**Verified conditions**:
- Target file: .claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py (AVAILABLE)
- Subprocess at lines 105-114 in _resolve_token() (AVAILABLE)
- python-gitlab already imported at lines 24-25 (AVAILABLE)
- Env var fallback at lines 102-103 unchanged (AVAILABLE)
- Single caller: get_gitlab_client() at line 127 (AVAILABLE)
**Assumptions to confirm**: Whether python-gitlab has config-file-reading for token discovery, or env-var-only auth is sufficient (making glab config fallback unnecessary)

## Groomed (2026-03-02)

### Priority

8/10 — Eliminates external binary dependency in widely-used script; fixes architectural gap where subprocess call violates auth separation pattern; reduces deployment friction by removing glab requirement.

### Impact

- Blocks: Contributors working in environments without glab installed; CI/CD pipelines that need MR data fetching
- Bottleneck: fetch_gitlab_mr.py is dependency for create-merge-request-changelog skill, limiting portability

### Benefits

- Removes glab binary dependency entirely; script runs in any environment with python-gitlab
- Eliminates S607 security linting pattern (subprocess with resolved path)
- Centralizes GitLab auth to library-level handling (no subprocess auth bypass)
- Aligns with python-gitlab usage pattern already present in codebase

### Expected Behavior

_resolve_token() returns GitLab API token from:
1. GITLAB_TOKEN environment variable (priority)
2. GITLAB_PRIVATE_TOKEN environment variable (fallback)
3. Returns None if neither exists

Function does not shell out to any external binary; all token resolution is library-internal.

### Acceptance Criteria

1. _resolve_token() contains no subprocess.run() call
2. _resolve_token() contains no shutil.which() call
3. Running ruff check shows no S607 errors in _resolve_token() function
4. fetch_gitlab_mr.py CLI runs successfully when GITLAB_TOKEN env var is set (no glab binary required)
5. Error message when token is missing is updated to reflect env-var-only auth (no longer mentions glab config fallback)

### Resources

| Type | Item |
|------|------|
| Skill | /create-merge-request-changelog |
| Prior work | plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py (similar S607 pattern) |
| Related item | P2 fix pre-existing linting errors in gitlab_context.py |
| Reference | python-gitlab Gitlab class constructor accepting private_token parameter |

### Dependencies

- Depends on: None
- Blocks: None (improvement to existing implementation)

### Effort

Small — Single function change; env var fallback already in place at lines 102-103; no new error cases to handle; existing error handling in get_gitlab_client() sufficient.