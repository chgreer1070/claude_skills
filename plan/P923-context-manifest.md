# Context Manifest — Migrate Milestone Skills from gh CLI to Project Tooling

## How Milestone Skills Currently Work: A Complete Flow

The four milestone skills (`/create-milestone`, `/start-milestone`, `/complete-milestone`, `/group-items-to-milestone`) form a sequence of operations that manage GitHub milestones as containers for organizing work. Understanding the current implementation requires tracing how each skill moves data through the system.

**User invocation entry point**: When a user invokes `/create-milestone` via Claude Code, the skill's SKILL.md frontmatter loads instructions that are rendered into a prompt. The skill then executes a series of steps, each calling either the PyGithub script (`github_project_setup.py`) or the `gh` CLI binary.

**Create-milestone workflow**: When a user wants to create a new milestone, Step 1 validates the milestone data (title, due date, description). Step 2 performs a duplicate check by calling `gh api repos/{owner}/{repo}/milestones --jq '.[] | select(.state=="open") | .title'` — this raw REST API call fetches all open milestones and filters by title to ensure the new milestone title does not already exist. If a duplicate is found, the skill exits with an error message. If no duplicate exists, Step 3 calls `uv run github_project_setup.py milestone create --title "{title}" --due-on "{date}" --description "{desc}"` which uses PyGithub to create the milestone via `repository.create_milestone()`.

The architecture here shows a split: read operations (Step 2's duplicate check) use raw `gh api` calls, while write operations (Step 3's creation) use the PyGithub script. This split is repeated across all four skills.

**Start-milestone workflow**: This skill transitions a milestone from "created" to "in progress" state. Step 1 resolves the milestone by number using `gh api repos/{owner}/{repo}/milestones/{N}` to fetch metadata including title, state, and issue counts. Step 2 lists all open issues assigned to that milestone using `gh issue list --milestone "{title}" --state open`. Step 3 transitions each issue's labels to "status:in-progress" — Step 4 first ensures the label exists with `gh label create "status:in-progress"`, then Step 5 calls the PyGithub script via `github_project_setup.py milestone start --number N` which performs bulk `issue.edit(labels=[...])` operations. Step 6 updates Projects V2 by calling `gh project list --owner` to verify project existence, then uses Project V2 GraphQL via the internal `_gh_graphql()` function.

**Complete-milestone workflow**: This is the most complex skill. Step 1 discovers the milestone using `gh api repos/{owner}/{repo}/milestones/{N}`, then queries open issues with `gh issue list --milestone "{title}" --state open` and closed issues with `gh issue list --milestone "{title}" --state closed`. Step 2 presents the user with options for handling open issues — carry-forward (Step 3A), close without moving (Step 3D), or dismiss the operation. Step 3A carries forward open issues to a new milestone by: (1) creating a new milestone with `gh api POST repos/{owner}/{repo}/milestones` receiving a JSON body with title/due-on/description, (2) reassigning each open issue to the new milestone using `gh api PATCH repos/{owner}/{repo}/issues/{N}` with a JSON body containing `"milestone": {M}`. Step 3C removes milestone assignment from issues using `gh api PATCH repos/{owner}/{repo}/issues/{N}` with `"milestone": null` in the body. Step 3D closes issues using `gh issue close {N} --comment "..."`. Step 4 closes the current milestone using the PyGithub script via `github_project_setup.py milestone close --number N`. Step 5 updates Projects V2 to move all issues out of the closed milestone.

**Group-items-to-milestone workflow**: This skill creates a set of new issues and assigns them all to an existing milestone. Step 1 resolves the milestone by number. Step 2 presents a form where the user defines issues to create (title, description per issue). Step 3 validates the input. Step 4 creates each issue with `github_project_setup.py issue create --title "..." --description "..."`. Step 5 assigns each created issue to the milestone using `gh api PATCH repos/{owner}/{repo}/issues/{N}` with milestone in the body. Step 6 updates Projects V2.

**Error handling pattern across all skills**: Each skill contains a fallback block that checks if `gh` CLI is available. If `gh` is not found, the skill directs the user to `setup_gh.py`. This error-handling path exists in all four SKILL.md files.

**GitHub authentication**: All these operations (both `gh` CLI and PyGithub script calls) authenticate using `GITHUB_TOKEN` from the environment. The token must have write permission to the repo.

**Why the split exists**: The initial design appears to have used `gh` CLI as the primary discovery mechanism because `gh` CLI was installed with CloudAI environments, and its jq output filtering made sense for simple queries. The PyGithub script was used for more complex mutations (label transitions, bulk updates) that benefited from programmatic error handling. This resulted in parallel code paths that must be maintained.

## For This Migration: What Needs to Connect

The migration replaces all `gh` CLI invocations with one of two alternatives: backlog MCP tools (for reads) or new PyGithub subcommands (for writes).

**Critical sequencing constraint**: Three new PyGithub subcommands must be implemented in `github_project_setup.py` and have passing unit tests before any SKILL.md can reference them. Tasks T01, T02, T03 create these subcommands. Tasks T04, T05, T06, T07 rewrite the skills to use them. The dependency graph prevents skill rewrites from starting until the subcommands exist.

**Backlog MCP tools integration**: The backlog MCP server (`mcp__plugin_dh_backlog__*`) already exists and provides tools like `backlog_list_milestones(state="open")` which returns structured JSON containing number, title, state, open_issues, closed_issues, due_on. This tool replaces `gh api repos/.../milestones` calls. Similarly, `backlog_list_issues(milestone="{title}", state="open")` replaces `gh issue list --milestone`. The skill agent rewriting them must know that the MCP tool is already available in the Claude Code session and can be invoked directly without subprocess.

