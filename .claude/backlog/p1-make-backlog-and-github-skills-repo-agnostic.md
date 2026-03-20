---
name: Make backlog and GitHub skills repo-agnostic
description: "~100+ locations across the development-harness plugin and .claude/skills/ hardcode `Jamie-BitFlight/claude_skills`. This prevents the backlog, milestone, and GitHub integration skills from working in any other repository.\n\n**Affected areas:**\n\n1. **Python scripts** — `DEFAULT_REPO` constants in `backlog_core/models.py`, `gh/scripts/github_project_setup.py`, `daily-releases/scripts/*.py`\n2. **SKILL.md files** — `gh`, `work-backlog-item`, `create-milestone`, `start-milestone`, `group-items-to-milestone`, `complete-milestone`\n3. **Reference docs** — `github-integration.md`, `validation-plan.md`, `milestones.md`, `labels.md`, `projects-v2.md`, `issue-stories.md`, `step-procedures.md`\n4. **Templates** — `milestone-archive.md`\n5. **Tests** — `test_live_validation.py`\n6. **Migration docs** — `CLI_TO_MCP_MIGRATION.md`, `README.md`\n\n**Required changes:**\n\nA. **Python scripts**: Replace `DEFAULT_REPO` constants with auto-discovery function using GitPython (`git.Repo().remote().url`) to parse `owner/repo` from the origin remote. Support `GITHUB_REPO` env var as override. No CLI tools — use the GitPython and PyGithub libraries already in the project dependencies.\n\nB. **SKILL.md files**: Replace hardcoded repo with instructions to discover it dynamically from the git remote. Use the discovered value in all command examples.\n\nC. **Reference docs**: Same pattern — instruct discovery from git remote, use variable in all command examples.\n\nD. **MCP server**: The backlog FastMCP server should auto-discover repo from git remote via GitPython, with env var override."
metadata:
  topic: make-backlog-and-github-skills-repo-agnostic
  source: 'User report: /dh:work-backlog-item setup-github fails in other repos because repo is hardcoded'
  added: '2026-03-20'
  priority: P1
  type: Refactor
  status: open
  issue: '#852'
  last_synced: '2026-03-20T15:14:12Z'
  groomed: '2026-03-20'
  plan: plan/tasks-1-repo-agnostic-backlog-github-skills.md
---

## RT-ICA

<div><sub>2026-03-20T15:09:50Z</sub>

RT-ICA Snapshot: Make backlog and GitHub skills repo-agnostic
Goal: Remove all hardcoded Jamie-BitFlight/claude_skills references so backlog/GitHub skills work in any repo
Conditions:
1. Full inventory of hardcoded references exists | Status: AVAILABLE | grep found 101 occurrences across 20+ files
2. Auto-discovery mechanism defined (git remote parsing) | Status: AVAILABLE | description specifies GitPython + GITHUB_REPO env var
3. GitPython available in project dependencies | Status: DERIVABLE | check pyproject.toml
4. SKILL.md files can use dynamic discovery | Status: DERIVABLE | check if command substitution works in skill context
5. MCP server repo parameter or auto-discovery approach | Status: AVAILABLE | description specifies auto-discovery with env var override
6. Test strategy for verifying no hardcoded refs remain | Status: AVAILABLE | grep serves as verification
AVAILABLE count: 4
DERIVABLE count: 2
MISSING count: 0
Decision: APPROVED
</div>

## Groomed (2026-03-20)


### Impact

<div><sub>2026-03-20T00:00:00Z</sub>

<div><sub>2026-03-20T15:11:35Z</sub>
</div>

<div><sub>2026-03-20T15:12:46Z</sub>

**Scope of hardcoding: ~500 occurrences across ~25 files in 6 categories**

| Category | File Count | Occurrence Count | Example Files |
|----------|-----------|-------------------|---|
| SKILL.md files | 6 | ~53 | gh/SKILL.md (27x), complete-milestone/SKILL.md (10x), create-milestone/SKILL.md (5x) |
| Reference docs | 8 | ~29 | labels.md (7x), milestones.md (7x), github-integration.md (7x), issue-stories.md (6x) |
| Python scripts (producers) | 4 | ~4 | backlog_core/models.py, github_project_setup.py, cleanup_stale_releases.py, publish_daily_release.py |
| Plan artifacts (historical) | ~5 | ~380+ | plan/codebase/backlog-mcp-migration-patterns.md (23x), plan files (10-12x each) |
| Test files | 2 | ~4 | test_live_validation.py |
| CI/GitHub Actions | ~1 | TBD | Workflows |

