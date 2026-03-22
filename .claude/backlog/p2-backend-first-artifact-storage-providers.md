---
name: Backend-first artifact storage providers
description: "The artifact manifest system (P965) stores manifests in GitHub Issue body with HTML comment delimiters. This works but has limitations: body edits can corrupt delimiters, and the same approach won't work for Linear (which uses Attachments) or GitLab. Research completed on GitHub Issue Fields (public preview 2026-03-12), GitHub Projects V2 fields, pinned comments, Linear attachments API, and GitLab (pending). The ArtifactBackend Protocol abstraction exists but only has one provider (GitHubArtifactProvider). Success: multiple providers exist, each using the backend's native storage primitive. Research files: /tmp/research-github-projects-v2-fields.md, /tmp/research-linear-custom-fields.md, /tmp/research-gitlab-custom-fields.md (pending)."
metadata:
  topic: backend-first-artifact-storage-providers
  source: 'Session observation — discovered during #965 implementation session 2026-03-21'
  added: '2026-03-22'
  priority: P2
  type: Feature
  status: open
  groomed: '2026-03-22'
---



## Groomed (2026-03-22)

### Research

<div><sub>2026-03-22T04:43:33Z</sub>

## Research Files (2026-03-21)

Six research files completed with verified findings from primary sources:

### Cross-Platform Artifact Linking Patterns
- [research/artifact-manifest-linear-patterns.md](research/artifact-manifest-linear-patterns.md) — Linear: Resources section as manifest, documents as first-class entities, MCP integration (21+ tools)
- [research/artifact-manifest-jira-asana-monday-patterns.md](research/artifact-manifest-jira-asana-monday-patterns.md) — Jira remote links (reference separation), Asana embedding (cautionary), Monday column-based metadata

### Backend Storage API Capabilities
- [research/artifact-manifest-github-fields.md](research/artifact-manifest-github-fields.md) — GitHub Issue Fields (public preview 2026-03-12), Projects V2 fields, pinned comments, 25 typed fields per org
- [research/artifact-manifest-linear-custom-fields.md](research/artifact-manifest-linear-custom-fields.md) — Linear has no custom fields; uses labels + Attachments API (key-value metadata, full GraphQL CRUD)
- [research/artifact-manifest-gitlab-custom-fields.md](research/artifact-manifest-gitlab-custom-fields.md) — GitLab custom fields (Premium+, GA 18.0), 4 types, 50 per group, 1024 char text limit
- [research/artifact-manifest-gitlab-api-deep.md](research/artifact-manifest-gitlab-api-deep.md) — Deep dive: GitLab custom field GraphQL read path documented, write path mutation exists in schema but not documented, REST has no custom field endpoints

### Key Findings Per Backend
- **GitHub**: Issue Fields (25 per org, typed, queryable) or pinned comments (65K chars, stable GA API)
- **Linear**: Attachments with metadata (native pattern, full API)
- **GitLab**: Custom fields read-only via API for now; write mutation exists in schema, docs incomplete. Fallback: issue description parsing
- **Supabase**: Database table (straightforward, no research needed)
</div>