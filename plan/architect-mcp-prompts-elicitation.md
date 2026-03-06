# Architecture: MCP Prompts and Guided Elicitation Tools for backlog_core

## Executive Summary

Add 5 MCP prompts and 2 guided tools to `server.py`, bringing the total from 10 tools to 10 tools
+ 5 prompts + 2 guided tools. All new code goes in
`.claude/skills/backlog/backlog_core/server.py` only — no changes to `operations.py`,
`models.py`, or any other module.

**Prerequisite**: Issue #472 (convert existing tool functions to `async def`) must land before
this work. The guided tools and dynamic prompts in this spec require `await` and `asyncio.to_thread`.

**No prerequisite**: Issue #465 (Context logging) can land before or after; both touch `server.py`
but do not conflict with this feature.

---

## Source File Reference

All functions described here are added to:

```text
.claude/skills/backlog/backlog_core/server.py
```

Existing patterns to follow (already in that file):

- Tool functions: `@mcp.tool()` decorator, sync `def`, `Output()` instantiation, `BacklogError`
  catch returning `{"error": str(e), **out.to_dict()}`
- Import block: `from fastmcp import FastMCP`, `from pydantic import Field`,
  `from . import operations`, `from .models import BacklogError, Output`

---

## New Imports Required

Add to the import block at the top of `server.py`:

```python
import asyncio
from dataclasses import dataclass
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.prompts import Message
from fastmcp.server.elicitation import NotSupportedError
from pydantic import Field
```

Notes on each import:

- `asyncio` — for `asyncio.to_thread()` in async prompt functions that call sync `operations.*`
- `dataclass` — for the `AddItemRequest` elicitation schema
- `Literal` — used in `AddItemRequest` field types
- `Context` — required parameter type for guided tools
- `Message` — return type for dynamic prompts returning `list[Message]`
- `NotSupportedError` — imported from `fastmcp.server.elicitation`; raised by `ctx.elicit()`
  when the MCP client does not implement the elicitation protocol

SOURCE: `.claude/worktrees/fastmcp/docs/servers/prompts.mdx` (read 2026-03-06)
SOURCE: `.claude/worktrees/fastmcp/docs/v2/servers/elicitation.mdx` (read 2026-03-06)

---

## Section 1: MCP Prompts (5 functions)

### Decorator syntax

Use `@mcp.prompt` (no parentheses) for all prompts. This is the canonical FastMCP form.

```python
@mcp.prompt
def my_prompt() -> str:
    ...
```

### 1.1 `backlog_guide()` — static, sync

**Purpose**: Return the full backlog usage guide so the LLM can orient itself without calling
any tool. Content is a verbatim copy of the substantive sections from
`.claude/skills/backlog/SKILL.md`.

**Signature**:

```python
@mcp.prompt
def backlog_guide() -> str:
    """Full guide to backlog operations: tools, selectors, return shapes, and common workflows."""
```

**Return type**: `str`

**Async**: No — pure string construction, no I/O.

**Content to include** (derive from `.claude/skills/backlog/SKILL.md`):

- The 10 tool parameter tables with defaults and descriptions
- The return value contract (error shape vs success shape)
- The selector formats: `#N`, bare number, GitHub issue URL, title substring
- The environment section (`GITHUB_TOKEN`)
- The integration section (which slash commands call which tools)
- The "Do not edit per-item files directly" warning

Do not include the YAML frontmatter. Do not include the CI/CLI section (that is not relevant
to MCP callers).

**Body structure**:

```python
return """
# Backlog — Usage Guide

[full content from SKILL.md, formatted as plain markdown string]
"""
```

---

### 1.2 `create_item_guided()` — static, sync

**Purpose**: Provide a structured prompt template that guides the LLM to elicit the right
information from the user before calling `backlog_add`. Does not call any tool or operation.

**Signature**:

```python
@mcp.prompt
def create_item_guided() -> str:
    """Prompt template guiding an LLM to collect all fields needed for backlog_add."""
```

**Return type**: `str`

**Async**: No.

**Content**: A multi-sentence natural language prompt instructing the LLM to ask the user for:

1. Title (required, concise action phrase)
2. Description (required, problem + context + why it matters)
3. Priority: P0 (must-have), P1 (should-have), P2 (could-have), Ideas (exploratory)
4. Type: Feature, Bug, Refactor, Docs, or Chore (default Feature)
5. Source: where this item came from (default "Not specified")

