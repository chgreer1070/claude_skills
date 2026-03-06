# Feature Context: MCP Prompts and Guided Elicitation Tools for backlog_core

## Document Metadata

- **Generated**: 2026-03-06
- **Input Type**: existing_document
- **Source**: `.claude/backlog/p1-add-mcp-prompts-and-guided-elicitation-tools-to-backlogcore-.md` (GitHub Issue #473)
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Add MCP prompts and guided elicitation tools to `backlog_core/server.py` to consolidate workflow logic currently scattered across four Claude Code skills (`/backlog`, `/create-backlog-item`, `/groom-backlog-item`, `/work-backlog-item`).

Two additions to `backlog_core/server.py`:

**5 MCP prompts** via `@mcp.prompt` decorator:
- `backlog_guide()` — full tool reference as messages; replaces `/backlog` skill
- `create_item_guided()` — intake instructions as messages
- `groom_item(selector: str)` — item state + grooming workflow as messages
- `work_item(selector: str)` — item state + planning instructions as messages
- `close_or_resolve(selector: str)` — item state + close vs. resolve decision guide as messages

**4 guided tools** via `@mcp.tool`, `async def`, `ctx: Context`:
- `backlog_add_guided` — multi-field elicitation then delegates to `operations.add_item()`
- `backlog_close_confirmed` — confirmation elicitation before `operations.close_item()`
- `backlog_resolve_confirmed` — summary elicitation before `operations.resolve_item()`
- `backlog_setup_github` — runs label taxonomy + milestone init

---

## Core Intent Analysis

### WHO (Target Users)

Two distinct user populations:

1. **Claude Code users** — currently served by skills (`/backlog`, `/create-backlog-item`, etc.). They have guided workflows today but those workflows live outside the MCP server and drift as the server evolves.

2. **Non-Claude-Code MCP clients** — users of Claude Desktop, Cursor, Zed, or any other MCP-compliant client. They have access to the 10 raw CRUD tools today but have no guided workflow, no intake prompts, and no interactive confirmation flows.

### WHAT (Desired Outcome)

The MCP server itself carries the workflow guidance — prompts that return structured messages any MCP client can consume, and interactive tools that elicit required fields instead of requiring callers to supply all parameters upfront. The four Claude Code skills become thinner or optional after this ships.

### WHEN (Trigger Conditions)

- A user on Claude Desktop or Cursor wants to create a backlog item but does not know which fields are required or what priority levels are valid.
- A user wants to close or resolve an item and is unsure which operation applies to their situation.
- A developer updates the MCP server's CRUD logic but the corresponding skill content is stale — the disconnect causes behavior divergence.
- An MCP client calls `prompts/list` and discovers available workflow templates without needing Claude Code installed.

### WHY (Problem Being Solved)

Workflow logic (intake field instructions, grooming steps, close vs. resolve decision guidance) currently lives exclusively in Claude Code skills. Skills are Claude Code-specific delivery mechanisms. Any MCP client that is not Claude Code receives only the raw CRUD tools with no guided workflow. Additionally, when the MCP server evolves, all four skills must be updated manually to stay current — a synchronization burden that grows over time. Moving the logic into the MCP server makes it client-agnostic and self-maintaining.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Existing synchronous tool registration in `server.py`

- **Location**: `.claude/skills/backlog/backlog_core/server.py:16-385`
- **Relevance**: All 10 existing tools follow a consistent pattern — `@mcp.tool()` decorator, synchronous `def`, typed `Annotated` parameters, delegate to `operations.*`, return `{**result, **out.to_dict()}`. The new guided tools add `async def` and `ctx: Context` to this pattern. The new MCP prompts use `@mcp.prompt` instead of `@mcp.tool`.
- **Reusable**: The `operations.*` delegation pattern is directly reused by all 4 guided tools. `operations.add_item()`, `operations.close_item()`, `operations.resolve_item()`, and `operations.view_item()` are the target callees.

#### Pattern 2: FastMCP `@mcp.prompt` decorator

- **Location**: `.claude/worktrees/fastmcp/docs/servers/prompts.mdx:26-49`
- **Relevance**: Prompts return `str`, `list[Message]`, or `PromptResult`. The `Message` class accepts content and an optional `role` (`"user"` or `"assistant"`). Import path is `from fastmcp.prompts import Message`. Prompts that call I/O (e.g., `operations.view_item()` which calls the GitHub API) must be `async def`.
- **Reusable**: The `groom_item`, `work_item`, and `close_or_resolve` prompts need `async def` because they call `operations.view_item()` which hits GitHub. The `backlog_guide` and `create_item_guided` prompts are pure string assembly and can be synchronous `def`.

#### Pattern 3: FastMCP `ctx.elicit()` API

- **Location**: `.claude/worktrees/fastmcp/docs/v2/servers/elicitation.mdx:33-59`
- **Relevance**: Tools using `ctx.elicit()` must be `async def` with `ctx: Context` parameter. Returns an `ElicitationResult` with `action` (`"accept"` | `"decline"` | `"cancel"`) and `data`. The MCP spec constrains elicitation response schemas to shallow objects with primitive fields — no nested models. `ctx.elicit()` raises `NotSupportedError` if the client does not implement an elicitation handler.
- **Reusable**: The structured elicitation dataclass pattern (`@dataclass class AddItemRequest` with `Literal` types for constrained fields) applies directly to `backlog_add_guided`. The `response_type=None` confirmation-only pattern applies to `backlog_close_confirmed`.

#### Pattern 4: `/backlog` SKILL.md Primary Interface section

- **Location**: `.claude/skills/backlog/SKILL.md:8-221`
- **Relevance**: This is the content that `backlog_guide()` prompt must replicate as MCP messages. The section documents all 10 tools with parameters and return shapes. The prompt version will make this content available to any MCP client without skill installation.
- **Reusable**: The prose and parameter tables from SKILL.md become the message body returned by `backlog_guide()`.

### Existing Infrastructure

- **`operations.view_item(selector, offset, limit, output)`** — called by `groom_item`, `work_item`, `close_or_resolve` prompts to fetch live item state before returning messages. Verified at `operations.py` (full file is 65KB; specific function signatures confirmed from `backlog_view` tool at `server.py:98-118`).
- **`operations.add_item()`**, **`operations.close_item()`**, **`operations.resolve_item()`** — called by guided tools after elicitation accepts. Confirmed as delegation targets from existing sync tools at `server.py:39-48`, `server.py:169-180`, `server.py:210-223`.
- **FastMCP version in worktree** — the local FastMCP worktree at `.claude/worktrees/fastmcp/` is the authoritative reference. Elicitation API confirmed present at `docs/v2/servers/elicitation.mdx` (VersionBadge 2.10.0).

### Code References

- `.claude/skills/backlog/backlog_core/server.py:1-13` — FastMCP server instantiation: `mcp = FastMCP("backlog")`
- `.claude/skills/backlog/backlog_core/server.py:16-51` — `backlog_add` tool: reference pattern for `operations.add_item()` delegation
- `.claude/skills/backlog/backlog_core/server.py:141-181` — `backlog_close` tool: reference pattern for `operations.close_item()` delegation
- `.claude/skills/backlog/backlog_core/server.py:184-224` — `backlog_resolve` tool: reference pattern for `operations.resolve_item()` delegation
- `.claude/worktrees/fastmcp/docs/servers/prompts.mdx:26-49` — `@mcp.prompt` basic usage and return types
- `.claude/worktrees/fastmcp/docs/servers/prompts.mdx:384-400` — async prompts and `Context` parameter
- `.claude/worktrees/fastmcp/docs/v2/servers/elicitation.mdx:33-59` — `ctx.elicit()` basic usage
- `.claude/worktrees/fastmcp/docs/v2/servers/elicitation.mdx:360-387` — structured dataclass response type
- `.claude/worktrees/fastmcp/docs/v2/servers/elicitation.mdx:189-201` — `response_type=None` confirmation pattern
- `.claude/backlog/p1-add-mcp-prompts-and-guided-elicitation-tools-to-backlogcore-.md:57-71` — Fact-check section: all API claims verified against FastMCP docs

---

## Use Scenarios

### Scenario 1: Claude Desktop user creates a backlog item

**Actor**: Developer using Claude Desktop (not Claude Code)
**Trigger**: Wants to log a new feature idea into the project backlog
**Goal**: Create a properly formatted backlog item without knowing the required fields
**Expected Outcome**: The client calls `backlog_add_guided`; the server elicits title, priority, description, and type interactively; the item is created and a GitHub issue is opened. The user never had to know field names or valid priority values.

### Scenario 2: Cursor user grooms a backlog item

**Actor**: Developer using Cursor with the backlog MCP server connected
**Trigger**: Wants to understand what grooming steps to follow for a specific item
**Goal**: Get the current item state and grooming workflow instructions in one response
**Expected Outcome**: The client calls `groom_item(selector="#473")`; the server fetches the item body via `operations.view_item()` and returns messages containing the item's current state plus the grooming workflow — all without requiring the user to have `/groom-backlog-item` skill installed.

### Scenario 3: Claude Code user resolves a completed item with confirmation

**Actor**: Developer in a Claude Code session completing a feature
**Trigger**: Work is done; wants to mark the item resolved with a completion summary
**Goal**: Resolve the item with a structured summary without accidentally using `backlog_close` (dismissal) instead of `backlog_resolve` (completion)
**Expected Outcome**: The client calls `backlog_resolve_confirmed`; the server elicits a summary field and presents a confirmation; the user confirms; `operations.resolve_item()` is called. The guided flow prevents the close-vs-resolve confusion that the raw tools expose.

### Scenario 4: Any MCP client discovers available workflows

**Actor**: Any MCP client performing discovery
**Trigger**: Client calls `prompts/list` to see what guided templates are available
**Goal**: Understand the full workflow capability of the backlog server without reading documentation
**Expected Outcome**: Client receives 5 prompt names (`backlog_guide`, `create_item_guided`, `groom_item`, `work_item`, `close_or_resolve`) with descriptions. A user can call `backlog_guide()` with no arguments and receive the complete tool reference as message content.

### Scenario 5: Elicitation-unsupported client calls a guided tool

**Actor**: An MCP client that does not implement elicitation (e.g., an older or minimal client)
**Trigger**: Client invokes `backlog_add_guided`
**Goal**: Graceful degradation — not a silent failure
**Expected Outcome**: The guided tool catches `NotSupportedError` from `ctx.elicit()` and returns a message directing the user to use `backlog_add` directly with the required parameters listed. No crash, no confusing error.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Integration | Prerequisite #472 (async tools) is P2; this item is P1. The priority mismatch means the blocking item may not be worked before this one. | Implementation cannot proceed until #472 merges — async def and asyncio.to_thread patterns are not yet established in server.py. |
| 2 | Integration | Prerequisite #465 (Context logging) touches server.py concurrently with this item. | Merge conflict risk if both items are worked in parallel on the same file. |
| 3 | Scope | The `backlog_setup_github` guided tool's source logic (label taxonomy + milestone init) lives in `/work-backlog-item` skill — it has not been verified as a self-contained callable that can be moved to the MCP server without the skill's surrounding context. | The implementer needs to read the setup-github command logic in the skill before coding the tool. |
| 4 | Behavior | The `backlog_guide()` prompt must replicate the content from `SKILL.md` Primary Interface section. It is unspecified whether this is a verbatim copy, a reformatted version, or a subset. | Content fidelity decision affects how much the skill can be thinned afterward. |
| 5 | Behavior | For the three prompts that call `operations.view_item()` (`groom_item`, `work_item`, `close_or_resolve`), there is no specified behavior when the selector does not match any item. | Unhandled `ItemNotFoundError` from `operations.view_item()` would surface as an unformatted exception to the MCP client. |
| 6 | Scope | Skills affected by this change (four SKILL.md files) are listed but the extent of thinning is unspecified. The item says skills "become thinner wrappers" but does not define what stays vs. what moves. | Risk of skill content being removed prematurely (before MCP prompts are verified as equivalent) or not removed at all (leaving duplicate maintenance burden). |
| 7 | User | `backlog_guide()` returns the full tool reference as messages — but MCP clients differ in how they surface prompt content to users. It is unclear whether the intended consumer of `backlog_guide` is the LLM (which uses it as context) or the human user (who reads it directly). | Affects how the content is structured: LLM-optimized instruction format vs. human-readable documentation. |

---

## Questions Requiring Resolution

### Q1: Prerequisites blocking order

- **Category**: Integration
- **Gap**: #472 (async tools, P2) must merge before #473 (this item, P1) can be implemented. The priority mismatch means #472 may sit in the queue below P1 items.
- **Question**: Should #472 be promoted to P1 to unblock this item, or should this item's P1 status be lowered to P2 to match its actual unblocked state?
- **Options**:
  - A) Promote #472 to P1 — implement async tools first, then this item
  - B) Lower #473 to P2 — keep priority consistent with its blocked state
  - C) Implement #473 conditionally — write the guided tools as sync stubs that become async when #472 lands
