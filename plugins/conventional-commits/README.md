# Conventional Commits Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A Claude Code plugin providing comprehensive guidance for writing commit messages following the Conventional Commits v1.0.0 specification. Enables automated changelog generation, semantic versioning, and structured commit history.

## Features

- Complete Conventional Commits v1.0.0 specification reference
- Commit type guidance (feat, fix, docs, etc.) with SemVer impact
- Breaking change notation (BREAKING CHANGE and ! syntax)
- Validation patterns and examples
- Integration with commitlint, semantic-release, and git-cliff
- Best practices from Angular commit guidelines
- Comprehensive examples for all commit scenarios

## Installation

### Prerequisites

- Claude Code version 2.1 or later
- Git repository (for commit message usage)

### Install Plugin

**Method 1: From Marketplace** (if published)

```bash
cc plugin marketplace add owner/repo
cc plugin install conventional-commits@marketplace-name
```

**Method 2: Manual Installation**

```bash
# Clone or copy to Claude plugins directory
git clone <repository-url> ~/.claude/plugins/conventional-commits
cc plugin reload
```

### Verify Installation

```bash
cc plugin list
```

You should see `conventional-commits` in the enabled plugins list.

## Quick Start

When writing a commit message, Claude will automatically activate this skill to ensure compliance with Conventional Commits format:

```bash
git add .
# Claude will help format your commit message
```

Basic commit message structure:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Common Examples

```bash
# Feature addition
feat: add user authentication

# Bug fix
fix: prevent crash on empty input

# Breaking change
feat!: remove support for Node 6

# With scope
feat(api): add new endpoint for user profiles

# With body and footer
fix: prevent racing of requests

Introduce a request id and reference to latest request.
Dismiss incoming responses other than from latest request.

Refs: #123
```

## Usage

### Automatic Activation

The conventional-commits skill is automatically activated by Claude when:

- Writing a git commit message
- Task completes and changes need committing
- Project uses semantic-release, commitizen, or git-cliff
- Choosing between commit types (feat/fix/chore/docs)
- Indicating breaking changes
- Generating changelogs from commit history

### Manual Activation

You can explicitly invoke the skill:

```text
@conventional-commits
```

Or programmatically:

```text
Skill(command: "conventional-commits")
```

### Core Concepts

#### Commit Types

| Type | Description | SemVer Impact | Example |
|------|-------------|---------------|---------|
| `feat` | New feature for users | MINOR (0.X.0) | `feat: add user authentication` |
| `fix` | Bug fix for users | PATCH (0.0.X) | `fix: prevent crash on empty input` |
| `docs` | Documentation changes | None | `docs: update API reference` |
| `style` | Code style changes | None | `style: fix indentation` |
| `refactor` | Code change with no fix/feature | None | `refactor: extract validation logic` |
| `perf` | Performance improvement | None | `perf: reduce bundle size by 20%` |
| `test` | Test additions/corrections | None | `test: add unit tests for parser` |
| `build` | Build system changes | None | `build: update webpack to v5` |
| `ci` | CI configuration changes | None | `ci: add Node 18 to test matrix` |
| `chore` | Other changes | None | `chore: update .gitignore` |
| `revert` | Revert previous commit | None | `revert: feat: add user auth` |

#### Breaking Changes

Three ways to indicate breaking changes (all trigger MAJOR version bump):

**1. Footer notation:**

```text
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

**2. Type suffix with `!`:**

```text
feat!: remove support for Node 6
```

**3. Type+scope suffix with `!`:**

```text
feat(api)!: send email when product shipped
```

#### Description Best Practices

- Use imperative, present tense: "change" not "changed" nor "changes"
- Do not capitalize first letter
- No period (.) at the end
- Keep entire header under 72 characters

**Good:**

```text
feat: add validation for email input
fix: handle null pointer in user service
```

**Bad:**

```text
feat: Added validation for email input     # Past tense
fix: Handles null pointer in user service  # Third person
docs: Update installation instructions.    # Period, capitalized
```

## Integration with Tools

### commitlint

Validate commits automatically:

```bash
# Install commitlint
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Create configuration
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Test commit message
echo 'feat(api): add new endpoint' | npx commitlint
```

For comprehensive commitlint setup, use the `commitlint` skill if available.

### semantic-release

Automate versioning and changelog generation:

```javascript
// release.config.js
module.exports = {
  branches: ['main'],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
  ],
};
```

### git-cliff

Generate changelogs from commit history:

```toml
# cliff.toml
[git]
conventional_commits = true
```

### Pre-commit Hooks

Enforce commit format with pre-commit hooks. Use the `pre-commit` skill if available for complete setup guidance.

## Examples

### Feature Development

```text
feat(auth): add OAuth2 authentication

