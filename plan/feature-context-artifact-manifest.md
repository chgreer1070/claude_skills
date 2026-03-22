# Feature Context: Plan Artifact Manifest — Backend-First Issue-Linked Artifact Registry

**GitHub Issue**: #965
**Priority**: P1
**Date**: 2026-03-21

---

## Problem Space

Plan artifacts — feature-context docs, architect specs, task plans, T0/TN baselines, codebase analyses — are local files in `plan/` with partial linking to GitHub Issues. Two structural gaps prevent reliable multi-agent workflows:

### Gap 1: Worktree Isolation Breaks Artifact Access

When `/work-milestone` dispatches agents into isolated git worktrees, those agents cannot access uncommitted plan files from the root worktree. Plan artifacts are produced during `/add-new-feature` and accumulate changes during `/implement-feature`, but worktree-isolated agents see only what has been committed and checked out into their branch. Uncommitted or root-worktree-only files are invisible.

This creates a blind spot: an implementation agent cannot read the architect spec or feature context that defines what it should build, unless those files happen to be committed on the branch the worktree tracks.

### Gap 2: No Structured Artifact Inventory Per Issue

There is no single place — on GitHub or locally — that lists ALL artifacts associated with a feature issue. The current state:

- Feature context files follow a naming convention (`plan/feature-context-{slug}.md`) but are not registered anywhere
- Architect specs follow a naming convention (`plan/architect-{slug}.md`) but are not registered anywhere
- Task plans are linked via SAM (`P{N}`) but the mapping from GitHub issue to plan number is implicit
- T0 baseline and TN verification files exist only when bookend tasks run, with no registry
- Codebase analysis files land in `plan/codebase/` with no back-reference to the originating issue

An agent that needs "all artifacts for issue #965" must glob the filesystem by slug, hope the naming conventions were followed, and has no way to know if an artifact is missing vs. never created.

### Why This Matters

The SAM workflow produces 3-6 artifacts per feature. Without a manifest:

- **Discovery is fragile**: consumers rely on naming conventions and filesystem scanning
- **Completeness is unverifiable**: no way to confirm all expected artifacts exist
- **Cross-worktree access requires commits**: agents in isolated worktrees cannot discover artifacts that haven't been committed
- **Backend portability is blocked**: local-file-only artifacts cannot be queried from GitLab, Linear, or Supabase backends

---

## Desired Outcomes

### 1. Artifact Registry in Issue Body

Each GitHub Issue that represents a feature (story-level) carries a structured Artifact Manifest section listing all associated plan artifacts. The manifest includes, per artifact:

- **Type**: the artifact category (feature-context, architect, task-plan, T0-baseline, TN-verification, codebase-analysis)
- **Path**: relative file path in the repository
- **Status**: lifecycle state (e.g., draft, current, superseded, archived)

### 2. Producer Registration

Agents that create plan artifacts register them in the manifest as part of their production workflow. Registration is a write operation to the backend (GitHub Issue body update), not a local file edit. This ensures the manifest is available to all consumers — including worktree-isolated agents — without requiring a git commit.

### 3. Consumer Discovery via MCP

Agents that need plan artifacts discover them through MCP tool calls, not filesystem globbing. A consumer agent asks "what artifacts exist for issue #965?" and receives a structured response with types, paths, and statuses. This works regardless of whether the consumer is in the root worktree, an isolated worktree, or a CI environment.

### 4. Backend-First, Local-Cache Architecture

GitHub (Issues, Projects V2, comments, sub-issues, issue links) is the central database. Local plan files are the cache. This inverts the current relationship where local files are primary and GitHub links are secondary.

This architecture must support future backend providers (GitLab, Linear, Supabase) without redesigning the manifest schema or consumer interface. The MCP layer abstracts the backend; consumers interact with artifact types and issue numbers, not provider-specific APIs.

### 5. Worktree Safety

Plan artifacts ALWAYS reside in the root worktree, never inside worktree agent paths. The manifest stores paths relative to the repository root. Worktree-isolated agents access artifact content through the backend (issue body, comments) or through MCP tools that read from the root worktree — never by expecting the file to exist in their own worktree checkout.

---

## Constraints

### Hard Constraints