After collecting these, the LLM should call `backlog_add` with `create_issue=True` (default).

---

### 1.3 `groom_item(selector: str)` — dynamic, async

**Purpose**: Fetch a backlog item by selector and return a prompt that instructs the LLM
to write structured groomed content for it.

**Signature**:

```python
@mcp.prompt
async def groom_item(selector: str) -> list[Message]:
    """Fetch a backlog item and return a grooming prompt pre-populated with its current content."""
```

**Return type**: `list[Message]`

**Async**: Yes — calls `operations.view_item()` via `asyncio.to_thread()`.

**Implementation contract**:

1. Call `operations.view_item(selector=selector, offset=0, limit=0, output=Output())` inside
   `asyncio.to_thread()`.
2. If the result dict contains `"error"`, return a single `Message` explaining the error and
   asking the user to provide a valid selector.
3. Otherwise build `list[Message]` with two entries:
   - `Message(role="user", content=<prompt text>)` — instructs the LLM to write groomed content
     for the item, including its current title, priority, description, and existing groomed content
     (if any). Groomed content should follow the sections: Background, Acceptance Criteria,
     Implementation Notes, Open Questions.
   - `Message(role="assistant", content="I'll help you groom this backlog item. Let me review it.")` — assistant acknowledgement.
4. After grooming, instruct the LLM to call `backlog_groom(selector=..., groomed_content=...)`.

**asyncio.to_thread pattern**:

```python
result = await asyncio.to_thread(
    operations.view_item, selector=selector, offset=0, limit=0, output=Output()
)
```

---

### 1.4 `work_item(selector: str)` — dynamic, async

**Purpose**: Fetch a backlog item and return a prompt that orients the LLM for implementation
work: what the item is, what the acceptance criteria are, and what to do when done.

**Signature**:

```python
@mcp.prompt
async def work_item(selector: str) -> list[Message]:
    """Fetch a backlog item and return a work-start prompt with acceptance criteria and completion instructions."""
```

**Return type**: `list[Message]`

**Async**: Yes — same `asyncio.to_thread` pattern as `groom_item`.

**Implementation contract**:

1. Call `operations.view_item` via `asyncio.to_thread`. Handle error the same as `groom_item`.
2. Build `list[Message]`:
   - `Message(role="user", content=<prompt text>)` — includes item title, priority, description,
     full body, and groomed content (if any). Instructs LLM to implement the acceptance criteria,
     then call `backlog_resolve(selector=..., summary=..., method=..., findings=...)` when done.
   - `Message(role="assistant", content="I'll start working on this backlog item now.")` — acknowledgement.

---

### 1.5 `close_or_resolve(selector: str)` — dynamic, async

**Purpose**: Fetch a backlog item and return a prompt that guides the LLM (and user) through
choosing whether to close (dismiss) or resolve (complete) the item, and collecting the required
fields for each path.

**Signature**:

```python
@mcp.prompt
async def close_or_resolve(selector: str) -> list[Message]:
    """Fetch a backlog item and return a decision prompt for closing or resolving it."""
```

**Return type**: `list[Message]`

**Async**: Yes — same `asyncio.to_thread` pattern.

**Implementation contract**:

1. Call `operations.view_item` via `asyncio.to_thread`. Handle error the same as `groom_item`.
2. Build `list[Message]`:
   - `Message(role="user", content=<prompt text>)` — shows item title, priority, description.
     Asks user: was this completed (resolve) or dismissed (close)?
     - If resolve: collect summary (required), method, notes, follow_ups, findings.
       Then call `backlog_resolve(selector=..., summary=..., ...)`.
     - If close: collect reason (one of: duplicate, out_of_scope, superseded, wontfix, blocked),
       reference (optional), comment (optional).
       Then call `backlog_close(selector=..., reason=..., ...)`.
   - `Message(role="assistant", content="I'll help you close out this backlog item. First, was this work completed or dismissed?")` — acknowledgement.

---

## Section 2: Guided Tools (2 functions)

Guided tools are `@mcp.tool` functions with `ctx: Context` parameter that call `ctx.elicit()`
to collect structured input interactively, then delegate to existing operations.