Implement OAuth2 flow with support for Google and GitHub providers.
Add configuration options for client ID and secret.

Refs: #456
```

### Bug Fixes

```text
fix(parser): handle edge case in array parsing

Previously failed when array contained strings with multiple spaces.
Now correctly tokenizes and preserves spacing.

Fixes: #789
```

### Breaking Changes

```text
feat(api)!: redesign user authentication API

BREAKING CHANGE: Authentication endpoints moved from /auth/* to /api/v2/auth/*.
Clients must update endpoint URLs. Token format remains unchanged.

Migration guide: docs/migration-v2.md
Refs: #123
```

### Performance Improvements

```text
perf(parser): reduce memory allocation by 40%

Replace string concatenation with StringBuilder pattern.
Benchmark results show 40% reduction in heap allocations
for typical 1MB input files.

Refs: #456
```

### Refactoring

```text
refactor(auth): extract validation into separate module

Move validation functions from auth.py to validators.py.
No functional changes. Improves testability and reusability.
```

### Documentation and Chores

```text
docs: add troubleshooting section to README
```

```text
chore: update dependencies to latest stable versions
```

```text
ci: add Node 18 and 20 to test matrix
```

## Benefits

Using Conventional Commits provides:

1. **Automated Changelog Generation** - Tools parse commit history and generate release notes
2. **Automated Semantic Versioning** - Version bumps determined by commit types
3. **Clear Communication** - Teammates and stakeholders understand change nature
4. **CI/CD Integration** - Pipelines react to specific commit types
5. **Easier Contribution** - Structured history aids exploration and onboarding

## Semantic Versioning Correlation

| Commit Pattern | Version Bump | Example |
|----------------|--------------|---------|
| `fix: ...` | PATCH (0.0.X) | 1.0.0 → 1.0.1 |
| `feat: ...` | MINOR (0.X.0) | 1.0.0 → 1.1.0 |
| `BREAKING CHANGE` or `!` | MAJOR (X.0.0) | 1.0.0 → 2.0.0 |

## Troubleshooting

### Commit message rejected by commitlint

**Error:** `type must be one of [...]`

**Solution:** Ensure you're using a valid commit type. The most common types are:
- `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

### Changelog not including my commits

**Cause:** Commits may not follow Conventional Commits format or use non-standard types.

**Solution:** Ensure all commits use `feat`, `fix`, or include `BREAKING CHANGE` for changelog inclusion. Other types may be excluded depending on your changelog tool configuration.

### Wrong version bump

**Cause:** Incorrect commit type used (e.g., `chore` instead of `fix`).

**Solution:** Before merging, use `git rebase -i` to edit commit messages. After release, you may need a manual version bump and new release.

### Breaking change not detected

**Cause:** Missing `BREAKING CHANGE:` footer or `!` in type.

**Solution:** Breaking changes must be explicitly marked:
- Add `!` after type: `feat!: ...`
- Or include footer: `BREAKING CHANGE: description`

## Frequently Asked Questions

**Can I use custom types?**

Yes. Types beyond `feat` and `fix` are allowed but have no implicit SemVer effect. Common additions include `wip`, `deps`, `security`.

**Is the specification case-sensitive?**

Most tools normalize to lowercase. Exception: `BREAKING CHANGE` must be uppercase. Best practice: be consistent.

**What about merge commits?**

Merge commits are typically ignored by changelog generators and don't need to follow the format.

**Do all contributors need to use this format?**

Not necessarily. With squash-based workflows, maintainers can clean up commit messages when merging pull requests.

## Related Skills

- **commitlint** - Configure and use commitlint for commit message validation
- **pre-commit** - Set up pre-commit hooks for automated validation
- **git-commit-helper** - Generate commit messages from git diffs
- **semantic-release** - Automate versioning and changelog generation

## Specification References

- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) - Official specification
- [Semantic Versioning (SemVer)](https://semver.org/) - Versioning standard
- [Angular Commit Guidelines](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md) - Inspiration for format
- [@commitlint/config-conventional](https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional) - Reference implementation
- [semantic-release](https://github.com/semantic-release/semantic-release) - Automated versioning tool
- [git-cliff](https://github.com/orhun/git-cliff) - Changelog generator

## Contributing

Contributions are welcome! When submitting changes:

1. Follow the Conventional Commits format (of course!)
2. Include tests for new functionality
3. Update documentation as needed
4. Ensure all validation passes

## License

Check the LICENSE file in the plugin directory for license information.

## Credits

This plugin implements the [Conventional Commits v1.0.0 specification](https://www.conventionalcommits.org/), which was inspired by the [Angular commit guidelines](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md).
