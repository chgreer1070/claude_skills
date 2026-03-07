# Feature Context: Context Logging and Progress Reporting for backlog_core Long-Running Tools

## Document Metadata

- **Generated**: 2026-03-06
- **Input Type**: simple_description (GitHub Issue #465)
- **Source**: Feature request — add `ctx: Context` parameter and progress/logging calls to 4 long-running MCP tools in backlog_core
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Add Context logging and progress reporting to backlog_core long-running tools (GitHub Issue #465).

The 4 long-running tools in backlog_core (`backlog_sync`, `backlog_pull`, `backlog_groom`,
`backlog_normalize`) make multiple sequential GitHub API calls but emit zero progress feedback.
MCP clients see nothing until the operation completes or errors.

Desired outcome:
- `ctx: Context` parameter added to `backlog_sync`, `backlog_pull`, `backlog_groom`, `backlog_normalize`
- `await ctx.info(...)` emitted at key milestones (e.g., "Fetching open issues...", "Syncing item: {title}")
- `await ctx.report_progress(i, total)` used for batch operations where total is known
- `await ctx.warning(...)` surfaces warnings currently buried in `out.warnings`
- All 6 non-long-running tools (`backlog_add`, `backlog_list`, `backlog_view`, `backlog_close`, `backlog_resolve`, `backlog_update`) are NOT modified

Files to examine:
- `.claude/skills/backlog/backlog_core/server.py` — 4 target tools
- `.claude/skills/backlog/backlog_core/operations.py` — to understand what milestones exist
- `.claude/worktrees/fastmcp/docs/servers/context.mdx` — FastMCP Context API

---

## Core Intent Analysis

### WHO (Target Users)

MCP client operators — any Claude Code session, IDE plugin, or agent that invokes `backlog_sync`,
`backlog_pull`, `backlog_groom`, or `backlog_normalize` via the MCP interface. The primary pain
is experienced by automated workflows where the tool call hangs silently for seconds or minutes
while GitHub API calls execute sequentially.

### WHAT (Desired Outcome)

MCP clients receive real-time feedback during long-running tool calls:
- Milestone log messages (`ctx.info`, `ctx.warning`) that describe what is happening now
- Numeric progress (`ctx.report_progress`) when the operation is iterating over a known-size collection

The tools remain functionally identical — no change to return values, behavior, or error handling.

### WHEN (Trigger Conditions)

Any time a user or agent invokes one of the four target tools (`backlog_sync`, `backlog_pull`,
`backlog_groom`, `backlog_normalize`) through the MCP interface. These are the only tools that
iterate over multiple GitHub issues or per-item files in sequence.

### WHY (Problem Being Solved)

The current tools are "black boxes" from the MCP client's perspective. A `backlog_sync` over 30
items may take 15-30 seconds. The client sees no activity during this time and cannot distinguish
between "still working" and "hung/errored silently". This degrades operator confidence and makes
debugging slow operations difficult.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Existing Output accumulation in server.py tools

- **Location**: `.claude/skills/backlog/backlog_core/server.py:122-138` (`backlog_sync`)
- **Relevance**: All 10 tools share the same structure — synchronous `def`, `out = Output()`,
  call `operations.*`, return `{**result, **out.to_dict()}`. The 4 target tools follow this
  exact pattern. Adding `ctx: Context` requires converting these 4 to `async def`.
- **Reusable**: The `out = Output()` / `out.to_dict()` pattern is retained alongside `ctx`
  calls — they serve different purposes (`out` populates the return dict; `ctx` streams live
  to the client).

#### Pattern 2: FastMCP Context legacy type-hint injection

- **Location**: `.claude/worktrees/fastmcp/docs/servers/context.mdx:77-93`
- **Relevance**: `ctx: Context` as a parameter type-hint is auto-injected by FastMCP and
  excluded from the MCP schema (clients never see it). This is the backwards-compatible
  injection approach — no import of `CurrentContext()` needed, just the `Context` type hint.
- **Reusable**: Pattern for adding ctx to any existing `@mcp.tool()` function without
  changing the tool's visible schema.

#### Pattern 3: operations.py function signatures for the 4 target operations

- **Location**: `.claude/skills/backlog/backlog_core/operations.py`
  - `sync_items` at line 1075
  - `groom_item` at line 1328
  - `normalize_items` at line 1368
  - `pull_by_selector` at line 1459 and `pull_items` at line 1500
- **Relevance**: All four are synchronous functions. They accept `output: Output | None` and
  perform iteration internally (loop over items, GitHub API calls per item). Milestones and
  progress calls must be placed in the `server.py` tool wrappers OR threaded through to
  `operations.py` functions — this is the key unresolved question.
- **Reusable**: The `output: Output | None` pattern could be extended with a `ctx` passthrough,
  or `ctx` calls could remain entirely in `server.py` wrappers.

### Existing Infrastructure

- `Output` class in `.claude/skills/backlog/backlog_core/models.py` already collects `messages`
  and `warnings` lists that are returned in the tool's dict response. These are end-of-call
  summaries, not live stream events.
- `FastMCP` version in the worktree supports `ctx.info()`, `ctx.warning()`,
  `ctx.report_progress(progress, total)` — all async, confirmed in context.mdx.
- The `backlog_pull` server tool has a branching code path (line 375-379 in server.py):
  single-item via `pull_by_selector` vs. bulk via `pull_items`. Both paths need consideration
  for progress reporting — only the bulk path (`pull_items`) has a knowable total.

### Code References

- `.claude/skills/backlog/backlog_core/server.py:122-138` — `backlog_sync` tool (target)
- `.claude/skills/backlog/backlog_core/server.py:292-323` — `backlog_groom` tool (target)
- `.claude/skills/backlog/backlog_core/server.py:326-344` — `backlog_normalize` tool (target)
- `.claude/skills/backlog/backlog_core/server.py:347-381` — `backlog_pull` tool (target)
- `.claude/skills/backlog/backlog_core/operations.py:1075` — `sync_items` signature
- `.claude/skills/backlog/backlog_core/operations.py:1328` — `groom_item` signature
- `.claude/skills/backlog/backlog_core/operations.py:1368` — `normalize_items` signature
- `.claude/skills/backlog/backlog_core/operations.py:1459` — `pull_by_selector` signature
- `.claude/skills/backlog/backlog_core/operations.py:1500` — `pull_items` signature
- `.claude/worktrees/fastmcp/docs/servers/context.mdx:77-93` — legacy type-hint ctx injection
- `.claude/worktrees/fastmcp/docs/servers/context.mdx:168-176` — `ctx.report_progress` API

---

## Use Scenarios

### Scenario 1: Syncing a large backlog

**Actor**: Agent running `/work-backlog-item` after a long offline period
**Trigger**: Calls `backlog_sync` to push local groomed content to GitHub
**Goal**: Know that progress is being made, not that the tool hung
**Expected Outcome**: MCP client receives a stream of log messages like
"Creating issue for: Add user auth", "Syncing groomed content: Fix CI", etc.
and a progress bar incrementing as each item is processed.

### Scenario 2: Pulling all GitHub issues into local cache

**Actor**: Operator running `backlog_pull` after a team sprint
**Trigger**: No selector provided — pulls all open issues
**Goal**: See how many items have been pulled so far out of the total
**Expected Outcome**: `ctx.report_progress(i, total)` messages incrementing from 0 to N
as each issue body is merged into the local per-item file.

### Scenario 3: Normalizing legacy per-item files

**Actor**: Repository maintainer running `backlog_normalize` for the first time
**Trigger**: Called after upgrading backlog format
**Goal**: Confirm operation is running and see which files have been normalized
**Expected Outcome**: `ctx.info("Normalizing: {filename}")` per file, plus final
`ctx.report_progress(total, total)` at completion.

### Scenario 4: Grooming a single item with GitHub sync

**Actor**: Claude Code session writing structured groomed content via `backlog_groom`
**Trigger**: Agent finishes analysis and calls groom to persist results
**Goal**: Know when the GitHub sync step starts (it is the slow part)
**Expected Outcome**: `ctx.info("Syncing groomed content to GitHub issue #N...")` emitted
before the GitHub API call, not after.

### Scenario 5: Warning surfacing during sync

**Actor**: Agent running `backlog_sync` when some items have issues locked or rate-limited
**Trigger**: GitHub API returns non-fatal error for one item during a batch
**Goal**: See warning in real time, not buried in the final return dict warnings list
**Expected Outcome**: `ctx.warning("Skipping {title}: rate limit hit")` emitted during the
operation so the operator can track which items were skipped without waiting for completion.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Where do `ctx` calls live — in server.py wrappers only, or threaded into operations.py functions? | Determines whether operations.py functions are modified at all |
| 2 | Behavior | `backlog_groom` appears to process a single item — does it still qualify as "long-running" for progress reporting purposes? | May need only `ctx.info` milestones, not `ctx.report_progress` |
| 3 | Behavior | When `backlog_pull` is called with a selector (single-item path), is progress reporting expected or only milestone logging? | Affects what ctx calls appear in the single-item branch |
| 4 | Behavior | How granular should `ctx.info` messages be? Per-item ("Syncing: {title}") vs. phase-level ("Fetching issues from GitHub...") | Determines verbosity contract |
| 5 | Behavior | What happens to `ctx.warning(...)` vs the existing `out.warnings` list — are they duplicated or is one deprecated for live ops? | Clarity on whether warnings appear in both stream and return dict |
| 6 | Integration | All 4 target tools are currently synchronous `def`. FastMCP `ctx` methods are `async`. Converting to `async def` is required — any callers of these tools outside MCP must be audited. | If operations.py functions receive `ctx`, they also need to become async |
| 7 | Scope | `backlog_groom` and `backlog_update` both call `operations.groom_item`. Should `backlog_update` (which is in the excluded 6) gain indirect ctx calls if `groom_item` is modified? | Determines if ctx passthrough into operations.py creates unintended scope expansion |

---

## Questions Requiring Resolution

### Q1: Where do ctx calls live — wrappers or operations.py?

- **Category**: Scope
- **Gap**: The feature request says to add `ctx` to the 4 server.py tool functions. The
  actual milestones (e.g., "Syncing item: {title}") require iteration context that only
  exists inside `operations.py` functions. Two approaches exist without designing them here.
- **Question**: Should `ctx` calls remain entirely within the 4 `server.py` tool wrappers
  (only coarse phase-level messages), or should `ctx` be threaded into the `operations.py`
  functions so per-item messages are possible?
- **Options**:
  - A) ctx stays in server.py only — messages are coarse ("Starting sync...", "Sync complete")
  - B) ctx is passed into operations.py functions — per-item messages ("Syncing: {title}")