- **Why It Matters**: Work cannot begin on the guided tools until the async pattern is established. A wrong priority assignment could cause wasted scheduling effort.
- **Resolution**: _pending_

### Q2: Skill thinning scope after MCP prompts land

- **Category**: Scope
- **Gap**: The backlog item says four skills become "thinner wrappers" but does not define which sections are removed, which stay, and whether the skills eventually disappear entirely.
- **Question**: After the MCP prompts and guided tools ship, which skill sections should be removed, and which Claude Code-specific orchestration logic (e.g., `--auto` mode in `/create-backlog-item`, SAM planning flow in `/work-backlog-item`) stays skill-only indefinitely?
- **Options**:
  - A) Thin skills immediately in the same PR as the server changes
  - B) Thin skills in a separate follow-up item after the server changes are verified
  - C) Leave skills unchanged for now — they remain as redundant but harmless Claude Code-specific wrappers
- **Why It Matters**: If skill content is removed before MCP prompt equivalence is verified, users on Claude Code lose workflow guidance during the gap. If skills are never thinned, the duplicate maintenance burden persists.
- **Resolution**: _pending_

### Q3: `backlog_guide()` content — LLM instruction format vs. human-readable documentation

- **Category**: Behavior
- **Gap**: MCP prompts return messages that are injected into LLM context. The SKILL.md Primary Interface section is already written as LLM-facing instruction. Whether `backlog_guide()` should be a verbatim lift of that content, a reformatted version, or a condensed version is unspecified.
- **Question**: Should `backlog_guide()` return the SKILL.md Primary Interface section verbatim (with tables and parameter lists), or should it be reformatted for LLM prompt injection (more prose, fewer markdown tables)?
- **Options**:
  - A) Verbatim lift from SKILL.md — minimal effort, consistent with existing content
  - B) Reformatted for LLM prompt injection — optimized for LLM comprehension, not human reading
  - C) Condensed reference — drop parameter tables, keep tool names and behavioral notes
