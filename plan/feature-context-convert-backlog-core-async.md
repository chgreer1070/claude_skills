# Feature Context: Convert backlog_core Tools to async def

## Document Metadata

- **Generated**: 2026-03-06
- **Input Type**: simple_description
- **Source**: GitHub Issue #472 — Convert backlog_core tools to async def for non-blocking GitHub API calls
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Convert all 10 tools in `.claude/skills/backlog/backlog_core/server.py` from synchronous `def` functions to `async def`. FastMCP runs sync tools in a thread pool automatically, but this prevents any tool from using `await`. As a result, `ctx.info()`, `ctx.report_progress()`, `ctx.warning()`, and `ctx.elicit()` are all unavailable to these tools.

Three P1/P1-adjacent features are blocked:
- #465 — Add Context logging and progress reporting (needs `ctx.info()`, `ctx.report_progress()`)
- #473 — Add MCP prompts and guided elicitation tools (needs `ctx.elicit()`)
- #469 — Background task support (needs `async def`)
- #470 — Parallel GitHub API calls (needs `asyncio.gather()`)

Desired outcome: All 10 tools in server.py are `async def`. Synchronous calls to `operations.py` are wrapped with `asyncio.to_thread()`. No existing tool signatures, parameters, or return values change. All existing tool behaviour is preserved identically.

---

## Core Intent Analysis

### WHO (Target Users)

