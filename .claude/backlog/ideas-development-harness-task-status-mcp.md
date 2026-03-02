---
name: 'development-harness: Task Status MCP'
description: 'Wrap `implementation_manager.py` CLI as MCP tools. Agents could query task status, list pending tasks, and update task state programmatically. Tools: `query_tasks`, `list_pending`, `update_task_status`, `parse_task_file`.'
metadata:
  topic: development-harness-task-status-mcp
  source: MCP backlog audit 2026-02-23
  added: '2026-02-23'
  priority: Ideas
  type: Feature
  status: open
  issue: '#257'
---

## Story

As a **developer using Claude Code skills**, I want to **development-harness: task status mcp** so that **the tooling becomes more capable and complete**.

## Description

Wrap `implementation_manager.py` CLI as MCP tools. Agents could query task status, list pending tasks, and update task state programmatically. Tools: `query_tasks`, `list_pending`, `update_task_status`, `parse_task_file`.

## Suggested Location

`plugins/development-harness/mcp/server.py`

## Context

- **Source**: MCP backlog audit 2026-02-23
- **Priority**: Ideas
- **Added**: 2026-02-23
- **Research questions**: None