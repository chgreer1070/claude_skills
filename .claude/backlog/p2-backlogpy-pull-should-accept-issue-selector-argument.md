---
name: backlog pull should accept issue selector argument
description: "Bug: backlog_pull MCP tool and backlog.py pull CLI only support bulk pull. There is no way to pull a single issue by #N, title, or URL. operations.pull_single_issue() already exists but isn't wired to MCP tool or CLI. Fix: add optional selector parameter to backlog_pull() in server.py and pull() in backlog.py."
metadata:
  topic: backlogpy-pull-should-accept-issue-selector-argument
  source: Session observation 2026-03-01
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: open
  issue: '#324'
  last_synced: '2026-03-01T03:10:32Z'
---

## Story

As a **developer using the backlog MCP server**, I want **backlog_pull to accept an optional selector** so that **I can refresh a single issue's local cache without doing a full bulk pull**.

## Description

Bug: The `backlog_pull` MCP tool and `backlog.py pull` CLI command only support bulk pull of all issues. There is no way to pull a single issue by `#N`, title substring, or URL into the local cache.

`backlog_pull(selector="#321")` is not supported — there's no `selector` parameter. Similarly `backlog.py pull #321` fails with `Got unexpected extra argument (#321)`.

The operations layer already has `pull_single_issue()` as a public function — it just isn't wired up to the MCP tool or CLI.

## Suggested Fix

**MCP server** (`backlog_core/server.py` — `backlog_pull()`):
- Add optional `selector: str | None = None` parameter with Field description
- When provided, parse with `_parse_issue_selector()` and route to `operations.pull_single_issue()`
- When None, existing bulk `operations.pull_items()` behavior preserved

**CLI** (`scripts/backlog.py` — `pull()`):
- Add optional `selector: str = typer.Argument(None, ...)` positional argument
- When provided, route to existing `_pull_single_issue()` helper
- When None, existing bulk pull preserved

**Operations layer** (`backlog_core/operations.py`):
- `pull_single_issue()` already exists and handles the single-issue case — no changes needed

## Acceptance Criteria

- [ ] MCP: `backlog_pull(selector="#321")` pulls issue #321 into local cache
- [ ] MCP: `backlog_pull(selector="some title")` pulls matching item by title substring
- [ ] MCP: `backlog_pull(selector="https://github.com/owner/repo/issues/321")` pulls by URL
- [ ] MCP: `backlog_pull()` (no selector) — bulk pull unchanged
- [ ] CLI: `backlog.py pull #321` pulls single issue
- [ ] CLI: `backlog.py pull` (no args) — bulk pull unchanged
- [ ] Selector format matches `view`/`close`/`resolve` (`#N`, bare number, URL, title substring)
- [ ] Error message when selector matches no local item and issue doesn't exist on GitHub
- [ ] Tests cover single-issue pull path for both MCP tool and CLI

## Context

- **Source**: Session observation 2026-03-01
- **Priority**: P2
- **Added**: 2026-03-01
- **Updated**: 2026-03-02 — reframed for MCP server migration; operations layer already ready