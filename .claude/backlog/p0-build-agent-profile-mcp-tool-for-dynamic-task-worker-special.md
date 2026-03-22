---
name: Build agent-profile MCP tool for dynamic task-worker specialization via skill bundling
description: "Build an MCP tool that dynamically compiles agent definitions into loadable skill bundles for the task-worker.\n\nConcept: The task-worker needs to become any specialist by loading the right skills. Currently this requires knowing which skills to load. An MCP tool can automate this by reading an agent definition file, parsing its skills: frontmatter, recursively resolving each skill (SKILL.md + references/), and returning the complete agent prompt with all skill content bundled.\n\nExample flow:\n1. SAM task metadata says: agent: python-cli-architect\n2. Task-worker calls: load_agent_profile('python-cli-architect')\n3. MCP tool reads: plugins/python3-development/agents/python-cli-architect.md\n4. Parses frontmatter: skills: [python3-development, python-cli-architect]\n5. For each skill: reads SKILL.md, resolves references/ contents\n6. Returns: bundled prompt = agent body + all skill content concatenated\n7. Task-worker injects this into its context and becomes the specialist\n\nFastMCP capabilities to use:\n- SkillsDirectoryProvider for accessing skill files\n- @mcp.prompt for parameterized agent profile prompts\n- PromptsAsTools to expose prompts as callable tools\n- mount() + Namespace for composing with existing sam/backlog servers\n\nThis replaces the current pattern where the orchestrator must know which subagent_type to route to. The task-worker self-configures by loading the agent profile that matches its task metadata.\n\nAlso applies to grooming: instead of the orchestrator spawning 5 different agent types (impact-analyst, fact-checker, etc.), the grooming swarm uses task-workers that load role-specific grooming skills. The roles become skills, not agent types."
metadata:
  topic: build-agent-profile-mcp-tool-for-dynamic-task-worker-special
  source: 'Session 2026-03-22: designing peak customization for task-worker agent composition'
  added: '2026-03-22'
  priority: P0
  type: Feature
  status: open
  issue: '#979'
  last_synced: '2026-03-22T01:19:03Z'
---