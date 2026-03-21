---
name: Create /groom-milestone skill
description: 'Create the /groom-milestone skill for the development-harness plugin. The skill batch-grooms milestone items, assesses scope gaps, analyzes cross-item dependencies via analyze_impact_radius_conflicts(), builds conflict groups, assigns items to execution waves, and writes a dispatch plan YAML via dispatch_schema. Design doc at .claude/reports/milestone-orchestration-design-20260320.md defines the 10-step workflow with Mermaid diagrams. All tooling dependencies are implemented: dispatch_schema (models, reader, writer, validator), github_branches (integration branch CRUD), quality gates runner, and conflict analysis.'
metadata:
  topic: create-groom-milestone-skill
  source: Milestone orchestration design — .claude/reports/milestone-orchestration-design-20260320.md
  added: '2026-03-21'
  priority: P0
  type: Feature
  status: open
  issue: '#934'
  last_synced: '2026-03-21T02:01:14Z'
  groomed: '2026-03-21'
---

## RT-ICA

<div><sub>2026-03-21T02:01:14Z</sub>

**RT-ICA**: Create /groom-milestone skill — APPROVED

All conditions AVAILABLE. Design doc has full workflow. All tooling dependencies implemented (dispatch_schema, github_branches, quality gates, conflict analysis). Skill creation patterns known.
</div>