---
name: Add MCP prompts and guided elicitation tools to backlog_core to consolidate workflow logic
description: "The workflow logic currently scattered across /backlog, /create-backlog-item, /groom-backlog-item, and /work-backlog-item skills should live in the MCP server so it travels with the tools and stays current without skill updates.\n\nTwo additions to backlog_core/server.py:\n\n**New MCP prompts** (return message content clients inject into LLM context):\n- `backlog_guide()` — full tool reference documentation as messages; replaces /backlog skill entirely\n- `create_item_guided()` — intake field instructions and format as messages\n- `groom_item(selector)` — fetches item via operations.view_item() server-side, returns item state + grooming workflow as messages\n- `work_item(selector)` — returns item state + planning instructions as messages\n- `close_or_resolve(selector)` — returns item state + close vs. resolve decision guide as messages\n\n**New guided tools using ctx.elicit()** (interactive versions of existing CRUD tools):\n- `backlog_add_guided` — elicits title, priority, description, type interactively then calls operations.add_item(); replaces the /create-backlog-item interactive flow\n- `backlog_close_confirmed` — elicits confirmation before closing, then delegates to operations.close_item(); absorbs the confirm step currently in the skill\n- `backlog_resolve_confirmed` — elicits summary + confirmation before resolving; absorbs the confirm step currently in the skill\n- `backlog_setup_github` — runs label taxonomy + milestone init; absorbs setup-github command from /work-backlog-item\n\nPrerequisites: ctx.elicit() requires async tools (see #472) and Context logging (#465).\n\nFiles: .claude/skills/backlog/backlog_core/server.py, operations.py"
metadata:
  topic: add-mcp-prompts-and-guided-elicitation-tools-to-backlogcore-
  source: 'GitHub Issue #473'
  added: '2026-03-06'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#473'
  last_synced: '2026-03-06T05:50:37Z'
---

## Story

As a **developer using Claude Code skills**, I want to **add mcp prompts and guided elicitation tools to backlog_core to consolidate workflow logic** so that **the tooling becomes more capable and complete**.

## Description

The workflow logic currently scattered across /backlog, /create-backlog-item, /groom-backlog-item, and /work-backlog-item skills should live in the MCP server so it travels with the tools and stays current without skill updates.

Two additions to backlog_core/server.py:

**New MCP prompts** (return message content clients inject into LLM context):
- `backlog_guide()` — full tool reference documentation as messages; replaces /backlog skill entirely
- `create_item_guided()` — intake field instructions and format as messages
- `groom_item(selector)` — fetches item via operations.view_item() server-side, returns item state + grooming workflow as messages
- `work_item(selector)` — returns item state + planning instructions as messages
- `close_or_resolve(selector)` — returns item state + close vs. resolve decision guide as messages

**New guided tools using ctx.elicit()** (interactive versions of existing CRUD tools):
- `backlog_add_guided` — elicits title, priority, description, type interactively then calls operations.add_item(); replaces the /create-backlog-item interactive flow
- `backlog_close_confirmed` — elicits confirmation before closing, then delegates to operations.close_item(); absorbs the confirm step currently in the skill
- `backlog_resolve_confirmed` — elicits summary + confirmation before resolving; absorbs the confirm step currently in the skill
- `backlog_setup_github` — runs label taxonomy + milestone init; absorbs setup-github command from /work-backlog-item

Prerequisites: ctx.elicit() requires async tools (see #472) and Context logging (#465).

Files: .claude/skills/backlog/backlog_core/server.py, operations.py

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Architecture review — consolidating Claude Code skills into MCP server
- **Priority**: P1
- **Added**: 2026-03-06
- **Research questions**: None