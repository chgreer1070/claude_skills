# Feature Context: Repo-Agnostic Backlog and GitHub Skills

## Document Metadata

- **Generated**: 2026-03-20
- **Input Type**: existing_document
- **Source**: `.claude/backlog/p1-make-backlog-and-github-skills-repo-agnostic.md` (GitHub Issue #852)
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

~500 occurrences of hardcoded `Jamie-BitFlight/claude_skills` across ~25 files prevent the development-harness plugin and `.claude/skills/` GitHub integration from working in any other repository. Replace all hardcoded repo references with dynamic auto-discovery so the plugin works in any GitHub repository without modification.

Source: User report that `/dh:work-backlog-item setup-github` fails in other repos because the repo is hardcoded.

---

## Core Intent Analysis

### WHO (Target Users)

1. **Plugin marketplace consumers** who install the development-harness plugin into their own GitHub repositories
2. **Multi-repo developers** who use the same plugin across different projects
3. **Plugin maintainers** who need the repo name to be maintainable (no bulk updates on rename)

### WHAT (Desired Outcome)

All GitHub-integrated skills (gh, backlog, milestone, daily-releases) automatically discover the current repository's `owner/repo` from the git remote. No manual configuration required. Users who need to override (e.g., testing, non-standard remotes) can set `GITHUB_REPO=owner/repo` as an environment variable.

Success: `grep -r "Jamie-BitFlight/claude_skills" --include="*.py" --include="*.md" plugins/development-harness .claude/skills --exclude-dir=plan --exclude-dir=.claude/backlog` returns 0 matches.

### WHEN (Trigger Conditions)

- A user installs the development-harness plugin in a repository other than `Jamie-BitFlight/claude_skills`
- A user invokes any GitHub-integrated skill (`/gh`, `/dh:work-backlog-item`, `/create-milestone`, `/start-milestone`, `/complete-milestone`, `/group-items-to-milestone`)
- The repository is renamed or forked

### WHY (Problem Being Solved)

- **Blocks marketplace adoption**: The plugin is unusable outside the original repository
- **Maintenance burden**: ~500 static references require bulk updates if the repo name changes
- **P1 priority**: Affects core GitHub integration functionality, not edge cases

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: _resolve_repo_root() in models.py

- **Location**: `plugins/development-harness/backlog_core/models.py` (referenced at line 60 area per fact-check)
- **Relevance**: Existing auto-discovery function that resolves the repository root directory from the current working directory. Demonstrates the project's established pattern for runtime discovery with no hardcoded paths.
- **Reusable**: Design philosophy (discover at runtime, no hardcoded defaults) is directly applicable. A sibling function for `owner/repo` discovery would follow the same pattern.

#### Pattern 2: github_project_setup.py parameterized CLI

- **Location**: `.claude/skills/gh/scripts/github_project_setup.py` (line 55 DEFAULT_REPO, lines 125/156/178/197 function signatures per fact-check)
- **Relevance**: Already accepts `--repo OWNER/REPO` as a CLI parameter. The DEFAULT_REPO constant is the fallback when no parameter is passed. This shows the codebase already has parameter-passing infrastructure — the gap is that the default falls back to a hardcoded value instead of auto-discovery.
- **Reusable**: The parameter-passing pattern in function signatures is the target state for all Python scripts.

#### Pattern 3: Daily-releases scripts with partial env var support

- **Location**: `.claude/skills/daily-releases/scripts/collect_day_dataset.py` (line 51), `list_daily_ranges.py` (line 45) per fact-check
- **Relevance**: Two of four daily-releases scripts already support env var override for the repo. Two others (`cleanup_stale_releases.py`, `publish_daily_release.py`) have bare hardcodes. This shows inconsistent adoption of a pattern that was partially started.
- **Reusable**: The env-var-with-fallback pattern in collect_day_dataset.py and list_daily_ranges.py is the target pattern.

### Existing Infrastructure

- **GitPython >=3.1.45** in `pyproject.toml` — can parse git remote URLs to extract `owner/repo`
- **PyGithub >=2.8.1** in `pyproject.toml` — already used for GitHub API calls; accepts `owner/repo` strings
- **GITHUB_TOKEN** already required in environment for GitHub API access
- **`gh` CLI** available via `/gh` skill — supports `gh repo view --json nameWithOwner` for discovery in shell contexts

### Code References

- `plugins/development-harness/backlog_core/models.py:60` — DEFAULT_REPO constant (fact-check verified)
- `.claude/skills/gh/scripts/github_project_setup.py:55` — DEFAULT_REPO constant (fact-check verified)
- `.claude/skills/daily-releases/scripts/cleanup_stale_releases.py:56` — bare hardcode (fact-check verified)
- `.claude/skills/daily-releases/scripts/publish_daily_release.py:51` — bare hardcode (fact-check verified)
- `.claude/skills/daily-releases/scripts/collect_day_dataset.py:51` — env var override support (fact-check verified)
- `.claude/skills/daily-releases/scripts/list_daily_ranges.py:45` — env var override support (fact-check verified)
- `plugins/development-harness/tests/test_live_validation.py:83` — hardcoded in test fixture (fact-check verified)
- `.claude/skills/gh/SKILL.md` — 27 occurrences (fact-check verified)
- `.claude/skills/complete-milestone/SKILL.md` — 10 occurrences (fact-check verified)

---

## Use Scenarios

### Scenario 1: New Repository Installation

**Actor**: Developer installing development-harness plugin from marketplace
**Trigger**: Runs `/dh:work-backlog-item setup-github` in their own repository
**Goal**: Set up GitHub issue tracking and backlog integration for their project
**Expected Outcome**: Skills auto-discover `owner/repo` from git remote. All `gh` commands target the correct repository. No configuration needed beyond having `GITHUB_TOKEN` set.

### Scenario 2: Multi-Repo Team Usage

**Actor**: Team member using the plugin across multiple repositories
**Trigger**: Switches between repositories and invokes GitHub skills in each
**Goal**: Each invocation targets the correct repository without manual switching
**Expected Outcome**: Discovery runs per-invocation, resolving the correct `owner/repo` from whichever repository the user is currently in.

### Scenario 3: Override for Non-Standard Setups

**Actor**: Developer with a fork, mirror, or CI environment where the git remote does not reflect the target GitHub repository
**Trigger**: Sets `GITHUB_REPO=owner/repo` environment variable before invoking skills
**Goal**: Force skills to target a specific repository regardless of git remote
**Expected Outcome**: The env var takes precedence over auto-discovery. Skills operate against the specified repository.

### Scenario 4: Repository Rename or Transfer

**Actor**: Repository owner who renames or transfers the repository
**Trigger**: Repository URL changes (GitHub redirects git operations but `owner/repo` string changes)
**Goal**: Skills continue working without manual updates to any configuration
**Expected Outcome**: Auto-discovery reads the updated remote URL. No code changes needed.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | `.claude/CLAUDE.md` contains hardcoded `Jamie-BitFlight/claude_skills` in the `gh_cli_usage` section (examples). Not listed in acceptance criteria. | If not updated, the project's own CLAUDE.md teaches agents to use the hardcoded repo |
| 2 | Scope | `.claude/scripts/` files (sync_issues_to_project.py, rebuild_issue_bodies.py, repair_from_original_register.py) mentioned in Impact Radius but absent from acceptance criteria file list | Unclear if these utility scripts are in scope or out |
| 3 | Scope | Agent instruction files (backlog-item-groomer.md, backlog-mcp-validator.md) mentioned in Impact Radius but absent from acceptance criteria | Agents may continue instructing use of hardcoded repo |
| 4 | Scope | GitHub Actions workflows listed as TBD in Impact Radius | CI workflows may fail in other repos if they hardcode the repo |
| 5 | Behavior | SKILL.md argument substitution — `$N` and `$ARGUMENTS` are substituted at load time, and env vars (`GITHUB_REPO`) are empty strings for project-level skills | Discovery mechanism in SKILL.md files must avoid `$` variables; the `gh repo view` preamble approach works but needs careful syntax |
| 6 | Integration | MCP server (backlog FastMCP) — fact-check marked INCONCLUSIVE on whether it hardcodes the repo | If MCP server hardcodes the repo, all MCP-based backlog operations fail in other repos |
| 7 | Behavior | Error messaging when discovery fails (no git remote, no GITHUB_REPO set) — no specification for error content or format | Users in environments without git remotes get unclear failures |

---

## Questions Requiring Resolution

### Q1: Is .claude/CLAUDE.md in scope?

- **Category**: Scope
- **Gap**: The `gh_cli_usage` section in `.claude/CLAUDE.md` contains hardcoded `Jamie-BitFlight/claude_skills` in all example commands. This file teaches the AI agent how to use `gh`.
- **Question**: Should `.claude/CLAUDE.md` be updated to use dynamic discovery in its `gh` examples, or is it excluded because it serves as project-level instructions specific to this repo?
- **Options**:
  - A) In scope -- update CLAUDE.md to show discovery pattern (makes the instructions portable)
  - B) Out of scope -- CLAUDE.md is project-specific and should reflect the actual repo
