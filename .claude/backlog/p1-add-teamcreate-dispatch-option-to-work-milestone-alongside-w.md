---
name: Add TeamCreate dispatch option to /work-milestone alongside worktree agents
description: "Add TeamCreate dispatch option to /work-milestone alongside the current Agent(isolation: 'worktree') dispatch.\n\nEvidence: User has a Claude Code session running 10+ hours autonomously on ../vm-flightsimulator, coordinating 60 issues through agent teams. This validates that teams work for sustained parallel execution.\n\nCurrent state: work-milestone SKILL.md hardcodes Agent(isolation: 'worktree') for all wave dispatch (redesigned in #970 based on the finding that teammates lack the Agent tool).\n\nCorrection: Both teammates AND subagents lack the Agent tool — they have identical tool access. The choice between teams and agents is about inter-worker communication, not capability. Teams add SendMessage for cross-worker coordination which is valuable for long-running milestone sessions.\n\nOptions:\n- --teams flag to select TeamCreate dispatch (teammates communicate via SendMessage)\n- --agents flag to select Agent(isolation: 'worktree') dispatch (independent workers, simpler)\n- Default: teams (validated by real-world 60-issue session)\n\nThe worktree-worker-protocol.md and merge-queue-protocol.md need corresponding updates to support team-based coordination alongside the agent-return model."
metadata:
  topic: add-teamcreate-dispatch-option-to-work-milestone-alongside-w
  source: 'Session 2026-03-21: user reports 10+ hour autonomous team session on vm-flightsimulator coordinating 60 issues successfully'
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: open
  issue: '#975'
  last_synced: '2026-03-22T00:07:11Z'
---