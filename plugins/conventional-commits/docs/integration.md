# Tool Integration Guide

This guide provides detailed instructions for integrating Conventional Commits with popular development tools and workflows.

## commitlint

Validate commit messages against Conventional Commits specification.

### Installation

```bash
npm install --save-dev @commitlint/cli @commitlint/config-conventional
```

### Configuration

**Basic Configuration** (`commitlint.config.js`):

```javascript
module.exports = {
  extends: ['@commitlint/config-conventional']
};
```

**Custom Configuration**:

```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'perf',
        'test',
        'build',
        'ci',
        'chore',
        'revert',
        'wip'  // Add custom type
      ]
    ],
    'scope-enum': [
      2,
      'always',
      ['api', 'ui', 'db', 'auth', 'core']  // Enforce specific scopes
    ],
    'header-max-length': [2, 'always', 72],
    'body-leading-blank': [2, 'always'],
    'footer-leading-blank': [2, 'always']
  }
};
```

### Usage

**Test commit message**:

```bash
echo 'feat(api): add user endpoint' | npx commitlint
```

**Lint last commit**:

```bash
npx commitlint --from HEAD~1 --to HEAD --verbose
```

**Lint commit range**:

```bash
npx commitlint --from main --to HEAD
```

### Git Hook Integration

**Using Husky**:

```bash
# Install husky
npm install --save-dev husky

# Enable Git hooks
npx husky install

# Add commit-msg hook
npx husky add .husky/commit-msg 'npx --no -- commitlint --edit $1'
```

**Manual Hook** (`.git/hooks/commit-msg`):

```bash
#!/bin/sh
npx --no -- commitlint --edit $1
```

Make executable:

```bash
chmod +x .git/hooks/commit-msg
```

### CI/CD Validation

**GitHub Actions** (`.github/workflows/commitlint.yml`):

```yaml
name: Commitlint

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Validate PR commits
        run: npx commitlint --from ${{ github.event.pull_request.base.sha }} --to HEAD --verbose
```

**GitLab CI** (`.gitlab-ci.yml`):

```yaml
commitlint:
  image: node:20
  stage: test
  before_script:
    - npm ci
  script:
    - npx commitlint --from main --to HEAD --verbose
  only:
    - merge_requests
```

---

## semantic-release

Automate version management and changelog generation.

### Installation

```bash
npm install --save-dev semantic-release
npm install --save-dev @semantic-release/changelog @semantic-release/git
```

### Configuration

**Basic Configuration** (`.releaserc.json`):

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/npm",
    "@semantic-release/github"
  ]
}
```

**Advanced Configuration** (`.releaserc.js`):

```javascript
module.exports = {
  branches: [
    'main',
    'next',
    { name: 'beta', prerelease: true },
    { name: 'alpha', prerelease: true }
  ],
  plugins: [
    // Analyze commits to determine version bump
    [
      '@semantic-release/commit-analyzer',
      {
        preset: 'conventionalcommits',
        releaseRules: [
          { type: 'docs', scope: 'README', release: 'patch' },
          { type: 'refactor', release: 'patch' },
          { type: 'style', release: 'patch' },
          { type: 'perf', release: 'patch' }
        ]
      }
    ],
    // Generate release notes
    [
      '@semantic-release/release-notes-generator',
      {
        preset: 'conventionalcommits',
        presetConfig: {
          types: [
            { type: 'feat', section: 'Features' },
            { type: 'fix', section: 'Bug Fixes' },
            { type: 'perf', section: 'Performance Improvements' },
            { type: 'revert', section: 'Reverts' },
            { type: 'docs', section: 'Documentation', hidden: false },
            { type: 'style', section: 'Styles', hidden: true },
            { type: 'chore', section: 'Miscellaneous', hidden: true },
            { type: 'refactor', section: 'Code Refactoring', hidden: false },
            { type: 'test', section: 'Tests', hidden: true },
            { type: 'build', section: 'Build System', hidden: true },
            { type: 'ci', section: 'Continuous Integration', hidden: true }
          ]
        }
      }
    ],
    // Update CHANGELOG.md
    [
      '@semantic-release/changelog',
      {
        changelogFile: 'CHANGELOG.md'
      }
    ],
    // Update package.json version
    '@semantic-release/npm',
    // Commit updated files
    [
      '@semantic-release/git',
      {
        assets: ['CHANGELOG.md', 'package.json', 'package-lock.json'],
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
      }
    ],
    // Create GitHub release
    '@semantic-release/github'
  ]
};
```

### GitHub Actions Workflow

**Release on Push** (`.github/workflows/release.yml`):

```yaml
name: Release

on:
  push:
    branches:
      - main

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npx semantic-release
```

### Dry Run (Testing)

```bash
npx semantic-release --dry-run
```

---

## git-cliff

Generate changelogs from git history.

### Installation

```bash
# Using Cargo
cargo install git-cliff

# Using Homebrew (macOS)
brew install git-cliff

