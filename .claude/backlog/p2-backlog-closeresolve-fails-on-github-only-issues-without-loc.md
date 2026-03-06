---
name: backlog close/resolve fails on GitHub-only issues without local cache file
description: "Bug: `backlog_close` and `backlog_resolve` (MCP tools) route through `operations.close_item()` and `operations.resolve_item()`, which call `parse_backlog()` → `find_item()`. These only search local `.claude/backlog/` files. If an issue exists on GitHub but has no local cache file (never synced, deleted, or not yet pulled), the operation fails with `ItemNotFoundError`.\n\nMeanwhile, `view_item()` already has a GitHub API fallback path — close/resolve should have the same.\n\n**Root cause**: `close_item()` and `resolve_item()` in `backlog_core/operations.py` only search the local cache via `find_item()`. No fallback to GitHub API when selector is `#N` or a URL.\n\n**Affected layers**:\n- `backlog_core/operations.py` — `close_item()` and `resolve_item()` (fix goes here)\n- `backlog_core/server.py` — `backlog_close()` and `backlog_resolve()` (no changes needed, pass-through)\n- `scripts/backlog.py` — `close()` and `resolve()` CLI commands (inherits fix from operations layer)"
metadata:
  topic: backlog-closeresolve-fails-on-github-only-issues-without-loc
  source: 'GitHub Issue #323'
  added: '2026-03-03'
  priority: P2
  type: Bug
  status: needs-grooming
  issue: '#323'
  last_synced: '2026-03-06T05:50:59Z'
---

## Story

As a **developer using the backlog MCP server**, I want **close and resolve to fall back to GitHub API lookup when no local cache file exists** so that **I can close/resolve any issue regardless of local sync state**.

## Description

Bug: `backlog_close` and `backlog_resolve` (MCP tools) route through `operations.close_item()` and `operations.resolve_item()`, which call `parse_backlog()` → `find_item()`. These only search local `.claude/backlog/` files. If an issue exists on GitHub but has no local cache file (never synced, deleted, or not yet pulled), the operation fails with `ItemNotFoundError`.

Meanwhile, `view_item()` already has a GitHub API fallback path — close/resolve should have the same.

**Root cause**: `close_item()` and `resolve_item()` in `backlog_core/operations.py` only search the local cache via `find_item()`. No fallback to GitHub API when selector is `#N` or a URL.

**Affected layers**:
- `backlog_core/operations.py` — `close_item()` and `resolve_item()` (fix goes here)
- `backlog_core/server.py` — `backlog_close()` and `backlog_resolve()` (no changes needed, pass-through)
- `scripts/backlog.py` — `close()` and `resolve()` CLI commands (inherits fix from operations layer)

## Suggested Fix

In `operations.close_item()` and `operations.resolve_item()`:
1. When `find_item()` returns None and selector looks like `#N`, bare number, or GitHub URL:
   - Call `pull_single_issue()` to fetch and create the local cache file
   - Re-parse and retry `find_item()`
2. If still not found after pull, raise `ItemNotFoundError`

This matches the pattern already used by `view_item()`.

## Acceptance Criteria

- [ ] `backlog_close(selector="#999")` works when issue #999 exists on GitHub but has no local file
- [ ] `backlog_resolve(selector="#999", reason="...")` works same
- [ ] Local cache file is created as side effect of the fallback
- [ ] Still raises `ItemNotFoundError` when issue doesn't exist on GitHub either
- [ ] `backlog.py close #999` inherits the fix (same operations layer)
- [ ] Tests cover the GitHub API fallback path for both close and resolve

## Context

- **Source**: Session observation 2026-03-01
- **Priority**: P2
- **Added**: 2026-03-01
- **Updated**: 2026-03-02 — reframed for MCP server migration; fix targets operations layer
