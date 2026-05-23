<p align="center">
  <img src="./assets/hero.png" alt="Conventional Commits" width="800" />
</p>

# Conventional Commits

Teaches Claude the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification so commit messages are structured, machine-readable, and useful.

## Why Install This?

When you ask Claude to commit changes without this plugin, you might get:

- "Updated files" (too vague)
- "Fixed bug" (no context, no type)
- Inconsistent casing and formatting across commits
- Messages that break automated changelog tools like semantic-release or git-cliff

This plugin gives Claude full knowledge of the Conventional Commits specification, including type selection, scope, breaking change notation, and how commit types map to semantic version bumps.

## What Changes

With this plugin, Claude will:

- Write commit messages that follow the Conventional Commits v1.0.0 specification
- Choose the correct commit type (`feat`, `fix`, `docs`, `refactor`, etc.)
- Use proper formatting with optional scope and body
- Indicate breaking changes with `!` or `BREAKING CHANGE:` footer
- Use imperative mood and lowercase descriptions
- Add context in the body when the change needs explanation

## Commit Format

```
<type>(<scope>): <description>

[optional body — explains why, not what]

[optional footer — BREAKING CHANGE, Fixes #N, Co-authored-by]
```

### Types and Their SemVer Impact

| Type | Description | SemVer Impact |
|------|-------------|---------------|
| `feat` | New feature | Minor bump (1.x.0) |
| `fix` | Bug fix | Patch bump (1.0.x) |
| `feat!` or `fix!` | Breaking change | Major bump (x.0.0) |
| `docs` | Documentation only | No release |
| `refactor` | Code change, no behavior change | No release |
| `perf` | Performance improvement | No release (patch if desired) |
| `test` | Test additions or corrections | No release |
| `build` | Build system changes | No release |
| `ci` | CI configuration changes | No release |
| `chore` | Routine tasks, dependency updates | No release |
| `style` | Formatting, no logic change | No release |
| `revert` | Reverts a previous commit | Patch bump |

### Breaking Changes

Two ways to indicate a breaking change:

```
feat(api)!: change response format to JSON-API

BREAKING CHANGE: All API responses now follow JSON-API spec.
Clients expecting plain JSON must update their parsers.
```

Or with `BREAKING CHANGE:` in the footer only (without `!`):

```
feat(auth): add OAuth2 support

BREAKING CHANGE: Basic auth endpoints removed. See migration guide.
```

Both approaches trigger a major version bump in semantic-release.

## Examples

```
feat(auth)!: add JWT token validation

Replace basic auth with JWT tokens for improved security.
Sessions now expire after 24 hours.

BREAKING CHANGE: API clients must now include Authorization: Bearer header
```

```
fix(parser): handle empty CSV rows without throwing

Rows with no data were causing an IndexError. Now returns
an empty dict for those rows instead.

Fixes #142
```

```
docs(readme): add quick start section
```

```
refactor(db): extract connection pool into separate module

No behavior change. Improves testability and makes the
pool configurable for different environments.
```

```
chore(deps): upgrade pydantic to 2.7.0
```

## Integration with Other Tools

When used alongside tools that parse commit history:

**semantic-release** — automatically determines version bump from commit types and generates changelog.

**git-cliff** — generates CHANGELOG.md from conventional commit history.

**commitlint** — validates that commits match the specification (install the `commitlint` plugin alongside this one).

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install conventional-commits@jamie-bitflight-skills
```

## Works Well With

- `commitlint@jamie-bitflight-skills` — validates commit messages before they are accepted
- `semantic-release` — automates versioning and changelog generation
- `git-cliff` — generates changelogs from commit history

## Requirements

- Claude Code v2.0+
