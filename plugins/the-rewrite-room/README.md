<p align="center">
  <img src="./assets/hero.png" alt="The Rewrite Room" width="800" />
</p>

# the-rewrite-room

Documentation tasks require different specialists: auditing doc-vs-code drift is not the same
as optimizing a SKILL.md prompt, which is not the same as writing a README, which is not the
same as converting library docs into a Claude skill. This plugin routes each task to the right
specialist agent via five slash commands.

## Commands

### `/rwr:audit` — Docs vs code drift

```text
/rwr:audit <task>
```

Audits documentation accuracy against code, syncs docs after code changes, and tracks doc
freshness. Delegates to `rewrite-room-auditor`, which uses the `development-harness`
doc-drift-auditor and service-docs-maintainer agents to produce evidence-based findings with
file:line citations and severity categorization.

```text
/rwr:audit "check if kaizen plugin docs match the code"
/rwr:audit "sync docs after refactoring DataProcessor"
/rwr:audit "add freshness tracking to the plugin-creator docs"
```

Requires: `development-harness` plugin installed.

### `/rwr:optimize` — AI-facing prompt improvement

```text
/rwr:optimize <file>
```

Optimizes CLAUDE.md files, SKILL.md files, and agent definitions using Anthropic prompt
engineering best practices. Delegates to `rewrite-room-optimizer`, which runs the RT-ICA
pre-check gate, applies a 6-step optimization, and produces a token impact report.

```text
/rwr:optimize "plugins/plugin-creator/skills/add-doc-updater/SKILL.md"
/rwr:optimize ".claude/CLAUDE.md"
/rwr:optimize "agents/my-agent.md"
```

Not for user-facing docs — use `/rwr:author` for those.

Requires: `plugin-creator` plugin installed.

### `/rwr:author` — User-facing docs and summarization

```text
/rwr:author <task>
```

Authors and validates user-facing documentation — READMEs, tutorials, API docs, GitLab Wiki
pages, and GLFM-formatted content. Also routes summarization requests for files, URLs, and
images to the appropriate summarizer agent.

```text
/rwr:author "summarize plugins/summarizer/skills/summarizer/SKILL.md"
/rwr:author "write a README for the kaizen plugin"
/rwr:author "validate GLFM in docs/wiki/setup.md"
```

Not for AI-facing docs — use `/rwr:optimize` for those.

Optional: `summarizer` plugin (file/URL/image summarization), `gitlab-skill` plugin (GitLab
wiki targets), `GITLAB_TOKEN` env var (GLFM validation).

### `/rwr:cite` — Source-attributed content

```text
/rwr:cite <source URL> [key points] [content type]
```

Fetches a source URL, cross-references every claim against the source material, and produces
attributed content with embedded hyperlinked citations. Delegates to `rewrite-room-cite`.

```text
/rwr:cite "https://docs.anthropic.com/en/docs/claude-code" "blog post about Claude Code"
/rwr:cite "https://example.com/article" "key metrics" "research summary"
```

Output structure: executive summary, deep dive with inline citations, key takeaways as
blockquotes, Cited From section.

### `/rwr:doc-to-skill` — Convert docs into a Claude skill

```text
/rwr:doc-to-skill <github-url or /path/to/docs> [output_skill_name]
```

Converts a documentation directory or GitHub repo into a complete Claude Code skill directory —
a `SKILL.md` with valid frontmatter plus thematically grouped `references/*.md` files.
Delegates to `rewrite-room-doc-converter`.

```text
/rwr:doc-to-skill "docs/my-library/" "my-library"
/rwr:doc-to-skill "https://github.com/owner/repo" "repo-skill"
/rwr:doc-to-skill "docs/fastapi/" "fastapi"
```

The converter runs a multi-phase SOP: inventory, type-appropriate extraction, workflow
identification (delegates those to `process-siren`), thematic grouping, writing reference
files, assembling `SKILL.md`, and running `skilllint` validation. Output is a complete skill
directory ready for `claude plugin validate .`

Requires: `process-siren` plugin installed (workflow diagram generation).

## Routing at a Glance

| Task | Command |
|------|---------|
| Docs are out of date after code changed | `/rwr:audit` |
| CLAUDE.md or SKILL.md feels ineffective | `/rwr:optimize` |
| Write or validate a README / wiki page | `/rwr:author` |
| Summarize a file, URL, or image | `/rwr:author` |
| Write content with source citations | `/rwr:cite` |
| Turn library docs into a Claude skill | `/rwr:doc-to-skill` |

## Example: Converting Library Docs to a Skill

You have a local `docs/httpx/` directory with the httpx Python library's user guide, API
reference, and quickstart. You want Claude to have expert-level httpx knowledge that loads
on demand.

```text
/rwr:doc-to-skill "docs/httpx/" "httpx"
```

The `rewrite-room-doc-converter` agent will:

1. Inventory `docs/httpx/` — count files by type, read the index
2. Extract content from each doc using type-appropriate patterns (API reference gets different
   treatment than a tutorial)
3. Identify workflow-shaped content (installation steps, request lifecycle) and generate
   workflow diagrams via `process-siren`
4. Group extracted knowledge into themes (authentication, async, error handling, etc.)
5. Write `plugins/httpx/skills/httpx/references/*.md` — one file per theme
6. Write `plugins/httpx/skills/httpx/SKILL.md` with frontmatter and references index
7. Run `skilllint` and frontmatter validation, report PASS/FAIL

Output: a complete skill directory at `plugins/httpx/` ready for `claude plugin validate .`

## Agents

All five agents share a canonical STATUS block output contract — every response includes
`STATUS`, `SUMMARY`, `ARTIFACTS`, and `VALIDATION` fields.

| Agent | Role |
|-------|------|
| `rewrite-room-auditor` | Docs vs code drift detection, post-change sync, freshness tracking |
| `rewrite-room-optimizer` | AI-facing prompt and SKILL.md optimization |
| `rewrite-room-author` | User-facing docs authoring, GLFM validation, summarization |
| `rewrite-room-cite` | Source-attributed content with primary source verification and citations |
| `rewrite-room-doc-converter` | Converts documentation directories into Claude Code skill directories |

## Installation

Add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Install the plugin:

```bash
/plugin install rwr@jamie-bitflight-skills
```

## Requirements

- Claude Code v2.0+
- `/rwr:audit`: `development-harness` plugin installed
- `/rwr:optimize`: `plugin-creator` plugin installed
- `/rwr:author` (summarization): `summarizer` plugin installed
- `/rwr:author` (GitLab targets): `gitlab-skill` plugin installed + `GITLAB_TOKEN` env var
- `/rwr:doc-to-skill` (workflow diagrams): `process-siren` plugin installed

---

> **The Ancient Woe**
>
> *The weeping royal archivist whose mountain of historical scrolls has been scattered to the four winds by a careless breeze through an open window.*

> **The Bard's Decree**
>
> *"A place for every parchment, and every parchment in its place! Route the decrees to the scribes, the histories to the monks, and let order reign o'er this library of madness!"*
