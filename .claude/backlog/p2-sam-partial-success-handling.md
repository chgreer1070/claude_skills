---
name: 'SAM: Partial Success Handling'
description: Define how to represent and handle partial task success. Task completes some DoD items but not all. How is this state represented in artifacts?
metadata:
  topic: sam-partial-success-handling
  source: Gap analysis of SAM framework
  added: '2026-02-01'
  priority: P2
  type: Feature
  status: open
  issue: '#227'
---

**Suggested location**: [`stateless-software-engineering-framework.md`](https://github.com/bitflight-devops/stateless-agent-methodology/blob/main/stateless-software-engineering-framework.md) (section 3.5 Execution Agent output)

**Research first**: How do GSD checkpoints represent partial progress? How do CI/CD systems handle partial test passes? What state machine patterns exist?
