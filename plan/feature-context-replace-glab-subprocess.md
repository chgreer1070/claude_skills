# Feature Context: Replace subprocess glab call with python-gitlab in fetch_gitlab_mr.py

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: simple_description
- **Source**: GitHub Issue #368 / backlog item p2-fetchgitlabmrpy-replace-subprocess-glab-call-with-python-git
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Replace subprocess glab call with python-gitlab library in fetch_gitlab_mr.py.

fetch_gitlab_mr.py shells out to the 'glab' binary (lines 105-114) to fetch MR data. The script already has python-gitlab as a dependency and the codebase uses python-gitlab elsewhere. Subprocess call to glab: (1) requires glab binary on PATH, (2) bypasses token auth handled by libraries, (3) triggered S607 linting error that was patched with shutil.which instead of fixed architecturally. Fix: replace subprocess.run(['glab', ...]) with python-gitlab equivalent API call. This eliminates the binary dependency entirely.

Priority: P2

---

## Core Intent Analysis

### WHO (Target Users)

Contributors and CI/CD pipelines running fetch_gitlab_mr.py in environments where the `glab` binary is not installed. This includes automated pipelines, containerized environments, and developer workstations that use python-gitlab but not the glab CLI.

### WHAT (Desired Outcome)

`_resolve_token()` in `fetch_gitlab_mr.py` discovers the GitLab token exclusively via environment variables (`GITLAB_TOKEN`, `GITLAB_PRIVATE_TOKEN`). No subprocess call to glab. No shutil.which call. The script requires only what is already declared in its dependencies header (python-gitlab, gitpython, typer).

### WHEN (Trigger Conditions)

Any invocation of fetch_gitlab_mr.py (and by extension the create-merge-request-changelog skill) in an environment where the `glab` binary is absent. Also triggered during ruff linting, which flags S607 on the current subprocess call.

### WHY (Problem Being Solved)

Three compounding problems exist in the current code:

1. **Binary dependency**: The glab CLI must be installed and on PATH. This blocks portability to CI/CD containers and environments that have python-gitlab but not glab.
2. **Auth bypass**: The subprocess call routes around the token-auth mechanism that python-gitlab manages. This creates two separate auth paths for the same script.
3. **Linting debt**: The S607 linting violation (subprocess with partial path) was suppressed with `shutil.which` as a workaround rather than eliminated architecturally. The underlying violation remains.

The goal is to close all three problems by making `_resolve_token()` env-var-only, matching the pattern already used in `gitlab_context.py`.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: gitlab_context.py — env-var-only _resolve_token()

- **Location**: `plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py:97-107`
- **Relevance**: This file has an identical `_resolve_token()` function that already uses env-var-only resolution with no subprocess call. It is the resolved form of the pattern that fetch_gitlab_mr.py should match.
- **Reusable**: The exact function body is the reference implementation. `_resolve_token()` in that file is a single-line return: `return os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN") or None`

#### Pattern 2: gitlab_context.py — get_gitlab_client() error message

- **Location**: `plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py:110-124`
- **Relevance**: The error message in `get_gitlab_client()` in this file reads "No GitLab token found. Set GITLAB_TOKEN env var." — the env-var-only message format that fetch_gitlab_mr.py's error should be updated to match.
- **Reusable**: Error message wording and the pattern of raising with a library exception type.

#### Pattern 3: fetch_gitlab_mr.py — existing env var fallback already in place

- **Location**: `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:102-103`
- **Relevance**: Lines 102-103 already handle env var resolution and return early before the subprocess block at lines 105-114. The subprocess block is only reached when both env vars are absent. Removing lines 105-115 makes the function correct without needing to add anything.
- **Reusable**: The early-return pattern at lines 102-103 is the complete replacement; the glab fallback block can be deleted entirely.

### Existing Infrastructure

- `fetch_gitlab_mr.py` declares `python-gitlab>=4.0.0` as a dependency at line 4. The library is already imported (`import gitlab`, `import gitlab.exceptions`) at lines 24-25.
- `get_gitlab_client()` at line 118 is the single caller of `_resolve_token()`. It already handles the `None` return case with a `GitLabFetchError` raise at line 129.
- The `shutil` and `subprocess` imports (lines 17-18) would become unused after the subprocess block is removed. Both imports can be deleted.
- `gitlab_context.py` already removed the glab fallback entirely and has no S607 findings. It is the established codebase pattern for this script type.

### Code References

- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:91-115` — `_resolve_token()` function containing the subprocess block to be removed
- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:102-103` — env var early-return that already works without glab
- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:105-115` — subprocess block (shutil.which + subprocess.run) to be eliminated
- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:127-132` — `get_gitlab_client()`, single caller of `_resolve_token()`, error message needs updating
- `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py:17-18` — `shutil` and `subprocess` imports that become unused after change
- `plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py:97-107` — reference implementation of env-var-only `_resolve_token()`
- `plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py:23-25` — separate file that still uses `shutil.which("glab")` pattern (noted as related, but out of scope for this item)