**PyGithub subcommand interface contract**: Each new subcommand (T01, T02, T03) is invoked from SKILL.md as `uv run .claude/skills/gh/scripts/github_project_setup.py {subcommand} {args}`. The agent implementing these must follow the interface signatures exactly as specified in the architecture spec section 4.1–4.3. The skill-rewriting agents (T04–T07) will embed these invocations as literal commands in SKILL.md instructions.

**Idempotency requirement**: The three new subcommands must be idempotent. If `issue remove-milestone` is called on an issue with no milestone, it prints a warning and exits 0 (does not error). If `issue close` is called on an already-closed issue, it prints a warning and exits 0. This allows SKILL.md to call these operations without conditional logic checking pre-state first.

**Removing fallback paths**: The skills currently contain a pattern where PyGithub script calls are "primary" but `gh` CLI calls are listed as fallback (e.g., "If the PyGithub script fails, try this gh command instead"). These fallback paths must be completely removed — PyGithub/MCP are the only paths after migration. The skill agents must understand that removing fallbacks is not simplification, it is the core requirement.

**Error handling replacement**: The "gh not installed" error blocks must be removed entirely. Post-migration, errors can only come from PyGithub exceptions (handled by the script) or MCP tool errors (handled by the session). The skill agent rewriting them must delete these blocks without replacement.

## Technical Reference Details

### Component Interfaces and Signatures

**Backlog MCP Tools** (available via Claude Code session):

```text
backlog_list_milestones(state="open" | "closed" | "all")
  Returns: {"milestones": [{"number": int, "title": str, "state": str, "open_issues": int, "closed_issues": int, "due_on": str | null, ...}]}

backlog_create_milestone(title: str, due_on: str | None, description: str)
  Returns: {"number": int, "title": str, "html_url": str, ...}

backlog_list_issues(milestone: str, state: str, labels: str | None)
  Returns: {"issues": [{"number": int, "title": str, "state": str, "labels": [str], "milestone": str | null, ...}]}
```

**New PyGithub Subcommands** (to be added to `.claude/skills/gh/scripts/github_project_setup.py`):

```text
issue set-milestone --issue N --milestone M
  Calls: repository.get_issue(N), repository.get_milestone(M), issue.edit(milestone=milestone_obj)
  Prints: "Issue #N assigned to milestone #M \"{title}\""
  Exit: 0 on success, 1 on error

issue remove-milestone --issue N
  Calls: repository.get_issue(N), issue.edit(milestone=None) [PyGithub API TBD — verify in T02]
  Prints: "Issue #N milestone removed" or warning if already unassigned
  Exit: 0 always (idempotent), 1 only if issue not found

issue close --number N --comment "..."
  Calls: repository.get_issue(N), issue.create_comment(...) if comment non-empty, issue.edit(state="closed")
  Prints: "Issue #N closed"
  Exit: 0 on success, 1 if issue not found or comment fails; does NOT close issue if comment fails
```

**Existing PyGithub Subcommands** (unchanged, already in use):

```text
milestone create --title "..." --due-on "..." --description "..."
milestone start --number N
milestone close --number N
issue create --title "..." --description "..."
project update-status -i N -s STATUS
labels {command}
```

### Data Structures

**PyGithub Issue object** (from `github` library):

```python
issue.number: int
issue.title: str
issue.state: str  # "open" or "closed"
issue.milestone: Milestone | None
issue.labels: list[Label]
issue.edit(milestone=Milestone | None, state="closed", ...)
issue.create_comment(body: str)
```

**PyGithub Milestone object**:

```python
milestone.number: int
milestone.title: str
milestone.state: str  # "open" or "closed"
milestone.open_issues: int
milestone.closed_issues: int
milestone.due_on: datetime | None
```

**Backlog MCP response shapes**:

```python
# backlog_list_milestones response
{
    "milestones": [
        {
            "number": int,
            "title": str,
            "state": str,  # "open", "closed"
            "description": str | None,
            "open_issues": int,
            "closed_issues": int,
            "due_on": str | None,  # ISO 8601 or null
            "url": str,
            "html_url": str
        }
    ],
    "count": int
}

# backlog_list_issues response
{
    "issues": [
        {
            "number": int,
            "title": str,
            "state": str,
            "milestone": str | None,
            "labels": [str],
            "url": str,
            "html_url": str
        }
    ],
    "count": int
}
```

### Configuration Requirements

No new configuration files. The script reads `GITHUB_TOKEN` from the environment. Default repo is `Jamie-BitFlight/claude_skills`. Skills may pass `--repo` to override.

### File Locations for Implementation

**New PyGithub subcommands**: `.claude/skills/gh/scripts/github_project_setup.py` — add to the existing `issue_app` Typer group

**Unit tests for new subcommands**: `.claude/skills/gh/tests/test_github_project_setup.py` — create if absent, extend if present. Use pytest + pytest-mock to mock PyGithub calls.

**Skills to be rewritten** (in this order by dependency):

- `.claude/skills/create-milestone/SKILL.md`
- `.claude/skills/start-milestone/SKILL.md`
- `.claude/skills/complete-milestone/SKILL.md`
- `.claude/skills/group-items-to-milestone/SKILL.md`

**Architecture spec** (reference for exact replacements): `plan/architect-migrate-milestone-skills-gh-cli.md` section 4.4 contains the replacement mapping table

**Feature context**: `plan/feature-context-migrate-milestone-skills-gh-cli.md` for problem statement and desired outcome

**Research report**: `.claude/reports/milestone-gh-migration-analysis-20260321.md` for analysis of which operations are replaceable and which need new code
