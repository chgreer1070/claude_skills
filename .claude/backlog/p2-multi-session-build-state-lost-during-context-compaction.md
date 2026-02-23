---
name: Multi-session build state lost during context compaction
description: During the agentskill-kaizen build (8-phase `/plugin-dev:create-plugin` workflow), context compaction mid-build converted structured task state into a narrative summary. The resuming session had to reconstruct 'what's done vs pending' from prose rather than a checklist. Background agent results that were already consumed and applied reappeared as late notifications after compaction, requiring manual deduplication ('did I already handle this?'). No persistent artifact tracked phase completion, co
metadata:
  topic: multi-session-build-state-lost-during-context-compaction
  source: agentskill-kaizen plugin build (2026-02-18), 3 sessions with 1 compaction
  added: '2026-02-18'
  priority: P2
  type: Feature
  status: open
---
