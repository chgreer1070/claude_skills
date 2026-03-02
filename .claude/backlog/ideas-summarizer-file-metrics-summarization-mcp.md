---
name: 'summarizer: File Metrics & Summarization MCP'
description: 'Wrap `file_metrics.py` as MCP tools. Agents could request file complexity analysis, token counts, and structured summaries. Tools: `count_tokens`, `scan_files`, `summarize_file`.'
metadata:
  topic: summarizer-file-metrics-summarization-mcp
  source: MCP backlog audit 2026-02-23
  added: '2026-02-23'
  priority: Ideas
  type: Feature
  status: open
  issue: '#258'
---

## Story

As a **developer using Claude Code skills**, I want to **summarizer: file metrics & summarization mcp** so that **the tooling becomes more capable and complete**.

## Description

Wrap `file_metrics.py` as MCP tools. Agents could request file complexity analysis, token counts, and structured summaries. Tools: `count_tokens`, `scan_files`, `summarize_file`.

## Suggested Location

`plugins/summarizer/mcp/server.py`

## Context

- **Source**: MCP backlog audit 2026-02-23
- **Priority**: Ideas
- **Added**: 2026-02-23
- **Research questions**: None