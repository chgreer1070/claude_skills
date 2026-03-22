# Development Harness Backend Providers

Reference for implementers planning backend integrations across the full development harness. Covers issues/backlog, plans/tasks, and artifact manifests for GitHub (current), Linear, GitLab, and Supabase.

For artifact-specific Protocol details, see [artifact-manifest-backends.md](./artifact-manifest-backends.md).
For detailed platform research with citations, see [research/task-management/artifact-manifest-backend-providers.md](../../../research/task-management/artifact-manifest-backend-providers.md).
For the architect spec, see `~/.dh/projects/{slug}/plan/architect-artifact-manifest.md` (state artifact, access via `artifact_read(artifact_type="architect")`).
For the feature context and desired outcomes, see `~/.dh/projects/{slug}/plan/feature-context-artifact-manifest.md` (state artifact, access via `artifact_read(artifact_type="feature-context")`).

## Current Architecture

The development harness uses three subsystems, all currently backed by GitHub and local files.

### Issues/Backlog (backlog MCP)

- **Source of truth**: GitHub Issues via GraphQL (bulk fetch) + PyGithub REST (single-item mutations)
- **Local cache**: `~/.dh/projects/{slug}/backlog/` per-item markdown files (resolved via `dh_paths.backlog_dir()`)
- **Implementation**: `backlog_core/` package, exposed as FastMCP 3.x server (`mcp__plugin_dh_backlog__*`)
- **Operations**: CRUD on issues, label management, grooming, syncing, milestone/project management
- **Sync direction**: GitHub Issues are canonical; local files are derived cache updated by `backlog_sync` and `backlog_pull`
- **Bulk sync primitive**: `sync_issues_graphql` in `backlog_core/github.py` — GraphQL cursor-paginated fetch with optional `since` filter for incremental sync. Full sync ~12s for 245 issues; incremental sync ~0.7s. `create_milestone` and `create_label` remain REST-only (no GraphQL mutations — ADR-004).

### Plans/Tasks (SAM MCP)

- **Source of truth**: Local YAML task files in `~/.dh/projects/{slug}/plan/` directory (resolved via `dh_paths.plan_dir()`)
- **GitHub link**: Each task YAML can contain a `github_issue` field linking to a GitHub sub-issue for status sync
- **Implementation**: `sam_schema/` package, exposed as FastMCP 3.x server (`mcp__plugin_dh_sam__*`)
- **Operations**: List plans, read/claim/update tasks, check readiness, create plans
- **Format**: YAML frontmatter per task file (legacy: monolithic markdown with `## Task {ID}` headers)

### Artifact Manifest (backlog MCP artifact tools)

- **Source of truth**: GitHub Issue body (structured section between `<!-- artifact-manifest:begin/end -->` delimiters)
- **Implementation**: `backlog_core/artifact_provider.py` defines the `ArtifactBackend` Protocol and `GitHubArtifactProvider`
- **Operations**: `get_manifest`, `set_manifest`, `read_artifact_content`
- **File content**: Always served from local filesystem regardless of manifest backend

## Backend Provider Concept

The `ArtifactBackend` Protocol in `backlog_core/artifact_provider.py` establishes the pattern for backend abstraction:

```python
@runtime_checkable
class ArtifactBackend(Protocol):
    def get_manifest(self, issue_number: int) -> ArtifactManifest: ...
    def set_manifest(self, issue_number: int, manifest: ArtifactManifest) -> None: ...
    def read_artifact_content(self, path: str) -> str: ...
```

This pattern extends to the other two subsystems. Each backend implements a Protocol using its platform's native primitives. MCP tool consumers call the same tools regardless of which backend is active.

## Platform Capabilities

All data below is sourced from verified research. See [research/task-management/artifact-manifest-backend-providers.md](../../../research/task-management/artifact-manifest-backend-providers.md) for full citations and access dates.

### GitHub (Current Backend)

