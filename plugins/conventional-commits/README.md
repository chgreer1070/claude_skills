# Conventional Commits

Compose commit messages following the Conventional Commits v1.0.0 specification for structured commit history, automated changelog generation, and semantic versioning.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install conventional-commits@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/conventional-commits
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [conventional-commits](./skills/conventional-commits/SKILL.md) | When writing a git commit message. When task completes and changes need committing. When project uses semantic-release, commitizen, git-cliff. When choosing between feat/fix/chore/docs types. When indicating breaking changes. When generating changelogs from commit history. |

## Quick Start

When you need to create a commit message, Claude will automatically activate this skill based on context, or you can explicitly invoke it:

```text
@conventional-commits
Create a commit message for the changes I just made
```

**Example output:**

```text
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh using refresh tokens
to maintain user sessions without re-authentication.

- Add RefreshTokenService with rotation logic
- Update AuthInterceptor to handle 401 responses
- Add token expiry detection and refresh flow

Refs: #234
```

## Message Format

The skill guides you to create properly structured commit messages:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Common types:**
- `feat` - New feature (triggers minor version bump)
- `fix` - Bug fix (triggers patch version bump)
- `docs` - Documentation changes
- `style` - Code style changes (formatting, no logic change)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Breaking changes:** Use `BREAKING CHANGE:` footer or `!` after type/scope to indicate breaking changes (triggers major version bump).

## Version

1.0.0
