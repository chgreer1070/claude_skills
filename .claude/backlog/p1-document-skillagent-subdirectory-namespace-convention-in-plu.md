---
name: Document skill/agent subdirectory namespace convention in plugin reference docs
description: "Document the skill/agent subdirectory namespace convention in plugin-creator reference docs so audit agents and plugin authors know about it.\n\nSubdirectories within skills/ or agents/ create colon-separated namespaces:\n- skills/workflows/discovery/SKILL.md → invoked as /plugin:workflows:discovery\n- skills/testing/foo/SKILL.md → invoked as /plugin:testing:foo\n\nThis is not documented in:\n- plugin-creator:claude-plugins-reference-2026 (the primary plugin schema reference)\n- plugin-creator:claude-skills-overview-2026 (the skills system reference)\n- dh CLAUDE.md (lists skills with wrong invocation paths — /dh:discovery instead of /dh:workflows:discovery)\n\nThe doc-drift-auditor agent reported these skills as phantom because it checked skills/discovery/ (flat) instead of skills/workflows/discovery/ (nested). Any agent auditing plugins will make the same mistake until this convention is documented in the reference material they load.\n\nFiles to update:\n1. plugins/plugin-creator/skills/claude-plugins-reference-2026/ — add subdirectory namespace section\n2. plugins/plugin-creator/skills/claude-skills-overview-2026/ — add namespace convention\n3. plugins/development-harness/CLAUDE.md — fix invocation paths for 10 skills (use full colon-separated paths)\n4. plugins/development-harness/README.md — same fixes"
metadata:
  topic: document-skillagent-subdirectory-namespace-convention-in-plu
  source: 'GitHub Issue #983'
  added: '2026-03-22'
  priority: P1
  type: Docs
  status: needs-grooming
  issue: '#983'
  last_synced: '2026-03-22T15:08:44Z'
---

## Story

As a **developer reading the documentation**, I want to **document skill/agent subdirectory namespace convention in plugin reference docs** so that **documentation is accurate and trustworthy**.

## Description

Document the skill/agent subdirectory namespace convention in plugin-creator reference docs so audit agents and plugin authors know about it.

Subdirectories within skills/ or agents/ create colon-separated namespaces:
- skills/workflows/discovery/SKILL.md → invoked as /plugin:workflows:discovery
- skills/testing/foo/SKILL.md → invoked as /plugin:testing:foo

This is not documented in:
- plugin-creator:claude-plugins-reference-2026 (the primary plugin schema reference)
- plugin-creator:claude-skills-overview-2026 (the skills system reference)
- dh CLAUDE.md (lists skills with wrong invocation paths — /dh:discovery instead of /dh:workflows:discovery)

The doc-drift-auditor agent reported these skills as phantom because it checked skills/discovery/ (flat) instead of skills/workflows/discovery/ (nested). Any agent auditing plugins will make the same mistake until this convention is documented in the reference material they load.

Files to update:
1. plugins/plugin-creator/skills/claude-plugins-reference-2026/ — add subdirectory namespace section
2. plugins/plugin-creator/skills/claude-skills-overview-2026/ — add namespace convention
3. plugins/development-harness/CLAUDE.md — fix invocation paths for 10 skills (use full colon-separated paths)
4. plugins/development-harness/README.md — same fixes

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session 2026-03-22: audit agent reported 10 phantom skills that exist in subdirectories — agent didn't know about subdirectory namespacing
- **Priority**: P1
- **Added**: 2026-03-22
- **Research questions**: None