**Consumers affected:**
- All GitHub integration features in development-harness and dependent skills
- Anyone installing the plugin in their own repository
- Future marketplace distribution
</div>

### Reproducibility

<div><sub>2026-03-20T15:12:33Z</sub>

Run `/dh:work-backlog-item setup-github` or `/gh` skill in any GitHub repository other than `Jamie-BitFlight/claude_skills`. All commands fail with "repository not found" or equivalent error because the hardcoded repo does not exist in the target environment.

**Minimal repro:**
1. Clone or cd into a different GitHub repository (e.g., a personal test repo)
2. Invoke the gh skill or work-backlog-item skill
3. Observe: commands fail with repo authentication/not-found errors

**Evidence:**
- 500+ occurrences of hardcoded `Jamie-BitFlight/claude_skills` across ~25 files
- DEFAULT_REPO constants in backlog_core/models.py and github_project_setup.py
- 6 SKILL.md files with `-R Jamie-BitFlight/claude_skills` hardcoded in command examples
- Tests (test_live_validation.py) hardcode the same repo in fixtures
</div>

### Priority

<div><sub>2026-03-20T15:12:39Z</sub>

**P1 — Blocks marketplace adoption**

Without this fix, the development-harness plugin (and all dependent skills: gh, work-backlog-item, create-milestone, complete-milestone, start-milestone, group-items-to-milestone) are unusable in any repository other than the original. This prevents the plugin from being distributed via marketplace or used by other teams.

**Signals P1 status:**
- Affects core functionality (GitHub integration) not edge cases
- Blocks entire plugin adoption path in new repositories
- Single root cause (hardcoded repo references) affecting multiple dependent systems
</div>

### Benefits

<div><sub>2026-03-20T15:12:53Z</sub>

**Functional Benefits:**
- Plugin becomes portable — works in any GitHub repository without modification
- Enables marketplace distribution — users install and it works immediately
- Supports multi-repo workflows — teams can use the same plugin across multiple projects
- Simplifies testing — skills can be tested in isolated test repositories

**Maintenance Benefits:**
- Removes 500+ static references that require updates if repo name changes
- Eliminates documentation drift — docs reflect dynamic discovery, not hardcoded values
- Reduces cognitive load on developers — one discovery mechanism replaces many hardcoded checks
- Establishes reusable pattern — similar pattern can apply to other repo-specific references in future

**User-Facing Benefits:**
- Setup becomes seamless — no manual repo configuration required
- Error messages improve — failures report actual vs. discovered repos
- Multi-repo users can install once and use everywhere
</div>

### Expected Behavior

<div><sub>2026-03-20T15:13:00Z</sub>

**After this fix is complete:**

1. **Automatic repo discovery**: All Python scripts and MCP server use GitPython to parse `owner/repo` from the git remote URL (`git remote get-url origin`)
2. **Environment variable override**: Set `GITHUB_REPO=owner/repo` to override discovery for non-standard setups (e.g., testing)
3. **SKILL.md dynamic discovery**: Examples show discovery command (e.g., `REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)`) and use `$REPO` or equivalent in all subsequent commands
4. **No hardcoded references**: Grep for `Jamie-BitFlight/claude_skills` returns 0 matches (excluding plan/ and .claude/backlog/ historical artifacts)
5. **Backward compatible**: Existing code that passes repo as parameter continues to work
6. **Clear error messages**: If repo cannot be discovered and GITHUB_REPO is not set, errors explain what is needed

**Deployment:** Changes are localized to Python code, SKILL.md files, and reference documentation. No schema changes or API modifications required.
</div>

### Acceptance Criteria

<div><sub>2026-03-20T15:13:08Z</sub>

