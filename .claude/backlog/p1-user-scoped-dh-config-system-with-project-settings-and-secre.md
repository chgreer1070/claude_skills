---
name: User-scoped ~/.dh/ config system with project settings and secrets management
description: 'As the development harness adds per-project agent/skill preferences, project management backend configuration (GitHub/GitLab/Linear/Supabase credentials), and task-level settings, there is no place to store project-specific preferences or secrets outside the repo. A user-scoped ~/.dh/ directory is needed with: ~/.dh/settings.json for global settings, ~/.dh/secrets.json (or equivalent) for credentials, and ~/.dh/projects/{project-path-as-slug}/ for per-project preferences that load automatically without being committed to the repo. Design needs research — Charmbracelet Crush (https://github.com/charmbracelet/crush) is the reference system to study for config, secrets, and project settings patterns. Research first: How does Crush handle config vs secrets separation, project-scoped overrides, and credential storage?'
metadata:
  topic: user-scoped-dh-config-system-with-project-settings-and-secre
  source: User request — session 2026-03-21, vision for DH config management as backends and per-project settings grow
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: open
  issue: '#982'
  last_synced: '2026-03-22T03:54:28Z'
---