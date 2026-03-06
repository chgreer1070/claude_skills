# Architecture: Convert backlog_core Tools to async def

**Generated:** 2026-03-06
**Source issues:** #472 (this task), unblocks #465, #469, #470, #473
**Target file:** `.claude/skills/backlog/backlog_core/server.py`

---

## Executive Summary

Convert all 10 `@mcp.tool()` functions in `server.py` from `def` to `async def`. Each tool's
single call into `operations.*` is wrapped with `asyncio.to_thread()` so PyGithub's blocking
HTTP calls do not hold the event loop. No other files change. No tool signatures change.
No test infrastructure changes are needed — FastMCP dispatches async tools natively.

---

## Scope Boundary

**In scope — `server.py` only:**

- Add `import asyncio` at the top of `server.py` (after existing imports)
- Change `def` to `async def` on all 10 `@mcp.tool()` functions
- Wrap each `operations.*` call with `asyncio.to_thread()`

**Out of scope — do not touch:**

- `operations.py` — remains synchronous `def` throughout
- `github.py` — remains synchronous `def` throughout
- `models.py` — data classes, no async needed
- Any test files — existing tests pass without modification
- Tool signatures — zero changes to parameter names, types, defaults, or return shapes
- `ctx: Context` parameter — not added in this task; deferred to #465 and #473

---

## Architectural Decisions

### Decision 1: asyncio.to_thread() at the server.py boundary

`operations.py` calls `github.py` functions which use PyGithub — a blocking sync HTTP library
with no async variant. Wrapping at the `server.py` → `operations.py` call boundary (not inside
`operations.py`) satisfies the conversion goal without touching any downstream file.

`asyncio.to_thread(fn, *args, **kwargs)` runs `fn` in the default thread pool executor and
returns a coroutine that resolves to `fn`'s return value. The tool body `await`s that coroutine.

### Decision 2: Wrap inside the existing try/except

The try/except block in every tool catches `BacklogError`. The `operations.*` call sits inside
that try block. The wrapped call replaces the bare call in the same position — inside try — so
`BacklogError` exceptions raised inside `operations.*` propagate through `asyncio.to_thread()`
and are caught by the existing `except BacklogError` clause unchanged.

Rationale: `asyncio.to_thread()` does not suppress exceptions. Any exception raised in the
thread propagates into the awaiting coroutine, where the existing `except` clause catches it.

### Decision 3: No keyword arguments to asyncio.to_thread()

`asyncio.to_thread(func, *args)` — pass positional args only. The existing `operations.*` calls
use keyword arguments; convert them to positional-equivalent form matching the `operations.*`
function signatures, or keep them as `**kwargs` via the `asyncio.to_thread(fn, **kwargs)` form.

The correct call form is:

```python
result = await asyncio.to_thread(operations.some_function, arg1, arg2, kwarg=value)
```

`asyncio.to_thread` accepts `*args` and `**kwargs` and passes them through to `func`.
Keyword arguments from the existing calls can be preserved exactly as written.

### Decision 4: backlog_pull dual-branch handling

`backlog_pull` conditionally calls either `operations.pull_by_selector()` or
`operations.pull_items()` based on whether `selector` is provided. Each branch gets its own
`asyncio.to_thread()` call. The existing if/else structure is preserved; only the calls inside
each branch change.

---

## Import Change

Add one line to the import block at the top of `server.py`:

```python
import asyncio
```

Position: after the existing standard library imports, before the third-party imports.
If no standard library imports are present, place it as the first import.

---

## Conversion Pattern

Every tool follows this transformation. The pattern is identical for all 10 tools.

**Before:**

```python
@mcp.tool()
def backlog_add(
    title: Annotated[str, Field(description="Item title")],
    # ... other params
) -> dict:
    out = Output()
    try:
        result = operations.add_item(title=title, ...)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

**After:**

```python
@mcp.tool()
async def backlog_add(
    title: Annotated[str, Field(description="Item title")],
    # ... other params
) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(operations.add_item, title=title, ...)
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

Two changes per tool:
1. `def` → `async def` on the function definition line
2. `operations.X(...)` → `await asyncio.to_thread(operations.X, ...)` inside the try block

The `out = Output()` line, the return statements, and the except clause are untouched.

---

## Per-Tool Conversion Specifications

### Tool 1: backlog_add (`server.py:16-51`)