- **Why It Matters**: Option B requires modifying operations.py and potentially making those
  functions async, which is a significantly larger change surface.
- **Resolution**: _pending_

### Q2: Is backlog_groom considered a "long-running" tool warranting progress reporting?

- **Category**: Behavior
- **Gap**: `backlog_groom` processes a single item (identified by selector), not a batch.
  It makes one GitHub sync call. The request groups it with the 3 batch tools.
- **Question**: For `backlog_groom`, is `ctx.report_progress` expected, or only `ctx.info`
  milestone logging?
- **Options**:
  - A) `ctx.info` milestones only (no progress fraction — total is always 1)
  - B) `ctx.report_progress(0, 1)` then `ctx.report_progress(1, 1)` for consistency
- **Why It Matters**: Affects the implementation contract and what the MCP client receives.
- **Resolution**: _pending_

### Q3: What granularity of ctx.info messages is expected?

- **Category**: Behavior
- **Gap**: The request gives two examples: "Fetching open issues..." (phase-level) and
  "Syncing item: {title}" (per-item). These are different granularities.
- **Question**: Should every item in a batch emit a `ctx.info` message, or only phase
  transitions? For a 50-item sync, is 50 info messages acceptable or noisy?
- **Options**:
  - A) Per-item info messages for every item in the batch
  - B) Phase-level only — start of each major operation phase, not per-item
  - C) Per-item progress (ctx.report_progress) but only phase-level info messages