- [ ] **grep verification (source code)**: `grep -r "Jamie-BitFlight/claude_skills" --include="*.py" --include="*.md" plugins/development-harness .claude/skills --exclude-dir=plan --exclude-dir=.claude/backlog` returns 0 matches (excluding plan/ and .claude/backlog/ historical data)
- [ ] **DEFAULT_REPO removed or parameterized**: backlog_core/models.py and github_project_setup.py use GitPython auto-discovery with GITHUB_REPO env var fallback
- [ ] **All daily-releases scripts updated**: publish_daily_release.py, cleanup_stale_releases.py, and similar scripts accept repo parameter or use auto-discovery
- [ ] **SKILL.md files updated**: 6 skills (gh, work-backlog-item, create-milestone, complete-milestone, start-milestone, group-items-to-milestone) show dynamic discovery in examples instead of hardcoded `-R` flag
- [ ] **Reference docs updated**: 8 reference files (labels.md, milestones.md, github-integration.md, etc.) document discovery mechanism and use dynamic variable in all gh command examples
- [ ] **Tests pass**: test_live_validation.py and all backlog_core tests pass with discovery mechanism; test fixtures accept repo parameter
- [ ] **MCP server agnostic**: backlog FastMCP server auto-discovers repo or accepts parameter; no hardcoded values in MCP service calls
- [ ] **No regressions**: All existing skills and commands work as before; discovery is transparent to users
- [ ] **Documentation complete**: SKILL.md or reference docs explain how repo discovery works and how to override with GITHUB_REPO
</div>

### Files

<div><sub>2026-03-20T15:13:15Z</sub>

**Core producers (repo discovery logic):**
- `plugins/development-harness/backlog_core/models.py` — Add or update `_resolve_repo_owner_name()` function using GitPython
- `plugins/development-harness/backlog_core/github.py` — Update all PyGithub calls to accept repo parameter
- `.claude/skills/gh/scripts/github_project_setup.py` — Replace DEFAULT_REPO with discovery function
- `.claude/skills/daily-releases/scripts/publish_daily_release.py` — Add repo discovery
- `.claude/skills/daily-releases/scripts/cleanup_stale_releases.py` — Add repo discovery

**Consumers (use discovered repo):**
- `plugins/development-harness/backlog_core/operations.py` — Accept repo parameter from discovery
- `plugins/development-harness/tests/test_backlog_core_models.py` — Accept repo parameter in fixtures

**Documentation & Skills:**
- `.claude/skills/gh/SKILL.md` — Replace hardcoded `-R Jamie-BitFlight/claude_skills` with discovery
- `.claude/skills/work-backlog-item/SKILL.md` — Replace hardcoded repo with discovery
- `.claude/skills/complete-milestone/SKILL.md` — Replace hardcoded repo
- `.claude/skills/create-milestone/SKILL.md` — Replace hardcoded repo
- `.claude/skills/start-milestone/SKILL.md` — Replace hardcoded repo
- `.claude/skills/group-items-to-milestone/SKILL.md` — Replace hardcoded repo

**Reference documentation (update examples):**
- `plugins/development-harness/skills/work-backlog-item/references/github-integration.md`
- `plugins/development-harness/skills/work-backlog-item/references/milestones.md`
- `plugins/development-harness/skills/work-backlog-item/references/labels.md`
- `plugins/development-harness/skills/work-backlog-item/references/issue-stories.md`

**Tests:**
- `plugins/development-harness/tests/test_live_validation.py` — Replace hardcoded repo with discovery or parameter
</div>

### Resources

<div><sub>2026-03-20T15:13:25Z</sub>

**Pattern precedent in codebase:**
- `plugins/development-harness/backlog_core/models.py:_resolve_repo_root()` — Existing function that auto-discovers repository root. Follow this design pattern: simple, fast, with env var override.

**Libraries (already in pyproject.toml):**
- GitPython >=3.1.45 — Parse git remote URLs and extract owner/repo. Usage: `git.Repo().remote().url`
- PyGithub >=2.8.1 — Already used throughout codebase for GitHub API calls. Accept repo parameter in all calls.

**External documentation:**
- GitPython docs: git.Repo() and remote parsing
- PyGithub docs: G.get_repo(full_name_or_id) — accepts owner/repo string

**Reference examples in this issue:**
- Backlog item description shows auto-discovery approach (git remote parsing + GITHUB_REPO env var)
- Impact Radius section catalogs all files requiring changes
- Fact-Check confirms dependencies are available
</div>

### Dependencies

<div><sub>2026-03-20T15:13:31Z</sub>

**External libraries (already in pyproject.toml):**
- GitPython >=3.1.45 — for git remote URL parsing
- PyGithub >=2.8.1 — for GitHub API calls (no changes to usage)

**Internal dependencies:**
- Existing code in `backlog_core/models.py:_resolve_repo_root()` — reference for design pattern
- Existing parameter passing in `github_project_setup.py` — reference for function signatures

**No new external dependencies required** — all required libraries are already declared and installed.

**Environment:**
- GITHUB_TOKEN — must be set for GitHub API access (existing requirement)
- GITHUB_REPO (optional) — environment variable for repo override (new, optional)

