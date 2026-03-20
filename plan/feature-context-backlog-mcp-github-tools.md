# Feature Context: Backlog MCP Server GitHub Tools Extension

## Document Metadata

- **Generated**: 2026-03-20
- **Input Type**: simple_description
- **Source**: gh CLI audit (session 2026-03-20) -- 38 `gh` CLI references across 12 plugin markdown files
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The development-harness plugin's SKILL.md files and reference docs instruct agents to run `gh` CLI commands for GitHub operations (issues, labels, milestones, Projects V2). `gh` is not a dependency of the plugin and is not installed in user environments. The backlog MCP server already uses PyGithub for issue CRUD -- extend it to cover all operations the plugin docs reference. Audit report at `.claude/reports/gh-cli-audit-2026-03-20.md`.

---

## Core Intent Analysis

### WHO (Target Users)

AI agents executing development-harness skills -- specifically agents running `/dh:groom-backlog-item`, `/dh:work-backlog-item`, and validation/setup procedures defined in the plugin's reference docs. These agents currently encounter `gh` commands they cannot execute.

### WHAT (Desired Outcome)

All GitHub operations referenced in development-harness plugin docs are available as MCP tools on the existing backlog FastMCP server. Agents call MCP tools instead of shelling out to `gh`. No new dependencies beyond PyGithub (already declared). No subprocess calls to `gh`.

### WHEN (Trigger Conditions)

Agents encounter GitHub operations during backlog grooming, work-item processing, validation, and initial project setup. Currently these operations fail silently or block the agent because `gh` is not installed.

### WHY (Problem Being Solved)

1. `gh` CLI is not installed in user environments -- agents cannot execute the documented commands
2. Plugin docs contain 38 references to `gh` commands across 12 files that produce runtime failures
3. PyGithub is already a declared dependency -- these operations are achievable without adding dependencies
4. The MCP server already handles issue CRUD -- the gap is ancillary operations (comments, labels, milestones, projects, PRs)

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Existing Backlog MCP Server

- **Location**: `plugins/development-harness/backlog_core/server.py`
- **Relevance**: This is the server being extended. Already exposes 11 tools: `backlog_add`, `backlog_list`, `backlog_view`, `backlog_sync`, `backlog_close`, `backlog_resolve`, `backlog_update`, `backlog_groom`, `backlog_normalize`, `backlog_pull`, `backlog_get_ready_sam_tasks`
- **Reusable**: Authentication setup (PyGithub client initialization), return format convention (dict with `messages`/`warnings`/`error` keys), FastMCP tool registration pattern

#### Pattern 2: GitHub Project Setup Script

- **Location**: Referenced in audit as `github_project_setup.py` -- invoked via `uv run .../github_project_setup.py milestone start` and `uv run .../github_project_setup.py labels`
- **Relevance**: This script already implements milestone and label operations but wraps `gh api` subprocess calls. The logic (what operations to perform, what parameters to pass) is relevant; the transport (subprocess to `gh`) is what gets replaced by PyGithub
- **Reusable**: Business logic for milestone creation, label provisioning -- needs transport replacement

#### Pattern 3: State Handler Label Transitions

- **Location**: Referenced in audit as `state_handler.apply_github_transition()` -- the canonical owner of label transitions
- **Relevance**: Label management is explicitly prohibited as a direct `gh` operation in plugin docs. The state handler owns label mutations. New tools should provide read-only label listing only -- not label set/create/delete
- **Reusable**: Establishes the boundary: new MCP tools cover read-only label listing, not label mutation

### Existing Infrastructure

The backlog MCP server (FastMCP-based) is the target for new tools. Key known properties from the MCP server description in session context:

- Tools return dicts with `messages` (list), `warnings` (list), and `error` (key present on failure)
- GitHub Issues are the source of truth; `.claude/backlog/` files are local cache
- Authentication uses `GITHUB_TOKEN` environment variable
- PyGithub is the GitHub client library

### Code References

- `plugins/development-harness/backlog_core/server.py` -- MCP server implementation (target for extension)
- `plugins/development-harness/tests/conftest.py` -- test fixtures for the server
- `.claude/reports/gh-cli-audit-2026-03-20.md` -- complete audit of all 38 `gh` references

