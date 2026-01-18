# fastmcp-creator

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A comprehensive Claude Code plugin for building Model Context Protocol (MCP) servers with specialization in the FastMCP framework (Python) and complete TypeScript/Node SDK coverage.

## Features

- **Dual Framework Support** - FastMCP (Python decorator-based) and TypeScript/Node MCP SDK
- **Agent-Centric Design Principles** - Build tools for AI agents, not just API wrappers
- **Comprehensive Reference Library** - 8 detailed guides covering all aspects of MCP development
- **Evaluation Harness** - Built-in testing framework to validate server effectiveness with LLMs
- **Production-Ready Patterns** - Security, performance, observability, and deployment best practices
- **Community Practices** - Mid-2025+ patterns including .mcpb packaging and FastMCP Cloud deployment
- **Standalone Operation** - No external dependencies required

## Installation

### Prerequisites

- Claude Code version 2.1 or later
- Python 3.11+ (for FastMCP development)
- Node.js 18+ (for TypeScript development)
- Optional: FastMCP framework (`pip install fastmcp`)

### Install Plugin

```bash
# Method 1: Using cc plugin install (if in marketplace)
cc plugin install fastmcp-creator

# Method 2: Manual installation
git clone <repository-url> ~/.claude/plugins/fastmcp-creator
cc plugin reload
```

## Quick Start

When you need to build an MCP server, simply mention MCP or server development in your request, and Claude will automatically activate this skill.

```
"Build an MCP server for GitHub that provides tools to list repositories,
create issues, and search code"
```

Claude will guide you through:
1. **Deep Research and Planning** - Understanding agent-centric design and API documentation
2. **Implementation** - Building tools with proper validation and error handling
3. **Review and Refine** - Code quality checks and testing
4. **Evaluation Creation** - Generating comprehensive test scenarios

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | fastmcp-creator | Build MCP servers with comprehensive coverage of FastMCP (Python) and TypeScript/Node implementations, agent-centric design principles, evaluation creation, and production deployment patterns | Auto-activated or `@fastmcp-creator` |

## Usage

### Automatic Activation

The skill automatically activates when you:
- Mention "MCP server" or "Model Context Protocol"
- Ask to build tools for AI agents
- Request FastMCP or TypeScript MCP implementation help
- Need evaluation harness or testing guidance

### Manual Activation

```
@fastmcp-creator
```

Or in code:
```
Skill(command: "fastmcp-creator")
```

### What This Skill Provides

**4-Phase Workflow:**
1. **Deep Research and Planning** - Agent-centric design, API documentation study, implementation planning
2. **Implementation** - Framework-specific patterns, validation, error handling
3. **Review and Refine** - Code quality checks, DRY principles, type safety
4. **Evaluation Creation** - Comprehensive testing with realistic scenarios

**Language Support:**
- **Python (Preferred)** - FastMCP decorator-based framework with Pydantic validation
- **TypeScript/Node** - Official MCP SDK with Zod validation
- **Generic** - Universal MCP best practices for any language

## Reference Library

The skill includes comprehensive reference documentation:

| Reference | Purpose |
|-----------|---------|
| [MCP Best Practices](./skills/fastmcp-creator/references/mcp-best-practices.md) | Universal guidelines for all MCP implementations |
| [FastMCP Development Guidelines](./skills/fastmcp-creator/references/development-guidelines.md) | Python FastMCP specialization with decorators and Pydantic |
| [TypeScript MCP Server Guide](./skills/fastmcp-creator/references/typescript-mcp-server.md) | Complete TypeScript/Node implementation patterns |
| [Community Practices](./skills/fastmcp-creator/references/community-practices.md) | Mid-2025+ patterns including .mcpb packaging |
| [Evaluation Guide](./skills/fastmcp-creator/references/evaluation-guide.md) | Creating comprehensive server quality tests |
| [Example Projects](./skills/fastmcp-creator/references/example-projects.md) | Real-world implementations and patterns |
| [Prompts and Templates](./skills/fastmcp-creator/references/prompts-and-templates.md) | Prompt system configuration for AI-native tools |
| [Accessing Online Resources](./skills/fastmcp-creator/references/accessing_online_resources.md) | Best practices for web research during development |

## Evaluation Harness

The plugin includes a complete evaluation framework for testing MCP server effectiveness:

```bash
# Install dependencies
pip install -r skills/fastmcp-creator/scripts/requirements.txt

# Set API key
export ANTHROPIC_API_KEY=your_api_key

# Run evaluation
python skills/fastmcp-creator/scripts/evaluation.py \
  -t stdio \
  -c python \
  -a my_mcp_server.py \
  evaluation.xml
```

