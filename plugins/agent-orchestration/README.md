# Agent Orchestration

Scientific delegation framework for orchestrator AIs coordinating specialist sub-agents. Provides world-building context (WHERE, WHAT, WHY) while preserving agent autonomy in implementation decisions (HOW).

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install agent-orchestration@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/agent-orchestration
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [agent-orchestration](./skills/agent-orchestration/SKILL.md) | Used when the model's ROLE_TYPE is orchestrator and needs to delegate tasks to specialist sub-agents. Provides scientific delegation framework ensuring world-building context (WHERE, WHAT, WHY) while preserving agent autonomy in implementation decisions (HOW). Use when planning task delegation, structuring sub-agent prompts, or coordinating multi-agent workflows. |

## Quick Start

When orchestrating sub-agents, activate this skill to access the delegation framework:

```text
@agent-orchestration
```

The skill applies when your ROLE_TYPE is orchestrator and you're using the Task tool for delegation.

### Example Delegation

```text
Your ROLE_TYPE is sub-agent.

Fix linting errors in the project.

OBSERVATIONS:
- User requested: "Fix all linting issues"
- Project uses ruff and mypy (observed in pyproject.toml)

DEFINITION OF SUCCESS:
- Pre-commit hooks pass without errors
- All configured linting rules satisfied
- Solutions follow existing project patterns

CONTEXT:
- Location: Project root
- Python project using uv for dependency management
- Linting configuration in pyproject.toml

YOUR TASK:
1. Run SlashCommand /is-it-done to understand completion criteria
2. Activate holistic-linting skill for linting workflows
3. Run linting tools to gather comprehensive error data
4. Research root causes for each error category
5. Implement fixes following project conventions
6. Verify /is-it-done checklist items satisfied with evidence

AVAILABLE RESOURCES:
- Check <functions> list for MCP tools - prefer specialists over built-in tools
- Python project uses `uv` - activate uv skill, use `uv run`/`uv pip`
- Full project context available including tests and configs
```

## Core Principle

**Provide world-building context (WHERE, WHAT, WHY). Define success criteria. Trust agent expertise for implementation (HOW).**

The orchestrator's role is to:
- Route context and observations between user and agents
- Define measurable success criteria
- Enable comprehensive discovery
- Trust agent expertise and their 200k context windows

Do not prescribe implementation steps (HOW), pre-gather data by running commands before delegation, make assumptions instead of stating observations, or limit agent discovery by restricting tool access.

## License

See [plugin.json](./plugin.json) for license information.