---

## Use Scenarios

### Scenario 1: Backlog Grooming Completion Evidence

**Actor**: Agent executing `/dh:groom-backlog-item`
**Trigger**: Agent reaches the "check if already done" step in grooming workflow
**Goal**: Search for merged PRs referencing the issue, post a completion comment, and close the issue
**Expected Outcome**: Agent calls MCP tools to list merged PRs by issue reference, add a comment with evidence, and close the issue -- without needing `gh` installed

### Scenario 2: Validation Plan Execution

**Actor**: Agent running validation checks from `validation-plan.md`
**Trigger**: Agent needs to verify labels exist, issues are open, milestones are assigned
**Goal**: Read-only queries to verify GitHub state matches expected configuration
**Expected Outcome**: Agent calls MCP tools for label listing, issue viewing (with state+labels), and milestone listing -- receives structured data it can validate against

### Scenario 3: Initial Project Setup

**Actor**: Agent or user running first-time GitHub project configuration
**Trigger**: New repository needs backlog project board, milestones, and labels provisioned
**Goal**: Create a Projects V2 board, link it to the repo, create initial milestones
**Expected Outcome**: Agent calls MCP tools for project creation, repo linking, and milestone creation -- all via PyGithub/GraphQL without `gh` CLI

### Scenario 4: External Repo File Fetch

**Actor**: Agent executing SAM definition retrieval from `sam-definition.md`
**Trigger**: Agent needs to fetch a raw file from an external public GitHub repo (e.g., `bitflight-devops/stateless-agent-methodology`)
**Goal**: Retrieve raw file content from a GitHub repo without cloning it
**Expected Outcome**: Agent calls an MCP tool that fetches file content via PyGithub's `get_contents()` API

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Projects V2 operations require GraphQL -- PyGithub has no native Projects V2 objects. PyGithub exposes raw `graphql_query()` methods but no typed V2 project support | Projects V2 tools may require raw GraphQL strings in the server code, or a new dependency |
| 2 | Scope | PR search operations (`gh pr list --search '#N' --state merged`) -- unclear if this is a core need or if it can be deferred | Grooming completion-evidence workflow is blocked without it |
| 3 | Integration | `github_project_setup.py` already implements some of these operations via `gh` subprocess -- unclear if that script should be replaced, refactored to call MCP tools, or left as-is with the MCP tools as the new canonical path | Two implementations of the same operations create maintenance burden |
| 4 | Behavior | Repo identity discovery (`gh repo view --json nameWithOwner`) -- the MCP server presumably already knows the repo. Is this already configured in the server? | If not configured, every tool needs a repo parameter |
| 5 | Scope | `gh auth status` and `gh api` for raw file content from external repos -- these are fundamentally different from backlog operations. Should they live on this server or a separate one? | Mixing concerns on the backlog server |
| 6 | Integration | Existing `backlog_view` and `backlog_close` may already cover some "view issue" and "close issue" operations from the audit. Need to verify what fields they return and whether they match the audit requirements | Risk of duplicate tools with slightly different behavior |
| 7 | Behavior | Anti-pattern documentation references `gh issue edit` and `gh label` as prohibited -- the new tools must not accidentally enable these prohibited operations | Could undermine the state handler's label transition ownership |

---

## Questions Requiring Resolution

### Q1: Projects V2 -- in scope or deferred?

- **Category**: Scope
- **Gap**: Projects V2 requires GraphQL. PyGithub has raw GraphQL methods but no typed Projects V2 support. This is the most complex part of the feature.
- **Question**: Should Projects V2 operations (list projects, create project, link to repo) be included in this feature, or deferred to a separate effort? If included, is raw GraphQL via PyGithub's `graphql_query()` acceptable, or should a dedicated library (e.g., `gh-project-v2`) be added?
- **Options**:
  - A) Include Projects V2 using PyGithub's raw GraphQL methods
  - B) Include Projects V2 using a dedicated third-party library
  - C) Defer Projects V2 entirely to a separate feature
- **Why It Matters**: Projects V2 is 3 of the 15 unique operations. Including it significantly increases scope and may require a new dependency.
- **Resolution**: _pending_

