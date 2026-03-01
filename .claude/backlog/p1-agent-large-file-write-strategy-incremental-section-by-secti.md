---
name: 'Agent Large File Write Strategy: Incremental Section-by-Section Writing'
description: Sub-agents writing large files (>30K chars) via single Write calls timeout or get stuck. Need a strategy where agents write the file structure/skeleton first, then fill in content section-by-section using Edit calls. Observed during task planner writing 57,800 char task plan that stalled. The pattern should be documented as agent guidance and possibly enforced via hooks or delegation instructions.
metadata:
  topic: agent-large-file-write-strategy-incremental-section-by-secti
  source: Session observation
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
  issue: '#367'
  last_synced: '2026-03-01T20:10:50Z'
---