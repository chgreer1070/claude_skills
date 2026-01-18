# Quick Start Guide

Get started building MCP servers with the fastmcp-creator plugin in minutes.

## Prerequisites

- Claude Code 2.1+
- Python 3.11+ (for FastMCP) or Node.js 18+ (for TypeScript)
- Basic understanding of REST APIs
- API credentials for the service you want to integrate (optional)

## 5-Minute FastMCP Server

### Step 1: Install FastMCP

```bash
pip install fastmcp
```

### Step 2: Create Server File

Create `weather_mcp.py`:

```python
from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated

mcp = FastMCP("weather-server")

@mcp.tool()
def get_weather(
    city: Annotated[str, Field(description="City name (e.g., 'San Francisco')")],
    units: Annotated[str, Field(description="Units: 'celsius' or 'fahrenheit'")] = "celsius"
) -> dict:
    """Get current weather for a city."""
    # Mock implementation - replace with real API call
    return {
        "city": city,
        "temperature": 72 if units == "fahrenheit" else 22,
        "units": units,
        "conditions": "sunny"
    }

@mcp.tool()
def get_forecast(
    city: Annotated[str, Field(description="City name")],
    days: Annotated[int, Field(ge=1, le=7, description="Number of days (1-7)")] = 3
) -> dict:
    """Get weather forecast for upcoming days."""
    forecast = []
    for i in range(days):
        forecast.append({
            "day": i + 1,
            "high": 75,
            "low": 60,
            "conditions": "partly cloudy"
        })
    return {"city": city, "forecast": forecast}

if __name__ == "__main__":
    mcp.run()
```

### Step 3: Test Syntax

```bash
python -m py_compile weather_mcp.py
```

### Step 4: Use in Claude Desktop

Add to Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/absolute/path/to/weather_mcp.py"]
    }
  }
}
```

Restart Claude Desktop, and you now have weather tools available!

## Using the Plugin for Complex Servers

### Example: Build a GitHub MCP Server

```
You: Build a FastMCP server for GitHub that provides tools to:
- List repositories in an organization
- Get repository details (stars, forks, description)
- List open issues in a repository
- Search code across repositories

Claude: I'll help you build a comprehensive GitHub MCP server following
agent-centric design principles.

[Claude automatically activates fastmcp-creator skill and guides you through:]
1. Deep Research and Planning
   - Studies GitHub API documentation
   - Plans tool structure and workflows
   - Designs for AI context efficiency

2. Implementation
   - Creates FastMCP server with proper validation
   - Implements error handling and pagination
   - Optimizes response formats

3. Review and Refine
   - Checks code quality
   - Ensures consistency
   - Validates syntax

4. Create Evaluations
   - Generates 10 test questions
   - Verifies answers
   - Creates evaluation.xml
```

The skill handles all the complexity while you focus on your requirements.

## Common Patterns

### Pattern 1: Simple Tool

```python
@mcp.tool()
def simple_operation(param: str) -> dict:
    """Short description for AI."""
    return {"result": "value"}
```

### Pattern 2: Tool with Validation

```python
from typing import Annotated, Literal

@mcp.tool()
def validated_operation(
    count: Annotated[int, Field(ge=1, le=100, description="Count between 1-100")],
    format: Annotated[Literal["json", "markdown"], Field(description="Output format")] = "json"
) -> dict:
    """Operation with strict validation."""
    return {"count": count, "format": format}
```

### Pattern 3: Async Tool for API Calls

```python
import httpx

@mcp.tool()
async def fetch_data(url: str) -> dict:
    """Fetch data from external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Pattern 4: Tool with Pagination

```python
@mcp.tool()
def list_items(
    limit: Annotated[int, Field(ge=1, le=100)] = 50,
    offset: Annotated[int, Field(ge=0)] = 0
) -> dict:
    """List items with pagination."""
    items = get_all_items()  # Your data source
    paginated = items[offset:offset + limit]

    return {
        "items": paginated,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(items)
    }
```

### Pattern 5: Resource for Configuration

```python
@mcp.resource("config://settings")
def get_settings() -> dict:
    """Provide server configuration to AI."""
    return {
        "version": "1.0.0",
        "features": ["search", "list", "get"],
        "rate_limit": "100 requests/hour"
    }
```

### Pattern 6: Prompt for Common Workflows

```python
@mcp.prompt()
def analyze_repository(repo: str) -> str:
    """Generate prompt to analyze a repository."""
    return f"""Analyze the repository '{repo}' by:
