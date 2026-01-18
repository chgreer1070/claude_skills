# Skill Reference

This document provides detailed information about the fastmcp-creator skill included in this plugin.

## fastmcp-creator

**Location**: `skills/fastmcp-creator/SKILL.md`

**Description**: Build Model Context Protocol (MCP) servers - comprehensive coverage of generic MCP protocol AND FastMCP framework specialization. Use when creating any MCP server (Python FastMCP preferred, TypeScript/Node also covered). Includes agent-centric design principles, evaluation creation, Pydantic/Zod validation, async patterns, STDIO/HTTP/SSE transports, FastMCP Cloud deployment, .mcpb packaging, security patterns, and mid-2025+ community practices. Standalone skill with no external dependencies.

**User Invocable**: Yes (default)

**Allowed Tools**: Not restricted - inherits from session

**Model**: Not specified - inherits from session

**Context**: inline (default)

### When to Use

Activate this skill when you need to:

- Build a new MCP server from scratch
- Implement MCP tools for any API or service
- Follow agent-centric design principles for AI tools
- Add proper validation with Pydantic (Python) or Zod (TypeScript)
- Create comprehensive evaluations to test server effectiveness
- Learn FastMCP decorators and patterns
- Implement TypeScript MCP servers with the official SDK
- Package servers with .mcpb for Claude Desktop distribution
- Apply security, performance, and observability best practices
- Deploy to FastMCP Cloud or production environments

**Trigger Keywords**: MCP server, Model Context Protocol, FastMCP, agent tools, server development, tool creation, API integration

### Activation

```
# Automatic activation (preferred)
"Build an MCP server for Slack"
"Create FastMCP tools for database access"
"Add evaluations to my MCP server"

# Manual activation
@fastmcp-creator

# Programmatic activation
Skill(command: "fastmcp-creator")
```

### Workflow Phases

The skill guides you through a structured 4-phase workflow:

#### Phase 1: Deep Research and Planning

**Agent-Centric Design Principles**:
- Build for workflows, not just API endpoints
- Optimize for limited AI context windows
- Design actionable error messages that guide agents
- Follow natural task subdivisions
- Use evaluation-driven development

**Research Process**:
1. Study MCP protocol documentation
2. Study framework documentation (FastMCP or TypeScript SDK)
3. Exhaustively study target API documentation
4. Create comprehensive implementation plan

**Tool Preferences for Research**:
1. `mcp__Ref__ref_search_documentation` - High-fidelity verbatim docs
2. `mcp__exa__get_code_context_exa` - Code examples and patterns
3. `mcp__exa__web_search_exa` - LLM-optimized web results
4. WebFetch - Fallback only

#### Phase 2: Implementation

**Python (FastMCP) Pattern**:
```python
from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated

mcp = FastMCP("service_mcp")

@mcp.tool()
def tool_name(
    param: Annotated[str, Field(description="Parameter description")]
) -> dict:
    """Tool description for the AI."""
    return {"result": "value"}

if __name__ == "__main__":
    mcp.run()  # STDIO transport
```

**TypeScript Pattern**:
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "service-mcp-server",
  version: "1.0.0",
});

const InputSchema = z.object({
  param: z.string().describe("Parameter description"),
}).strict();

