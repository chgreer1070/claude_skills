---
name: Add Context logging and progress reporting to backlog_core long-running tools
description: "No tool in backlog_core/server.py uses `ctx: Context`. Operations like `backlog_sync`, `backlog_pull`, and `backlog_groom` make multiple sequential GitHub API calls but emit zero progress feedback to the client. The client sees nothing until the operation completes or errors.\n\nFastMCP v3 provides `ctx.info()`, `ctx.warning()`, `ctx.report_progress(progress, total)` for real-time feedback during tool execution. These map directly to MCP protocol log messages and progress notifications.\n\nFiles affected: `.claude/skills/backlog/backlog_core/server.py`\n\nWork required:\n- Add `ctx: Context` parameter to backlog_sync, backlog_pull, backlog_groom, backlog_normalize\n- Emit `ctx.info()` at key milestones (e.g., 'Fetching open issues…', 'Syncing item: {title}')\n- Use `ctx.report_progress(i, total)` for batch operations where total is known\n- Use `ctx.warning()` to surface warnings currently buried in `out.warnings`\n\nSource: FastMCP v3 docs `servers/context.mdx` — `ctx.info()`, `ctx.warning()`, `ctx.report_progress()` send real-time messages to the MCP client."
metadata:
  topic: add-context-logging-and-progress-reporting-to-backlogcore-lo
  source: 'GitHub Issue #465'
  added: '2026-03-06'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#465'
  last_synced: '2026-03-06T18:05:49Z'
  groomed: '2026-03-06'
  plan: plan/tasks-1-context-logging-progress.md
---

## Story

As a **developer using Claude Code skills**, I want to **add context logging and progress reporting to backlog_core long-running tools** so that **the tooling becomes more capable and complete**.

## Description

No tool in backlog_core/server.py uses `ctx: Context`. Operations like `backlog_sync`, `backlog_pull`, and `backlog_groom` make multiple sequential GitHub API calls but emit zero progress feedback to the client. The client sees nothing until the operation completes or errors.

FastMCP v3 provides `ctx.info()`, `ctx.warning()`, `ctx.report_progress(progress, total)` for real-time feedback during tool execution. These map directly to MCP protocol log messages and progress notifications.

Files affected: `.claude/skills/backlog/backlog_core/server.py`

Work required:
- Add `ctx: Context` parameter to backlog_sync, backlog_pull, backlog_groom, backlog_normalize
- Emit `ctx.info()` at key milestones (e.g., "Fetching open issues…", "Syncing item: {title}")
- Use `ctx.report_progress(i, total)` for batch operations where total is known
- Use `ctx.warning()` to surface warnings currently buried in `out.warnings`

Source: FastMCP v3 docs `servers/context.mdx` — `ctx.info()`, `ctx.warning()`, `ctx.report_progress()` send real-time messages to the MCP client.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: fastmcp-creator skill review of backlog_core/server.py
- **Priority**: P1
- **Added**: 2026-03-06
- **Research questions**: None

## Groomed (2026-03-06)

### Issue Classification

Type: unbounded-design — no defect, no recurrence. New capability addition that gives MCP clients real-time visibility into long-running operations that currently emit zero feedback.

Analysis method: design-framing. All API facts verified against primary sources before grooming.

### Priority

7/10 — P1 feature with direct user-visible impact. Operations like `backlog_sync` and `backlog_pull` make multiple sequential GitHub API calls; the client sees nothing until the operation completes or errors out. Progress feedback is table-stakes UX for long-running MCP tools. Held from P0 only because tools remain functional (not broken) without it.

### Impact

- Blocks: #473 (MCP prompts and guided elicitation) — both items touch `server.py`; sequencing #465 first avoids merge conflicts
- Bottleneck: Users of `backlog_sync`, `backlog_pull`, `backlog_groom`, `backlog_normalize` receive no feedback during execution, making the client appear frozen for multi-issue operations

### Benefits

- MCP clients (Claude Code, Claude Desktop, Cursor, Zed) display real-time log messages and progress indicators during long-running operations
- Warnings currently buried inside `out.warnings` (returned only at completion) surface immediately via `ctx.warning()`
- Establishes `ctx: Context` parameter pattern in `server.py` for all subsequent tools requiring feedback

### Expected Behavior

When a client calls `backlog_sync`, it receives MCP log messages at each sync milestone (e.g., "Fetching open issues…", "Syncing: #42 Fix the widget") and progress notifications that drive a progress indicator. The client does not wait in silence until the call completes. Warnings (e.g., "Skipping item with no GitHub issue") appear as they occur, not as a batch at the end.

### Desired Structure

After this item ships, the following is observable:

- `backlog_sync`, `backlog_pull`, `backlog_groom`, `backlog_normalize` each accept a `ctx: Context` parameter
- Each tool emits at least one `ctx.info()` call at start and one at completion
- Batch operations (`backlog_sync`, `backlog_pull`, `backlog_normalize`) emit `ctx.report_progress(i, total)` per item processed
- Warnings from `out.warnings` are mirrored via `ctx.warning()` as they are added, not only at return
- `ctx.info()`, `ctx.warning()`, `ctx.report_progress()` are the only `ctx` methods used — no elicitation, no sampling
- No changes to the 6 non-target tools (`backlog_add`, `backlog_list`, `backlog_view`, `backlog_update`, `backlog_close`, `backlog_resolve`)

### Acceptance Criteria

