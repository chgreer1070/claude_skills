# Reference Materials

The fastmcp-creator skill includes a comprehensive reference library covering all aspects of MCP server development. These materials are loaded progressively on demand to keep Claude's context efficient.

## Reference Files Overview

| Reference | Size | Primary Focus | When Loaded |
|-----------|------|---------------|-------------|
| mcp-best-practices.md | ~16KB | Universal MCP guidelines | All MCP work |
| development-guidelines.md | ~16KB | FastMCP Python patterns | Python implementation |
| typescript-mcp-server.md | ~19KB | TypeScript/Node patterns | TypeScript implementation |
| community-practices.md | ~20KB | Mid-2025+ advanced patterns | Deployment & production |
| evaluation-guide.md | ~14KB | Testing with LLMs | Evaluation creation |
| example-projects.md | ~9KB | Real-world implementations | Learning & inspiration |
| prompts-and-templates.md | ~12KB | Prompt engineering | Advanced features |
| accessing_online_resources.md | ~varies | Web research best practices | Research phase |

**Total**: ~115KB of reference material loaded on demand

## Detailed Reference Summaries

### mcp-best-practices.md

**Universal MCP Server Guidelines**

**Coverage**:
- Tool naming conventions: `{service}_{action}_{resource}`
- Response format patterns (JSON and Markdown)
- Pagination and large dataset handling
- Error message design for LLMs
- Security and compliance requirements
- Tool description best practices
- Parameter validation patterns
- Resource and prompt design
- Transport considerations
- Testing and quality assurance

**Key Sections**:
- **Tool Design**: Workflow-oriented tools, not API wrappers
- **Naming Patterns**: Consistent prefixes for discoverability
- **Response Formats**: Support both JSON and Markdown
- **Pagination**: Limit/offset patterns with has_more flags
- **Error Handling**: Actionable messages that guide agents
- **Security**: Path validation, confirmation flags, rate limiting
- **Validation**: Schema-driven with clear constraints
- **Documentation**: 5-part tool description structure

**Applies To**: All MCP implementations regardless of language

**Source Citations**:
- Model Context Protocol Official Specification
- FastMCP framework patterns
- Community consensus from example projects

### development-guidelines.md

**Complete FastMCP Framework Guide (Python)**

**Coverage**:
- FastMCP installation and setup
- Decorator patterns: @mcp.tool(), @mcp.resource(), @mcp.prompt()
- Pydantic validation with Field() constraints
- Type hints with Annotated types
- Async patterns for I/O operations
- Error handling with ToolError
- Context parameters for server access
- Annotations (readOnlyHint, destructiveHint, etc.)
- Transport options: STDIO, HTTP, SSE
- Production deployment patterns
- Testing strategies
- Packaging and distribution

**Key Patterns**:

```python
# Basic tool
@mcp.tool()
def tool_name(
    param: Annotated[str, Field(description="Description")]
) -> dict:
    """Tool description for AI."""
    return {"result": "value"}

# Async tool
@mcp.tool()
async def async_tool(param: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Resource
@mcp.resource("config://settings")
def get_config() -> dict:
    return {"setting": "value"}

# Prompt
@mcp.prompt()
def workflow_prompt(context: str) -> str:
    return f"Analyze {context} by..."
```

**Applies To**: Python FastMCP implementations

**Source Citations**:
- FastMCP official documentation
- FastMCP GitHub repository examples
- Community best practices from real implementations

### typescript-mcp-server.md

**Complete TypeScript/Node MCP SDK Guide**

**Coverage**:
- TypeScript project setup and configuration
- MCP SDK installation and imports
- registerTool pattern with full type safety
- Zod schema validation with .strict()
- Error handling and type definitions
- Transport setup (STDIO and HTTP)
- Build and production deployment
- npm packaging and distribution
- Testing strategies for TypeScript
- Integration with Claude Desktop

**Key Patterns**:

```typescript
// Tool registration
const InputSchema = z.object({
  param: z.string().describe("Description")
}).strict();

server.registerTool(
  "tool_name",
  {
    title: "Tool Title",
    description: "Tool description for AI",
    inputSchema: InputSchema,
    annotations: { readOnlyHint: true }
  },
  async (params) => {
    return {
      content: [{
        type: "text",
        text: JSON.stringify(result, null, 2)
      }]
    };
  }
);

// Error handling
try {
  // operation
} catch (error) {
  return {
    content: [{
      type: "text",
      text: `Error: ${error.message}`
    }],
    isError: true
  };
}
```

**Applies To**: TypeScript/Node MCP implementations

**Source Citations**:
- MCP TypeScript SDK official documentation
- MCP TypeScript SDK GitHub repository
- Community examples and patterns

