# FastMCP v3 Transforms Reference

How transforms modify components as they flow from providers to clients. Covers all five built-in transforms and custom transform authoring.

SOURCE: `.claude/worktrees/fastmcp/docs/servers/transforms/transforms.mdx`, `namespace.mdx`, `tool-transformation.mdx`, `resources-as-tools.mdx`, `prompts-as-tools.mdx`, `.claude/worktrees/fastmcp/docs/servers/authorization.mdx` (visibility/Enabled) (accessed 2026-03-05)

---

## Mental Model

Transforms are filters in a pipeline. Components flow from providers through transforms to reach clients:

```text
Provider -> [Transform A] -> [Transform B] -> Client
```

When listing components, transforms receive sequences and return transformed sequences. When a client requests a component by name, transforms work in reverse — mapping the client's requested name back to the original.

---

## Built-in Transforms (v3.0.0)

FastMCP provides exactly five built-in transforms:

| Transform | Purpose |
|-----------|---------|
| `Namespace` | Prefix component names to prevent conflicts |
| `ToolTransform` | Rename tools, modify descriptions, reshape arguments |
| `Enabled` (visibility) | Control which components are visible at runtime |
| `ResourcesAsTools` | Expose resources to tool-only clients |
| `PromptsAsTools` | Expose prompts to tool-only clients |

---

## Namespace Transform

RULE: Use `Namespace` to prefix all component names from a provider or server. The most common use is through `mcp.mount(server, namespace="name")`.

```python
from fastmcp import FastMCP

weather = FastMCP("Weather")
calendar = FastMCP("Calendar")

@weather.tool
def get_data() -> str:
    return "Weather data"

@calendar.tool
def get_data() -> str:
    return "Calendar data"

# Without namespacing, both tools are named "get_data" — conflict
main = FastMCP("Main")
main.mount(weather, namespace="weather")
main.mount(calendar, namespace="calendar")

# Clients see: weather_get_data, calendar_get_data
```

Naming rules:

| Component | Original | With `Namespace("api")` |
|-----------|----------|-------------------------|
| Tool | `my_tool` | `api_my_tool` |
| Prompt | `my_prompt` | `api_my_prompt` |
| Resource | `data://info` | `data://api/info` |
| Template | `data://{id}` | `data://api/{id}` |

PATTERN: Apply `Namespace` directly using `mcp.add_transform()` or `provider.add_transform()` for explicit control.

```python
from fastmcp.server.transforms import Namespace

mcp = FastMCP("Server")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

mcp.add_transform(Namespace("v1"))

# Tool is now: v1_greet
```

---

## ToolTransform

`ToolTransform` modifies tool schemas as they flow through a provider. Provide a dictionary mapping original tool names to their `ToolTransformConfig`.

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig

mcp = FastMCP("Server")

@mcp.tool
def verbose_internal_data_fetcher(query: str) -> str:
    """Fetches data from the internal database."""
    return f"Results for: {query}"

mcp.add_transform(ToolTransform({
    "verbose_internal_data_fetcher": ToolTransformConfig(
        name="search",
        description="Search the database.",
    )
}))

# Clients see "search" with the cleaner description
```

PATTERN: Use `Tool.from_tool()` for immediate transformation when you have direct access to the tool object.

```python
from fastmcp.tools import Tool, tool
from fastmcp.tools.tool_transform import ArgTransform

@tool
def search(q: str, limit: int = 10) -> list[str]:
    """Search for items."""
    return [f"Result {i} for {q}" for i in range(limit)]

better_search = Tool.from_tool(
    search,
    name="find_items",
    description="Find items matching your search query.",
    transform_args={
        "q": ArgTransform(name="query", description="The search terms to look for."),
        "limit": ArgTransform(name="max_results"),
    },
)

mcp = FastMCP("Server")
mcp.add_tool(better_search)
```

### Tool-Level Modification Options

| Option | Description |
|--------|-------------|
| `name` | New name for the tool |
| `description` | New description |
| `title` | Human-readable title |
| `tags` | Set of tags for categorization |
| `annotations` | MCP ToolAnnotations |
| `meta` | Custom metadata dictionary |
| `enabled` | Whether the tool is visible to clients |

### Argument-Level Options (via ArgTransform)

| Option | Description |
|--------|-------------|
| `name` | Rename the argument |
| `description` | New description |
| `default` | New default value |
| `default_factory` | Callable that generates a default (requires `hide=True`) |
| `hide` | Remove from client-visible schema (inject as constant) |
| `required` | Make an optional argument required |
| `type` | Change the argument's type |

PATTERN: Hide arguments to inject constants or secrets.

```python
from fastmcp.tools.tool_transform import ArgTransform
import uuid

transform_args = {
    "api_key": ArgTransform(hide=True, default="secret-key"),
    "request_id": ArgTransform(hide=True, default_factory=lambda: str(uuid.uuid4())),
}
```

CONSTRAINT: `default_factory` requires `hide=True`. Visible arguments need static defaults representable in JSON Schema.

### Custom Transform Functions

For advanced scenarios, provide a `transform_fn` that intercepts tool execution.

```python
from fastmcp.tools import Tool, tool
from fastmcp.tools.tool_transform import forward, ArgTransform

@tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    return a / b

async def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        raise ValueError("Cannot divide by zero")
    return await forward(numerator=numerator, denominator=denominator)

safe_division = Tool.from_tool(
    divide,
    name="safe_divide",
    transform_fn=safe_divide,
    transform_args={
        "a": ArgTransform(name="numerator"),
        "b": ArgTransform(name="denominator"),
    },
)
```

`forward()` handles argument mapping automatically using transformed names. Use `forward_raw()` for direct calls with original parameter names.

---

## Enabled (Visibility Transform)

FastMCP uses enable/disable APIs to control component visibility at runtime. Disabled components do not appear in list responses and cannot be called.

```python
from fastmcp import FastMCP

