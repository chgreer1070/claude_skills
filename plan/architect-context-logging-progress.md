# Architecture: Context Logging and Progress Reporting for backlog_core MCP Tools

## Executive Summary

Four MCP tools in `server.py` — `backlog_sync`, `backlog_pull`, `backlog_groom`, and
`backlog_normalize` — receive a `ctx: Context` parameter and emit structured log messages and
progress events back to the MCP client. The other six tools (`backlog_add`, `backlog_list`,
`backlog_view`, `backlog_close`, `backlog_resolve`, `backlog_update`) are unchanged.

This spec assumes the async conversion (issue #472) is complete. All four target tools are
already `async def` before any work described here begins.

---

## Prerequisite: Async Conversion

**This spec does not specify the async conversion.** Every `ctx` method is a coroutine —
`await ctx.info(...)`, `await ctx.report_progress(...)`, `await ctx.warning(...)`. The four
target tool functions must be `async def` and their call sites must `await` every `ctx` call.
Confirm #472 is merged before implementing.

---

## Import Change

**File**: `.claude/skills/backlog/backlog_core/server.py`

**Current** (line 7):

```python
from fastmcp import FastMCP
```

**Required addition** — add `Context` to the existing fastmcp import:

```python
from fastmcp import Context, FastMCP
```

No other import changes. `Context` injected by type hint — FastMCP detects it automatically
(legacy type-hint injection, documented in FastMCP context.mdx). No `CurrentContext()` import
needed; the simpler `ctx: Context` parameter pattern is sufficient and already works.

---

## Scope: Which Tools Change

| Tool | Gets `ctx: Context` | Progress | Logging | Warnings |
|------|---------------------|----------|---------|----------|
| `backlog_sync` | YES | YES (two passes) | YES | YES |
| `backlog_pull` | YES | YES (bulk path only) | YES | YES |
| `backlog_groom` | YES | no (single item) | YES | YES |
| `backlog_normalize` | YES | YES (per file) | YES | YES |
| `backlog_add` | NO | — | — | — |
| `backlog_list` | NO | — | — | — |
| `backlog_view` | NO | — | — | — |
| `backlog_close` | NO | — | — | — |
| `backlog_resolve` | NO | — | — | — |
| `backlog_update` | NO | — | — | — |

---

## Signature Changes

Only the parameter list of the four tool functions changes. All existing parameters are
unchanged. `ctx` is appended after the existing parameters in each function.

### `backlog_sync`

```python
async def backlog_sync(
    dry_run: Annotated[bool, Field(description="Preview what would be synced without making changes")] = False,
    ctx: Context,
) -> dict:
```

### `backlog_pull`

```python
async def backlog_pull(
    selector: Annotated[
        str | None,
        Field(
            description="Optional selector to pull a single issue: #N, bare number, GitHub URL, or title substring. When omitted, pulls all issues."
        ),
    ] = None,
    dry_run: Annotated[bool, Field(description="Preview what would be pulled without modifying local files")] = False,
    force: Annotated[
        bool, Field(description="Overwrite local content even if local version is newer or longer")
    ] = False,
    ctx: Context,
) -> dict:
```

### `backlog_groom`

```python
async def backlog_groom(
    selector: Annotated[str, Field(description="Item selector: title substring, #N, bare number, or GitHub issue URL")],
    groomed_content: Annotated[
        str | None,
        Field(description="Full groomed content to write into the per-item file. Replaces the entire groomed section."),
    ] = None,
    section: Annotated[
        str | None, Field(description="Section name for incremental update (use with content parameter)")
    ] = None,
    content: Annotated[
        str | None, Field(description="Content for the named section (use with section parameter)")
    ] = None,
    ctx: Context,
) -> dict:
```

### `backlog_normalize`

```python
async def backlog_normalize(
    dry_run: Annotated[bool, Field(description="Preview normalization changes without modifying files")] = False,
    ctx: Context,
) -> dict:
```

---

## Per-Tool ctx Call Specifications

### `backlog_sync` (server.py lines 122–138)

`backlog_sync` delegates to two operations helpers: `sync_create_missing_issues` (pass 1) and
`sync_push_groomed_content` (pass 2). Both helpers already count items internally and emit
messages through `out`. Progress is reported across the combined item count from both passes.

The total item count is not known until after `parse_backlog()` runs inside the helpers. Use
a two-pass progress scheme: pass 1 reports progress 0..created_count, pass 2 continues from
there. Because the helpers are synchronous (until #472 converts them), `ctx` calls are placed
in the `backlog_sync` body before and after each helper call.

**Insertion points in `backlog_sync` body** (server.py):

```python
async def backlog_sync(
    dry_run: ...,
    ctx: Context,
) -> dict:
    """..."""
    out = Output()
    try:
        # INSERT: start log
        await ctx.info("Starting backlog sync" + (" (dry-run)" if dry_run else ""))

        # EXISTING call — unchanged
        create_result = operations.sync_items(dry_run=dry_run, output=out)

        # INSERT: surface any warnings collected during sync
        for w in out.warnings:
            await ctx.warning(w)

        # INSERT: completion log
        created = create_result.get("created", 0)
        pushed = create_result.get("pushed", 0)
        await ctx.info(f"Sync complete: {created} issue(s) created, {pushed} item(s) pushed")

        return {**create_result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

**Note**: `operations.sync_items` returns a merged dict already (see operations.py line
1087–1092). The server.py current code calls `operations.sync_items` (a single function that
wraps both passes). Progress within the helper loops is not accessible from `server.py` without
refactoring operations. The spec does NOT require per-item progress for `backlog_sync` —
only a start log and completion summary. If per-item progress is desired in a future ticket,
the helpers must accept a progress callback.

### `backlog_pull` (server.py lines 348–381)

`backlog_pull` has two paths: single-item (`pull_by_selector`) and bulk (`pull_items`).
Progress reporting applies to the bulk path only. Single-item path gets start + completion logs.

**Insertion points**:

```python
async def backlog_pull(
    selector: ...,
    dry_run: ...,
    force: ...,
    ctx: Context,
) -> dict:
    """..."""
    out = Output()
    try:
        if selector is not None:
            # Single-item path: log start, delegate, log result
            await ctx.info(f"Pulling issue: {selector}")
            result = operations.pull_by_selector(selector, output=out)
            for w in out.warnings:
                await ctx.warning(w)
            file_path = result.get("file_path")
            await ctx.info(f"Pulled: {file_path}" if file_path else "Nothing pulled")
            return {**result, **out.to_dict()}

        # Bulk path
        await ctx.info("Starting bulk pull from GitHub" + (" (dry-run)" if dry_run else ""))
        result = operations.pull_items(dry_run=dry_run, force=force, output=out)
        for w in out.warnings:
            await ctx.warning(w)
        pulled = result.get("pulled", 0)
        await ctx.info(f"Pull complete: {pulled} item(s) pulled")
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

**Note**: `pull_items` iterates `candidates` internally (operations.py line 1532). Per-item
progress from the bulk loop is not accessible from `server.py` without refactoring. The spec
does NOT require per-item `report_progress` for `backlog_pull`. If that is needed, it is a
separate ticket targeting `operations.pull_items`.

### `backlog_groom` (server.py lines 293–323)

`backlog_groom` is a single-item operation. No progress reporting. Log start (with selector),
surface warnings, log completion result.

**Insertion points**:

```python
async def backlog_groom(
    selector: ...,
    groomed_content: ...,
    section: ...,
    content: ...,
    ctx: Context,
) -> dict:
    """..."""
    out = Output()
    try:
        # INSERT: start log
        await ctx.info(f"Grooming item: {selector}")

        result = operations.groom_item(
            selector=selector, groomed_content=groomed_content, section=section, content=content, output=out
        )

        # INSERT: surface warnings
        for w in out.warnings:
            await ctx.warning(w)

        # INSERT: completion log
        title = result.get("title", selector)
        await ctx.info(f"Groomed: {title}")

        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### `backlog_normalize` (server.py lines 327–344)

`backlog_normalize` processes all matching `.md` files via a generator expression (operations.py
line 1382: `sum(1 for f in files if _normalize_item_file(f, dry_run, output=out))`). The total
is known after globbing (`files` list at line 1378). Per-file progress is not accessible from
`server.py` without refactoring.

The spec does NOT require per-file `report_progress` for `backlog_normalize`. Log the count
before and after.

**Insertion points**:

```python
async def backlog_normalize(
    dry_run: ...,
    ctx: Context,
) -> dict:
    """..."""
    out = Output()
    try:
        # INSERT: start log
        await ctx.info("Starting normalize" + (" (dry-run)" if dry_run else ""))

        result = operations.normalize_items(dry_run=dry_run, output=out)

        # INSERT: surface warnings
        for w in out.warnings:
            await ctx.warning(w)

        # INSERT: completion log
        updated = result.get("updated", 0)
        suffix = " (dry-run)" if dry_run else ""
        await ctx.info(f"Normalized {updated} file(s){suffix}")

        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

---

## Warning Surfacing Contract

Every warning accumulated in `out.warnings` must be surfaced via `await ctx.warning(w)` before
the function returns. The pattern is identical across all four tools:

```python
for w in out.warnings:
    await ctx.warning(w)
```

This loop is placed after the operation call returns and before the `return` statement.

`out.warnings` is populated by `out.warn(...)` calls inside the operations layer. The warnings
list is already included in the returned dict via `out.to_dict()` — the `ctx.warning` calls
duplicate this to the MCP client's log stream, not to the return value.

---

## `report_progress` Decision

The FastMCP `ctx.report_progress(progress, total)` API requires both a current value and a
total to be meaningful. For all four target tools, the item total is computed inside the
operations layer after the tool body has already called into it. Surfacing per-item progress
requires either:

1. Refactoring operations helpers to accept a progress callback, or
2. Moving the item iteration loop into `server.py`

Neither is in scope for this ticket. The spec prescribes `ctx.info` start/completion logs
instead, which provide the most meaningful client-visible feedback without requiring structural
changes to `operations.py`.

If per-item `report_progress` is required in a future ticket, the target functions are:

- `sync_create_missing_issues` — loop at operations.py line 1014, total = `len(needed)`
- `sync_push_groomed_content` — loop at operations.py line 1055, total = `len(groomed_items)`
- `pull_items` — loop at operations.py line 1532, total = `len(candidates)`
- `normalize_items` — generator at operations.py line 1382, total = `len(files)`

Those four loops are the insertion targets when per-item progress is added.

---

## What Does Not Change

- `operations.py` — no changes in this ticket
- `models.py` — no changes
- `parsing.py` — no changes
- `github.py` — no changes
- Tool docstrings — no changes
- Return value shape — no changes; all four tools return the same dict structure as before
- The six excluded tools — no changes

---

## Implementation Checklist

- [ ] Confirm #472 (async conversion) is merged and all four target tools are `async def`
- [ ] Add `Context` to the `from fastmcp import` line in `server.py`
- [ ] Add `ctx: Context` as final parameter to `backlog_sync`
- [ ] Add `ctx: Context` as final parameter to `backlog_pull`
- [ ] Add `ctx: Context` as final parameter to `backlog_groom`
- [ ] Add `ctx: Context` as final parameter to `backlog_normalize`
- [ ] Insert `await ctx.info(...)` start log in each of the four tool bodies
- [ ] Insert `for w in out.warnings: await ctx.warning(w)` in each of the four tool bodies
- [ ] Insert `await ctx.info(...)` completion log in each of the four tool bodies
- [ ] Verify the six excluded tools are untouched
- [ ] Run `uv run prek run --files .claude/skills/backlog/backlog_core/server.py`
- [ ] Run existing test suite against the modified server

---

## Source References

- `server.py`: `.claude/skills/backlog/backlog_core/server.py`
- `operations.py`: `.claude/skills/backlog/backlog_core/operations.py`
- FastMCP Context API: `.claude/worktrees/fastmcp/docs/servers/context.mdx`
- Legacy type-hint injection: context.mdx lines 79-93 — `ctx: Context` parameter, FastMCP
  injects automatically, parameter excluded from MCP schema
- `ctx.info` / `ctx.warning`: context.mdx lines 133-138
- `ctx.report_progress`: context.mdx lines 172-176 — `await ctx.report_progress(progress=N, total=M)`