### community-practices.md

**Mid-2025+ Advanced Patterns and Best Practices**

**Coverage**:
- .mcpb packaging format for Claude Desktop distribution
- manifest.json structure with user_config fields
- Security by design patterns and threat modeling
- Observability: logging, metrics, tracing
- Testing strategies: unit, integration, evaluation
- Performance tuning and optimization
- Caching strategies (lru_cache, Redis, in-memory)
- Ecosystem compatibility (Claude Desktop, API, other clients)
- Agent orchestration patterns
- Production deployment checklist
- CI/CD integration
- Version management and updates

**Key Sections**:
- **.mcpb Packaging**: Single-file distribution with embedded manifest
- **Security Patterns**: Input validation, sandboxing, audit logging
- **Observability**: Structured logging with context, metrics collection
- **Performance**: Async by default, connection pooling, request batching
- **Testing**: Multi-layer approach with evaluation harness
- **Deployment**: Environment variables, health checks, graceful shutdown

**Advanced Patterns**:

```python
# Caching pattern
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param: str) -> dict:
    # Expensive computation
    return result

# Connection pooling
class APIClient:
    def __init__(self):
        self.session = httpx.AsyncClient()

    async def close(self):
        await self.session.aclose()

# Rate limiting
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=3600)
def rate_limited_operation():
    pass
```

**Applies To**: Production MCP servers in any language

**Source Citations**:
- FastMCP Cloud deployment docs
- Community best practices circa mid-2025
- Real-world production patterns
- Security frameworks and standards

### evaluation-guide.md

**Comprehensive Testing with LLMs**

**Coverage**:
- Evaluation philosophy and purpose
- Question generation guidelines
- Answer verification process
- XML format specification
- Evaluation harness usage
- Interpreting results
- Debugging failed evaluations
- Continuous improvement cycle
- Example evaluations for different domains

**Question Requirements**:
- **Independent**: Not dependent on other questions
- **Read-Only**: Non-destructive operations only
- **Complex**: Multiple tool calls required
- **Realistic**: Based on real use cases
- **Verifiable**: Single, clear answer
- **Stable**: Answer won't change over time

**Evaluation Process**:
1. Tool inspection - List available tools
2. Content exploration - Use read-only operations
3. Question generation - Create 10 complex questions
4. Answer verification - Solve each question yourself
5. XML generation - Format as evaluation file
6. Harness execution - Run with evaluation.py
7. Result analysis - Debug failures, iterate

**XML Format**:

```xml
<evaluation>
  <qa_pair>
    <question>Complex question requiring multiple tool calls</question>
    <answer>Single verifiable answer</answer>
  </qa_pair>
</evaluation>
```

**Applies To**: All MCP servers for quality validation

**Source Citations**:
- Anthropic evaluation best practices
- MCP testing patterns
- Real-world evaluation examples

### example-projects.md

**Real-World MCP Server Implementations**

**Coverage**:
- Ultimate MCP Server (AI Agent OS) - Comprehensive tool suite
- Hugging Face MCP - ML model integration
- Browser automation servers - Puppeteer/Playwright
- Database integrations - PostgreSQL, Redis
- DevOps tools - GitHub, GitLab, Kubernetes
- Coding assistants - Code analysis, generation
- Template servers - Starting points for new servers
- Aggregator patterns - Multiple service integration

**For Each Project**:
- Purpose and use cases
- Key tools provided
- Design patterns used
- Notable implementations
- Links to source code
- Lessons learned

**Example: Ultimate MCP Server**
- 50+ tools across multiple categories
- File system, web scraping, data analysis
- Database operations, API integrations
- Demonstrates tool composition patterns
- Shows how to handle large tool suites

**Example: Hugging Face MCP**
- Model search and discovery
- Inference API integration
- Dataset access tools
- Shows ML service integration patterns

**Applies To**: Learning and inspiration for new servers

**Source Citations**:
- Links to GitHub repositories
- Documentation from each project
- Analysis of implementation patterns

### prompts-and-templates.md

**Prompt Engineering for MCP Servers**

**Coverage**:
- @mcp.prompt() decorator usage
- Prompt template patterns
- System instructions for tool use
- Configuration for AI-native tools
- Prompt composition techniques
- Context management in prompts
- Parameter substitution patterns
- Multi-step workflow prompts

**Key Concepts**:

**Prompt Tools**: Templated instructions that help LLMs use your tools effectively

```python
@mcp.prompt()
def analyze_project(project: str) -> str:
    """Generate analysis workflow for a project."""
    return f"""Analyze the project '{project}' by:
1. Getting project details
2. Listing recent activity
3. Checking health metrics
4. Summarizing findings"""
```

