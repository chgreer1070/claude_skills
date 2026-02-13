# Research Directory Index

Curated research on tools, libraries, and patterns relevant to Claude Code development.

---

## Categories

### Async Libraries

Foundational async/concurrency libraries for Python async development.

| Resource | Description | Version | Last Updated |
|----------|-------------|---------|--------------|
| [AnyIO](./async-libraries/anyio.md) | Unified async API across asyncio/Trio with structured concurrency | 4.12.1 | 2026-02-04 |

### Context Management

Memory, RAG, context window tools for persistent AI knowledge.

| Resource | Description | Version | Last Updated |
|----------|-------------|---------|--------------|
| [Local Memory](./context-management/local-memory.md) | Persistent memory infrastructure for AI agents with MCP, REST API, CLI, and multi-provider AI backend | 1.4.0 | 2026-02-07 |

### Skill Generation Tools

Tools that create, translate, and manage AI agent skills and prompts.

| Resource | Description | Version | Last Updated |
|----------|-------------|---------|--------------|
| [SkillKit](./skill-generation-tools/skillkit.md) | Universal package manager for AI agent skills with cross-agent translation (32 agents), marketplace (15K+ skills), session memory, and AI generation | 1.14.0 | 2026-02-08 |

### Developer Tools

Open-source developer utilities, file processing, and infrastructure tools.

| Resource | Description | Version | Last Updated |
|----------|-------------|---------|--------------|
| [GrepAI](./developer-tools/grepai.md) | Semantic code search CLI with AI embeddings (Ollama/OpenAI), call graph tracing (12 languages), built-in MCP server, and 27 AI agent skills | v0.31.0 | 2026-02-13 |
| [VERT](./developer-tools/vert.md) | WebAssembly-based file converter (250+ formats) with client-side processing via FFmpeg, ImageMagick, and Pandoc WASM | 0.0.1 | 2026-02-08 |
| [Loguru](./developer-tools/loguru.md) | Zero-config Python logging library replacing stdlib `logging` with modern formatting, structured output, file rotation, and exception catching | 0.7.3 | 2026-02-09 |

---

## Adding New Entries

Use the `/research-curator` skill to add new resources:

```text
/research-curator https://example.com/tool-documentation
```

The skill will:

1. Research the resource from primary sources
2. Create a standardized entry in the appropriate category
3. Update this index

---

## Review Schedule

Entries are reviewed every 3 months. Check the "Next Review" date in each entry's Freshness Tracking section.
