<p align="center">
  <img src="./assets/hero.png" alt="The Rewrite Room" width="800" />
</p>

# the-rewrite-room

Documentation and authoring workflow router: audit docs vs code drift, sync docs after
changes, optimize prompts and SKILL.md files, validate GLFM and Markdown formatting,
summarize files/URLs/images with fidelity enforcement.

## What it does

Routes documentation, authoring, and optimization tasks to the correct specialist agents.
Use it when docs are out of date, CLAUDE.md needs improving, a SKILL.md needs optimizing,
you want to check whether documentation matches code, or you need to summarize files or
URLs. The `user-docs-to-ai-skill` skill converts existing human-facing documentation into
fully structured Claude Code skill directories.

## Skills

- `the-rewrite-room` — Main router. Activates with `/rwr:audit`, `/rwr:optimize`,
  `/rwr:author`, or `/rwr:doc-to-skill` and delegates to the matching specialist agent
- `user-docs-to-ai-skill` — Converts user-facing documentation directories (how-to guides,
  tutorials, API references) into Claude Code skill directories with SKILL.md and
  thematically grouped reference files

## Agents

- `rewrite-room-auditor` — Detects drift between documentation and code; tracks freshness
- `rewrite-room-optimizer` — Improves CLAUDE.md and SKILL.md files for AI consumption
- `rewrite-room-author` — Writes user-facing docs, validates GLFM, summarizes sources
- `rewrite-room-doc-converter` — Converts user-facing docs into Claude Code skill format

## Installation

```bash
/plugin install rwr@jamie-bitflight-skills
```

## Usage

```text
/rwr:audit "check if kaizen plugin docs match the code"
/rwr:optimize "plugins/plugin-creator/skills/add-doc-updater/SKILL.md"
/rwr:author "summarize plugins/summarizer/skills/summarizer/SKILL.md"
/rwr:doc-to-skill "docs/my-library/"
```
