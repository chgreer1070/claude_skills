# GitLab Skill Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Comprehensive GitLab CI/CD pipeline configuration, GitLab Flavored Markdown (GLFM) documentation, and local testing expertise for Claude Code.

## Features

- **CI/CD Pipeline Configuration**: .gitlab-ci.yml creation, optimization, caching strategies, Docker-in-Docker workflows, and GitLab CI Steps composition
- **GitLab Flavored Markdown**: GLFM syntax for documentation, alert blocks, collapsible sections, Mermaid diagrams, and GitLab-specific references
- **Local Pipeline Testing**: gitlab-ci-local setup, debugging, and validation workflows
- **GitLab CLI Integration**: glab CLI for pipeline monitoring, linting, and CI configuration validation
- **Validation Tools**: Python scripts for GLFM rendering validation and documentation synchronization
- **Token Management**: Automated CI/CD publishing token creation and rotation

## Installation

### Prerequisites

- Claude Code 2.1 or higher
- Git repository with GitLab remote
- Optional: gitlab-ci-local for local testing
- Optional: glab CLI for GitLab operations

### Install Plugin

```bash
# Method 1: Manual installation (if not in marketplace)
git clone <repository-url> ~/.claude/plugins/gitlab-skill
/plugin reload

# Method 2: From marketplace (if published)
/plugin marketplace add <marketplace-url>
/plugin install gitlab-skill
```

## Quick Start

The skill activates automatically when working with GitLab CI/CD configuration or documentation.

**Create a GitLab CI pipeline:**

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - npm test
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
```

**Validate GLFM syntax:**

```bash
uv run --with requests ./scripts/validate-glfm.py --file README.md
```

**Test pipeline locally:**

```bash
gitlab-ci-local test
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | gitlab-skill | CI/CD pipeline configuration, GLFM syntax, gitlab-ci-local testing, GitLab CLI operations | Auto-invoked when working with .gitlab-ci.yml or GLFM |
| Command | /setup-ci-publish-token | Create GitLab project access token for CI/CD publishing | `/setup-ci-publish-token` |

## Usage

### Skills

The **gitlab-skill** covers four capability domains that activate automatically based on your task:

1. **CI/CD Pipeline Configuration** - Triggers when modifying .gitlab-ci.yml, implementing caching, or optimizing pipelines
2. **GitLab Flavored Markdown** - Triggers when writing README files, Wiki pages, or documentation with GitLab-specific syntax
3. **Local Pipeline Testing** - Triggers when testing pipelines locally with gitlab-ci-local
4. **GitLab CLI** - Triggers when using glab for pipeline monitoring, linting, or CI operations

See [Skills Reference](./docs/skills.md) for detailed documentation.

### Commands

**Setup CI Publishing Token** (`/setup-ci-publish-token`):

Creates a GitLab project access token with permissions for publishing releases and uploading artifacts, then adds it as a protected, masked CI/CD variable. Solves the `CI_JOB_TOKEN` limitation for release asset uploads.

See [Commands Reference](./docs/commands.md) for complete usage instructions.

## Configuration

The gitlab-skill automatically maintains up-to-date GitLab CI/CD documentation:

```bash
# Run on first skill activation (auto-executes)
uv run scripts/sync-gitlab-docs.py --working-dir .

# Force update (bypass 3-day cooldown)
uv run scripts/sync-gitlab-docs.py --working-dir . --force
```

No hooks, MCP servers, or LSP servers are configured.

## Examples

### Example 1: Optimize CI/CD Pipeline Caching

**Scenario**: Reduce pipeline execution time by implementing dependency caching.

**Steps**:
1. Claude analyzes your .gitlab-ci.yml
2. Identifies cache opportunities for dependencies
3. Implements cache configuration with proper keys
4. Tests locally with gitlab-ci-local

**Result**: Build time reduced from 5 minutes to 2 minutes by caching node_modules/.

---

### Example 2: Create GLFM Documentation with Alert Blocks

**Scenario**: Write a README with GitLab-specific alert syntax.

**Steps**:
1. Claude writes documentation using GLFM alert blocks
2. Validates syntax: `[!note]`, `[!warning]` (lowercase)
3. Runs validate-glfm.py to confirm rendering
4. Ensures collapsible sections use single-line format

**Result**: Professional GitLab README with properly rendered alerts and collapsible sections.

---

### Example 3: Debug Pipeline Locally

**Scenario**: Test pipeline changes without pushing to GitLab.

**Steps**:
1. Configure gitlab-ci-local authentication
2. Run specific job: `gitlab-ci-local build`
3. Inspect artifacts in .gitlab-ci-local/artifacts/
4. Fix issues and re-test

**Result**: Pipeline validated locally, preventing CI failures after push.

See [Examples Documentation](./docs/examples.md) for more use cases.

## Troubleshooting

### Skill Not Activating

**Symptoms**: GitLab skill doesn't load when editing .gitlab-ci.yml

**Solutions**:
- Ensure file is named `.gitlab-ci.yml` exactly
- Check that plugin is enabled: `/plugin list`
- Reload plugins: `/plugin reload`

### GLFM Validation Fails

**Symptoms**: validate-glfm.py returns errors

**Solutions**:
- Ensure `GITLAB_TOKEN` environment variable is set
- Check token has `api` scope
- Verify alert blocks use lowercase: `[!note]` not `[!NOTE]`
- Confirm `<details><summary>` is single-line format

### gitlab-ci-local Authentication Issues

**Symptoms**: Local pipeline execution fails with authentication errors

**Solutions**:
- Configure tokens in `$HOME/.gitlab-ci-local/variables.yml`
- Set project-specific variables in `.gitlab-ci-local-variables.yml`
- Verify token has required permissions
- Check token hasn't expired

### CI_JOB_TOKEN Permission Errors

**Symptoms**: `401 Unauthorized` when uploading release assets

**Solutions**:
- Run `/setup-ci-publish-token` to create elevated token
- Ensure job runs on protected branch (CI_PUBLISH_TOKEN is protected)
- Use `CI_PUBLISH_TOKEN` instead of `CI_JOB_TOKEN` in scripts
- Verify token hasn't expired: `glab token list`

## Contributing

Contributions are welcome! The plugin structure:

```
plugins/gitlab-skill/
├── .claude-plugin/plugin.json    # Plugin manifest
├── commands/                      # Slash commands
├── skills/gitlab-skill/           # Main skill
│   ├── SKILL.md                  # Skill instructions
│   ├── references/               # Domain-specific docs
│   └── scripts/                  # Validation utilities
└── README.md                      # This file
```

## License

No license specified.

## Credits

Created for GitLab CI/CD workflow optimization and GLFM documentation standards.
