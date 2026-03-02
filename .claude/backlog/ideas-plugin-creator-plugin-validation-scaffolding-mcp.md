---
name: 'plugin-creator: Plugin Validation & Scaffolding MCP'
description: 'Wrap `plugin_validator.py`, `auto_sync_manifests.py`, `create_plugin.py`, and `normalize_frontmatter.py` as MCP tools. Agents could validate plugins, scaffold new ones, sync manifests, and normalize frontmatter without shell invocations. Tools: `validate_plugin`, `create_plugin`, `sync_manifests`, `normalize_frontmatter`, `list_validation_errors`.'
metadata:
  topic: plugin-creator-plugin-validation-scaffolding-mcp
  source: MCP backlog audit 2026-02-23
  added: '2026-02-23'
  priority: Ideas
  type: Feature
  status: open
  issue: '#253'
---

## Story

As a **developer using Claude Code skills**, I want to **plugin-creator: plugin validation & scaffolding mcp** so that **the tooling becomes more capable and complete**.

## Description

Wrap `plugin_validator.py`, `auto_sync_manifests.py`, `create_plugin.py`, and `normalize_frontmatter.py` as MCP tools. Agents could validate plugins, scaffold new ones, sync manifests, and normalize frontmatter without shell invocations. Tools: `validate_plugin`, `create_plugin`, `sync_manifests`, `normalize_frontmatter`, `list_validation_errors`.

## Suggested Location

`plugins/plugin-creator/mcp/server.py`

## Context

- **Source**: MCP backlog audit 2026-02-23
- **Priority**: Ideas
- **Added**: 2026-02-23
- **Research questions**: None