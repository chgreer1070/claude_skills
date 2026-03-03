<p align="center">
  <img src="./assets/hero.png" alt="summarizer" width="800" />
</p>

# summarizer

Faithful information summarization with fidelity preservation, structured output, and
anti-hallucination methodology. Provides skills for file, URL, and image summarization;
agents for autonomous summarization tasks; and hooks for validating agent output structure.

## What it does

Summarizes files, URLs, and images while enforcing source fidelity. The methodology requires
reading the full source before summarizing, preserving exact counts and dates, and
distinguishing "not found in search" from "does not exist." Output uses structured YAML
frontmatter with confidence notes. A relay skill prevents information corruption when
orchestrators pass agent results between tasks.

## Skills

- `summarizer` — Main entry point for all summarization tasks; routes by source type
- `file-summarization` — Summarizes files by reading content fully and applying type-specific
  strategies for code, config, data, documentation, and markup
- `url-summarization` — Summarizes web pages and documentation URLs with source citation
- `image-summarization` — Describes images, screenshots, and diagrams with structured output
- `multi-source-synthesis` — Combines summaries from multiple sources into a single synthesis
- `agent-result-relay` — Rules for orchestrators relaying sub-agent results without lossy
  re-summarization or count dropping

## Agents

- `file-summarizer` — Autonomously reads and summarizes a file given its path
- `url-summarizer` — Fetches and summarizes a URL, citing the source
- `image-summarizer` — Describes an image or screenshot given its path

## Installation

```bash
/plugin install summarizer@jamie-bitflight-skills
```

## Usage

```text
/summarizer:file-summarization "plugins/summarizer/skills/summarizer/SKILL.md"
/summarizer:url-summarization "https://docs.anthropic.com/en/docs/claude-code/overview"
```
