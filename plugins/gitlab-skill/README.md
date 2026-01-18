# GitLab Skill

Expert guidance for GitLab CI/CD pipeline configuration, GitLab Flavored Markdown (GLFM) syntax, gitlab-ci-local testing, CI/CD pipeline optimization, GitLab CI Steps composition, Docker-in-Docker workflows, and GitLab documentation creation.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install gitlab-skill@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/gitlab-skill
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [gitlab-skill](./skills/gitlab-skill/SKILL.md) | The model must apply when tasks involve .gitlab-ci.yml configuration, GitLab Flavored Markdown (GLFM) syntax, gitlab-ci-local testing, CI/CD pipeline optimization, GitLab CI Steps composition, Docker-in-Docker workflows, or GitLab documentation creation. Triggers include modifying pipelines, writing GitLab README/Wiki content, debugging CI jobs locally, implementing caching strategies, or configuring release workflows. |
| Command | [setup-ci-publish-token](./commands/setup-ci-publish-token.md) | Create GitLab project access token for CI/CD publishing and add as masked CI variable |

## Quick Start

**Optimize an existing GitLab CI pipeline:**

```text
@gitlab-skill
Review my .gitlab-ci.yml and suggest optimizations for caching and parallelization
```

**Create GitLab-formatted documentation:**

```text
@gitlab-skill
Convert this README to GitLab Flavored Markdown with proper syntax highlighting and task lists
```

**Setup CI publishing token:**

```bash
/setup-ci-publish-token
```

## License

See repository root for license information.
