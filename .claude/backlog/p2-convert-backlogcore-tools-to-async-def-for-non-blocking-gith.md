---
name: Convert backlog_core tools to async def for non-blocking GitHub API calls
description: "All 10 tools in backlog_core/server.py are synchronous `def` functions. FastMCP runs sync tools in a thread pool automatically, but this prevents any tool from using `await` — meaning GitHub API calls, file I/O, and `ctx` methods all block.\n\nConverting tools to `async def` unblocks:\n1. `ctx.info()`, `ctx.report_progress()`, `ctx.elicit()` — these are all coroutines and require async context\n2. Future async GitHub client (e.g., `httpx` + `PyGithub` async variant) for true non-blocking I/O\n3. Background tasks via `task=True` — which requires async functions\n4. Parallel GitHub API calls via `asyncio.gather()` in batch operations\n\nFiles affected: `.claude/skills/backlog/backlog_core/server.py`, `.claude/skills/backlog/backlog_core/operations.py`, `.claude/skills/backlog/backlog_core/github.py`\n\nNote: This is a prerequisite for the background tasks item (#469) and a dependency for Context logging (#465). The PyGithub library is synchronous; async calls to it must use `asyncio.to_thread()` in the interim until an async client is adopted.\n\nSource: FastMCP v3 docs `servers/tools.mdx` — FastMCP supports both `def` and `async def`; sync tools run in threadpool; async preferred for I/O-bound operations."
metadata:
  topic: convert-backlogcore-tools-to-async-def-for-non-blocking-gith
  source: 'GitHub Issue #472'
  added: '2026-03-06'
  priority: P2
  type: Refactor
  status: needs-grooming
  issue: '#472'
  last_synced: '2026-03-06T05:50:38Z'
---

## Story

As a **maintainer of the codebase**, I want to **convert backlog_core tools to async def for non-blocking github api calls** so that **the code is cleaner and more maintainable**.

## Description

All 10 tools in backlog_core/server.py are synchronous `def` functions. FastMCP runs sync tools in a thread pool automatically, but this prevents any tool from using `await` — meaning GitHub API calls, file I/O, and `ctx` methods all block.

Converting tools to `async def` unblocks:
1. `ctx.info()`, `ctx.report_progress()`, `ctx.elicit()` — these are all coroutines and require async context
2. Future async GitHub client (e.g., `httpx` + `PyGithub` async variant) for true non-blocking I/O
3. Background tasks via `task=True` — which requires async functions
4. Parallel GitHub API calls via `asyncio.gather()` in batch operations

Files affected: `.claude/skills/backlog/backlog_core/server.py`, `.claude/skills/backlog/backlog_core/operations.py`, `.claude/skills/backlog/backlog_core/github.py`

Note: This is a prerequisite for the background tasks item (#469) and a dependency for Context logging (#465). The PyGithub library is synchronous; async calls to it must use `asyncio.to_thread()` in the interim until an async client is adopted.

Source: FastMCP v3 docs `servers/tools.mdx` — FastMCP supports both `def` and `async def`; sync tools run in threadpool; async preferred for I/O-bound operations.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: fastmcp-creator skill review of backlog_core/server.py
- **Priority**: P2
- **Added**: 2026-03-06
- **Research questions**: None