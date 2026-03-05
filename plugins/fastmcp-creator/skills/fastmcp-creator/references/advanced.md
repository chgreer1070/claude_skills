# FastMCP Advanced Features Reference

Background tasks, server-side elicitation, and advanced execution patterns — use this when building tools that run for seconds or minutes, require multi-turn user interaction, or need fine-grained execution control.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

---

## Background Tasks

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

CONSTRAINT: Background tasks require the `tasks` optional extra. Install with:

```bash
pip install "fastmcp[tasks]"
```

RULE: Use `task=True` as the v3 pattern for background task support. `task=True` enables background execution — clients may request it or call the tool synchronously.

```python
import asyncio
from fastmcp import FastMCP

mcp = FastMCP("MyServer")

@mcp.tool(task=True)
async def slow_computation(duration: int) -> str:
    """A long-running operation."""
    for i in range(duration):
        await asyncio.sleep(1)
    return f"Completed in {duration} seconds"
```

CONSTRAINT: Background tasks require async functions. Using `task=True` with a sync function raises `ValueError` at registration time.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

PATTERN: Enable background tasks globally for all server components:

```python
mcp = FastMCP("MyServer", tasks=True)
```

CONSTRAINT: If any synchronous tools exist on a server with `tasks=True`, those must explicitly set `task=False` to avoid errors.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

### Progress Reporting

PATTERN: Inject the `Progress` dependency to report progress back to clients during task execution:

```python
from fastmcp import FastMCP
from fastmcp.dependencies import Progress

mcp = FastMCP("MyServer")

@mcp.tool(task=True)
async def process_files(files: list[str], progress: Progress = Progress()) -> str:
    await progress.set_total(len(files))

    for file in files:
        await progress.set_message(f"Processing {file}")
        # ... do work ...
        await progress.increment()

    return f"Processed {len(files)} files"
```

Progress API:

- `await progress.set_total(n)` — set the total number of steps
- `await progress.increment(amount=1)` — increment progress counter
- `await progress.set_message(text)` — update the status message

RULE: Progress works in both immediate and background execution modes — use the same code regardless of how the client invokes the function.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

### Task Backends

PATTERN: Default is in-memory backend — zero configuration, no external dependencies. Limitations: ephemeral (tasks lost on restart), ~250ms pickup latency, no horizontal scaling.

PATTERN: Redis backend for production — configure via environment variable:

```bash
export FASTMCP_DOCKET_URL=redis://localhost:6379
```

Redis advantages: persistent across restarts, single-digit millisecond pickup latency, horizontal scaling.

PATTERN: Add additional workers via CLI for horizontal scaling (Redis backend required):

```bash
fastmcp tasks worker server.py
```

Configure worker concurrency:

```bash
export FASTMCP_DOCKET_CONCURRENCY=20
fastmcp tasks worker server.py
```

CONSTRAINT: Task-enabled components must be defined at server startup. Components added dynamically after the server starts are not available for background execution.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

### Advanced Docket Dependencies

PATTERN: Access Docket instance and worker metadata from within tasks:

```python
from docket import Docket, Worker
from fastmcp import FastMCP
from fastmcp.dependencies import Progress, CurrentDocket, CurrentWorker

mcp = FastMCP("MyServer")

@mcp.tool(task=True)
async def my_task(
    progress: Progress = Progress(),
    docket: Docket = CurrentDocket(),
    worker: Worker = CurrentWorker(),
) -> str:
    # Schedule additional background work
    await docket.add(another_task, arg1, arg2)
    worker_name = worker.name
    return "Done"
```

SOURCE: `.claude/worktrees/fastmcp/docs/servers/tasks.mdx` (accessed 2026-03-05)

---

## Server-Side Elicitation

SOURCE: `.claude/worktrees/fastmcp/docs/servers/elicitation.mdx` (accessed 2026-03-05)

PATTERN: Use `ctx.elicit()` to request structured input from users mid-execution. The tool pauses until the client provides a response.

```python
from fastmcp import FastMCP, Context
from dataclasses import dataclass

mcp = FastMCP("Elicitation Server")

@dataclass
class UserInfo:
    name: str
    age: int

@mcp.tool
async def collect_user_info(ctx: Context) -> str:
    result = await ctx.elicit(
        message="Please provide your information",
        response_type=UserInfo
    )

    if result.action == "accept":
        user = result.data
        return f"Hello {user.name}, you are {user.age} years old"
    elif result.action == "decline":
        return "Information not provided"
    else:  # cancel
        return "Operation cancelled"
```