---

## Use Scenarios

### Scenario 1: CI/CD pipeline without glab installed

**Actor**: Automated CI pipeline running create-merge-request-changelog
**Trigger**: Pipeline job invokes fetch_gitlab_mr.py to retrieve MR data; `GITLAB_TOKEN` is set as a CI secret; `glab` binary is not present
**Goal**: Fetch MR metadata and produce changelog without requiring glab installation
**Expected Outcome**: Script authenticates via `GITLAB_TOKEN`, fetches MR data successfully, exits 0. No "glab not found" failure.

### Scenario 2: Developer workstation without glab

**Actor**: Developer running the create-merge-request-changelog skill locally
**Trigger**: Developer has `GITLAB_TOKEN` in their shell environment but has not installed the glab CLI
**Goal**: Run the skill without needing to install an additional binary
**Expected Outcome**: Script resolves token from environment variable, runs to completion. No dependency on glab.

### Scenario 3: Ruff linting in CI

**Actor**: CI linting step running `ruff check` on the repository
**Trigger**: Pre-commit hook or CI workflow lints fetch_gitlab_mr.py
**Goal**: Linting passes with no S607 violations
**Expected Outcome**: `ruff check` exits 0 with no S607 errors in fetch_gitlab_mr.py.

### Scenario 4: User with no token configured

**Actor**: Developer who has not set `GITLAB_TOKEN` or `GITLAB_PRIVATE_TOKEN`
**Trigger**: Runs fetch_gitlab_mr.py without any token in environment
**Goal**: Receive a clear error message explaining what to set
**Expected Outcome**: Error message states that `GITLAB_TOKEN` (or `GITLAB_PRIVATE_TOKEN`) environment variable is required. Message no longer references glab CLI config as an alternative.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | `get_gitlab_context.py` in the gitlab-skill plugin (`plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py`) also uses `shutil.which("glab")` — the feature request names this file as related but the acceptance criteria cover only fetch_gitlab_mr.py | If left unresolved, the same S607 pattern and glab binary dependency persists in a second file; however this is explicitly out of scope for this item per the issue |
| 2 | Behavior | The backlog RT-ICA noted an open assumption: whether python-gitlab has a config-file-reading mechanism for token discovery (beyond env vars), or whether env-var-only is sufficient | Resolved by the acceptance criteria: env-var-only is the desired end state; no python-gitlab config-file reading is required |
| 3 | Integration | Removing the glab fallback changes observable behavior: previously a glab-authenticated user with no env var set would succeed; after the change they will get a token-not-found error | This is intentional per the feature request; the behavior change is the goal |

---

## Questions Requiring Resolution

No blocking questions remain. The acceptance criteria are explicit, the reference implementation exists in `gitlab_context.py`, the scope is a single function in a single file, and the backlog RT-ICA was approved. All gaps noted above are either explicitly resolved by the acceptance criteria or acknowledged as intentional behavior changes.

For completeness, one informational question is noted:

### Q1: Scope of related get_gitlab_context.py fix

- **Category**: Scope
- **Gap**: `plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py` also uses `shutil.which("glab")` + subprocess. The issue notes it as related but does not include it in acceptance criteria.
- **Question**: Should fixing `get_gitlab_context.py` be part of this item, or handled as a separate backlog item?
- **Options**:
  - A) Include in this item (expand scope slightly, fix both files in one change)
  - B) Leave for the existing related backlog item "Fix pre-existing linting errors in gitlab_context.py"
- **Why It Matters**: The answer affects whether the implementer touches one file or two.
- **Resolution**: _pending — default to B (separate item) unless orchestrator confirms otherwise_

---

## Goals (Pending Resolution)

_These goals are derived from verified facts and the accepted acceptance criteria. No open user questions block them._

1. Remove the subprocess block (lines 105-115) from `_resolve_token()` in `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py`.
2. Remove the now-unused `shutil` and `subprocess` imports (lines 17-18).
3. Update the error message in `get_gitlab_client()` (line 129) to reflect env-var-only auth, removing the reference to glab config.
4. Verify `ruff check` reports no S607 errors on the modified file.
5. Confirm the script runs successfully when `GITLAB_TOKEN` is set and glab is absent.

---

## Next Steps

Goals are clear and acceptance criteria are pre-defined. No user questions are blocking.

1. Proceed directly to architecture design (python-cli-design-spec) — the change is a single-function deletion with one import cleanup and one string update.
2. Alternatively, proceed directly to implementation — the reference implementation exists at `plugins/gitlab-skill/skills/gitlab-skill/scripts/gitlab_context.py:97-107`.
3. After implementation, run `ruff check .claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py` to confirm no S607 violations remain.