- **Root worktree only**: Plan artifacts are never created inside `/.claude/worktrees/` paths. They live in `plan/` at the repository root.
- **Backend is source of truth**: If the GitHub Issue manifest says an artifact exists, it exists. If the local file is missing, it is a cache miss — not an error in the manifest.
- **No new GitHub features required**: Implementation uses existing GitHub primitives — issue body markdown, comments, Projects V2 custom fields, sub-issues, issue links. No GitHub Apps or custom webhooks.
- **Backward compatibility**: Existing plan artifacts (`plan/feature-context-*.md`, `plan/architect-*.md`, etc.) continue to work. The manifest is additive — it registers what exists, it does not replace how artifacts are stored.

### Soft Constraints

- **Minimize API calls**: Manifest reads should be cacheable. Avoid designs that require N API calls to discover N artifacts.
- **Human-readable**: The Artifact Manifest section in the issue body should be readable by humans browsing GitHub, not just parseable by machines.
- **Idempotent registration**: Registering the same artifact twice produces the same manifest state, not duplicates.

---

## Artifact Taxonomy

### Primary Artifacts (always produced for every feature)

| Type | Naming Convention | Producer Agent |
|------|-------------------|----------------|
| `feature-context` | `plan/feature-context-{slug}.md` | `feature-researcher` |
| `architect` | `plan/architect-{slug}.md` | `python-cli-design-spec` |
| `task-plan` | `plan/tasks-{N}-{slug}/` or `plan/tasks-{N}-{slug}.md` | `swarm-task-planner` |

### Secondary Artifacts (produced when conditions are met)

| Type | Naming Convention | Producer Agent | Condition |
|------|-------------------|----------------|-----------|
| `T0-baseline` | `plan/T0-baseline-{slug}.yaml` | `t0-baseline-capture` | `acceptance-criteria-structured` present |
| `TN-verification` | `plan/TN-verification-{slug}.yaml` | `tn-verification-gate` | T0 baseline exists |
| `codebase-analysis` | `plan/codebase/{focus}.md` | `codebase-analyzer` | Optional phase in `/add-new-feature` |

### Transient Artifacts (never registered in manifest)

- `.claude/context/active-task-{session_id}.json` — ephemeral per-session state
- Grooming session transcripts — human-decision artifacts, immutable, not plan artifacts

---

## Industry Research Findings

Research into how established project management platforms handle artifact-to-issue linking reveals several architectural patterns relevant to this feature.

### Linear: Resources Section as Manifest

Linear treats each issue's Resources section as an artifact manifest. Documents are first-class entities — not file attachments — with full versioning, inline comments, and bi-directional @ mention cross-references. The Resources section aggregates embedded documents, external links, and related issues into a single container per issue.

Key insight for this feature: Linear's MCP server (21+ tools) does NOT expose a dedicated artifact/document query tool. Artifact access flows through issue relationship queries — you fetch the issue and traverse its relationships. This suggests artifact discovery should be issue-centric (query by issue number), not artifact-centric (query by artifact type globally).

Linear's template system enforces consistent artifact structure across issues, which parallels our need for a consistent Artifact Manifest section format.

SOURCE: `/tmp/research-linear-artifacts.md` (research dated 2026-03-21), citing Linear Docs for Issue Documents, Issue Relations, Parent and Sub-issues, MCP Server.

### Jira: Remote Links Separate Ownership from Reference

Jira uses two complementary mechanisms: issue links (bidirectional edges between Jira issues) and remote links (references to external resources). The remote link pattern is architecturally significant: the artifact stays in its authoritative system (Confluence page, external spec), while the Jira issue maintains a structured reference (URL + title + relationship type + metadata) without owning or duplicating the content.

Key insight for this feature: our plan artifacts are local files — analogous to Jira's external resources. The GitHub Issue should hold structured references (path, type, status) without duplicating content. Multiple issues can reference the same artifact without redundancy. The remote link's `relationship` field (e.g., "documents", "is documented by") provides semantic meaning beyond a plain URL.

SOURCE: `/tmp/research-jira-asana-monday-artifacts.md` (research dated 2026-03-21), citing Jira issue linking model, Creating Remote Issue Links, Jira Cloud REST API.

### Monday.com: Column-Based Metadata with Queryable Schemas

Monday.com treats all relationships — files, dependencies, cross-board connections — as column types with defined schemas. Each column is a first-class data container queryable via GraphQL. The Connect Boards column creates bidirectional cross-board references with automatic linking.

Key insight for this feature: relationships should be structured and queryable, not free-text annotations. A manifest section with defined fields (type, path, status) per artifact follows the Monday pattern of treating metadata as structured data, not prose.

SOURCE: `/tmp/research-jira-asana-monday-artifacts.md` (research dated 2026-03-21), citing Monday.com Files Column, Connect Boards Column, Assets API.

