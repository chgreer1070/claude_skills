---
name: gates.py subprocess timeout not applied
description: The subprocess.run call in dispatch_schema/gates.py has no timeout parameter. A hung gate command blocks indefinitely with no recovery. The simplify review fix T01 was supposed to add timeout=300.0 default and convert TimeoutExpired to CommandResult(exit_code=124) but did not complete this change. Follow-up from code review of issue 938.
metadata:
  topic: gatespy-subprocess-timeout-not-applied
  source: 'Code review of Issue #938 — simplify review fixes'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: open
  issue: '#951'
  last_synced: '2026-03-21T04:44:01Z'
---