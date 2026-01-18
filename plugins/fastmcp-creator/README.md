# FastMCP Creator

Build Model Context Protocol (MCP) servers with comprehensive coverage of generic MCP protocol and FastMCP framework specialization. Includes agent-centric design principles, evaluation creation, Pydantic/Zod validation, async patterns, STDIO/HTTP/SSE transports, FastMCP Cloud deployment, .mcpb packaging, security patterns, and mid-2025+ community practices.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install fastmcp-creator@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/fastmcp-creator
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [fastmcp-creator](./skills/fastmcp-creator/SKILL.md) | Build Model Context Protocol (MCP) servers - comprehensive coverage of generic MCP protocol AND FastMCP framework specialization. Use when creating any MCP server (Python FastMCP preferred, TypeScript/Node also covered). |

## Quick Start

Create a new MCP server with FastMCP:

```bash
# Activate the skill and ask Claude to build an MCP server
@fastmcp-creator

# Example request:
"Create a GitHub MCP server with tools for:
- Listing repositories
- Creating issues
- Searching code

Use FastMCP with async support and proper error handling."
```

The skill will guide you through:

1. **Deep Research and Planning** - Understanding agent-centric design principles
2. **Implementation** - Building with FastMCP decorators and Pydantic validation
3. **Testing** - Creating evaluation harnesses for quality assurance
4. **Deployment** - Packaging and configuring for production use

## Key Features

- **Agent-Centric Design** - Build workflows, not just API wrappers
- **FastMCP Framework** - Python decorator-based development with Pydantic
- **TypeScript Support** - Generic MCP SDK patterns for Node.js
- **Evaluation Harness** - Test server quality with automated checks
- **Production Ready** - Security, performance, and observability patterns
- **Complete Documentation** - Extensive reference materials and examples

## Reference Materials

The skill includes comprehensive reference documentation:

- [MCP Best Practices](./skills/fastmcp-creator/references/mcp-best-practices.md)
- [Development Guidelines](./skills/fastmcp-creator/references/development-guidelines.md)
- [Evaluation Guide](./skills/fastmcp-creator/references/evaluation-guide.md)
- [Example Projects](./skills/fastmcp-creator/references/example-projects.md)
- [Community Practices](./skills/fastmcp-creator/references/community-practices.md)
- [Prompts and Templates](./skills/fastmcp-creator/references/prompts-and-templates.md)
- [TypeScript MCP Server](./skills/fastmcp-creator/references/typescript-mcp-server.md)

## License

See plugin manifest for license information.
