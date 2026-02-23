---
name: 'gitlab-skill: Remove hardcoded corporate URL'
description: '`validate_glfm.py` lines 152-153 hardcode `https://sourcery.assaabloy.net` as the default GitLab instance URL. `gitlab-ci-local-guide.md` line 51 also references this URL. This leaks a corporate internal URL into a public repository. Replace with a generic placeholder (e.g., `https://gitlab.example.com`) or make the URL a required argument with no default.'
metadata:
  topic: gitlab-skill-remove-hardcoded-corporate-url
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: P1
  type: Feature
  status: done
---