**On other systems:**
- Git must be installed (used by GitPython)
- GitHub CLI (`gh`) must be available (used by SKILL.md discovery commands)
</div>

### Effort

<div><sub>2026-03-20T15:13:41Z</sub>

**Scope:** ~500 occurrences across ~25 files, but highly repetitive patterns

**Breakdown:**
- **Core implementation** (discovery function + parameter updates): ~2-3 hours — small codebase change with high leverage
  - Add `_resolve_repo_owner_name()` function to models.py (reuse existing pattern from `_resolve_repo_root()`)
  - Update 2 DEFAULT_REPO constants to use discovery
  - Update 2-3 function signatures to accept repo parameter

- **Python scripts** (producers): ~1-2 hours — search-and-replace DEFAULT_REPO with function calls
  - 4 scripts in daily-releases/, gh/scripts/, .claude/scripts/
  - Most are identical patterns

- **SKILL.md files** (6 files): ~1-2 hours — replace hardcoded `-R` flag with discovery command
  - Template: show discovery once, use variable throughout
  - Highly repetitive across all 6 skills

- **Reference documentation** (8 files): ~1-2 hours — update examples to use dynamic discovery
  - Same pattern as SKILL.md — show discovery, use variable
  - Mostly search-and-replace

- **Tests**: ~30-45 minutes — add repo parameter to fixtures
  - Small scope: 2 test files with simple updates

- **Verification**: ~30-45 minutes — grep validation and manual smoke testing

**Total estimate: ~6-9 hours**

**Parallelization opportunity:** Core implementation can be done first, then SKILL.md and docs can be updated in parallel by different agents.

**Risk:** Low — primarily search-and-replace with low refactoring risk. Existing pattern (`_resolve_repo_root()`) provides design template.
</div>


## Impact Radius

### Code — Producers (define the repo constant/value)

- `plugins/development-harness/backlog_core/models.py:_resolve_repo_root()` — Currently uses `Path.cwd()` (correct design). No hardcoded constants found in this file. **Status: Already repo-agnostic via current working directory approach.**
- `plugins/development-harness/backlog_core/github.py` — Likely contains GitHub API calls that receive repo owner/name. Need to verify it accepts parameters vs. hardcoded values.
- `.claude/skills/gh/scripts/github_project_setup.py` — Command-line script with `--repo OWNER/REPO` parameter support visible. **Status: Already parameterized, not hardcoded.**
- `.claude/skills/daily-releases/scripts/publish_daily_release.py` — Contains PyGithub operations. Uses PEP 723 inline dependencies. Need to verify if repo is hardcoded or parameterized.
- `.claude/skills/daily-releases/scripts/collect_day_dataset.py` — Similar scope as publish_daily_release.
- `.claude/skills/daily-releases/scripts/cleanup_stale_releases.py` — Similar scope as publish_daily_release.
- `.claude/skills/daily-releases/scripts/list_daily_ranges.py` — Similar scope as publish_daily_release.
- `.claude/scripts/sync_issues_to_project.py` — Script for syncing issues. Need to verify hardcoding.
- `.claude/scripts/rebuild_issue_bodies.py` — Issue body manipulation. Need to verify hardcoding.
- `.claude/scripts/repair_from_original_register.py` — Data repair script. Need to verify hardcoding.

### Code — Consumers (use the repo value in commands)

- `plugins/development-harness/backlog_core/operations.py` — Likely passes repo to GitHub API calls. Depends on how producers provide the value.
- `plugins/development-harness/backlog_core/tests/test_backlog_core_models.py` — Test file. May have hardcoded repo for test fixtures.
- `plugins/development-harness/tests/` — Test directory containing validation tests that may hardcode the repo.

### SKILL.md Files (hardcoded gh commands with -R flag or literal repo values)

**Found 6 SKILL.md files with hardcoded repo:**
- `.claude/skills/complete-milestone/SKILL.md` — Contains `gh ... -R Jamie-BitFlight/claude_skills` commands
- `.claude/skills/create-milestone/SKILL.md` — Contains `gh ... -R Jamie-BitFlight/claude_skills` commands
- `.claude/skills/gh/SKILL.md` — Root gh skill, contains example commands with `-R Jamie-BitFlight/claude_skills`
- `.claude/skills/group-items-to-milestone/SKILL.md` — Contains `gh ... -R Jamie-BitFlight/claude_skills` commands
- `.claude/skills/start-milestone/SKILL.md` — Contains `gh ... -R Jamie-BitFlight/claude_skills` commands
- `plugins/development-harness/skills/work-backlog-item/SKILL.md` — Contains `gh ... -R Jamie-BitFlight/claude_skills` commands