- **Issues API**: GraphQL (bulk fetch via `sync_issues_graphql`) + REST/PyGithub (single-item CRUD, label/milestone creation), 65,536 char body limit
- **Projects V2**: Project-level custom fields (5 types, 50 field max), GraphQL CRUD, text fields support exact match only
- **Issue Fields**: Org-level typed fields (25 max), public preview since 2026-03-12, full GraphQL + REST API, searchable/filterable
- **Sub-issues**: Native parent-child issue relationships
- **Labels**: Unlimited, cross-repo within org
- **Milestones**: Per-repo, title + description + due date + open/closed issue counts

### Linear

- **Issues**: Full GraphQL API for CRUD, rich state machine (backlog/triage/in-progress/done/cancelled)
- **Attachments**: Key-value metadata pairs, fully queryable/writable via GraphQL, used for external resource linking
- **Labels**: Label groups supported, no custom fields
- **Sub-issues**: Native parent-child issue relationships
- **MCP server**: Exposes labels, standard properties, attachments
- **Limits**: Attachment metadata limits not publicly documented

SOURCE: [Linear API Documentation](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)

### GitLab

- **Issues**: REST + GraphQL API, description body (similar to GitHub)
- **Epics**: Group-level containers for issues (Premium/Ultimate)
- **Linked items**: Three relationship types ("relates to", "blocks", "is blocked by"), bi-directional, cross-project, full REST API support
- **Custom fields**: Premium/Ultimate only, 4 types (text, number, single-select, multi-select), 50 per group, 10 per work item type, 1,024 char max. REST API has NO custom field access as of 2026-03; GraphQL `CustomField` type queries/mutations are undocumented
- **Attachments**: Upload supported via REST; download via API NOT supported