- **Why It Matters**: High-verbosity per-item messages may flood clients that display all
  log lines; progress ticks are the less noisy mechanism for item-by-item feedback.
- **Resolution**: _pending_

### Q4: Should ctx.warning duplicate or replace out.warnings for live operations?

- **Category**: Behavior
- **Gap**: `out.warnings` currently collects warnings returned in the final dict.
  `ctx.warning` would stream them to the client live. The request says to surface warnings
  "currently buried in out.warnings" — unclear if both channels should carry the same warning.
- **Question**: When a non-fatal warning occurs during a long-running operation, should it
  appear in both `ctx.warning(...)` (live stream) and `out.warnings` (return dict), or
  should the live-ops tools drop out.warnings in favor of ctx exclusively?
- **Options**:
  - A) Both — ctx.warning for live visibility, out.warnings retained for structured return
  - B) ctx.warning only — out.warnings omitted from the 4 target tools' return dicts
- **Why It Matters**: Callers that parse the return dict `warnings` field will break if
  option B is chosen.
- **Resolution**: _pending_

### Q5: Does the single-item backlog_pull path get progress reporting?

- **Category**: Behavior
- **Gap**: `backlog_pull` has two branches: single-item (`pull_by_selector`) and bulk
  (`pull_items`). The bulk path has a knowable total. The single-item path does not.
- **Question**: For `backlog_pull` when called with a selector (single item), what ctx
  calls are expected?
- **Options**:
  - A) `ctx.info` milestones only for single-item path; `ctx.report_progress` only for bulk
  - B) Same treatment for both paths for consistency