### 2.1 `backlog_add_guided` — elicitation tool

**Purpose**: Walk the user through creating a backlog item step by step, then call
`operations.add_item` with the collected fields.

**Elicitation dataclass**:

```python
@dataclass
class AddItemRequest:
    title: str
    priority: Literal["P0", "P1", "P2", "Ideas"]
    description: str
    type_: Literal["Feature", "Bug", "Refactor", "Docs", "Chore"] = "Feature"
```

Place this dataclass at module level in `server.py`, above the tool function. It is not
exported — it is only used by `backlog_add_guided`.

Notes on the dataclass:

- `type_` uses trailing underscore to avoid shadowing the built-in `type`. The field renders
  to the user as `type_` but the underlying value is one of the five valid strings.
- `priority` is `Literal` — the elicitation client renders this as a constrained dropdown.
- No `source` field in the dataclass — source is not interactive; it defaults to the
  `"Not specified"` value already in `operations.add_item`.

**Signature**:

```python
@mcp.tool()
async def backlog_add_guided(ctx: Context) -> dict:
    """Interactively collect backlog item fields, then create the item via backlog_add."""
```

**Return type**: `dict` — same shape as `backlog_add` (success or error dict).

**Implementation contract**:

```text
1. Call ctx.elicit(
       message="Provide details for the new backlog item",
       response_type=AddItemRequest
   )

2. Handle all three ElicitationResult.action values:
   - "accept":
       Call operations.add_item(
           title=result.data.title,
           priority=result.data.priority,
           description=result.data.description,
           source="Not specified",
           type_=result.data.type_,
           create_issue=True,
           force=False,
           output=out,
       )
       Return {**add_result, **out.to_dict()}
   - "decline":
       Return {"messages": ["Item creation declined by user."], "warnings": []}
   - "cancel":
       Return {"messages": ["Item creation cancelled."], "warnings": []}

3. Catch NotSupportedError:
       Return {
           "error": "This MCP client does not support interactive elicitation. "
                    "Use backlog_add directly with all required fields: "
                    "title, priority, description.",
           "messages": [],
           "warnings": [],
       }

4. Catch BacklogError as e:
       Return {"error": str(e), **out.to_dict()}
```

**Exception handling order**: The `NotSupportedError` catch must come before `BacklogError`
because `NotSupportedError` does not inherit from `BacklogError`.

---

### 2.2 `backlog_setup_github` — no elicitation, guided verification

**Purpose**: Run the GitHub setup check and return a structured status dict. No elicitation.
This tool exists to give the user a single named tool for "is GitHub configured?" without
requiring them to know the internal setup mechanism.

**Signature**:

```python
@mcp.tool()
async def backlog_setup_github(ctx: Context) -> dict:
    """Check GitHub configuration status and return setup instructions if GITHUB_TOKEN is missing."""
```

**Return type**: `dict`

**Implementation contract**:

```text
1. Attempt: result = await asyncio.to_thread(operations.check_github_setup, output=out)
   Note: if operations.check_github_setup does not exist yet, raise NotImplementedError
   with message "check_github_setup not yet implemented in operations.py — add this function."
   Do NOT silently substitute another operation or fabricate a result.

2. Return {**result, **out.to_dict()} on success.

3. Catch BacklogError as e:
       Return {"error": str(e), **out.to_dict()}
```

**IMPORTANT**: Before implementing `backlog_setup_github`, verify that
`operations.check_github_setup` exists by reading `.claude/skills/backlog/backlog_core/operations.py`
and searching for `def check_github_setup`. If it does not exist, add it to the operations module
as a separate task — do not implement it inline in server.py, and do not call a different function
as a substitute. Raise `NotImplementedError` as specified above so the gap surfaces at test time.

---

## Section 3: Complete Function Inventory After This Feature

After merging this feature, `server.py` contains:

```text
Tools (10, unchanged):
  backlog_add, backlog_list, backlog_view, backlog_sync, backlog_close,
  backlog_resolve, backlog_update, backlog_groom, backlog_normalize, backlog_pull

Prompts (5, new):
  backlog_guide, create_item_guided, groom_item, work_item, close_or_resolve

Guided tools (2, new):
  backlog_add_guided, backlog_setup_github
```

