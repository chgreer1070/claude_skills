# Feature Context — Migrate Milestone Skills from gh CLI to Project Tooling

**Backlog item**: #923
**Status**: In-progress (P1)
**Added**: 2026-03-20
**Source**: Groomed backlog item #923 + `.claude/reports/milestone-gh-migration-analysis-20260321.md`
**Generated**: 2026-03-21

---

## Problem Statement

Four project-level milestone skills — `/create-milestone`, `/start-milestone`,
`/complete-milestone`, and `/group-items-to-milestone` — use direct `gh` CLI invocations
for GitHub operations including milestone discovery, issue listing, label creation, issue
milestone assignment, issue close, and new milestone creation.

This creates two concrete problems:

**1. Dual-dependency fragility.** Each skill carries two code paths: a PyGithub/MCP primary
path and a `gh` CLI fallback. The fact-check for this item found the split is more uneven
than previously believed — `gh` CLI is the first-reached path for discovery and issue-level
operations across all four skills, not merely a fallback. `/complete-milestone` alone
contains 10+ `gh api` and `gh issue` calls covering the majority of its workflow.

**2. Maintenance confusion.** The `gh` skill was deliberately removed as a dependency from
the `development-harness` plugin (#968, resolved). Project-level milestone skills were not
updated in that sweep. The residual `gh` usage in `.claude/skills/` creates an inconsistency:
the plugin layer is `gh`-free, but the underlying project-level skills it delegates to are
not. Users and agents cannot tell which dependency set is authoritative.

A secondary problem exists within the tooling layer: three GitHub operations needed by
milestone skills — assigning an issue to a milestone, removing an issue from a milestone,
and closing an issue with an optional comment — have no representation in `github_project_setup.py`
or the backlog MCP server. These operations are currently performed only via inline `gh api`
calls embedded in SKILL.md instruction steps.

---

## Desired Outcome

All four milestone skills operate exclusively through project tooling — backlog MCP tools
for read operations and `github_project_setup.py` for write operations — with no `gh` CLI
invocations remaining.

The outcome is observable and verifiable:

1. `grep -r "gh api\|gh issue\|gh label\|gh project"` across the four skill directories
   returns zero matches.
2. `grep -r "setup_gh\b"` across the four skill directories returns zero matches.
3. Three new subcommands exist in `github_project_setup.py` and are callable from the
   command line: `issue set-milestone`, `issue remove-milestone`, `issue close`.
4. Pytest unit tests for each new subcommand pass with mocked PyGithub calls.
5. Each skill can be invoked in a Claude Code session and reaches its main workflow step
   without failing on a missing `gh` dependency.

The migration scope is atomic: all four skills must complete migration together. Partial
migration produces mixed error messages and inconsistent dependency requirements across
skills that share the same underlying milestone operations.

---

## Stakeholders

**Direct users** — Claude Code sessions invoking `/create-milestone`, `/start-milestone`,
`/complete-milestone`, or `/group-items-to-milestone`. They encounter `gh`-not-found
errors in environments where the `gh` CLI is absent.

**Indirect consumers** — `/groom-milestone` and `/work-milestone` in the
`development-harness` plugin. Both invoke the four milestone skills via `Skill()` calls.
They do not read skill implementations and will continue to function after migration
without modification. They benefit from the cleaner dependency surface.

**Repository maintainers** — maintaining two independent GitHub API paths (PyGithub and
`gh` CLI) across the same operations doubles the surface area for drift and breakage. This
item reduces that surface.

**Downstream test suite** — `plugins/development-harness/tests/test_scenarios.py` mocks
PyGithub and MCP responses, not `gh` CLI calls. It is unaffected by this migration and
requires no changes.

---

## Risks

**Missing subcommands block skill rewrites.** `github_project_setup.py` does not currently
expose `issue set-milestone`, `issue remove-milestone`, or `issue close`. SKILL.md rewrites
that reference these subcommands cannot be validated until the script changes exist.
Sequencing constraint: the script must be extended before or in parallel with the skill
rewrites (with skill agents treating the new subcommand names as given inputs rather than
verifying existence at write time).

**Scope creep to `milestone get --number N`.** The research report initially recommended
adding a `milestone get` subcommand. The fact-check found this is not needed — filtering the
result of `backlog_list_milestones()` client-side is sufficient. Adding the subcommand
anyway would expand scope without observable benefit.

**Partial migration.** If only some of the four skills are migrated before a pause or
interruption, the result is a mixed state worse than the current state — some skills fail
on missing `gh`, others do not, and the inconsistency is invisible at invocation time.
Migration must be treated as an atomic unit.

**`gh` references in error handling.** Beyond the operational call sites, each skill
contains "gh not installed" error blocks that reference `setup_gh.py`. These must be
removed alongside the operational calls; leaving them produces dead-code noise and false
documentation.

**No live integration test.** Acceptance criteria 6 (skill reaches its main workflow step
without failing on missing `gh`) is validated by inspection of SKILL.md content, not by
running the skill end-to-end against a live GitHub repo. Behavioral regression in live
scenarios is not caught by the unit tests (which mock PyGithub) or the existing
`test_scenarios.py` (which also mocks).

---

## Dependencies

**Already available — no action needed:**

- Backlog MCP tools: `backlog_list_milestones`, `backlog_create_milestone`,
  `backlog_list_issues`, `backlog_comment_issue` — confirmed live in the running MCP
  server; cover the majority of discovery and read operations.
- PyGithub library — already installed and in active use in `github_project_setup.py`.
- `milestone start` and `milestone close` subcommands in `github_project_setup.py` —
  already handle bulk label transitions and milestone state changes.
- #968 resolved — the `development-harness` plugin layer is already `gh`-free; no
  coordination needed there.

**Prerequisite within this item — not yet available:**

- `issue set-milestone --issue N --milestone M` in `github_project_setup.py`
- `issue remove-milestone --issue N` in `github_project_setup.py`
- `issue close --number N [--comment "..."]` in `github_project_setup.py`

These three subcommands must exist (and have passing unit tests) before the SKILL.md
rewrites for `/complete-milestone` and `/group-items-to-milestone` can be completed.

**No external blockers.** No other open items gate this work.

---

## Scope Boundary

In scope:

- `.claude/skills/create-milestone/SKILL.md`
- `.claude/skills/start-milestone/SKILL.md`
- `.claude/skills/complete-milestone/SKILL.md`
- `.claude/skills/group-items-to-milestone/SKILL.md`
- `.claude/skills/gh/scripts/github_project_setup.py` — new subcommands only
- `.claude/skills/gh/tests/test_github_project_setup.py` — unit tests for new subcommands

Out of scope:

- The `gh` skill itself — it remains a general-purpose tool; this item removes milestone
  skill dependencies on it, not the skill itself
- `plugins/development-harness/` — already migrated via #968
- `plugins/development-harness/tests/test_scenarios.py` — no changes needed
- `.claude/skills/gh/references/milestones.md` — archival is optional, not a blocker
- A `milestone get --number N` subcommand — not needed; `backlog_list_milestones` +
  client-side filter is sufficient

SOURCE: Backlog item #923 (groomed 2026-03-20), fact-check section.
SOURCE: `.claude/reports/milestone-gh-migration-analysis-20260321.md` (2026-03-21).