**System Instructions**: Configure how LLMs interact with your tools

```python
@mcp.tool()
def complex_operation() -> dict:
    """Complex operation.

    USAGE GUIDANCE:
    1. First call list_resources to see what's available
    2. Then call get_resource for specific items
    3. Finally call this operation with resource IDs
    """
    return result
```

**Applies To**: Advanced MCP server features

**Source Citations**:
- FastMCP prompt documentation
- MCP prompt specification
- Prompt engineering best practices

### accessing_online_resources.md

**Web Research Best Practices**

**Coverage**:
- MCP tool preferences for research
- High-fidelity vs summarized sources
- Tool selection criteria
- API documentation research strategies
- Code example discovery
- Community practice research

**Research Tool Hierarchy**:
1. `mcp__Ref__ref_search_documentation` - Verbatim official docs
2. `mcp__exa__get_code_context_exa` - Code examples and patterns
3. `mcp__exa__web_search_exa` - LLM-optimized web results
4. WebFetch - Fallback for general web pages

**Rationale**: MCP tools provide higher fidelity and better accuracy than generic web fetching.

**Applies To**: Research phase of MCP development

**Source Citations**:
- MCP tool documentation
- Best practices for technical research
- Source fidelity comparison studies

## Progressive Loading Strategy

The skill uses progressive disclosure to optimize context usage:

### Always Loaded (Phase 1)
- Skill frontmatter and main instructions
- High-level workflow overview
- Quick reference patterns

### Loaded on Language Selection (Phase 2)
- **Python**: development-guidelines.md
- **TypeScript**: typescript-mcp-server.md
- **Both**: mcp-best-practices.md

### Loaded on Specific Needs (Phase 3)
- **Deployment questions**: community-practices.md
- **Testing requests**: evaluation-guide.md
- **Learning/examples**: example-projects.md
- **Advanced features**: prompts-and-templates.md
- **Research phase**: accessing_online_resources.md

### Context Efficiency

By loading references on demand:
- **Initial context**: ~18KB (SKILL.md only)
- **Python work**: +16KB (development-guidelines.md)
- **TypeScript work**: +19KB (typescript-mcp-server.md)
- **Full stack**: All references available but loaded only when needed

This means Claude can work efficiently with just the guidance needed for the current task.

## Using References in Your Work

### Asking Questions

```
"What are the naming conventions for MCP tools?"
→ Claude loads mcp-best-practices.md

"How do I implement async tools in FastMCP?"
→ Claude loads development-guidelines.md

"Show me real-world MCP server examples"
→ Claude loads example-projects.md

"How do I package my server for distribution?"
→ Claude loads community-practices.md
```

### During Development

As you build, Claude automatically loads relevant references:
- Implementation → language-specific guide
- Testing → evaluation-guide.md
- Deployment → community-practices.md
- Questions → appropriate reference

### Building Intuition

Study the references directly to understand:
- Why patterns exist (not just how)
- Trade-offs between approaches
- Real-world usage examples
- Common pitfalls and solutions

## Keeping References Current

These references were accurate as of January 2025. For the latest information:

- **MCP Protocol**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
- **FastMCP**: [https://github.com/jlowin/fastmcp](https://github.com/jlowin/fastmcp)
- **TypeScript SDK**: [https://github.com/modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk)

If you encounter outdated information, Claude can use web research tools to supplement references with current documentation.

## Reference Quality Standards

All references follow these standards:

✅ **Cited Sources**: Every pattern cites official docs or real examples
✅ **Code Examples**: All examples are tested and working
✅ **Language Specifiers**: All code blocks have proper syntax highlighting
✅ **Relative Links**: Internal references use `./path/to/file.md` format
✅ **Progressive Detail**: Start simple, add complexity progressively
✅ **Practical Focus**: Real-world patterns over theoretical concepts
✅ **Error Guidance**: Common issues and solutions included

## Contributing to References

To improve these references:

1. Test all code examples in real projects
2. Cite sources for all patterns and best practices
3. Use markdown links for all file references: `[text](./file.md)`
4. Add language specifiers to all code fences
5. Include both good and bad examples where helpful
6. Focus on practical, actionable guidance
7. Update access dates for external resources

## Summary

The fastmcp-creator reference library provides:
- **115KB** of comprehensive guidance
- **8 specialized** reference documents
- **Progressive loading** for context efficiency
- **Dual framework** coverage (Python & TypeScript)
- **Production-ready** patterns and best practices
- **Real-world examples** from successful servers
- **Complete evaluation** framework and testing guide

All references are standalone, cited, and designed for AI consumption while remaining useful for human readers.
