# Commitlint

Validate commit messages against Conventional Commits format using commitlint configuration and rules.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install commitlint@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/commitlint
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [commitlint](./skills/commitlint/SKILL.md) | When setting up commit message validation for a project. When project has commitlint.config.js or .commitlintrc files. When configuring CI/CD to enforce commit format. When extracting commit rules for LLM prompt generation. When debugging commit message rejection errors. |

## Quick Start

### Setting Up Commitlint in a Project

```bash
# Install commitlint dependencies
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Create configuration file
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Add to pre-commit hook or CI/CD pipeline
npx commitlint --from HEAD~1 --to HEAD --verbose
```

### Extracting Rules for LLM Prompts

When you need Claude to generate commit messages following your project's commitlint rules, the skill will:

1. Detect commitlint configuration files in your project
2. Parse the rules and shareable configurations
3. Extract validation rules (type-enum, scope-enum, subject-case, etc.)
4. Generate LLM-friendly prompts encoding those rules

This ensures Claude generates commit messages that pass your project's validation.

## Use Cases

- **Setup**: Configure commitlint for a new repository
- **CI/CD Integration**: Add commit message validation to your pipeline
- **LLM Integration**: Generate commit messages that match your commitlint rules
- **Debugging**: Understand why commit messages are rejected
- **Configuration**: Work with commitlint rule syntax and severity levels

## License

See plugin metadata for license information.
