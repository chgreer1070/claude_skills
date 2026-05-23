<p align="center">
  <img src="./assets/hero.png" alt="summarizer" width="800" />
</p>

# summarizer

Faithful information summarization with fidelity preservation and anti-hallucination methodology.
Skills for file, URL, and image summarization. Agents for autonomous summarization tasks. Rules
for orchestrators relaying sub-agent results without lossy re-summarization.

## Problem

Generic summarization drops exact counts, merges distinct items, and invents connections between
sources. This plugin enforces a read-before-summarize discipline, type-specific strategies, and
explicit rules for preserving numbers, lists, and source attribution across the relay chain.

## Installation

```bash
/plugin install summarizer@jamie-bitflight-skills
```

## Quick Start

```text
/summarizer "plugins/summarizer/skills/summarizer/SKILL.md"
/summarizer:file-summarization "src/api/routes.ts"
/summarizer:url-summarization "https://docs.anthropic.com/en/docs/claude-code/overview"
/summarizer:image-summarization "screenshots/dashboard.png"
```

## Skills

### `summarizer`

Main entry point. Activates on: "summarize", "tl;dr", "what's important in this", "what does
this code do", "describe this image". Routes automatically to the type-specific skill based on
whether the source is a file path, URL, or image.

### `file-summarization`

Summarizes files with type-specific strategies:

- **Code files** — public API surface, exports, key algorithms, entry points; no line-by-line listing
- **Config files** — effective settings, non-default values, environment-specific blocks
- **Documentation** — main claims, prerequisites, step counts (exact); no paraphrase
- **Data files** — schema, row count, field types, sample values

Size-based routing: files under a threshold are read in full; larger files use chunked
progressive reading with section-level summaries.

### `url-summarization`

Summarizes web pages and documentation URLs. Fetches full content, applies source citation with
access date. Distinguishes official documentation from community content in the output.

### `image-summarization`

Describes images, screenshots, and diagrams with structured output. Type-specific strategies:

- **UI screenshots** — layout structure, visible navigation, primary content area, any error/status messages
- **Diagrams** — node types, relationships, flow direction, labels
- **Charts** — axes, data series, trend direction, notable values

### `multi-source-synthesis`

Combines summaries from multiple sources into a single synthesis. This is the *reduce* step
after individual summarization (the *map* step). Enforces deduplication with citation of all
contributing sources, conflict surfacing, and confidence scoring. Activates on: "combine these
summaries", "synthesize results", "merge findings".

### `agent-result-relay`

Rules for orchestrators relaying sub-agent results. Prevents the most common relay failure:
re-summarizing a summary and losing exact counts or item lists in the process. When an agent
returns "found 14 issues", the relay must say "14 issues" — not "several issues".

## Agents

| Agent | Role |
|-------|------|
| `file-summarizer` | Autonomously reads and summarizes a file given its path |
| `url-summarizer` | Fetches and summarizes a URL, citing the source with access date |
| `image-summarizer` | Describes an image or screenshot given its path |

## Usage Examples

```text
# Single file
/summarizer:file-summarization "plugins/bash-development/skills/bash-development/SKILL.md"

# Web page
/summarizer:url-summarization "https://code.visualstudio.com/docs/editor/extension-marketplace"

# Image
/summarizer:image-summarization "docs/screenshots/dashboard.png"

# Multi-source synthesis (after summarizing each source individually)
/summarizer:multi-source-synthesis

# Relay discipline for orchestrators
/summarizer:agent-result-relay
```

---

> **The Ancient Woe**
>
> *The windbag courtier who takes three hours to explain that the treasury is empty, embellishing the tale with mythical dragons that do not actually exist.*

> **The Bard's Decree**
>
> *"Boil away the fat! Give me the marrow of the truth, unspiced by thy wandering imagination, that a King may know his kingdom in a single, solitary breath!"*