### Q2: What happens to `github_project_setup.py`?

- **Category**: Integration
- **Gap**: The setup script wraps `gh api` for milestone and label operations. The new MCP tools would provide the same operations via PyGithub.
- **Question**: After the MCP tools are added, should `github_project_setup.py` be (A) deleted and its callers updated to use MCP tools, (B) refactored to call PyGithub directly instead of `gh`, or (C) left as-is with MCP tools as the preferred path and the script deprecated?
- **Options**:
  - A) Delete script, update all callers to MCP tools
  - B) Refactor script internals to use PyGithub (no `gh` subprocess)
  - C) Leave script as-is, deprecate in docs, MCP tools are canonical
- **Why It Matters**: Two implementations of the same operations is a maintenance burden. The 12 doc files that reference `gh` commands also need updating regardless.
- **Resolution**: _pending_

### Q3: External repo file fetch -- backlog server or separate?

- **Category**: Scope
- **Gap**: Fetching raw files from external repos (`gh api repos/OWNER/REPO/contents/FILE`) is not a backlog operation. It is a general GitHub utility.
- **Question**: Should the "fetch raw file from external repo" operation be added to the backlog MCP server, or should it be a separate tool/server?
- **Options**:
  - A) Add to backlog server (pragmatic -- reuses PyGithub client)
  - B) Separate MCP server or tool (cleaner separation of concerns)
  - C) Out of scope -- handled differently (e.g., `mcp__Ref__ref_read_url` can fetch public GitHub files)
- **Why It Matters**: The backlog server's responsibility boundary. Adding general GitHub utilities expands its scope beyond backlog management.
- **Resolution**: _pending_

### Q4: Do existing `backlog_view` and `backlog_close` already cover audit requirements?

- **Category**: Integration
- **Gap**: The audit requires "view issue (state+labels)" and "close issue (--reason completed)". Existing MCP tools `backlog_view` and `backlog_close` may already provide these.
- **Question**: Do the existing tools return sufficient data (state, labels, title) and accept sufficient parameters (close reason) to satisfy the audit requirements, or do they need enhancement?
- **Why It Matters**: Determines whether new tools are needed or existing tools just need parameter/return-value additions.
- **Resolution**: _pending_ -- requires inspecting current tool signatures and return values

### Q5: Doc migration -- in scope or separate effort?

- **Category**: Scope
- **Gap**: After MCP tools are added, 12 plugin markdown files containing 38 `gh` references need to be updated to reference MCP tools instead.
- **Question**: Is updating the 12 doc files part of this feature, or is it a separate follow-up effort?
- **Options**:
  - A) In scope -- deliver tools + doc migration together
  - B) Separate effort -- deliver tools first, migrate docs in a follow-up
- **Why It Matters**: Doc migration is significant work (12 files, 38 references) but the tools are useless without it -- agents will continue trying `gh` commands until docs are updated.
- **Resolution**: _pending_

### Q6: PR search -- in scope or deferred?

- **Category**: Scope
- **Gap**: The grooming workflow searches for merged PRs as completion evidence (`gh pr list --search '#N' --state merged`). This is a GitHub search operation, not a backlog operation.
- **Question**: Should merged-PR search be included as an MCP tool, or should the grooming workflow be updated to use a different completion-evidence mechanism?
- **Options**:
  - A) Add PR search tool to backlog server
  - B) Out of scope -- grooming workflow uses alternative evidence
- **Why It Matters**: PR search is only used in one workflow (grooming). Adding it expands the server's scope.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. All issue-adjacent operations (comment, view with labels/state) available as MCP tools on the backlog server
2. Read-only label listing available as an MCP tool (no label mutation -- state handler owns that)
3. Milestone CRUD (list, get soonest open, create) available as MCP tools
4. Projects V2 operations available as MCP tools (pending Q1 resolution on scope/approach)
5. Repo identity discovery handled internally by the server (not exposed as a separate tool)
6. All new tools follow existing return format convention (dict with `messages`/`warnings`/`error`)
7. Plugin docs updated to reference MCP tools instead of `gh` commands (pending Q5 resolution)

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