**Evaluation Scripts:**
- `evaluation.py` - Main evaluation harness
- `connections.py` - MCP connection utilities
- `example_evaluation.xml` - Example evaluation format
- `requirements.txt` - Python dependencies

## Examples

### Example 1: Building a GitHub MCP Server

**Scenario**: Create an MCP server that helps AI agents work with GitHub repositories.

**Steps**:
1. "Build a FastMCP server for GitHub with tools to list repos, create issues, and search code"
2. Claude activates fastmcp-creator skill automatically
3. Follows 4-phase workflow: research → implement → refine → evaluate
4. Generates complete server with proper validation and error handling

**Result**: Production-ready MCP server with agent-optimized tools, comprehensive error handling, and evaluation suite.

---

### Example 2: Adding Evaluations to Existing Server

**Scenario**: You have an MCP server but need to test its effectiveness with LLMs.

**Steps**:
1. "Create comprehensive evaluations for my Slack MCP server"
2. Claude uses evaluation guide to generate 10 complex, realistic questions
3. Each question tests multi-step workflows using server tools
4. Provides answers for verification

**Result**: XML evaluation file ready for use with evaluation harness.

---

### Example 3: TypeScript MCP Server Development

**Scenario**: Build an MCP server in TypeScript for a REST API.

**Steps**:
1. "Build a TypeScript MCP server for the Notion API"
2. Claude uses TypeScript patterns from references
3. Implements with Zod validation and proper type safety
4. Includes build configuration and production deployment

**Result**: Type-safe TypeScript server with Zod schemas, error handling, and npm build scripts.

## Configuration

This plugin operates standalone with no additional configuration required. All reference materials are bundled and loaded on demand for optimal context window usage.

### Progressive Disclosure

Reference files are loaded only when needed, keeping Claude's context efficient. The skill automatically loads relevant guides based on:
- Target language (Python vs TypeScript)
- Implementation phase (planning vs coding vs testing)
- Specific questions (security, performance, deployment)

## Troubleshooting

### MCP Server Hangs When Testing

**Problem**: Running `python my_server.py` causes process to hang indefinitely.

**Solution**: MCP servers are long-running processes. Use one of these approaches:
```bash
# Option 1: Syntax check only
python -m py_compile my_server.py

# Option 2: Run with timeout
timeout 5s python my_server.py

# Option 3: Use evaluation harness
python scripts/evaluation.py -t stdio -c python -a my_server.py eval.xml

# Option 4: Run in tmux/screen for interactive testing
tmux new -s mcp
python my_server.py
# Ctrl+B then D to detach
```

### Evaluation Fails with Connection Error

**Problem**: Evaluation script can't connect to MCP server.

**Solution**: Check transport configuration:
```bash
# For STDIO transport (default)
python scripts/evaluation.py -t stdio -c python -a server.py eval.xml

# For HTTP transport
# Start server: python server.py --transport http --port 8000
# Run eval: python scripts/evaluation.py -t http -u http://localhost:8000 eval.xml
```

### Import Errors with FastMCP

**Problem**: `ModuleNotFoundError: No module named 'fastmcp'`

**Solution**: Install FastMCP framework:
```bash
pip install fastmcp
# Or with uv:
uv pip install fastmcp
```

### Type Validation Not Working

**Problem**: Invalid inputs accepted by tools.

**Solution Python**: Use `Annotated` with `Field()` constraints:
```python
from typing import Annotated
from pydantic import Field

def tool(
    count: Annotated[int, Field(ge=1, le=100)] = 10
) -> dict:
    pass
```

**Solution TypeScript**: Use Zod with `.strict()`:
```typescript
const Schema = z.object({
  count: z.number().int().min(1).max(100).default(10)
}).strict();
```

## Contributing

This plugin is part of the Claude Code plugin ecosystem. To contribute improvements or additional reference materials:

1. Follow the [plugin development guide](https://code.claude.com/docs/en/plugins)
2. Ensure all reference files use markdown links with relative paths: `[text](./path/file.md)`
3. Add language specifiers to all code fences
4. Update this README with any new capabilities

## License

License not specified. Please refer to the plugin repository for licensing information.

## Credits

This plugin synthesizes best practices from:
- [Model Context Protocol Official Docs](https://modelcontextprotocol.io)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- Mid-2025 community practices and real-world implementations

---

## Related Resources

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [MCP Protocol Specification](https://modelcontextprotocol.io/llms-full.txt)
- [FastMCP Framework Documentation](https://github.com/jlowin/fastmcp)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