1. `grep -c "ctx: Context" .claude/skills/backlog/backlog_core/server.py` returns at least `4` (one per target tool)
2. Each of `backlog_sync`, `backlog_pull`, `backlog_groom`, `backlog_normalize` contains at least one `await ctx.info(...)` call visible in the source
3. Each batch tool contains at least one `await ctx.report_progress(...)` call
4. MCP client (Claude Code) displays streaming log messages during `backlog_sync` with 3+ GitHub issues to sync — no silent wait
5. `uv run python -c "from backlog_core.server import mcp"` exits 0 — import succeeds, no runtime errors
6. `uv run ruff check .claude/skills/backlog/backlog_core/server.py` exits 0
7. The 6 non-target tools have no new `ctx` parameter — their signatures are unchanged

### Resources

| Type | Item |
|------|------|
| Reference | `.claude/worktrees/fastmcp/docs/servers/context.mdx` — FastMCP Context API (VERIFIED 2026-03-06) |
| Prior work | `.claude/skills/backlog/backlog_core/server.py` — 4 target tools: `backlog_sync` (line 122), `backlog_pull` (line 348), `backlog_groom` (line 293), `backlog_normalize` (line 327) |
| Agent | `@python3-development:python-cli-architect` — for implementation |

**FastMCP Context API — VERIFIED from `.claude/worktrees/fastmcp/docs/servers/context.mdx` (accessed 2026-03-06)**

Import (legacy type-hint injection — works in FastMCP v3, no `CurrentContext` needed):

```python
from fastmcp import FastMCP, Context
```

Parameter pattern on an async tool:

```python
@mcp.tool()
async def backlog_sync(dry_run: bool = False, ctx: Context = None) -> dict:
    await ctx.info("Fetching open issues from GitHub...")
    await ctx.report_progress(progress=0, total=total_items)
    # ... per item ...
    await ctx.info(f"Syncing: {title}")
    await ctx.report_progress(progress=i, total=total_items)
    await ctx.warning("Skipping item with no GitHub issue")
```

`ctx` methods are all coroutines — `await` is required on every call. SOURCE: context.mdx line 47 (`await ctx.info(...)`), line 173 (`await ctx.report_progress(progress=50, total=100)`).

Context injection: FastMCP automatically excludes `ctx: Context` from the MCP schema — the client never sees it as a parameter. SOURCE: context.mdx — "Dependency parameters are automatically excluded from the MCP schema—clients never see them."

### Dependencies

- Depends on: **#472** (P2, open, in-progress) — "Convert backlog_core tools to async def" — `ctx` methods are coroutines; the 4 target tools are currently `def` (verified by grep). They must be `async def` before `ctx` can be used. **#472 must merge before #465 can be implemented.**
- Blocks: #473 (P1, open) — "Add MCP prompts and guided elicitation" — both items modify `server.py`. Completing #465 first reduces merge conflict risk when #473 adds new functions.

### Blockers

- **#472 not yet merged** — the 4 target tools (`backlog_sync`, `backlog_pull`, `backlog_groom`, `backlog_normalize`) are synchronous `def` as of 2026-03-06. FastMCP runs sync tools in a thread pool, which prevents `await` inside the tool body. `ctx.info()`, `ctx.warning()`, and `ctx.report_progress()` are all coroutines — calling them without `await` in a sync function raises `RuntimeError`. Implementation of #465 cannot begin until #472 lands.

### Effort

Small — additive only. Four tools receive `ctx: Context` parameter additions and `await ctx.*` call sites. No changes to `operations.py`, `github.py`, `models.py`, or the 6 non-target tools. Scope is bounded to `server.py` and limited to inserting `ctx` calls at existing operation boundaries.

## Fact-Check

Claims checked: 4 | VERIFIED: 4 | REFUTED: 0 | INCONCLUSIVE: 0

**VERIFIED** — FastMCP v3 provides `ctx.info()`, `ctx.warning()`, `ctx.report_progress(progress, total)` as async coroutines on the `Context` object.
SOURCE: `.claude/worktrees/fastmcp/docs/servers/context.mdx` lines 134-136, 173 (accessed 2026-03-06)

**VERIFIED** — Import path: `from fastmcp import FastMCP, Context`; `ctx: Context` parameter is auto-excluded from MCP tool schema.
SOURCE: `.claude/worktrees/fastmcp/docs/servers/context.mdx` lines 72, 82-84 (accessed 2026-03-06)

**VERIFIED** — 4 target tools (`backlog_sync`, `backlog_pull`, `backlog_groom`, `backlog_normalize`) are currently synchronous `def` in server.py.
SOURCE: Direct grep of `.claude/skills/backlog/backlog_core/server.py` (accessed 2026-03-06)

**VERIFIED** — `ctx` methods are coroutines requiring `await`; tools must be `async def` to use them. #472 (async conversion) must land first.
SOURCE: `.claude/worktrees/fastmcp/docs/servers/context.mdx`; confirmed by #472 description (accessed 2026-03-06)

## RT-ICA

Goal: Add `ctx: Context` parameter and real-time feedback (`ctx.info()`, `ctx.report_progress()`, `ctx.warning()`) to the 4 long-running tools in server.py so MCP clients receive progress notifications during GitHub API operations.

| # | Condition | Status | Info Needed |
|---|-----------|--------|-------------|
| 1 | Target tools identified | AVAILABLE | backlog_sync, backlog_pull, backlog_groom, backlog_normalize |
| 2 | FastMCP Context API understood | AVAILABLE | ctx.info(), ctx.warning(), ctx.report_progress(i, total) — all coroutines |
| 3 | Import path known | AVAILABLE | from fastmcp import FastMCP, Context |
| 4 | Key milestones per tool identified | AVAILABLE | groomable from operations.py call sites |
| 5 | #472 (async def) merged | MISSING | Tools must be async def before ctx methods can be awaited |

Decision: APPROVED for planning (prerequisite is plannable — #472 now has a task plan). Execution is blocked on #472 merge.
Missing inputs: #472 merged (in planning as of 2026-03-06).