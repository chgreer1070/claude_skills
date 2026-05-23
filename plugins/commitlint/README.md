<p align="center">
  <img src="./assets/hero.png" alt="Commitlint" width="800" />
</p>

# Commitlint

Gives Claude knowledge of [commitlint](https://commitlint.js.org/) — the tool that validates commit messages against a configured ruleset — so Claude reads your project's configuration and generates messages that pass validation on the first try.

## Why Install This?

If your project uses commitlint to enforce commit message standards, Claude needs this plugin to:

- Read your commitlint configuration and apply your project's specific rules
- Generate commit messages that pass your validation without retry loops
- Set up or modify commitlint configuration with correct syntax
- Explain commitlint validation errors and how to fix them
- Extract commit rules for use in prompt generation (LLM integration pattern)

Without this plugin, Claude may generate commit messages that fail your project's commitlint rules, requiring multiple back-and-forth attempts.

## How commitlint Differs from the conventional-commits Plugin

| Plugin | Purpose |
|--------|---------|
| `conventional-commits` | Teaches Claude the Conventional Commits specification — the message format and type vocabulary |
| `commitlint` | Teaches Claude to read your project's commitlint configuration and apply project-specific rules |

They complement each other. Install `conventional-commits` for the specification knowledge. Install `commitlint` when your project has a commitlint config file that defines additional constraints (allowed types, header length limits, scope requirements, etc.).

## What Changes

With this plugin, Claude will:

- Detect commitlint configuration files in your project (`commitlint.config.js`, `.commitlintrc`, `.commitlintrc.json`, `.commitlintrc.yaml`)
- Extract your specific allowed types, scope rules, header length limits, and other constraints
- Apply those project-specific rules when generating commit messages
- Help you configure commitlint with correct rule syntax and severity levels
- Integrate commitlint with pre-commit hooks and CI pipelines
- Diagnose why a commit message was rejected and how to fix it

## Supported Configuration Formats

```javascript
// commitlint.config.js (ES Modules)
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', ['feat', 'fix', 'docs', 'chore']],
    'header-max-length': [2, 'always', 72],
  },
};
```

```json
// .commitlintrc.json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "scope-enum": [2, "always", ["api", "ui", "db"]]
  }
}
```

```yaml
# .commitlintrc.yaml
extends:
  - "@commitlint/config-conventional"
rules:
  type-enum:
    - 2
    - always
    - [feat, fix, docs, refactor, test, chore]
```

## Common Rules Claude Understands

| Rule | What It Controls |
|------|-----------------|
| `type-enum` | Allowed commit types (`feat`, `fix`, etc.) |
| `header-max-length` | Maximum characters in the first line |
| `scope-enum` | Allowed scope values (e.g., `api`, `ui`) |
| `scope-case` | Case requirement for scope (`lower-case`, `camel-case`) |
| `subject-case` | Case requirement for description |
| `body-max-line-length` | Maximum line length in body |
| `footer-leading-blank` | Require blank line before footer |

## Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
    rev: v9.5.0
    hooks:
      - id: commitlint
        stages: [commit-msg]
        additional_dependencies: ['@commitlint/config-conventional']
```

## Usage

Just install it — it works automatically. Claude detects commitlint configuration in your project and applies those rules when:

- Creating a commit
- Setting up or modifying commitlint configuration
- Explaining a commitlint validation error
- Integrating commitlint with CI or pre-commit hooks

## Example

**Without this plugin:**

You say: "Create a commit for these changes"

Claude writes: `"Updated the authentication system"` — fails because your project requires a `type:` prefix and enforces lowercase.

**With this plugin:**

Same request. Claude reads your `commitlint.config.js`, sees you require `@commitlint/config-conventional` with types `[feat, fix, docs, refactor]` and a 72-character header limit, and generates:

```
feat(auth): add OAuth2 authentication support
```

Which passes validation immediately.

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install commitlint@jamie-bitflight-skills
```

## Works Well With

- `conventional-commits@jamie-bitflight-skills` — provides the Conventional Commits specification knowledge that most commitlint configurations enforce
- `semantic-release` — uses commit types from commitlint-validated history to automate versioning

## Requirements

- Claude Code v2.0+
- commitlint configured in your project (the plugin is most useful when a config file is present)
