# Plugin Project: the-rewrite-room
Created: 2026-02-20

## Goal
Multi-component plugin that inventories authoring/documentation agents, skills, and validators
in this repo, normalizes them into a shared framework, and provides dynamic routing to the right
workflow for a given task.

## Primary Outcomes
1. Discovery and inventory of all relevant agents, skills, scripts, references, templates
2. Classification taxonomy and deduplication mapping
3. Routing layer that selects workflows based on task intent, source types, artifact targets
4. Validation harness running the right checks per workflow
5. Test suite with fixtures proving each workflow works end-to-end

## Non-Goals
- Do not create "one big agent prompt" as the deliverable
- Do not rewrite source agents/skills unless needed for normalization adapters
- Do not change product code — governs authoring, docs, prompts, summaries only

## Seed Inputs
- plugins/gitlab-skill/skills/gitlab-skill/references/glfm-syntax.md
- plugins/gitlab-skill/skills/gitlab-skill/scripts/validate_glfm.py
- research/documentation-tools
- plugins/plugin-creator/skills/add-doc-updater/references/doc-updater-template.md
- plugins/python3-development/skills/pypi-readme-creator
- plugins/development-harness/agents/service-docs-maintainer.md
- Agents: service-docs-maintainer, doc-drift-auditor, contextual-ai-documentation-optimizer, summarizer

## Deliverables Layout
plugins/the-rewrite-room/
├── .claude-plugin/plugin.json
├── skills/the-rewrite-room/
│   ├── SKILL.md
│   ├── registry/
│   │   ├── workflows.yaml
│   │   ├── validators.yaml
│   │   └── routing-rules.yaml
│   ├── workflows/          # canonical workflow specs + adapter specs
│   ├── scripts/            # router, shared utilities, validator wrappers
│   ├── references/         # consolidated references
│   ├── templates/          # report templates
│   └── tests/              # fixtures, expected outputs, runner
└── README.md