# Using Scoop (Windows)
scoop install git-cliff

# Using npm
npm install -g git-cliff
```

### Configuration

**Basic Configuration** (`cliff.toml`):

```toml
[git]
conventional_commits = true
filter_unconventional = false
split_commits = false

[changelog]
header = """
# Changelog

All notable changes to this project will be documented in this file.\n
"""
body = """
{% for group, commits in commits | group_by(attribute="group") %}
    ## {{ group | upper_first }}
    {% for commit in commits %}
        - {{ commit.message | upper_first }} ([{{ commit.id | truncate(length=7, end="") }}]({{ commit.id }}))
    {% endfor %}
{% endfor %}
"""
trim = true

[commit_parsers]
# Default parsers for conventional commits
commit_parsers = [
    { message = "^feat", group = "Features" },
    { message = "^fix", group = "Bug Fixes" },
    { message = "^doc", group = "Documentation" },
    { message = "^perf", group = "Performance" },
    { message = "^refactor", group = "Refactoring" },
    { message = "^style", group = "Styling" },
    { message = "^test", group = "Testing" },
    { message = "^chore\\(release\\):", skip = true },
    { message = "^chore", group = "Miscellaneous" },
    { body = ".*security", group = "Security" },
]
```

**Advanced Configuration**:

```toml
[git]
conventional_commits = true
filter_unconventional = false
filter_commits = true
tag_pattern = "v[0-9]*"
skip_tags = "v0.1.0-beta.1"
ignore_tags = ""
topo_order = false
sort_commits = "oldest"

[changelog]
header = """
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n
"""
body = """
{% if version %}\
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
    ## [Unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | upper_first }}
    {% for commit in commits %}
        - {% if commit.scope %}**{{ commit.scope }}:** {% endif %}{{ commit.message | upper_first }} ([{{ commit.id | truncate(length=7, end="") }}](https://github.com/yourorg/yourrepo/commit/{{ commit.id }}))
        {%- if commit.breaking %} **BREAKING** {% endif %}
    {% endfor %}
{% endfor %}\n
"""
footer = """
[unreleased]: https://github.com/yourorg/yourrepo/compare/{{ tag }}...HEAD
"""
trim = true

[commit_parsers]
commit_parsers = [
    { message = "^feat", group = "Features" },
    { message = "^fix", group = "Bug Fixes" },
    { message = "^docs", group = "Documentation" },
    { message = "^perf", group = "Performance" },
    { message = "^refactor", group = "Refactoring" },
    { message = "^style", group = "Styling" },
    { message = "^test", group = "Testing" },
    { message = "^build", group = "Build" },
    { message = "^ci", group = "CI/CD" },
    { message = "^chore\\(release\\):", skip = true },
    { message = "^chore", group = "Miscellaneous Tasks" },
    { message = "^revert", group = "Reverts" },
    { body = ".*security", group = "Security" },
    { message = "^[Bb]reaking[- ]?[Cc]hange", group = "Breaking Changes" },
]
```

### Usage

**Generate full changelog**:

```bash
git cliff --output CHANGELOG.md
```

**Generate changelog for specific range**:

```bash
git cliff --tag v1.0.0..v2.0.0 --output CHANGELOG-v2.md
```

**Generate unreleased changes**:

```bash
git cliff --unreleased --tag v2.0.0
```

**Update existing changelog**:

```bash
git cliff --unreleased --tag v2.1.0 --prepend CHANGELOG.md
```

### GitHub Actions Integration

```yaml
name: Changelog

on:
  push:
    tags:
      - 'v*'

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        uses: orhun/git-cliff-action@v3
        with:
          config: cliff.toml
          args: --verbose
        env:
          OUTPUT: CHANGELOG.md

      - name: Commit changelog
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email 'github-actions[bot]@users.noreply.github.com'
          git add CHANGELOG.md
          git commit -m "docs: update CHANGELOG for ${{ github.ref_name }}"
          git push
```

---

## Pre-commit Hooks

Enforce commit message format before commit is created.

### Using pre-commit Framework

**Installation**:

```bash
pip install pre-commit
```

**Configuration** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args:
          - feat
          - fix
          - docs
          - style
          - refactor
          - perf
          - test
          - build
          - ci
          - chore
          - revert

  # Optional: Run commitlint
  - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
    rev: v9.11.0
    hooks:
      - id: commitlint
        stages: [commit-msg]
        additional_dependencies: ['@commitlint/config-conventional']
```

**Install hooks**:

```bash
pre-commit install --hook-type commit-msg
```

### Using Commitizen

Interactive commit message builder.

**Installation**:

```bash
npm install -g commitizen cz-conventional-changelog
```

**Initialize**:

```bash
commitizen init cz-conventional-changelog --save-dev --save-exact
```

**Configuration** (`package.json`):

```json
{
  "config": {
    "commitizen": {
      "path": "cz-conventional-changelog"
    }
  }
}
```

**Usage**:

```bash
git add .
git cz
```

