# Prompt Optimization for Claude 4.5

Optimize CLAUDE.md files and Skills for Claude Code CLI. Transforms negative instructions into positive patterns following Anthropic's official best practices.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install prompt-optimization-claude-45@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/prompt-optimization-claude-45
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [prompt-optimization-claude-45](./skills/prompt-optimization-claude-45/SKILL.md) | Optimize CLAUDE.md files and Skills for Claude Code CLI. Use when reviewing, creating, or improving system prompts, CLAUDE.md configurations, or Skill files. Transforms negative instructions into positive patterns following Anthropic's official best practices. |

## Quick Start

Activate the skill when working with AI-facing documentation:

```text
@prompt-optimization-claude-45
Review my CLAUDE.md file and suggest improvements
```

The skill automatically applies Anthropic's prompt engineering best practices:

- **Positive framing** - "Use Y instead" rather than "Never use X"
- **Specificity** - "Use 2-space indentation" instead of "Format properly"
- **Context and motivation** - Explain WHY behind each instruction
- **Structured markdown** - Group related instructions under headings
- **Examples over rules** - Show concrete patterns instead of abstract guidelines

### Example Usage

**Before optimization:**

```markdown
Don't use cat to read files. Never run commands without checking first.
```

**After optimization:**

```markdown
## File Operations

Use the Read tool for all file reading operations.
**Reason**: Provides direct file access with better error handling than shell commands.

## Command Execution

Verify command safety before executing with Bash tool:
1. Check working directory with pwd
2. Validate file paths exist
3. Test commands in safe contexts first
```

## Use Cases

- Creating new CLAUDE.md files for projects
- Optimizing existing system prompts
- Reviewing and improving Skill definitions
- Converting prohibitive language to constructive guidance
- Adding context and motivation to instructions
- Structuring AI-facing documentation

## License

See project LICENSE file.