SOURCE: [GitLab Custom Fields](https://docs.gitlab.com/ee/user/custom_fields.html), [GitLab Linked Issues API](https://docs.gitlab.com/ee/api/issue_links.html)

### Supabase

- **Storage**: PostgreSQL tables with columns matching domain models
- **API**: Auto-generated REST API (PostgREST) + client SDK
- **Query**: Full SQL capability, no field type or count limits beyond PostgreSQL constraints
- **Realtime**: WebSocket subscriptions for row-level changes
- **Auth**: Row-level security policies for multi-tenant access control

## Platform Mapping

How each platform maps to the development harness core concepts:

| Concept | GitHub | Linear | GitLab | Supabase |
|---------|--------|--------|--------|----------|
| Issues/Backlog | Issues (GraphQL bulk via `sync_issues_graphql`; REST for mutations) | Issues (GraphQL) | Issues (REST + GraphQL) | `issues` table (REST + SQL) |
| Plans/Tasks | Sub-issues linked from parent issue | Sub-issues linked from parent issue | Linked issues ("relates to") | `tasks` table with `plan_id` FK |
| Artifact Manifest | Issue body section (HTML comment delimiters) | Attachments with metadata key-value pairs | Issue description section (HTML comment delimiters) | `artifact_manifests` table |
| Sub-issues/Decomposition | Native sub-issues | Native sub-issues | Linked items + Epics (Premium) | `parent_id` self-referential FK |
| Status Tracking | Labels + Projects V2 status field | Built-in state machine (backlog/triage/in-progress/done/cancelled) | Labels + board lists | `status` column (enum) |
| Relationships/Links | Sub-issues, cross-references, Projects V2 | Parent/child issues, relations | Linked items (relates/blocks/blocked by), Epics | Foreign keys, junction tables |

## Design Principles

1. **Follow each platform's native primitive** -- Linear uses Attachments for structured metadata, not fake custom fields. GitLab uses issue description sections until its custom field API matures. Each provider maps to what the platform actually supports.

2. **Backend as source of truth, local files as cache** -- same pattern as the current backlog MCP where GitHub Issues are canonical and `~/.dh/projects/{slug}/backlog/` files are derived. Future backends maintain this direction: the remote platform is authoritative, local state is a sync target.

3. **Protocol-based abstraction** -- consumers call the same MCP tools (`backlog_*`, `sam_*`, `artifact_*`) regardless of which backend is active. Backend selection is a server configuration concern, not a consumer concern.

4. **Implement GitHub first, define interfaces for others** -- the existing `ArtifactBackend` Protocol and `GitHubArtifactProvider` demonstrate the pattern. New backends implement the same Protocol. Interfaces are defined during architecture; implementations are added incrementally.

5. **`read_artifact_content` is always filesystem-based** -- manifests store references (paths), content lives in plan files on disk. This method does not vary by backend.

## Implementation Roadmap

Three Protocol abstractions are needed, one per subsystem:

### ArtifactBackend Protocol (exists)

Defined in `backlog_core/artifact_provider.py`. `GitHubArtifactProvider` is the current implementation.

Methods: `get_manifest`, `set_manifest`, `read_artifact_content`

### IssueBackend Protocol (to be created)

Abstracts the backlog/issue operations currently hardcoded to GitHub in `backlog_core/github.py` and `backlog_core/operations.py`. The current GitHub implementation uses `sync_issues_graphql` as the bulk fetch primitive; the Protocol interface expresses this as `list_issues`.

Expected methods (derived from current `backlog_core` operations):

- `get_issue(number) -> IssueData`
- `create_issue(title, body, labels, ...) -> IssueData`
- `update_issue(number, ...) -> None`
- `close_issue(number) -> None`
- `list_issues(state, labels, ...) -> list[IssueData]`
- `add_label(number, label) -> None`
- `remove_label(number, label) -> None`
- `create_sub_issue(parent, title, body, ...) -> IssueData`
- `list_sub_issues(parent) -> list[IssueData]`
- `sync_status(number, status) -> None`

### TaskBackend Protocol (to be created)

Abstracts SAM task storage currently implemented as local YAML files in `sam_schema/`.

Expected methods (derived from current `sam_schema` operations):

- `list_plans() -> list[PlanSummary]`
- `read_plan(plan_id) -> PlanData`
- `read_task(plan_id, task_id) -> TaskData`
- `claim_task(plan_id, task_id) -> bool`
- `update_task_status(plan_id, task_id, status) -> None`
- `get_ready_tasks(plan_id) -> list[TaskData]`
- `create_plan(slug, goal, tasks) -> PlanData`

### Composition

The three Protocols compose independently. A deployment could use:

- GitHub for issues + local files for tasks + GitHub for artifacts (current)
- Linear for issues + Supabase for tasks + Linear for artifacts
- Any valid combination

Backend selection is configured at server startup. Each MCP server (`backlog`, `sam`) receives its backend provider instance via dependency injection.

```text
backlog MCP server
  ├── IssueBackend  (GitHubIssueProvider | LinearIssueProvider | ...)
  └── ArtifactBackend  (GitHubArtifactProvider | LinearArtifactProvider | ...)

sam MCP server
  └── TaskBackend  (LocalYamlTaskProvider | SupabaseTaskProvider | ...)
```

## References

- [graphql-usage-guide.md](./graphql-usage-guide.md) -- `sync_issues_graphql` usage, parameters, anti-patterns, and performance data
- [research/task-management/artifact-manifest-backend-providers.md](../../../research/task-management/artifact-manifest-backend-providers.md) -- cross-platform research with full citations
- `~/.dh/projects/{slug}/plan/architect-artifact-manifest.md` -- architecture spec for ArtifactBackend Protocol (access via `artifact_read`)
- `~/.dh/projects/{slug}/plan/feature-context-artifact-manifest.md` -- problem space and desired outcomes (access via `artifact_read`)
- [artifact-manifest-backends.md](./artifact-manifest-backends.md) -- artifact-specific backend details
- [backlog_core/artifact_provider.py](../backlog_core/artifact_provider.py) -- ArtifactBackend Protocol definition and GitHubArtifactProvider
- [backlog_core/github.py](../backlog_core/github.py) -- current GitHub-specific issue operations
- [sam_schema/](../sam_schema/) -- current local YAML task implementation