The development team maintaining the `backlog_core` MCP server. The change is internal infrastructure — no end-user-visible behaviour changes. The immediate consumers of this change are the three blocked feature issues (#465, #473, #469, #470).

### WHAT (Desired Outcome)

All 10 MCP tools in `server.py` become `async def` functions. The tools' external contracts (names, parameter signatures, return shapes) are identical to today. The server continues to handle all existing tool calls correctly.

The 10 tools confirmed in `server.py` (lines 16–381):
- `backlog_add` (line 17)
- `backlog_list` (line 55)
- `backlog_view` (line 98)
- `backlog_sync` (line 122)
- `backlog_close` (line 141)
- `backlog_resolve` (line 184)
- `backlog_update` (line 227)
- `backlog_groom` (line 292)
- `backlog_normalize` (line 326)
- `backlog_pull` (line 347)

### WHEN (Trigger Conditions)

This change is needed now. It is a prerequisite for implementing features #465, #473, #469, and #470. None of those features can be implemented without `async def` tools.

### WHY (Problem Being Solved)

FastMCP documents (`tools.mdx` line 155) that sync tools run in a thread pool. The thread pool execution context prevents any `await` expression inside the tool body. The FastMCP `Context` object's methods — `ctx.info()`, `ctx.report_progress()`, `ctx.warning()`, `ctx.elicit()` — are all coroutines that require `await`. Because the current tools are `def`, they cannot call these methods. Converting to `async def` allows tools to `await` context calls directly, unlocking the four blocked features.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: FastMCP async tool support (documented)

- **Location**: `.claude/worktrees/fastmcp/docs/servers/tools.mdx:155`
- **Relevance**: Confirms FastMCP supports `async def` tools natively. Sync tools run in a thread pool; async tools are awaited directly. Both are valid `@mcp.tool()` targets.
- **Reusable**: The existing `@mcp.tool()` decorator requires no changes when converting from `def` to `async def`.

#### Pattern 2: FastMCP Context usage in async tools (documented)

- **Location**: `.claude/worktrees/fastmcp/docs/servers/tools.mdx:995–1022`
- **Relevance**: Shows `async def process_data(data_uri: str, ctx: Context)` with `await ctx.info(...)`, `await ctx.report_progress(...)`, `await ctx.read_resource(...)`. This is the exact pattern the blocked issues need to adopt after this conversion.
- **Reusable**: The `Context` import and parameter injection pattern is ready to use once tools are `async def`.

#### Pattern 3: Current server.py tool structure

- **Location**: `.claude/skills/backlog/backlog_core/server.py:16–381`
- **Relevance**: All 10 tools follow an identical structure: accept typed parameters, create `Output()`, call a single `operations.*` function, return `{**result, **out.to_dict()}` or `{"error": str(e), **out.to_dict()}` on `BacklogError`. The uniformity means the conversion pattern is the same for all 10.
- **Reusable**: The try/except structure, `Output()` handling, and return shape are unchanged by the conversion.

#### Pattern 4: operations.py — synchronous call layer

- **Location**: `.claude/skills/backlog/backlog_core/operations.py` (65KB file)
- **Relevance**: All operations called from server.py (`operations.add_item`, `operations.list_items`, `operations.view_item`, `operations.sync_items`, `operations.close_item`, `operations.resolve_item`, `operations.update_item`, `operations.groom_item`, `operations.normalize_items`, `operations.pull_items`, `operations.pull_by_selector`) are synchronous `def` functions. They call `github.py` functions which are also synchronous and use PyGithub (a blocking HTTP library).
- **Reusable**: None of these functions change in this task. They are called via `asyncio.to_thread()` from the async tool bodies.

#### Pattern 5: github.py — synchronous PyGithub calls

- **Location**: `.claude/skills/backlog/backlog_core/github.py:38–437`
- **Relevance**: All GitHub API operations use PyGithub (`github.Github`, `repo.get_issue()`, `issue.edit()`, etc.). PyGithub is a synchronous blocking library — it is not async-compatible. This is why `asyncio.to_thread()` (not `await`) is the correct wrapping mechanism for the `operations.*` calls.
- **Reusable**: No changes needed to `github.py` in this task.

### Existing Infrastructure

- `FastMCP` instance `mcp` already created at `server.py:13` — no changes needed to the server setup.
- `@mcp.tool()` decorator at each tool already supports async functions per FastMCP docs.
- `Output` and `BacklogError` models in `models.py` are synchronous data structures — compatible with async tool bodies without modification.

### Code References

- `.claude/skills/backlog/backlog_core/server.py:13` — `mcp = FastMCP("backlog")` — server instance
- `.claude/skills/backlog/backlog_core/server.py:16` — first tool `backlog_add`, `def` (sync)
- `.claude/skills/backlog/backlog_core/server.py:381` — last tool `backlog_pull`
- `.claude/skills/backlog/backlog_core/operations.py:1` — all operations are `def` (sync)
- `.claude/skills/backlog/backlog_core/github.py:38` — `get_github()` — sync PyGithub calls
- `.claude/worktrees/fastmcp/docs/servers/tools.mdx:155` — FastMCP thread pool behaviour for sync tools
- `.claude/worktrees/fastmcp/docs/servers/tools.mdx:995` — FastMCP async tool + Context example

---

## Use Scenarios

### Scenario 1: Developer adds progress reporting to backlog_sync

**Actor**: Engineer implementing GitHub Issue #465
**Trigger**: Assigned to implement context logging and progress reporting in `backlog_sync`
**Goal**: Call `ctx.report_progress()` as each backlog item is synced to GitHub
**Expected Outcome**: After this conversion, the engineer can add `ctx: Context` parameter and `await ctx.report_progress(...)` calls to `backlog_sync` without hitting "can't await in sync function" errors

### Scenario 2: Developer adds guided elicitation to backlog_close

**Actor**: Engineer implementing GitHub Issue #473
**Trigger**: Assigned to implement MCP prompts and guided elicitation in `backlog_close`
**Goal**: Use `ctx.elicit()` to ask the user for a close reason interactively
**Expected Outcome**: After this conversion, `backlog_close` is `async def` and can `await ctx.elicit(...)` calls

### Scenario 3: Background task or parallel API call support

**Actor**: Engineer implementing GitHub Issues #469 or #470
**Trigger**: Needs `asyncio.gather()` to fetch multiple GitHub issues in parallel inside `backlog_list`
**Goal**: Fan out multiple GitHub API calls concurrently within a single tool invocation
**Expected Outcome**: After this conversion, `backlog_list` is `async def` and can use `asyncio.gather()` over `asyncio.to_thread()` wrapped calls

### Scenario 4: Existing tool calls continue working unchanged

**Actor**: Any MCP client currently using the backlog tools
**Trigger**: Routine backlog operation (add, list, view, sync, etc.)
**Goal**: Tool returns the same dict structure as before
**Expected Outcome**: Tool signatures, parameter names, return shapes, and error handling are identical. The async conversion is invisible to callers.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Does this task include adding `ctx: Context` parameter to any tools, or is it strictly the `def` → `async def` conversion only? | Determines whether any tool signatures change in this task |
| 2 | Scope | Does `operations.py` get any changes in this task, or only `server.py`? | Determines file scope for the implementation agent |
| 3 | Behavior | Should `asyncio.to_thread()` wrap the entire `operations.*` call (including the try/except), or just the call inside the existing try/except? | Affects error propagation — `BacklogError` must still be caught |
| 4 | Integration | Are there any existing tests for `server.py` tools that will need to be updated for async? | Determines whether test changes are in or out of scope |
| 5 | Scope | `backlog_pull` calls two different `operations.*` functions depending on `selector`. Does `asyncio.to_thread()` wrap each call individually, or the whole body? | Minor but must be consistent |

---

## Questions Requiring Resolution

### Q1: Strict conversion only, or include Context parameter addition?

- **Category**: Scope
- **Gap**: The request says "all 10 tools are `async def`" and "no existing tool signatures change." But the blocked issues (#465, #473) will need a `ctx: Context` parameter added. Is adding `ctx` in scope for this task, or is it explicitly deferred to the individual feature issues?
- **Question**: Should this task add `ctx: Context` as an optional parameter to any or all tools, or should it be strictly `def` → `async def` with no other signature changes?
- **Options**:
  - A) Strictly `def` → `async def`, zero other changes. Context parameters are added in separate feature issues.
  - B) Add `ctx: Context = None` (optional) to all 10 tools as part of this conversion so the next feature can just start using it.
