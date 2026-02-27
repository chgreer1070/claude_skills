---
name: 'SAM: Scope Creep Detection'
description: Define mechanism to detect when execution diverges from plan. How does Forensic Review detect that the execution agent solved a different problem than planned?
metadata:
  topic: sam-scope-creep-detection
  source: Gap analysis of SAM framework
  added: '2026-02-01'
  priority: completed
  type: Feature
  status: done
  issue: '#203'
  plan: N/A
---

**Suggested location**: [`stateless-software-engineering-framework.md`](https://github.com/bitflight-devops/stateless-agent-methodology/blob/main/stateless-software-engineering-framework.md) (section 3.6 Forensic Review)

**Research first**: How does GSD plan-checker detect deviation? What diff/comparison techniques exist? How do code review tools detect scope creep in PRs?