mcp = FastMCP("MyServer")

@mcp.tool(tags={"admin"})
def delete_all() -> str:
    return "Deleted"

@mcp.tool(tags={"public"})
def get_status() -> str:
    return "OK"

# Disable by tag
mcp.disable(tags={"admin"})

# Disable by component key
mcp.disable(keys={"tool:delete_all"})

# Allowlist: only enable components with specific tags
mcp.enable(tags={"public"}, only=True)
```

PATTERN: Control visibility per-session using `ctx.enable_components()` and `ctx.disable_components()` from within a tool.

```python
from fastmcp import FastMCP, Context

@mcp.tool
async def activate_namespace(namespace: str, ctx: Context) -> str:
    """Enable all tools in the given namespace tag."""
    await ctx.enable_components(tags={namespace})
    return f"Enabled components tagged '{namespace}'"
```

RULE: Component-level `enabled=False` on decorators is deprecated in v3.0.0. Use `mcp.disable()` instead.

---

## ResourcesAsTools

`ResourcesAsTools` bridges the gap for tool-only clients that cannot use the MCP resource protocol. It generates two tools that clients can call:

- `list_resources` — returns JSON describing all available resources and templates
- `read_resource` — reads a specific resource by URI

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import ResourcesAsTools

mcp = FastMCP("My Server")

@mcp.resource("config://app")
def app_config() -> str:
    """Application configuration."""
    return '{"app_name": "My App", "version": "1.0.0"}'

@mcp.resource("user://{user_id}/profile")
def user_profile(user_id: str) -> str:
    """Get a user's profile by ID."""
    return f'{{"user_id": "{user_id}"}}'

# Add the transform — creates list_resources and read_resource tools
mcp.add_transform(ResourcesAsTools(mcp))
```

PATTERN: `list_resources` output distinguishes static resources (field `"uri"`) from templates (field `"uri_template"`).

PATTERN: Binary resources are automatically base64-encoded in `read_resource` responses.

---

## PromptsAsTools

`PromptsAsTools` bridges the gap for tool-only clients that cannot use the MCP prompt protocol. It generates two tools:

- `list_prompts` — returns JSON describing all prompts and their arguments
- `get_prompt` — renders a specific prompt with provided arguments

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import PromptsAsTools

mcp = FastMCP("My Server")

@mcp.prompt
def analyze_code(code: str, language: str = "python") -> str:
    """Analyze code for potential issues."""
    return f"Analyze this {language} code:\n{code}"

# Add the transform — creates list_prompts and get_prompt tools
mcp.add_transform(PromptsAsTools(mcp))
```

---

## Provider-Level vs Server-Level Transforms

Transforms can be applied at two levels.

**Provider-level**: Affects only components from that provider. Runs first.

```python
from fastmcp.server.providers import FastMCPProvider
from fastmcp.server.transforms import Namespace, ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig

sub_server = FastMCP("Sub")

@sub_server.tool
def process(data: str) -> str:
    return f"Processed: {data}"

provider = FastMCPProvider(sub_server)
provider.add_transform(Namespace("api"))
provider.add_transform(ToolTransform({
    "api_process": ToolTransformConfig(description="Process data through the API"),
}))

main = FastMCP("Main", providers=[provider])
# Tool is now: api_process with updated description
```

PATTERN: The `mount()` method returns a provider reference, letting you add transforms directly.

```python
main = FastMCP("Main")
mount = main.mount(sub_server, namespace="api")
mount.add_transform(ToolTransform({...}))
```

**Server-level**: Affects all components from all providers. Runs after provider transforms.

```python
# API versioning — prefix all tools
mcp.add_transform(Namespace("v1"))
```

### Transform Order

Transforms stack in the order added. First added is innermost (closest to the provider).

```python
provider.add_transform(Namespace("api"))           # Applied first
provider.add_transform(ToolTransform({             # Sees namespaced names
    "api_verbose_name": ToolTransformConfig(name="short"),
}))

# Flow: "verbose_name" -> "api_verbose_name" -> "short"
```

---

## Custom Transforms

Subclass `Transform` and override the methods you need. Leave unneeded methods as the pass-through default.

```python
from collections.abc import Sequence
from fastmcp.server.transforms import Transform, GetToolNext
from fastmcp.tools.tool import Tool

class TagFilter(Transform):
    """Filter tools to only those with specific tags."""

    def __init__(self, required_tags: set[str]):
        self.required_tags = required_tags

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        return [t for t in tools if t.tags & self.required_tags]

    async def get_tool(self, name: str, call_next: GetToolNext) -> Tool | None:
        tool = await call_next(name)
        if tool and tool.tags & self.required_tags:
            return tool
        return None
```

Transform method signatures:

| Method | Pattern | Purpose |
|--------|---------|---------|
| `list_tools(tools)` | Pure function | Transform the sequence of tools |
| `get_tool(name, call_next)` | Middleware | Transform lookup by name |
| `list_resources(resources)` | Pure function | Transform the sequence of resources |
| `get_resource(uri, call_next)` | Middleware | Transform lookup by URI |
| `list_prompts(prompts)` | Pure function | Transform the sequence of prompts |
| `get_prompt(name, call_next)` | Middleware | Transform lookup by name |

RULE: When implementing `get_*` methods, use `call_next` for routing. Map the client's requested name back to the original before calling `call_next()`.

---

## Cross-Reference

- Provider configuration: [./providers.md](./providers.md)
- Server core setup: [./server-core.md](./server-core.md)
- Scope-based auth (restricts visibility by scope): [./auth.md](./auth.md)