- **Why It Matters**: If A, the plugin becomes fully self-contained. If B, every repo that installs the plugin still needs to manually update their CLAUDE.md.
- **Resolution**: _pending_

### Q2: Are .claude/scripts/ utility scripts in scope?

- **Category**: Scope
- **Gap**: Three utility scripts in `.claude/scripts/` (sync_issues_to_project.py, rebuild_issue_bodies.py, repair_from_original_register.py) were identified in the Impact Radius but not listed in the acceptance criteria.
- **Question**: Are these scripts part of the plugin distribution, or are they repo-specific utilities that stay hardcoded?
- **Options**:
  - A) In scope -- they ship with the plugin and must be repo-agnostic
  - B) Out of scope -- they are repo-specific maintenance scripts
- **Why It Matters**: If A, adds 3 more files to the implementation. If B, they remain hardcoded but do not affect marketplace users.
- **Resolution**: _pending_

### Q3: Are agent instruction files in scope?

- **Category**: Scope
- **Gap**: `backlog-item-groomer.md` and `backlog-mcp-validator.md` may contain hardcoded repo references. Listed in Impact Radius but not in acceptance criteria.
- **Question**: Do these agent files reference the hardcoded repo, and if so, should they be updated?
- **Options**:
  - A) In scope -- agents must work in any repo
  - B) Out of scope -- agents are repo-specific
