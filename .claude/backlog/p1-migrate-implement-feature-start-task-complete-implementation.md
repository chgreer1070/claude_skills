---
name: Migrate implement-feature, start-task, complete-implementation, add-new-feature skills and bookend agents to development-harness
description: "Migrate language-agnostic SAM workflow skills from python3-development to development-harness.\n\nSkills to migrate (all confirmed language-agnostic except noted Python-specific parts):\n\n1. **implement-feature** — SAM execution loop. dh already has identical copy at `workflows/execution/SKILL.md` marked `user-invocable: false`. Make dh version user-invocable, remove python3-dev copy.\n\n2. **start-task** — individual task claim and dispatch. Language-agnostic. Hook path in frontmatter (`${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py`) must be updated after hook scripts migrate (depends on hook script migration item).\n\n3. **complete-implementation** — quality gates after all tasks complete. Language-agnostic EXCEPT Phase 1 hardcodes `code-reviewer` agent (Python-specific). Migration requires resolving code-reviewer via language manifest role resolution.\n\n4. **add-new-feature** — SAM planning pipeline. Language-agnostic EXCEPT Phase 3 hardcodes `python-cli-design-spec` agent. Migration requires resolving architect role via language manifest.\n\n5. **t0-baseline-capture** (agent) — runs check commands, records output. Fully language-agnostic. Move to `dh/agents/`.\n\n6. **tn-verification-gate** (agent) — re-runs checks, compares against baseline. Fully language-agnostic. Move to `dh/agents/`.\n\nSkills that should NOT migrate:\n- `orchestrate` — entirely Python-specific entry point, belongs in python3-development\n\nDependency: Hook script migration must complete first (for start-task hook path)."
metadata:
  topic: migrate-implement-feature-start-task-complete-implementation
  source: 'Session 2026-03-21: skill-migration-comparison report (.claude/reports/skill-migration-comparison-2026-03-21.md)'
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: open
  issue: '#959'
  last_synced: '2026-03-21T13:49:54Z'
  plan: plan/tasks-1-consolidate-sam-workflow-skills.md
---