Total: 17 registered MCP components.

---

## Section 4: Architectural Constraints

### 4.1 No logic in server.py beyond delegation

Server functions must not contain business logic. They call `operations.*` (via
`asyncio.to_thread` when the operation is sync) and format the result. All parsing,
GitHub API calls, file I/O, and validation live in `operations.py`.

### 4.2 Output collector pattern

Every function that calls `operations.*` must instantiate `out = Output()` and pass it.
Return `{**result, **out.to_dict()}` on success, `{"error": str(e), **out.to_dict()}` on
`BacklogError`. This is the existing pattern from all 10 tools — do not deviate.

### 4.3 Async vs sync

| Function | async? | Reason |
|---|---|---|
| `backlog_guide` | No | Pure string, no I/O |
| `create_item_guided` | No | Pure string, no I/O |
| `groom_item` | Yes | Calls operations.view_item via asyncio.to_thread |
| `work_item` | Yes | Calls operations.view_item via asyncio.to_thread |
| `close_or_resolve` | Yes | Calls operations.view_item via asyncio.to_thread |
| `backlog_add_guided` | Yes | Calls ctx.elicit (awaitable) |
| `backlog_setup_github` | Yes | Calls operations.check_github_setup via asyncio.to_thread |

FastMCP runs sync prompt/tool functions in a threadpool automatically. Only use `async def`
when the function body contains `await`.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/prompts.mdx` — "Synchronous functions
automatically run in a threadpool to avoid blocking the event loop." (read 2026-03-06)

### 4.4 Prerequisite: issue #472

All existing tool functions in `server.py` must be `async def` before this feature lands.
The dynamic prompts (`groom_item`, `work_item`, `close_or_resolve`) and guided tools use
`await asyncio.to_thread(...)` and `await ctx.elicit(...)`. If the file still has sync tool
functions at implementation time, convert them first as part of the #472 scope, then add
the new functions.

### 4.5 NotSupportedError import path

Import `NotSupportedError` from `fastmcp.server.elicitation`, not from `fastmcp` directly.

```python
from fastmcp.server.elicitation import NotSupportedError
```

SOURCE: `.claude/worktrees/fastmcp/docs/v2/servers/elicitation.mdx` (read 2026-03-06) —
example imports show `from fastmcp.server.elicitation import AcceptedElicitation, ...`

### 4.6 dataclass placement

`AddItemRequest` must be defined at module level in `server.py`, above `backlog_add_guided`.
Do not define it inside the function — FastMCP introspects the type annotation at registration
time and requires a resolvable module-level name.

### 4.7 Message constructor

`Message` takes positional `content` and optional keyword `role`:

```python
Message("text content")                          # role defaults to "user"
Message("text content", role="assistant")        # explicit assistant role
```

SOURCE: `.claude/worktrees/fastmcp/docs/servers/prompts.mdx` — "Message accepts two fields:
content (Any) and role (Literal['user', 'assistant'], default 'user')" (read 2026-03-06)

---

## Section 5: Verification Requirements

After implementing all 9 functions, verify:

1. `uv run prek run --files .claude/skills/backlog/backlog_core/server.py` — passes with no
   ruff or type-check errors.
2. The MCP server starts without error:
   `uv run python -c "from .claude.skills.backlog.backlog_core.server import mcp; print(len(mcp.tools), len(mcp.prompts))"`
   — or equivalent import path. Expected output: `10 5`.
3. Each prompt function is callable in isolation:
   - `backlog_guide()` returns a non-empty string.
   - `create_item_guided()` returns a non-empty string.
4. `backlog_add_guided` with a mock context that returns `action="decline"` returns
   `{"messages": ["Item creation declined by user."], "warnings": []}`.
5. No `from __future__ import annotations` conflict with dataclass field evaluation — confirm
   that `AddItemRequest` fields resolve correctly under `from __future__ import annotations`.
   If there is a conflict, wrap the Literal types in string quotes or remove the future import.

---

## Section 6: Files Modified

| File | Change |
|---|---|
| `.claude/skills/backlog/backlog_core/server.py` | Add imports, AddItemRequest dataclass, 5 prompts, 2 guided tools |

No other files are modified by this feature. If `operations.check_github_setup` does not exist,
adding it to `operations.py` is a separate prerequisite task.
