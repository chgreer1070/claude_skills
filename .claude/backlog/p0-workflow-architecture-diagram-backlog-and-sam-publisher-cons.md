---
name: 'Workflow architecture diagram: backlog and SAM publisher-consumer data flow'
description: 'Create a comprehensive workflow architecture diagram that maps the full backlog and SAM development-harness pipeline. Must track: (1) each node/stage in the workflow (skills, agents, MCP tools, hooks), (2) the data structures each node receives as input and produces as output, (3) how each node transforms or generates data, (4) publisher-consumer relationships between components, (5) state transitions and lifecycle, (6) dependencies between the backlog system (create/groom/work-backlog-item, backlog MCP) and SAM system (add-new-feature, implement-feature, complete-implementation, sam CLI/MCP). Current gap: local-workflow.md has a text data flow but does not track data structure shapes, publisher-consumer edges, or cross-system dependencies. This causes holes in the workflow where components assume inputs that are not produced by any upstream stage.'
metadata:
  topic: workflow-architecture-diagram-backlog-and-sam-publisher-cons
  source: User observation — keeps finding holes in the workflow; dependencies between publishers and consumers are not tracked
  added: '2026-03-21'
  priority: P0
  type: Feature
  status: open
  issue: '#933'
  last_synced: '2026-03-21T01:20:27Z'
---