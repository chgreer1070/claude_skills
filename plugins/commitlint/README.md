# commitlint

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Validate and configure commit message standards using commitlint in Claude Code. This plugin helps you set up, configure, and troubleshoot commitlint for enforcing Conventional Commits format across your projects.

## Features

- **Configuration Detection** - Identify commitlint config files across all supported formats (JS, TS, JSON, YAML)
- **Rule Extraction** - Parse commitlint rules and convert them to LLM-friendly prompts for commit message generation
- **Validation Integration** - Programmatically validate commit messages against project rules
- **Comprehensive Rule Reference** - Complete documentation of all commitlint rules with examples
- **LLM Integration Patterns** - Code examples for integrating commitlint with AI-powered commit tools
- **Troubleshooting Guidance** - Common issues and solutions for commitlint configuration

## Installation

### Prerequisites

- **Claude Code**: Version 2.1 or higher
- **Node.js**: Version 18 or higher (if using commitlint CLI)
- **npm/yarn/pnpm**: For installing commitlint packages

### Install Plugin

```bash
# Using the plugin system
cc plugin install commitlint

# Manual installation
git clone <repository-url> ~/.claude/plugins/commitlint
cc plugin reload
```

## Quick Start

When working with commit message validation or configuring commitlint:

```text
@commitlint help me set up commitlint with the conventional config
```

Claude will automatically activate the commitlint skill and guide you through:
1. Installing required packages
2. Creating the appropriate config file for your project
3. Setting up pre-commit hooks or CI/CD integration
4. Configuring custom rules if needed

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | commitlint | Validate commit messages, configure rules, integrate with CI/CD, extract rules for LLM prompts, debug validation errors | `@commitlint` |

## Usage

### Automatic Activation

Claude automatically activates this skill when you:

- Mention setting up commitlint for a repository
- Work with `commitlint.config.js` or `.commitlintrc` files
- Configure CI/CD to enforce commit message format
- Need to extract commit rules for generating prompts
- Debug commit message rejection errors

### Manual Activation

Explicitly activate the skill:

```text
@commitlint
```

### Common Use Cases

**Setting Up Commitlint:**

```text
@commitlint configure this project to use conventional commits with a 72 character limit
```

**Extracting Rules for AI Integration:**

```text
@commitlint read the commitlint config and generate validation rules I can use in my commit message generator
```

**Troubleshooting:**

```text
@commitlint my commit message "Fix: bug" is being rejected, why?
```

**Custom Rule Configuration:**

```text
@commitlint add a rule that only allows these types: feat, fix, docs, test
```

## Configuration

This plugin provides one skill with comprehensive commitlint knowledge. No additional configuration is required. The skill includes:

- Detection of all commitlint configuration file formats
- Complete rule reference with examples
- CLI usage patterns
- Programmatic validation integration
- LLM-specific integration patterns for commit message generation

## Examples

### Example 1: Initial Setup

**Scenario**: You want to enforce conventional commits on a new project

**Steps**:

1. Activate the skill: `@commitlint set up conventional commits`
2. Claude guides you through installation
3. Creates appropriate config file
4. Suggests pre-commit hook integration

**Result**: Project configured with `@commitlint/config-conventional` and validation hooks

### Example 2: Custom Type Restrictions

**Scenario**: Your team only uses specific commit types

**Steps**:

1. Ask: `@commitlint configure rules for only feat, fix, docs, and test types`
2. Claude creates config with custom `type-enum` rule
3. Provides example valid/invalid messages

**Code**:
```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', ['feat', 'fix', 'docs', 'test']],
  },
};
```

**Result**: Commitlint rejects commits with other types like 'chore' or 'refactor'

### Example 3: LLM Integration

**Scenario**: Building a tool that generates commit messages and needs validation

**Steps**:

1. Ask: `@commitlint show me how to validate messages programmatically`
2. Claude provides Node.js code examples
3. Explains validation loop pattern for LLM retry logic

**Code**:
```javascript
import load from '@commitlint/load';
import lint from '@commitlint/lint';

async function validateMessage(message) {
  const config = await load();
  const result = await lint(message, config.rules);

  return {
    valid: result.valid,
    errors: result.errors,
    warnings: result.warnings,
  };
}
```

**Result**: Programmatic validation integrated into commit message generation workflow

## Skill Reference

### commitlint

**Description**: Validate commit messages against Conventional Commits format using commitlint configuration and rules.

**When to Use**:
- Setting up commitlint for a repository
- Configuring commitlint rules and shareable configurations
- Integrating commitlint with pre-commit hooks or CI/CD pipelines
- Extracting rules from commitlint config to generate LLM prompts for commit message generation
- Validating commit messages programmatically
- Troubleshooting commitlint configuration or validation errors
- Understanding commitlint rule syntax and severity levels
- Detecting commitlint configuration files in a repository

**Key Knowledge Areas**:

1. **Configuration Formats** - JavaScript (ES/CJS), TypeScript, JSON, YAML, package.json
2. **Rule System** - Severity levels (0=disabled, 1=warning, 2=error), applicability (always/never)
3. **Common Configurations** - `@commitlint/config-conventional` with full rule table
4. **CLI Usage** - All command-line options and exit codes
5. **Programmatic API** - `@commitlint/load` and `@commitlint/lint` usage
6. **LLM Integration** - Patterns for extracting rules and validation loops

**Related Skills**:
- `pre-commit` - For pre-commit hook integration
- `conventional-commits` - For Conventional Commits format specification

**References in Skill**:
- [Commitlint Official Site](https://commitlint.js.org/)
- [Configuration Reference](https://commitlint.js.org/reference/configuration.html)
- [Rules Reference](https://commitlint.js.org/reference/rules.html)
- [CLI Reference](https://commitlint.js.org/reference/cli.html)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)

## Troubleshooting

### Issue: Config file not found

**Symptom**: `commitlint` reports no configuration found

**Solution**: Ensure you have one of the supported config file names in your project root:
- `commitlint.config.js` (recommended for ES modules)
- `.commitlintrc.json`
- `commitlint` field in `package.json`

See skill documentation for complete list of supported formats.

### Issue: "Please add rules" error

**Symptom**: Empty configuration causes validation to fail

**Solution**: Add at least `extends` or `rules` to your config:

```javascript
export default {
  extends: ['@commitlint/config-conventional'],
};
```

### Issue: Subject case validation confusion

**Symptom**: Commits rejected for case issues despite appearing correct

**Solution**: `@commitlint/config-conventional` uses `never` with specific cases, meaning those cases are **forbidden** (not required). Lowercase subjects without sentence case, start case, pascal case, or upper case will pass.

### Issue: Node v24 ESM compatibility

**Symptom**: Config file fails to load in Node v24+

**Solution**: Use `.mjs` extension or add `"type": "module"` to package.json

## Contributing

Contributions to improve this plugin are welcome. When contributing:

1. Ensure documentation remains accurate to official commitlint specification
2. Include source citations for any new rules or configuration patterns
3. Test examples with actual commitlint CLI
4. Update version in plugin.json

## License

This plugin is provided as-is for use with Claude Code.

## Credits

Created for Claude Code plugin system. Based on official commitlint documentation and the commit-polish repository (2025-12-01).
