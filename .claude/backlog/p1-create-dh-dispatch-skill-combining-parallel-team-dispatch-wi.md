---
name: Create /dh:dispatch skill combining parallel team dispatch with delegation quality
description: "Create a /dh:dispatch skill in development-harness that combines parallel team dispatch mechanics with delegation quality guidelines.\n\nSources to synthesize:\n1. superpowers dispatching-parallel-agents skill (https://raw.githubusercontent.com/johnpwilkinson/superpowers/3367002498a12c8ef70a118454401082805229b0/skills/dispatching-parallel-agents/SKILL.md) — TeamCreate pattern, when to parallelize, agent prompt structure, common mistakes\n2. agent-orchestration:agent-orchestration skill — delegation template (WHERE/WHAT/WHY), pre-gathering prohibition, verification questions, anti-patterns\n3. agent-orchestration:how-to-delegate skill — quick delegation framework\n\nThe skill should cover:\n- When to dispatch parallel work (2+ independent tasks)\n- How to set up the team (TeamCreate → TaskCreate → Agent with team_name)\n- How to write agent prompts (observations + success criteria, no prescriptions)\n- How to handle results (review, conflict check, integrate)\n- Common mistakes from both sources\n- Real examples\n\nKeep it concise — a single SKILL.md with the essential patterns, not a comprehensive reference. The agent-orchestration skill is the comprehensive reference; this skill is the quick-start for 'I need to dispatch parallel work right now.'"
metadata:
  topic: create-dh-dispatch-skill-combining-parallel-team-dispatch-wi
  source: 'Session 2026-03-21: combining superpowers dispatching-parallel-agents pattern with agent-orchestration delegation quality'
  added: '2026-03-22'
  priority: completed
  type: Feature
  status: done
  issue: '#976'
  last_synced: '2026-03-22T00:37:05Z'
---