Elicitation result actions:

- `accept` — user provided valid input; data in `result.data`
- `decline` — user chose not to provide information
- `cancel` — user cancelled the entire operation

SOURCE: `.claude/worktrees/fastmcp/docs/servers/elicitation.mdx` (accessed 2026-03-05)

### Pattern Matching

PATTERN: Use typed result classes for pattern matching:

```python
from fastmcp.server.elicitation import (
    AcceptedElicitation,
    DeclinedElicitation,
    CancelledElicitation,
)

@mcp.tool
async def pattern_example(ctx: Context) -> str:
    result = await ctx.elicit("Enter your name:", response_type=str)

    match result:
        case AcceptedElicitation(data=name):
            return f"Hello {name}!"
        case DeclinedElicitation():
            return "No name provided"
        case CancelledElicitation():
            return "Operation cancelled"
```

SOURCE: `.claude/worktrees/fastmcp/docs/servers/elicitation.mdx` (accessed 2026-03-05)

### Multi-Turn Elicitation

PATTERN: Make multiple `ctx.elicit()` calls to gather information progressively:

```python
@mcp.tool
async def plan_meeting(ctx: Context) -> str:
    title_result = await ctx.elicit("What's the meeting title?", response_type=str)
    if title_result.action != "accept":
        return "Meeting planning cancelled"

    duration_result = await ctx.elicit("Duration in minutes?", response_type=int)
    if duration_result.action != "accept":
        return "Meeting planning cancelled"

    priority_result = await ctx.elicit(
        "Is this urgent?",
        response_type=["yes", "no"]
    )
    if priority_result.action != "accept":
        return "Meeting planning cancelled"

    urgent = priority_result.data == "yes"
    return f"Meeting '{title_result.data}' for {duration_result.data} minutes (Urgent: {urgent})"
```

SOURCE: `.claude/worktrees/fastmcp/docs/servers/elicitation.mdx` (accessed 2026-03-05)

### Elicitation Response Types

PATTERN: Scalar types — FastMCP automatically wraps them in MCP-compatible object schemas:

```python
result = await ctx.elicit("What's your name?", response_type=str)
result = await ctx.elicit("Pick a number!", response_type=int)
result = await ctx.elicit("True or false?", response_type=bool)
```

PATTERN: Constrained choices using list of strings, `Literal`, or Python enum:

```python
from typing import Literal

result = await ctx.elicit(
    "What priority level?",
    response_type=["low", "medium", "high"],
)

result = await ctx.elicit(
    "What priority level?",
    response_type=Literal["low", "medium", "high"]
)
```

PATTERN: Multi-select — wrap choices in an additional list level (available in v2.14.0+):

```python
result = await ctx.elicit(
    "Choose tags",
    response_type=[["bug", "feature", "documentation"]]  # List of a list
)
```

PATTERN: Titled options for better UI display (SEP-1330 compliant, available in v2.14.0+):

```python
result = await ctx.elicit(
    "What priority level?",
    response_type={
        "low": {"title": "Low Priority"},
        "medium": {"title": "Medium Priority"},
        "high": {"title": "High Priority"}
    }
)
```

PATTERN: Structured responses via dataclass or Pydantic model:

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class TaskDetails:
    title: str
    description: str
    priority: Literal["low", "medium", "high"]
    due_date: str

result = await ctx.elicit(
    "Please provide task details",
    response_type=TaskDetails
)
```

CONSTRAINT: MCP spec only supports shallow objects with scalar (`string`, `number`, `boolean`) or enum properties. Nested objects are not supported.

PATTERN: Default values for elicitation fields — pre-populate form fields (available in v2.14.0+):

```python
from pydantic import BaseModel, Field
from enum import Enum

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskDetails(BaseModel):
    title: str = Field(description="Task title")
    description: str = Field(default="", description="Task description")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority")

result = await ctx.elicit("Please provide task details", response_type=TaskDetails)
```

PATTERN: Approval-only elicitation (no data needed) — pass `None` as response type:

```python
result = await ctx.elicit("Approve this action?", response_type=None)

if result.action == "accept":
    return do_action()
else:
    raise ValueError("Action rejected")
```

CONSTRAINT: Elicitation requires the client to implement an elicitation handler. If the client does not support elicitation, calls to `ctx.elicit()` raise an error. See [./client-sdk.md](./client-sdk.md) for client-side elicitation handler implementation.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/elicitation.mdx` (accessed 2026-03-05)