### Asana: Cautionary Embedding Pattern

Asana embeds attachments within task scope with no back-references. Artifacts cannot be shared across tasks, custom fields don't connect to attachments, and dependencies model timing rather than artifact relationships. The embedding model creates redundancy and limits cross-referencing.

Key insight for this feature: avoid the Asana pattern. Artifacts should be referenced (like Jira remote links), not embedded (like Asana attachments). The manifest is a registry of references, not a container of content.

SOURCE: `/tmp/research-jira-asana-monday-artifacts.md` (research dated 2026-03-21), citing Asana Attachments API, Task dependencies.

### Cross-Platform Synthesis

Three patterns emerge across all platforms:

1. **Separate reference from ownership**: The artifact lives in its authoritative location (local file, Confluence page, external system). The issue holds a structured reference. This avoids redundancy and enables single-source-of-truth per artifact.

2. **Issue-centric discovery**: Consumers find artifacts by querying the issue, not by scanning all artifacts for issue references. The issue is the entry point; artifacts are discoverable from it.

3. **Structured over free-text**: Queryable schemas (Monday columns, Jira link types, Linear Resources) outperform free-text references (Asana descriptions) for programmatic access. The manifest format must be machine-parseable.

---

## User Personas Affected

### Producer Agents

Agents that run during `/add-new-feature` — `feature-researcher`, `python-cli-design-spec`, `swarm-task-planner`, `codebase-analyzer` — and during `/implement-feature` — `t0-baseline-capture`, `tn-verification-gate`. These agents currently write files and move on. With the manifest, they additionally register each artifact in the backend.

### Consumer Agents

Agents that need plan artifacts to do their work — `start-task` sub-agents (need architect spec, feature context), `code-reviewer` (needs architect spec for review criteria), `feature-verifier` (needs feature context for goal verification), `context-refinement` (needs all artifacts for freshness check). These agents currently rely on file paths passed in delegation prompts or filesystem conventions. With the manifest, they discover artifacts via MCP.

### Worktree-Isolated Agents

Agents dispatched via `/work-milestone` into isolated git worktrees. Currently cannot access uncommitted plan artifacts at all. With the manifest, they query the backend (GitHub Issue) and receive artifact metadata — paths for committed files, or content via issue body/comments for uncommitted artifacts.

### Human Operators

Users browsing GitHub Issues who want to see what planning work has been done for a feature. Currently must check the local filesystem. With the manifest, the issue body shows all artifacts with their types and statuses.

---

## Open Questions

1. **Manifest location within issue body**: Should the Artifact Manifest be a section in the issue body (requires body editing), a pinned comment (avoids body mutation), or a linked sub-issue (dedicated artifact tracker)? Each has trade-offs for editability, discoverability, and API complexity.

2. **Content access for uncommitted artifacts**: When a worktree-isolated agent needs the content of an uncommitted artifact, should the manifest include a content snapshot (e.g., via issue comment), or should the agent access the root worktree filesystem through a dedicated MCP tool? Comments have size limits; filesystem access requires cross-worktree permissions.

3. **Artifact versioning**: When an architect spec is updated during implementation (divergence notes, refinements), should the manifest track versions, or is "current path points to current content" sufficient?

4. **Backend abstraction boundary**: How thin is the abstraction layer? Does it expose provider-specific features (GitHub Projects V2 custom fields, Linear Resources) or only the common denominator (type, path, status per artifact)?

5. **Migration of existing artifacts**: The `plan/` directory contains artifacts for completed features that were never registered in any manifest. Should these be retroactively registered, or does the manifest apply only to new features going forward?

6. **Manifest format**: Markdown table, YAML block within HTML comment, JSON in issue body, or structured comment format? Must balance human readability with machine parseability.

---

## Alignment with Backend-First Principle

This feature advances the project's architectural direction: GitHub Issues (and eventually other backends) are the central database; local files are cache. The current state inverts this — local files are primary, GitHub links are secondary. The Artifact Manifest makes the backend the authoritative registry of what artifacts exist, while local files remain the authoritative store of artifact content.

This separation mirrors Jira's remote link pattern: ownership of content stays with the file system, ownership of the registry stays with the backend. Neither system duplicates the other's responsibility.

The Linear/GitHub Projects V2 alignment principle guides the data model: use structures that map naturally to both Linear's Resources section and GitHub's issue body sections, so future backend migration is a provider swap rather than a schema redesign.
