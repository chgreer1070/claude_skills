---
name: Create a broad simplify skill that reviews all changed file types, not just code
description: 'The built-in /simplify skill only reviews source code (redundant state, copy-paste, N+1 queries, JSX nesting). It skips markdown, YAML, skill files, agent definitions, and plan artifacts. Sessions that produce only planning artifacts, documentation, or skill edits get no quality review. A custom /simplify-all (or replacement) skill should also check for: duplicate content across markdown files, stale cross-references and broken links, inconsistent formatting, invalid documentation claims, redundant instructions across skills/agents, and plan artifact quality (missing sections, incomplete acceptance criteria).'
metadata:
  topic: create-a-broad-simplify-skill-that-reviews-all-changed-file-
  source: Session observation 2026-03-21 — /simplify ran on a planning-only session and found nothing to review
  added: '2026-03-22'
  priority: P2
  type: Feature
  status: open
  issue: '#977'
  last_synced: '2026-03-22T00:53:31Z'
---