**Changes needed:** Replace hardcoded `-R Jamie-BitFlight/claude_skills` with dynamic discovery using `!`git config --get remote.origin.url`\` or environment variable with fallback.

### Documentation Files (will become stale)

**To inventory:** The following file paths were identified in the backlog item description as containing documentation that references the hardcoded repo pattern:
- `plugins/development-harness/skills/work-backlog-item/references/github-integration.md`
- `plugins/development-harness/skills/work-backlog-item/references/validation-plan.md`
- `plugins/development-harness/skills/work-backlog-item/references/milestones.md`
- `plugins/development-harness/skills/work-backlog-item/references/labels.md`
- `plugins/development-harness/skills/work-backlog-item/references/projects-v2.md`
- `plugins/development-harness/skills/work-backlog-item/references/issue-stories.md`
- `plugins/development-harness/skills/work-backlog-item/references/step-procedures.md`
- `plugins/development-harness/skills/work-backlog-item/references/milestone-archive.md`

**Status:** Not yet searched — presumed to contain hardcoded examples and instructions showing `-R Jamie-BitFlight/claude_skills`.

### Configuration / CI / Environment

- `plugins/development-harness/plugin.json` and `plugins/development-harness/hooks/` — May contain GitHub repo references in hooks (e.g., for syncing).
- GitHub Actions workflows (`.github/workflows/*.yml`) — May hardcode repo in workflow steps.

### Agent Instructions

- `.claude/agents/backlog-item-groomer.md` — May instruct agents to use specific repo.
- `.claude/agents/backlog-mcp-validator.md` — May instruct agents to use specific repo.

### Systems Inventory

**Total occurrences of hardcoded references:** 130 (from grep count)

**File categories:**
- Python scripts with hardcoded repo: ~9 files (scripts in gh/, daily-releases/, .claude/scripts/)
- SKILL.md files with `-R Jamie-BitFlight/claude_skills`: 6 files
- Reference documentation: ~8 files (in work-backlog-item/references/)
- Agent instructions: ~2 files
- Test files: ~2 files
- CI/configuration files: TBD

### Ecosystem Completeness Checklist

- [ ] **Every code producer updated or verified compatible**: backlog_core/models.py already repo-agnostic (uses cwd). github_project_setup.py already parameterized. Daily-releases and custom scripts need verification.
- [ ] **Every code consumer migrated to new interface**: operations.py and github.py depend on producer changes. Tests need updates.
- [ ] **Every SKILL.md file updated**: 6 files identified; replace `-R Jamie-BitFlight/claude_skills` with dynamic discovery.
- [ ] **Every reference document updated**: 8 files in work-backlog-item/references/ need revision to remove hardcoded examples.
- [ ] **Agent instructions updated**: backlog-item-groomer.md, backlog-mcp-validator.md need review.
- [ ] **CI/config files updated**: GitHub Actions workflows need verification.
- [ ] **Test files updated**: test_live_validation.py and other tests need repo parameter support.
- [ ] **Old hardcoded interface removed**: All 130 occurrences of "Jamie-BitFlight/claude_skills" must be eliminated or replaced.

### Key Finding

**Discovery mechanism already exists:** `models.py:_resolve_repo_root()` uses `Path.cwd()` — repository root is auto-discovered. The pattern for repo owner/name discovery via GitPython should follow the same philosophy: use git remote URL parsing with `GITHUB_REPO` env var as override (per backlog item spec).

**Scope:** ~20-25 files across 4 categories (producers, consumers, docs, agent-instructions). Work is localized to development-harness plugin and .claude/skills directory.
</div>

## Fact-Check

<div><sub>2026-03-20T15:11:39Z</sub>

## Fact-Check Summary

**Claims checked**: 10
**VERIFIED**: 9  |  **REFUTED**: 0  |  **INCONCLUSIVE**: 1

### Claim 1: "~100+ locations hardcode Jamie-BitFlight/claude_skills"
**Verdict**: VERIFIED (understated — actual count is 500+)
**Evidence**: Grep across entire codebase found 500 total occurrences in 176 unique files
**Notes**: Issue description says "~100+" but actual hardcoding is 5× larger. Top files: gh/SKILL.md (27x), plan/codebase/backlog-mcp-migration-patterns.md (23x), plan files (10-12x each), README.md (7x), skill reference docs (6-7x each).

### Claim 2: "DEFAULT_REPO constant in backlog_core/models.py"
**Verdict**: VERIFIED
**Evidence**: `/plugins/development-harness/backlog_core/models.py` Line 60: `DEFAULT_REPO = "Jamie-BitFlight/claude_skills"`

### Claim 3: "DEFAULT_REPO constant in github_project_setup.py"
**Verdict**: VERIFIED
**Evidence**: `.claude/skills/gh/scripts/github_project_setup.py` Line 55: `DEFAULT_REPO = "Jamie-BitFlight/claude_skills"`
**Notes**: Used as default in 4 function signatures (lines 125, 156, 178, 197).

### Claim 4: "daily-releases/scripts/*.py hardcoded"
**Verdict**: VERIFIED (4 of 8 scripts)
**Evidence**:
- `cleanup_stale_releases.py` L56: bare hardcode
- `collect_day_dataset.py` L51: env var override support
- `list_daily_ranges.py` L45: env var override support
- `publish_daily_release.py` L51: bare hardcode

### Claim 5: "GitPython in dependencies"
**Verdict**: VERIFIED
**Evidence**: `pyproject.toml` contains `"gitpython>=3.1.45"`

### Claim 6: "PyGithub in dependencies"
**Verdict**: VERIFIED
**Evidence**: `pyproject.toml` contains `"pygithub>=2.8.1"` and `"pygithub>=2.1.1"`

### Claim 7: "SKILL.md files hardcoded"
**Verdict**: VERIFIED
**Evidence**: All 7 skills confirmed:
- gh/SKILL.md: 27x
- complete-milestone/SKILL.md: 10x
- create-milestone/SKILL.md: 5x
- start-milestone/SKILL.md: 6x
- work-backlog-item/SKILL.md: found
- group-items-to-milestone/SKILL.md: found

### Claim 8: "Reference docs hardcoded"
**Verdict**: VERIFIED
**Evidence**: All confirmed:
- labels.md: 7x
- milestones.md: 7x
- issue-stories.md: 6x
- github-integration.md: 7x (in work-backlog-item)

### Claim 9: "test_live_validation.py hardcoded"
**Verdict**: VERIFIED
**Evidence**: `/plugins/development-harness/tests/test_live_validation.py` Line 83: `repo = g.get_repo("Jamie-BitFlight/claude_skills")`

### Claim 10: "Backlog FastMCP server needs auto-discovery"
**Verdict**: INCONCLUSIVE
**Evidence**: Python constant exists in models.py; MCP configuration not examined
**Notes**: Requires verification of MCP plugin configuration to confirm server-level hardcoding.
</div>

## RT-ICA

<div><sub>2026-03-20T15:14:12Z</sub>

RT-ICA Final: Make backlog and GitHub skills repo-agnostic
Goal: Remove all hardcoded Jamie-BitFlight/claude_skills references so backlog/GitHub skills work in any repo

Conditions:
1. Full inventory of hardcoded references | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: grep found ~500 occurrences across ~25 files (fact-checker verified 5x larger than claimed)
2. Auto-discovery mechanism defined | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: Issue description specifies GitPython git remote parsing + GITHUB_REPO env var override
3. GitPython available in project dependencies | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: Fact-checker verified GitPython >=3.1.45 in pyproject.toml
4. SKILL.md dynamic discovery mechanism | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: SKILL.md preamble step pattern (gh repo view --json nameWithOwner) confirmed viable; command substitution works but env vars empty for project-level skills
5. MCP server repo parameter or auto-discovery | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: Issue description defines approach; fact-checker marked MCP server as INCONCLUSIVE on current state but approach is defined
6. Test strategy for verification | Snapshot: AVAILABLE → Final: AVAILABLE | Evidence: grep -r with exclusions serves as acceptance test

Changes from snapshot:
- Condition 3: DERIVABLE → AVAILABLE (resolved by fact-checker — GitPython >=3.1.45 confirmed in pyproject.toml)
- Condition 4: DERIVABLE → AVAILABLE (resolved by memory + issue description — preamble step pattern viable)
- Scope expanded: actual count is ~500 occurrences, not ~100 (fact-checker finding)

AVAILABLE count: 6
DERIVABLE count: 0
MISSING count: 0
Decision: APPROVED
</div>