- **Why It Matters**: The format determines how effectively MCP clients can use the guide to assist users. A table-heavy format works in Claude Code but may not render well in other clients.
- **Resolution**: _pending_

### Q4: Error handling in selector-based prompts

- **Category**: Behavior
- **Gap**: `groom_item(selector)`, `work_item(selector)`, and `close_or_resolve(selector)` call `operations.view_item()`. If the selector does not match, `operations.view_item()` raises `ItemNotFoundError`. No specified behavior for this case in the prompt context.
- **Question**: When a selector-based prompt cannot find the item, what should the prompt return — an error message, an empty message list, or a raised exception?
- **Options**:
  - A) Return a user-facing error message as a prompt message: "Item not found for selector X"
  - B) Raise the exception — let the MCP client handle it
  - C) Return a partial prompt with the grooming/working instructions but no item state
- **Why It Matters**: MCP prompts that raise unhandled exceptions produce poor UX in non-Claude-Code clients. A user-facing message is more consistent with how the existing CRUD tools handle `BacklogError`.
- **Resolution**: _pending_

### Q5: `backlog_setup_github` — source of label taxonomy logic

- **Category**: Scope
- **Gap**: The label taxonomy and milestone initialization logic that `backlog_setup_github` should encapsulate currently lives in the `/work-backlog-item` skill. The backlog item references this but does not confirm whether that logic is already callable from Python or requires shell invocations.
- **Question**: Is the setup-github logic in `/work-backlog-item` already implemented as Python operations callable from `operations.py`, or does it require reading and porting skill-level logic into the MCP server?
- **Why It Matters**: If the logic is already in Python (e.g., in `github.py`), the tool is a thin wrapper. If it is only in the skill as orchestration instructions, the tool requires a new Python implementation to be written first.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Add 5 MCP prompts to `backlog_core/server.py` using `@mcp.prompt`, returning `list[Message]` content that guides any MCP client through backlog workflows without requiring Claude Code skills.

2. Add 4 guided tools to `backlog_core/server.py` using `@mcp.tool` with `async def` and `ctx: Context`, using `ctx.elicit()` for interactive field collection before delegating to existing `operations.*` functions.

3. All 10 existing synchronous tools remain unmodified and continue to pass existing tests.

4. All guided tools handle all three elicitation outcomes (`accept`, `decline`, `cancel`) with explicit return messages for each path.

5. All guided tools handle `NotSupportedError` from `ctx.elicit()` with a fallback message directing users to the equivalent non-guided tool.

6. The three selector-based prompts (`groom_item`, `work_item`, `close_or_resolve`) handle item-not-found errors with user-facing message content rather than raised exceptions.

7. Implement only after prerequisites #472 (async tools) and #465 (Context logging) have merged into `server.py`.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Confirm prerequisite merge order (#472 priority reassignment if needed)
3. Finalize skill thinning scope (same PR vs. follow-up)
4. Proceed to architecture design with `@python3-development:python-cli-design-spec`
5. Implement with `@python3-development:python-cli-architect`
6. Review with `@python3-development:python-code-reviewer` — verify async patterns, elicitation response handling (all 3 action outcomes), and no regressions to existing sync tools
