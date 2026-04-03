---
name: User-scoped ~/.dh/ config system with project settings and secrets management
description: 'As the development harness adds per-project agent/skill preferences, project management backend configuration (GitHub/GitLab/Linear/Supabase credentials), and task-level settings, there is no place to store project-specific preferences or secrets outside the repo. A user-scoped ~/.dh/ directory is needed with: ~/.dh/settings.json for global settings, ~/.dh/secrets.json (or equivalent) for credentials, and ~/.dh/projects/{project-path-as-slug}/ for per-project preferences that load automatically without being committed to the repo. Design needs research — Charmbracelet Crush (https://github.com/charmbracelet/crush) is the reference system to study for config, secrets, and project settings patterns. Research first: How does Crush handle config vs secrets separation, project-scoped overrides, and credential storage?'
metadata:
  topic: user-scoped-dh-config-system-with-project-settings-and-secre
  source: 'GitHub Issue #982'
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#982'
  last_synced: '2026-03-22T15:08:45Z'
---

## Story

As a **developer using Claude Code skills**, I want to **user-scoped ~/.dh/ config system with project settings and secrets management** so that **the tooling becomes more capable and complete**.

## Description

As the development harness adds per-project agent/skill preferences, project management backend configuration (GitHub/GitLab/Linear/Supabase credentials), and task-level settings, there is no place to store project-specific preferences or secrets outside the repo. A user-scoped ~/.dh/ directory is needed with: ~/.dh/settings.json for global settings, ~/.dh/secrets.json (or equivalent) for credentials, and ~/.dh/projects/{project-path-as-slug}/ for per-project preferences that load automatically without being committed to the repo. Design needs research — Charmbracelet Crush (https://github.com/charmbracelet/crush) is the reference system to study for config, secrets, and project settings patterns. Research first: How does Crush handle config vs secrets separation, project-scoped overrides, and credential storage?

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: User request — session 2026-03-21, vision for DH config management as backends and per-project settings grow
- **Priority**: P1
- **Added**: 2026-03-22
- **Research questions**: None