Interactive prompts:
```
? Select the type of change: (Use arrow keys)
❯ feat:     A new feature
  fix:      A bug fix
  docs:     Documentation only changes
  style:    Changes that don't affect code meaning
  refactor: A code change that neither fixes a bug nor adds a feature
  perf:     A code change that improves performance
  test:     Adding missing tests
```

---

## CI/CD Integration

### GitHub Actions

**Validate PR Titles** (`.github/workflows/pr-title.yml`):

```yaml
name: PR Title Check

on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  check-title:
    runs-on: ubuntu-latest
    steps:
      - uses: amannn/action-semantic-pull-request@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          types: |
            feat
            fix
            docs
            style
            refactor
            perf
            test
            build
            ci
            chore
            revert
          requireScope: false
          subjectPattern: ^[a-z].+$
          subjectPatternError: |
            The subject "{subject}" found in the pull request title "{title}"
            didn't match the configured pattern. Please ensure that the subject
            starts with a lowercase letter.
```

**Auto-label PRs** (`.github/workflows/auto-label.yml`):

```yaml
name: Auto Label

on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/labeler@v5
        with:
          configuration-path: .github/labeler.yml
          repo-token: ${{ secrets.GITHUB_TOKEN }}
```

**Labeler Configuration** (`.github/labeler.yml`):

```yaml
'feature':
  - head-branch: '^feat/'
  - title: '^feat(\(.*\))?:'

'bug':
  - head-branch: '^fix/'
  - title: '^fix(\(.*\))?:'

'documentation':
  - head-branch: '^docs/'
  - title: '^docs(\(.*\))?:'

'refactoring':
  - head-branch: '^refactor/'
  - title: '^refactor(\(.*\))?:'

'breaking-change':
  - title: '!:'
  - body: 'BREAKING CHANGE'
```

### GitLab CI

**Validate Commits** (`.gitlab-ci.yml`):

```yaml
stages:
  - validate
  - test
  - release

validate-commits:
  stage: validate
  image: node:20
  before_script:
    - npm install -g @commitlint/cli @commitlint/config-conventional
  script:
    - echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js
    - npx commitlint --from $CI_MERGE_REQUEST_DIFF_BASE_SHA --to HEAD --verbose
  only:
    - merge_requests

release:
  stage: release
  image: node:20
  before_script:
    - npm ci
  script:
    - npx semantic-release
  only:
    - main
  except:
    - tags
```

---

## Development Workflow Best Practices

### Branch Naming Convention

Align branch names with commit types:

```bash
feat/user-authentication
fix/session-timeout
docs/api-reference
refactor/auth-module
perf/database-queries
```

### Commit Message Template

**Create template** (`.gitmessage`):

```text
# <type>[optional scope]: <description>
#
# [optional body]
#
# [optional footer(s)]
#
# Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
# Scope: api, ui, db, auth, core, etc.
# Description: imperative mood, lowercase, no period
#
# Body: explain motivation, previous vs new behavior
# Footer: BREAKING CHANGE, Refs, Fixes, Reviewed-by
#
# Examples:
#   feat(auth): add OAuth2 authentication
#   fix: prevent crash on empty input
#   docs: update API reference
#   feat!: remove support for Node 6
```

**Configure Git**:

```bash
git config commit.template .gitmessage
```

### Team Conventions

**Document in CONTRIBUTING.md**:

```markdown
## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Types
- feat: New feature for users
- fix: Bug fix for users
- docs: Documentation changes
- style: Formatting changes
- refactor: Code restructuring
- perf: Performance improvements
- test: Test additions/corrections
- build: Build system changes
- ci: CI configuration changes
- chore: Other changes

### Scopes
Our project uses these scopes:
- api: REST API endpoints
- ui: Frontend components
- db: Database and migrations
- auth: Authentication and authorization
- core: Core business logic

### Examples
```
feat(api): add user profile endpoint
fix(ui): prevent modal close on backdrop click
docs: update installation instructions
```
```

---

## Troubleshooting

### commitlint Errors

**Error**: `type must be one of [...]`

**Solution**: Ensure commit type matches configured types in commitlint.config.js

**Error**: `scope must be one of [...]`

**Solution**: Either remove scope or use approved scope from configuration

### semantic-release Not Creating Release

**Cause**: No commits match release criteria since last release

**Solution**: Verify commits have `feat`, `fix`, or `BREAKING CHANGE`

**Debug**:

```bash
npx semantic-release --dry-run --debug
```

### Git Hooks Not Running

**Cause**: Hook scripts not executable or not installed

**Solution**:

```bash
chmod +x .git/hooks/*
# Or reinstall with husky/pre-commit
```

### CI Validation Passing but Local Failing

**Cause**: Different commitlint versions or configurations

**Solution**: Pin versions in package.json and ensure consistent config

```json
{
  "devDependencies": {
    "@commitlint/cli": "^18.4.3",
    "@commitlint/config-conventional": "^18.4.3"
  }
}
```
