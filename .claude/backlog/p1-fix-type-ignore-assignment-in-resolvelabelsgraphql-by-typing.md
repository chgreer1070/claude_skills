---
name: 'Fix type: ignore[assignment] in _resolve_labels_graphql by typing repo_node as dict'
description: 'The function `_resolve_labels_graphql` uses a `type: ignore[assignment]` suppression comment. The root cause is that `repo_node` is not typed as `dict`, causing a type assignment mismatch that mypy/ty cannot resolve without the suppression. The suppression masks a real type error. Success looks like: `repo_node` is typed as `dict` (or an appropriate typed dict), the `type: ignore[assignment]` comment is removed, and the type checker passes without suppressions on that line.'
metadata:
  topic: fix-type-ignore-assignment-in-resolvelabelsgraphql-by-typing
  source: Agent task — auto-derived from task description
  added: '2026-03-18'
  priority: P1
  type: Bug
  status: open
  plan: plan/P775-migrate-backlog-github-rest-to-graphql-followup-2.yaml
  issue: '#836'
---