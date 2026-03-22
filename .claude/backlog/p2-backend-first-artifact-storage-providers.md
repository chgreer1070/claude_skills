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
---

