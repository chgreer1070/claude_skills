---
name: 'Mission interview: clang-format'
description: "Interview the user with 5 mission statement questions to draft and refine `plugins/clang-format/mission.json`.\n\nRun: `/plugin-creator:mission-statement plugins/clang-format --interview`\n\n**Q1 — Non-Negotiable:** 'What is the one thing this plugin must never sacrifice, even to ship faster?'\n\n**Q2 — Bad Twin:** 'What would a superficially similar but wrong version of this plugin do? What makes it wrong?'\n\n**Q3 — Trade-offs:** 'When forced to choose between breadth vs depth / correctness vs speed / explicit vs implicit — which does this plugin choose, and why?' (Ask all three. If 'both', ask 'if you could only have one.')\n\n**Q4 — Removal Trigger:** 'What would make you remove this plugin from the marketplace entirely?'\n\n**Q5 — Anti-Pattern Example:** 'Give me a specific example of a fix or improvement this plugin should refuse to make, even if asked.'\n\nAfter interview: update `mission.json` with answers, set `interview_backlog_item` to this issue number, validate with 3 known past decisions."
metadata:
  topic: mission-interview-clang-format
  source: Mission statement development process
  added: '2026-03-07'
  priority: P2
  type: Chore
  status: open
  issue: '#526'
  last_synced: '2026-03-07T17:14:20Z'
---