server.registerTool(
  "tool_name",
  {
    title: "Tool Title",
    description: "Tool description for the AI",
    inputSchema: InputSchema,
    annotations: { readOnlyHint: true },
  },
  async (params) => {
    return { content: [{ type: "text", text: "result" }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

**Python Project Setup Note**: The skill activates the `python3-development` skill when setting up Python projects to ensure proper project structure, pyproject.toml configuration, and modern Python patterns.

#### Phase 3: Review and Refine

**Code Quality Checklist**:
- [ ] DRY Principle: No duplicated code between tools
- [ ] Composability: Shared logic extracted into functions
- [ ] Consistency: Similar operations return similar formats
- [ ] Error Handling: All external calls have error handling
- [ ] Type Safety: Full type coverage
- [ ] Documentation: Comprehensive docstrings/descriptions

**Testing Approach**:
- **DON'T** run MCP servers directly (they hang indefinitely)
- **DO** use syntax checking: `python -m py_compile server.py`
- **DO** use evaluation harness for functional testing
- **DO** run in tmux/screen for interactive testing
- **DO** use timeout for quick checks: `timeout 5s python server.py`

#### Phase 4: Create Evaluations

**Purpose**: Test whether LLMs can effectively use your MCP server to answer realistic, complex questions.

**Evaluation Process**:
1. Tool inspection - List available tools
2. Content exploration - Use read-only operations
3. Question generation - Create 10 complex, realistic questions
4. Answer verification - Solve each question to verify answers

**Question Requirements**:
- Independent (not dependent on other questions)
- Read-only (non-destructive operations only)
- Complex (requiring multiple tool calls)
- Realistic (based on real use cases)
- Verifiable (single, clear answer)
- Stable (answer won't change over time)

**Output Format**:
```xml
<evaluation>
  <qa_pair>
    <question>Complex question requiring multiple tool calls</question>
    <answer>Single verifiable answer</answer>
  </qa_pair>
</evaluation>
```

### Reference Files

The skill includes 8 comprehensive reference documents loaded progressively on demand:

**[mcp-best-practices.md](../skills/fastmcp-creator/references/mcp-best-practices.md)**
- Universal MCP guidelines for all implementations
- Naming conventions and tool design patterns
- Response formats and pagination
- Security and compliance requirements

**[development-guidelines.md](../skills/fastmcp-creator/references/development-guidelines.md)**
- Complete FastMCP development guide
- Decorators: @mcp.tool(), @mcp.resource(), @mcp.prompt()
- Pydantic validation with Field() constraints
- Async patterns and error handling
- Context parameters and annotations
- Transport options (STDIO, HTTP, SSE)
- Production deployment

**[typescript-mcp-server.md](../skills/fastmcp-creator/references/typescript-mcp-server.md)**
- Complete TypeScript/Node implementation guide
- Project structure and build configuration
- registerTool patterns with full type safety
- Zod validation schemas with .strict()
- Error handling and production builds

**[community-practices.md](../skills/fastmcp-creator/references/community-practices.md)**
- Mid-2025+ best practices from the community
- .mcpb packaging for Claude Desktop
- Security by design patterns
- Observability and testing approaches
- Performance tuning and caching
- Ecosystem compatibility
- Agent orchestration patterns

**[prompts-and-templates.md](../skills/fastmcp-creator/references/prompts-and-templates.md)**
- FastMCP @mcp.prompt() decorator usage
- System instructions for tool use
- Configuration for AI-native tools
- Prompt engineering for MCP servers

**[example-projects.md](../skills/fastmcp-creator/references/example-projects.md)**
- Real-world FastMCP implementations
- Ultimate MCP Server (AI Agent OS)
- Hugging Face MCP server
- Browser automation servers
- Data/DevOps integrations
- Coding assistants
- Templates and aggregators

**[evaluation-guide.md](../skills/fastmcp-creator/references/evaluation-guide.md)**
- Complete evaluation creation guide
- Question guidelines and requirements
- Answer verification process
- Output format specification
- Examples and anti-patterns

**[accessing_online_resources.md](../skills/fastmcp-creator/references/accessing_online_resources.md)** (symlinked)
- Best practices for web research
- Tool preferences for documentation
- High-fidelity vs summarized sources

### Scripts and Tools

**Evaluation Harness** (`scripts/evaluation.py`):
- Tests MCP server effectiveness with LLMs
- Supports STDIO and HTTP transports
- Validates answers against expected results
- Provides pass/fail metrics

**Usage**:
```bash
pip install -r scripts/requirements.txt
export ANTHROPIC_API_KEY=your_api_key

python scripts/evaluation.py \
  -t stdio \
  -c python \
  -a my_server.py \
  evaluation.xml
```

**Supporting Files**:
- `connections.py` - MCP connection utilities
- `example_evaluation.xml` - Example evaluation format
- `requirements.txt` - Python dependencies

### Best Practices Summary

**Tool Design**:
- Use service prefix: `{service}_{action}_{resource}`
- Design for workflows, not API endpoints
- Optimize for AI context efficiency
- Provide actionable error messages

**Input/Output**:
- Support JSON and Markdown formats
- Implement pagination for lists
- Enforce CHARACTER_LIMIT (typically 25,000)
- Use human-readable identifiers

**Validation**:
- Python: Pydantic Field() with constraints
- TypeScript: Zod schemas with .strict()
- Validate all inputs against schema
- Sanitize file paths and identifiers

**Error Handling**:
- Don't expose internal errors
- Provide clear, actionable messages
- Use ToolError for business logic errors
- Handle timeouts and rate limits

**Security**:
- Validate file paths against allowed directories
- Use confirmation flags for destructive operations
- Set destructiveHint annotation for state changes
- Rate limit expensive operations
- Store secrets in environment variables

**Performance**:
- Use async for I/O-bound operations
- Cache repeated queries with lru_cache
- Stream large responses in HTTP mode
- Extract common functionality into reusable functions

**Deployment**:
- Package as .mcpb for Claude Desktop
- Provide manifest.json with user_config fields
- Support environment variable configuration
- Test with evaluation harness before release

### Standalone Operation

This skill is completely self-contained:
- ✅ All generic MCP best practices included
- ✅ All FastMCP Python patterns included
- ✅ All TypeScript/Node patterns included
- ✅ All evaluation creation guidance included
- ✅ All security, performance, and observability patterns included
- ✅ All community practices and .mcpb packaging included
- ✅ All scripts and evaluation harness included
- ✅ All reference files self-contained
- ✅ No references to external skills (except python3-development for project setup)

### Related Skills

**python3-development**: Automatically activated for Python project setup, providing:
- Python project layouts (src/ vs flat)
- pyproject.toml structure with uv
- Modern Python 3.11+ patterns
- Package structure best practices
- Build/publishing guides

### Integration with Claude Code

**Progressive Disclosure**: Reference files are loaded on demand rather than all at once, keeping context efficient:
- Protocol basics loaded for all MCP work
- FastMCP patterns loaded for Python implementation
- TypeScript patterns loaded for Node implementation
- Evaluation guide loaded during testing phase
- Community practices loaded for deployment questions

**No Hooks**: This skill doesn't configure any hooks, allowing it to work seamlessly in any environment without modifying tool behavior.

**No Model Override**: Inherits the session's model selection, working with any Claude model.

**No Tool Restrictions**: Can use any tools available in the session, enabling flexibility for research, implementation, and testing.