- **Why It Matters**: If agents hardcode the repo, they will produce incorrect `gh` commands in other repositories.
- **Resolution**: _pending_

### Q4: Are GitHub Actions workflows in scope?

- **Category**: Scope
- **Gap**: Impact Radius lists CI workflows as TBD. Unknown if any `.github/workflows/*.yml` files hardcode the repo in ways that affect the plugin.
- **Question**: Should GitHub Actions workflows be inventoried and updated as part of this feature?
- **Options**:
  - A) In scope -- workflows are part of the portable development tooling
  - B) Out of scope -- workflows are inherently repo-specific (they run in the repo's own CI)
- **Why It Matters**: Workflows typically use `${{ github.repository }}` already, but this needs verification.
- **Resolution**: _pending_

### Q5: How should SKILL.md files handle the $-substitution constraint?

- **Category**: Behavior
- **Gap**: Claude Code substitutes `$N`, `$ARGUMENTS`, and `${VAR}` in SKILL.md at load time. Environment variables like `GITHUB_REPO` are empty strings for project-level skills. The backlog item proposes `REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)` as a preamble, but the `$REPO` usage in subsequent commands would be substituted (and destroyed) at load time.
- **Question**: Does the architecture phase need to design a SKILL.md discovery pattern that avoids `$`-variable substitution, or is the `gh repo view` preamble evaluated at runtime via `!` backtick command substitution and therefore safe?
- **Options**:
  - A) The `!` backtick form (`!`\`command\``) executes at load time and inlines the result -- this could work if the discovery command runs at skill load
  - B) A different mechanism is needed (e.g., the SKILL.md instructs the agent to run discovery as its first step, storing the result in the agent's working memory rather than in a shell variable)
- **Why It Matters**: If the chosen pattern is corrupted by substitution, every SKILL.md update would silently break. This is the highest-risk technical constraint.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. All Python scripts that reference `Jamie-BitFlight/claude_skills` use runtime auto-discovery with `GITHUB_REPO` env var override
2. All SKILL.md files that contain hardcoded `-R Jamie-BitFlight/claude_skills` use a dynamic discovery mechanism compatible with SKILL.md argument substitution constraints
3. All reference documentation files replace hardcoded repo examples with dynamic discovery examples
4. MCP server (backlog FastMCP) auto-discovers the repository
5. Tests accept repo as a parameter or use auto-discovery
6. Zero hardcoded occurrences remain in `plugins/development-harness/` and `.claude/skills/` (excluding `plan/` and `.claude/backlog/` historical artifacts)
7. Clear error messages when discovery fails (no git remote and no `GITHUB_REPO` set)

---

## Scope Boundaries

### In Scope (confirmed)

- Python scripts in `plugins/development-harness/backlog_core/` (models.py, operations.py, github.py)
- Python scripts in `.claude/skills/gh/scripts/` (github_project_setup.py)
- Python scripts in `.claude/skills/daily-releases/scripts/` (4 scripts)
- SKILL.md files for 6 skills: gh, work-backlog-item, create-milestone, complete-milestone, start-milestone, group-items-to-milestone
- Reference docs in `plugins/development-harness/skills/work-backlog-item/references/` (8 files)
- Test file: `plugins/development-harness/tests/test_live_validation.py`
- MCP server configuration (pending verification of hardcoding)

### Out of Scope (confirmed)

- `plan/` directory (historical artifacts)
- `.claude/backlog/` directory (historical artifacts)
- Template files used for archive formatting (content is generated, not executed)

### Scope TBD (pending question resolution)

- `.claude/CLAUDE.md` gh_cli_usage section (Q1)
- `.claude/scripts/` utility scripts (Q2)
- Agent instruction files in `.claude/agents/` (Q3)
- GitHub Actions workflows in `.github/workflows/` (Q4)

---

## Design Constraints (for architecture phase)

These constraints are verified facts that the architecture phase must respect:

1. **SKILL.md substitution**: `$N`, `$ARGUMENTS`, `${VAR}` are all substituted at load time. Env vars are empty for project-level skills. Any SKILL.md pattern using `$` for repo values will be corrupted. (SOURCE: MEMORY.md, verified via canary test 2026-03-08)
2. **GitPython available**: >=3.1.45 in pyproject.toml (fact-check verified)
3. **PyGithub available**: >=2.8.1 in pyproject.toml (fact-check verified)
4. **Existing pattern**: `_resolve_repo_root()` in models.py uses `Path.cwd()` -- follow this design philosophy
5. **Git remote proxy**: In Claude Code sessions, git remote points to `127.0.0.1` (local proxy), not `github.com`. The `gh` CLI cannot auto-detect the repository from the remote. (SOURCE: `.claude/CLAUDE.md` gh_cli_usage section)
6. **Plan artifacts immutable**: Per plan artifact lifecycle policy, `plan/` and `.claude/backlog/` files must not be modified

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
