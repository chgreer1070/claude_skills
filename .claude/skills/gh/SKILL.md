---
description: 'Install and configure the GitHub CLI (gh) for AI agent environments where gh may not be pre-installed and git remotes use local proxies instead of github.com. Provides auto-install script with SHA256 verification and GITHUB_TOKEN auth with anonymous fallback. Use when gh command not found, shutil.which("gh") returns None, need GitHub API access (issues, PRs, releases, workflow runs), or repository operations fail with "failed to determine base repo" error. Documents required -R flag for all gh commands in proxy environments.'
---
# GitHub CLI (gh) — Setup and Usage

## Purpose

Ensures the GitHub CLI (`gh`) is available and provides correct usage patterns for AI agents operating in environments where `gh` may not be pre-installed and where git remotes point to local proxies instead of `github.com`.

## When to Use

- `gh` command not found or `shutil.which("gh")` returns None
- Need to interact with GitHub API (issues, PRs, releases, workflows)
- Repository remote does not point to `github.com` (proxy environments)
- Need authenticated GitHub operations with `GITHUB_TOKEN`

---

## Installation

If `gh` is not installed, run the setup script:

```bash
uv run .claude/skills/gh/scripts/setup_gh.py
```

The script:

1. Checks if `gh` is already installed via `shutil.which`
2. Detects platform (Linux, macOS, Windows) and architecture
3. Fetches the latest release from `https://github.com/cli/cli/releases/latest`
4. Downloads the correct archive with SHA256 verification from checksums file
5. Extracts and installs the binary to a writable PATH directory
6. Uses `GITHUB_TOKEN` for authenticated requests; falls back to anonymous if auth fails (401/403)

**CLI options:**

```text
--force     Reinstall even if already at latest version
--dry-run   Show what would happen without installing
--bin-dir   Override install directory (default: auto-detect from PATH)
```

---

## Authentication

`GITHUB_TOKEN` environment variable provides automatic authentication. No manual `gh auth login` needed.

```bash
# Verify authentication
gh auth status
```

If `GITHUB_TOKEN` is set, `gh` authenticates automatically for all API calls.

---

## Repository Detection

<repo_detection>

Git remote points to a local proxy (`127.0.0.1`), NOT `github.com`. Every `gh` command fails without explicit repo specification:

```text
failed to determine base repo: none of the git remotes configured for this
repository point to a known GitHub host.
```

**RULE: Pass `-R` (or `--repo`) on EVERY `gh` command:**

```bash
gh <command> -R Jamie-BitFlight/claude_skills
```

This applies to ALL `gh` subcommands: `pr`, `issue`, `run`, `api`, `release`, etc.

</repo_detection>

---

## Common Commands (v2.87.0)

<gh_commands>

### Pull Requests

```bash
# List open PRs
gh pr list -R Jamie-BitFlight/claude_skills

# View PR details
gh pr view <number> -R Jamie-BitFlight/claude_skills

# Check PR CI status
gh pr checks <number> -R Jamie-BitFlight/claude_skills

# Create PR
gh pr create -R Jamie-BitFlight/claude_skills --title "title" --body "body"

# View PR comments
gh api repos/Jamie-BitFlight/claude_skills/pulls/<number>/comments
```

### Issues

```bash
# List issues
gh issue list -R Jamie-BitFlight/claude_skills

# Create issue
gh issue create -R Jamie-BitFlight/claude_skills --title "title" --body "body"

# View issue
gh issue view <number> -R Jamie-BitFlight/claude_skills
```

### Workflow Runs

```bash
# List recent runs
gh run list -R Jamie-BitFlight/claude_skills --limit 5

# View specific run
gh run view <run-id> -R Jamie-BitFlight/claude_skills

# View failed job logs
gh run view <run-id> -R Jamie-BitFlight/claude_skills --log-failed
```

### Releases

```bash
# List releases
gh release list -R Jamie-BitFlight/claude_skills

# View latest release
gh release view --repo <owner>/<repo>
```

### API (Direct)

```bash
# GET request
gh api repos/<owner>/<repo>

# GET with query params
gh api repos/<owner>/<repo>/releases/latest

# POST with fields
gh api repos/<owner>/<repo>/issues -f title="Bug" -f body="Details"

# GraphQL
gh api graphql -f query='{ viewer { login } }'

# Paginated results
gh api repos/<owner>/<repo>/contributors --paginate
```

### Repository

```bash
# Clone
gh repo clone <owner>/<repo>

# View repo info
gh repo view -R <owner>/<repo>

# List repos
gh repo list <owner> --limit 10
```

</gh_commands>

---

## Output Formatting

```bash
# JSON output
gh pr list -R Jamie-BitFlight/claude_skills --json number,title,state

# JQ filtering
gh pr list -R Jamie-BitFlight/claude_skills --json number,title --jq '.[].title'

# Template formatting
gh pr list -R Jamie-BitFlight/claude_skills --json number,title \
  --template '{{range .}}#{{.number}} {{.title}}{{"\n"}}{{end}}'
```

---

## Sources

- [GitHub CLI Manual](https://cli.github.com/manual) — official reference
- [GitHub CLI Releases](https://github.com/cli/cli/releases) — binary downloads
- `gh version 2.87.0 (2026-02-18)` — version verified by installation test