- **Why It Matters**: Determines how the branching logic in the server.py tool is written.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Add `ctx: Context` parameter to `backlog_sync`, `backlog_pull`, `backlog_groom`,
   and `backlog_normalize` in `.claude/skills/backlog/backlog_core/server.py`
2. Convert the 4 target tool functions from synchronous `def` to `async def` (required
   because `ctx.info`, `ctx.warning`, and `ctx.report_progress` are all async)
3. Emit `ctx.info(...)` messages at key milestones within each of the 4 tools
4. Emit `ctx.report_progress(i, total)` for batch operations where the total item count
   is known before iteration begins
5. Emit `ctx.warning(...)` for non-fatal conditions that are currently captured only in
   `out.warnings` (scope: live-ops tools only, per Q4 resolution)
6. Leave all 6 excluded tools (`backlog_add`, `backlog_list`, `backlog_view`,
   `backlog_close`, `backlog_resolve`, `backlog_update`) completely unmodified
7. Leave the return dict shape of all 4 target tools unchanged (ctx calls are additive;
   no existing fields removed)

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section (Q1 through Q5)
2. Finalize Goals section based on Q1 resolution (scope of operations.py changes)
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design with `@python3-development:python-cli-design-spec`

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-06_

### Design Refinements

1. **Q1 resolved — ctx stays in server.py only (Option A)**: The architect spec chose Option A: `ctx` calls remain entirely within the 4 `server.py` tool wrappers. `operations.py` is unchanged. Log messages are phase-level only ("Starting backlog sync", "Sync complete: N issue(s) created, M item(s) pushed"). Per-item messages require future operations.py refactoring.
   - Original: Q1 marked "Resolution: _pending_"
   - Actual: Option A implemented; `operations.py` has zero ctx-related changes
   - Recorded in: plan/architect-context-logging-progress.md, "report_progress Decision" section

2. **Q2 resolved — backlog_groom gets ctx.info milestones only, no report_progress**: The feature request listed `backlog_groom` alongside batch tools. The architect spec and implementation treat it as single-item (no progress fraction). Only `ctx.info` start and completion logs are emitted.
   - Original: Q2 marked "Resolution: _pending_"
   - Actual: Option A implemented (ctx.info milestones only, no progress fraction)
   - Recorded in: plan/tasks-1-context-logging-progress.md, T1 task spec

3. **Q3 resolved — phase-level only (Option B)**: No per-item `ctx.info` messages. Each tool emits exactly one start log and one completion summary. For a 50-item sync, only 2 info messages are emitted (not 50).
   - Original: Q3 marked "Resolution: _pending_"
   - Actual: Option B implemented across all 4 tools
   - Recorded in: plan/architect-context-logging-progress.md, per-tool ctx call specifications

4. **Q4 resolved — both channels preserved (Option A)**: `ctx.warning` and `out.warnings` both carry the same warnings. Callers parsing the return dict `warnings` field are unaffected.
   - Original: Q4 marked "Resolution: _pending_"
   - Actual: Option A implemented; warning surfacing loop (`for w in out.warnings: await ctx.warning(w)`) added to all 4 tools
   - Recorded in: plan/architect-context-logging-progress.md, "Warning Surfacing Contract" section

5. **Q5 resolved — single-item backlog_pull gets ctx.info milestones only**: The single-item branch of `backlog_pull` (when selector is provided) gets `ctx.info("Pulling issue: {selector}")` start log and `ctx.info("Pulled: {file_path}")` completion log. No `report_progress` on either branch.
   - Original: Q5 marked "Resolution: _pending_"
   - Actual: Option A implemented (ctx.info for single-item path; ctx.info start+completion for bulk path with no report_progress on either)
   - Recorded in: plan/architect-context-logging-progress.md, backlog_pull ctx call specification

6. **ctx.report_progress not delivered — scope boundary from original request not achievable at server.py layer**: The original feature request (Goals section, item 4) specifies `ctx.report_progress(i, total)` for batch operations. The architect spec determined this requires operations.py refactoring and deferred it. The implementation contains zero `ctx.report_progress` calls. This is a scope reduction relative to the original request's Goals, resolved at architecture phase.
   - Original: Goal 4 — "Emit `ctx.report_progress(i, total)` for batch operations where the total item count is known before iteration begins"
   - Actual: Not implemented; deferred to future ticket targeting operations.py loop refactoring
   - Recorded in: plan/architect-context-logging-progress.md, "report_progress Decision" section; plan/tasks-1-context-logging-progress.md, Discovered During Implementation
