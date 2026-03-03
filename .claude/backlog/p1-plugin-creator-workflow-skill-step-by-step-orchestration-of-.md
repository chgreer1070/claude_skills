---
name: plugin-creator workflow skill — step-by-step orchestration of assess, research, design, debug, create, optimize, and verify phases
description: 'The plugin-creator plugin lacks a unified workflow skill that guides users through the full plugin lifecycle in the correct sequence. Currently, individual skills and agents exist (assessor, skill-creator, agent-creator, refactor-plugin, etc.) but there is no single entry point that chains them together with the right handoffs, decision gates, and phase transitions. Users and orchestrators must know which skill to invoke at each phase, what artifacts each phase produces, and what conditions trigger moving to the next phase. Success looks like: a single /plugin-creator:plugin-lifecycle (or similar) skill that defines the ordered phases, names the correct skill/agent for each phase, specifies the input artifacts and output artifacts per phase, includes decision gates (e.g., skip research if plugin already exists, skip debug if no errors), and handles the full lifecycle from blank canvas to marketplace-ready plugin. The skill is working when an orchestrator can follow it end-to-end and produce a validated, linted plugin without needing to know the plugin-creator internals.'
metadata:
  topic: plugin-creator-workflow-skill-step-by-step-orchestration-of-
  source: User request
  added: '2026-03-02'
  priority: P1
  type: Feature
  status: open
  issue: '#427'
  last_synced: '2026-03-03T14:07:09Z'
  groomed: '2026-03-03'
---

## Groomed (2026-03-03)

### Issue Classification

**Type**: unbounded-design
**Rationale**: New capability with open solution space; no traceable failure, no prior recurrence. Phase sequence, gate conditions, and artifact schema must be designed from scratch.
**Analysis Method**: design-framing
**Scenario Target**: Orchestrator/user building a plugin from scratch → follows a single skill end-to-end without knowing plugin-creator internals

## Groomed (2026-03-03)

### Priority

P1 — Blocks orchestrators from executing unified plugin lifecycle workflows; creates friction where users must manually chain skills in the correct sequence.

### Impact

Blocks users and orchestrators building plugins end-to-end without internal knowledge of plugin-creator internals. No single entry point exists — currently distributed across /plugin-creator, /assessor, /refactor-plugin, /skill-creator, /agent-creator, /lint — users must know which to call when.

### Expected Behavior

The skill guides users through seven phases in sequence:

1. **Assess** — current state analysis of the plugin (if existing) or blank canvas setup
2. **Research** — domain research and documentation discovery (skip if plugin already ready)
3. **Design** — architecture specification and component planning
4. **Debug** — identification and fix of structure/validation errors (skip if no errors found)
5. **Create** — implementation of plugins, agents, skills, or commands
6. **Optimize** — refactoring for quality, size, complexity, and performance
7. **Verify** — final validation, linting, and marketplace readiness

Each phase names the correct skill or agent to invoke, specifies input artifacts, defines output artifacts, and includes decision gates to branch or skip based on conditions.

### Acceptance Criteria

1. Skill file exists at plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md with valid frontmatter
2. Skill documents all seven phases with a Mermaid flowchart showing decision gates and phase transitions
3. For each phase: correct skill/agent to invoke, required input artifacts, expected output artifacts, and completion condition are documented
4. Decision gates use observable conditions (e.g., 'If validation report shows errors → Debug; if no errors → Optimize')
5. An orchestrator can follow the skill end-to-end and reach a marketplace-ready plugin without consulting plugin-creator internals
6. Skill passes plugin_validator.py with no SK006/SK007 warnings
7. References section documents which existing skills are composed

### Skills

plugin-creator:plugin-creator, plugin-creator:assessor, plugin-creator:refactor-plugin, plugin-creator:skill-creator, plugin-creator:agent-creator, plugin-creator:lint, plugin-creator:ensure-complete

### Agents

plugin-assessor, refactor-planner

### Files

plugins/plugin-creator/CLAUDE.md, plugins/plugin-creator/.claude-plugin/plugin.json

### Dependencies

None — all required skills and agents already exist. Blocks no downstream items.

### Effort

Medium — requires designing phase sequence logic, decision gates, and artifact schema by composing existing skills into a documented workflow. No new skill/agent creation needed.