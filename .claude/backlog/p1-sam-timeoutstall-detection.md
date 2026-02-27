---
name: 'SAM: Timeout/Stall Detection'
description: Define mechanism to detect when an agent is stuck or has stalled. Include timeout thresholds per stage, health check patterns, and recovery actions.
metadata:
  topic: sam-timeoutstall-detection
  source: Gap analysis of SAM framework
  added: '2026-02-01'
  priority: completed
  type: Feature
  status: done
  issue: '#201'
  plan: N/A
---

**Suggested location**: [`stateless-software-engineering-framework.md`](https://github.com/bitflight-devops/stateless-agent-methodology/blob/main/stateless-software-engineering-framework.md) (Orchestrator section 3.8)

**Research first**: How do orchestration frameworks (Temporal, Prefect, Airflow) handle task timeouts? What heartbeat patterns exist? How does Gas Town handle session recycling?