1. Getting repository details (stars, forks, description)
2. Listing recent issues
3. Checking programming languages used
4. Summarizing the project's purpose and activity"""
```

## TypeScript Quick Start

### Step 1: Initialize Project

```bash
mkdir my-mcp-server
cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D @types/node typescript
npx tsc --init
```

### Step 2: Create Server

Create `src/server.ts`:

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "weather-server",
  version: "1.0.0",
});

const WeatherSchema = z.object({
  city: z.string().describe("City name (e.g., 'San Francisco')"),
  units: z.enum(["celsius", "fahrenheit"]).default("celsius"),
}).strict();

server.registerTool(
  "get_weather",
  {
    title: "Get Weather",
    description: "Get current weather for a city",
    inputSchema: WeatherSchema,
    annotations: { readOnlyHint: true },
  },
  async (params) => {
    const temp = params.units === "fahrenheit" ? 72 : 22;
    const result = {
      city: params.city,
      temperature: temp,
      units: params.units,
      conditions: "sunny",
    };

    return {
      content: [{
        type: "text",
        text: JSON.stringify(result, null, 2)
      }]
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Step 3: Build and Run

```bash
npx tsc
node dist/server.js
```

## Next Steps

### 1. Add Real API Integration

Replace mock data with actual API calls:

```python
import httpx
import os

API_KEY = os.getenv("SERVICE_API_KEY")

@mcp.tool()
async def real_api_call(param: str) -> dict:
    """Call external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.service.com/endpoint",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"param": param}
        )
        return response.json()
```

### 2. Add Error Handling

```python
from fastmcp import ToolError

@mcp.tool()
async def safe_operation(param: str) -> dict:
    """Operation with proper error handling."""
    try:
        result = await external_api_call(param)
        return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ToolError(f"Resource '{param}' not found. Try listing available resources first.")
        elif e.response.status_code == 429:
            raise ToolError("Rate limit exceeded. Please wait a moment and try again.")
        else:
            raise ToolError(f"API error: {e.response.status_code}")
    except Exception as e:
        raise ToolError(f"Operation failed. Please check your parameters and try again.")
```

### 3. Create Evaluations

```
You: Create comprehensive evaluations for my weather MCP server

Claude: [Activates fastmcp-creator skill and creates evaluation.xml with 10 questions]
```

Then test:

```bash
pip install -r plugins/fastmcp-creator/skills/fastmcp-creator/scripts/requirements.txt
export ANTHROPIC_API_KEY=your_key

python plugins/fastmcp-creator/skills/fastmcp-creator/scripts/evaluation.py \
  -t stdio \
  -c python \
  -a weather_mcp.py \
  evaluation.xml
```

### 4. Package for Distribution

For Python servers:

```python
# Add packaging configuration
# See Community Practices reference for .mcpb format
```

For TypeScript:

```bash
npm run build
npm publish
```

## Common Issues

### Import Error: `ModuleNotFoundError: No module named 'fastmcp'`

**Solution**:
```bash
pip install fastmcp
```

### Server Hangs When Testing

**Solution**: MCP servers are long-running processes. Don't run directly:
```bash
# ❌ DON'T
python my_server.py  # Hangs indefinitely

# ✅ DO
python -m py_compile my_server.py  # Syntax check
timeout 5s python my_server.py     # Quick test
tmux new -s mcp                    # Interactive testing
python my_server.py                # In tmux session
```

### Claude Can't Find My Tools

**Solution**: Check Claude Desktop config path is absolute:
```json
{
  "mcpServers": {
    "myserver": {
      "command": "python",
      "args": ["/Users/name/path/to/server.py"]  // Must be absolute
    }
  }
}
```

## Getting Help

### Ask the Plugin

```
"What are best practices for MCP tool naming?"
"How do I implement pagination in FastMCP?"
"Show me examples of async tool patterns"
"How do I handle rate limiting?"
```

The skill includes comprehensive references that Claude can access on demand.

### Reference Documentation

- [Skill Reference](./skill-reference.md) - Complete skill capabilities
- [Evaluation Harness Guide](./evaluation-harness.md) - Testing your server
- [MCP Best Practices](../skills/fastmcp-creator/references/mcp-best-practices.md) - Universal guidelines
- [FastMCP Development](../skills/fastmcp-creator/references/development-guidelines.md) - Python patterns
- [TypeScript Guide](../skills/fastmcp-creator/references/typescript-mcp-server.md) - Node patterns

### External Resources

- [MCP Protocol Docs](https://modelcontextprotocol.io)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)

## Examples Repository

The plugin includes detailed examples in [example-projects.md](../skills/fastmcp-creator/references/example-projects.md):

- Ultimate MCP Server (AI Agent OS)
- Hugging Face integration
- Browser automation
- Database integrations
- DevOps tools
- Coding assistants

Study these for patterns and best practices used in real-world servers.
