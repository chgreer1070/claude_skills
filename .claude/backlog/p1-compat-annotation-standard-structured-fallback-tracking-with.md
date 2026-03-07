---
name: COMPAT annotation standard — structured fallback tracking with CI enforcement
description: 'Establish a COMPAT annotation standard for all compatibility shims, fallbacks, and temporary workarounds in the codebase. Every fallback must document why it exists, what condition allows removal, and when it was added. A pre-commit hook scans for COMPAT annotations and fails CI when removal conditions are met or annotations are malformed. Companion: ADR records in .claude/decisions/ for architectural decisions that motivated the fallback. Motivated by claim-task fix (2026-03-07) which added a silent field-name fallback with no removal condition documented.'
metadata:
  topic: compat-annotation-standard-structured-fallback-tracking-with
  source: Session observation — claim-task fix introduced silent compatibility shim with no removal tracking
  added: '2026-03-07'
  priority: P1
  type: Feature
  status: open
  issue: '#549'
  last_synced: '2026-03-07T19:05:57Z'
---