```python
async def backlog_add(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.add_item,
            title=title,
            priority=priority,
            description=description,
            source=source,
            type_=type_,
            create_issue=create_issue,
            force=force,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 2: backlog_list (`server.py:54-94`)

```python
async def backlog_list(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.list_items,
            with_status=with_status,
            from_github=from_github,
            label=label,
            section=section,
            status=status,
            title=title,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 3: backlog_view (`server.py:97-118`)

```python
async def backlog_view(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.view_item,
            selector=selector,
            offset=offset,
            limit=limit,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 4: backlog_sync (`server.py:121-138`)

```python
async def backlog_sync(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.sync_items,
            dry_run=dry_run,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 5: backlog_close (`server.py:141-181`)

```python
async def backlog_close(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.close_item,
            selector=selector,
            reason=reason,
            reference=reference,
            comment=comment,
            cleanup=cleanup,
            force=force,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 6: backlog_resolve (`server.py:184-224`)

```python
async def backlog_resolve(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.resolve_item,
            selector=selector,
            summary=summary,
            plan=plan,
            method=method,
            notes=notes,
            follow_ups=follow_ups,
            findings=findings,
            cleanup=cleanup,
            force=force,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 7: backlog_update (`server.py:227-289`)

```python
async def backlog_update(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.update_item,
            selector=selector,
            plan=plan,
            status=status,
            create_issue=create_issue,
            groomed_content=groomed_content,
            section=section,
            content=content,
            title=title,
            description=description,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 8: backlog_groom (`server.py:292-323`)

```python
async def backlog_groom(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.groom_item,
            selector=selector,
            groomed_content=groomed_content,
            section=section,
            content=content,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 9: backlog_normalize (`server.py:326-344`)

```python
async def backlog_normalize(...) -> dict:
    out = Output()
    try:
        result = await asyncio.to_thread(
            operations.normalize_items,
            dry_run=dry_run,
            output=out,
        )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

### Tool 10: backlog_pull (`server.py:347-381`)

`backlog_pull` is the only tool with a conditional branch selecting between two `operations.*`
functions. Each branch gets its own `asyncio.to_thread()` call.

```python
async def backlog_pull(...) -> dict:
    out = Output()
    try:
        if selector is not None:
            result = await asyncio.to_thread(
                operations.pull_by_selector,
                selector=selector,
                dry_run=dry_run,
                force=force,
                output=out,
            )
        else:
            result = await asyncio.to_thread(
                operations.pull_items,
                dry_run=dry_run,
                force=force,
                output=out,
            )
        return {**result, **out.to_dict()}
    except BacklogError as e:
        return {"error": str(e), **out.to_dict()}
```

---

## Argument Verification Requirement

Before writing the converted tool, the implementing agent MUST read the actual `server.py`
function body at the specified line range to extract the exact keyword arguments passed to each
`operations.*` call. The per-tool argument lists in this spec are derived from the codebase
analysis and should be treated as authoritative, but the agent must verify against the live file
in case the file has changed since analysis was performed.

Verification procedure:

1. Read `server.py` lines 16-381
2. For each tool, identify the exact `operations.*` call arguments
3. Reproduce those arguments verbatim inside `asyncio.to_thread(operations.fn, ...)`
4. Do not add, remove, or rename any argument

---

## FastMCP Dispatch Behaviour

FastMCP 3.x (>=3.0.2) handles async tools natively:

- `async def` tools: FastMCP `await`s the coroutine directly in the event loop
- `def` tools: FastMCP runs the function in a thread pool via `asyncio.to_thread()` internally

After this conversion, FastMCP will `await` each tool coroutine. The `asyncio.to_thread()` call
inside each tool offloads the blocking `operations.*` call to the thread pool. This maintains
the same threading behaviour as before while allowing `await` inside the tool body.

No changes to FastMCP server setup (`mcp = FastMCP("backlog")` at `server.py:13`) are needed.

---

## Testing

No test infrastructure changes are needed.

FastMCP's test client handles async tools the same way it handles sync tools. Existing tests
that invoke tools via the MCP protocol layer are unaffected because the tool dispatch interface
(name, parameters, return shape) is identical.

If existing tests call tool functions directly as Python callables (bypassing FastMCP), they
would need to be updated to `await` the async function or run it with `asyncio.run()`. Read the
test files to check for direct calls before declaring tests unchanged. If direct calls exist,
wrap them with `asyncio.run(backlog_add(...))` in the test.

---

## Constraints

- Python 3.11+ — `asyncio.to_thread()` is available (added in 3.9)
- No new dependencies — `asyncio` is stdlib
- No refactoring beyond the two mechanical changes per tool (keyword + call site)
- Preserve all existing comments in tool docstrings and inline comments exactly as written
- Do not reorder parameters, rename variables, or reformat unrelated code

---

## Verification Checklist (for implementing agent)

After conversion:

- [ ] `import asyncio` present at top of `server.py`
- [ ] All 10 tool functions are `async def`
- [ ] All 10 tools have `await asyncio.to_thread(operations.X, ...)` replacing bare `operations.X(...)` call
- [ ] `backlog_pull` has two separate `asyncio.to_thread()` calls in its if/else branches
- [ ] No tool parameter names, types, defaults, or return shapes changed
- [ ] `out = Output()` line unchanged in all tools
- [ ] `except BacklogError as e:` clause unchanged in all tools
- [ ] `operations.py`, `github.py`, `models.py` have zero modifications (`git diff` confirms)
- [ ] `uv run python -c "from backlog_core.server import mcp"` succeeds without error

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-06_

### Design Refinements

1. **`pull_by_selector` argument list was wrong in spec**: The Tool 10 specification listed `dry_run=dry_run` and `force=force` as arguments to `operations.pull_by_selector`. The actual `operations.pull_by_selector` function does not accept those parameters — it accepts only `selector` and `output`. The implementing agent read the live files, detected the discrepancy, and applied the correct arguments. The implemented code is `pull_by_selector(selector, output=out)` (positional selector) rather than the spec's `pull_by_selector(selector=selector, dry_run=dry_run, force=force, output=out)`.
   - Original: "`selector=selector, dry_run=dry_run, force=force, output=out`" (Tool 10 spec, lines 334-338)
   - Actual: `pull_by_selector(selector, output=out)` — `dry_run` and `force` omitted; `selector` passed positionally
   - Recorded in: `plan/tasks-1-convert-backlog-core-async.md`, Context Manifest, Discovered During Implementation

2. **`import asyncio` placed at line 5 (alphabetically)**: Spec said "after existing stdlib imports, before third-party imports." The file had `from __future__ import annotations` (line 1) and `from typing import Annotated` (line 3). The `import asyncio` was correctly inserted at line 5 between them, which is alphabetically correct order (`asyncio` before `typing`).
   - Original: "after existing stdlib imports" (ambiguous position relative to `typing`)
   - Actual: line 5, between `from __future__ import annotations` and `from typing import Annotated`
   - Recorded in: `plan/tasks-1-convert-backlog-core-async.md`, Context Manifest, Discovered During Implementation
