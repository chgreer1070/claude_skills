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

### Developer Tools

Open-source developer utilities, file processing, and infrastructure tools.

| Resource | Description | Version | Last Updated |
|----------|-------------|---------|--------------|
| [VERT](./developer-tools/vert.md) | WebAssembly-based file converter (250+ formats) with client-side processing via FFmpeg, ImageMagick, and Pandoc WASM | 0.0.1 | 2026-02-08 |

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
