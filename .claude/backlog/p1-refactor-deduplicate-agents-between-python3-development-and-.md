---
name: 'refactor: Deduplicate agents between python3-development and dh (Phase 4)'
description: "python3-development currently has 16 specialist agents that duplicate the generic agents in dh. Phase 4 removes the specialist agents from python3-development, replacing them with domain skills only. The 10 shared agents between dh and python3-development (already synced in Phase 1) are deduplicated — python3-development retains only domain skills, references, conventions, and quality gates. dh becomes the sole provider of agents.\n\nScope:\n- Remove the 10 synced agents from plugins/python3-development/agents/ (feature-researcher, codebase-analyzer, context-gathering, context-refinement, plan-validator, feature-verifier, integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher)\n- Verify dh counterparts are complete and correct (done in Phase 1)\n- Update any python3-development skills that reference these agents to use @dh: namespace\n- Update CLAUDE.md and documentation in python3-development to reflect agents-only-in-dh model\n- Verify plugin validator passes for both plugins after removal\n- Add forwarding note in python3-development README pointing to dh for agent access\n\nDependencies: Depends on Phase 1 (dh agents synced) — done. Depends on Phase 3 (backlog lift) — should be done first so backlog agents move before specialist agents are removed."
metadata:
  topic: refactor-deduplicate-agents-between-python3-development-and-
  source: 'GitHub Issue #581 — Development Harness Architecture Refactor, Phase 4'
  added: '2026-03-18'
  priority: P1
  type: Refactor
  status: open
  issue: '#850'
---