- **Why It Matters**: Changes the scope of work and whether any tool signatures differ from today.
- **Resolution**: _pending_

### Q2: Does operations.py change in this task?

- **Category**: Scope
- **Gap**: The request explicitly scopes the change to `server.py` and wrapping `operations.py` calls with `asyncio.to_thread()`. This implies `operations.py` is unchanged. Confirming this avoids scope creep.
- **Question**: Is `operations.py` read-only for this task, with all blocking calls handled via `asyncio.to_thread()` at the `server.py` layer?
- **Options**:
  - A) Yes — `operations.py` unchanged, `asyncio.to_thread()` in `server.py` only.
  - B) Some operations in `operations.py` should also be converted (e.g., those that will be called directly with `await` in future work).
- **Why It Matters**: Determines which files the implementation agent touches.
- **Resolution**: _pending_

### Q3: Are test updates in scope?

- **Category**: Integration
- **Gap**: Converting sync tools to async tools changes how they are tested (pytest-asyncio, `@pytest.mark.asyncio`, etc.). If existing tests exist for `server.py` tools, they may need updates. If no tests exist, this is a non-issue.
- **Question**: Are test file updates (if any test suite covers `server.py` tools) in scope for this task, or are they a separate follow-up?
- **Options**:
  - A) In scope — update any existing tests that break due to async conversion.
  - B) Out of scope — test updates are a separate task.
- **Why It Matters**: Determines whether the implementation agent needs to verify and update test files.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. All 10 `@mcp.tool()` functions in `server.py` are `async def`.
2. Each tool body wraps its `operations.*` call(s) with `asyncio.to_thread()` so the blocking PyGithub calls do not block the event loop.
3. No tool names, parameter names, parameter types, or return value shapes change.
4. All existing `BacklogError` exception handling is preserved.
5. The server starts and handles all tool calls identically to the current synchronous implementation.
6. The four blocked issues (#465, #473, #469, #470) are unblocked by this change.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-06_

### Design Refinements

1. **`backlog_pull` `pull_by_selector` branch — `dry_run`/`force` not passed**: The architecture spec erroneously specified `dry_run` and `force` as arguments to `operations.pull_by_selector`. The actual function signature does not accept those parameters. The implementation correctly omits them — `dry_run` and `force` are passed only to `operations.pull_items` in the else branch. This aligns with the feature's core intent (preserve tool behaviour identically) since `pull_by_selector` never accepted those parameters.
   - Original spec: included `dry_run=dry_run, force=force` in `pull_by_selector` call
   - Actual: `pull_by_selector(selector, output=out)` only
   - Recorded in: `plan/tasks-1-convert-backlog-core-async.md`, Context Manifest, Discovered During Implementation

2. **Gap Q1 resolved — strictly `def` → `async def`**: Option A was implemented. No `ctx: Context` parameter was added to any tool. Context parameters are deferred to #465 and #473 as the spec required.

3. **Gap Q2 resolved — `operations.py` unchanged**: Option A. Only `server.py` was modified. All blocking calls handled via `asyncio.to_thread()` at the `server.py` boundary.

4. **Gap Q3 resolved — test updates not needed**: All 411 tests pass without modification to test files. 6 pre-existing live-API failures are unrelated to this change. The `state_handler` import error in `test_backlog_gh_first.py` is also pre-existing and unrelated.
