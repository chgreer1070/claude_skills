# The Rewrite Room

A workflow router for documentation and authoring tasks in Claude Code. Describe what you need to do — the router selects the correct canonical workflow, runs the validation harness, and enforces output contracts.

## Installation

```bash
/plugin install the-rewrite-room@jamie-bitflight-skills --scope local
```

Or for local development:

```bash
claude --plugin-dir ./plugins/the-rewrite-room
```

## Quick Start

Describe your task and the skill routes it to the right workflow:

```text
"The README is out of sync with the code after last week's refactor"
→ drift-audit → @doc-drift-auditor → evidence report with file:line citations

"Rewrite this SKILL.md — too many prohibitions, reads poorly for AI"
→ prompt-optimization → @contextual-ai-documentation-optimizer → before/after diff

"Summarize this architecture document for the team"
→ summarization → summarizer skill → structured summary with fidelity check
```

## Workflows

| Workflow | Trigger Keywords | Canonical Component | Validators |
|---|---|---|---|
| drift-audit | drift, docs out of date, undocumented, documented but | @doc-drift-auditor | link-checker, citation-check |
| documentation-sync | sync docs, upstream docs, automate documentation | add-doc-updater skill | link-checker, frontmatter-validator |
| authoring | rewrite, rephrase, tone, audience, make clearer | prompt-optimization-claude-45 skill | prompt-structure-validator |
| prompt-optimization | optimize CLAUDE.md, SKILL.md quality, AI-facing | optimize-claude-md skill | frontmatter-validator, prompt-structure-validator |
| summarization | summarize, tldr, condense, explain file | summarizer skill | fidelity-enforcer |
| formatting-validation | validate frontmatter, lint plugin, GLFM, broken links | plugin-creator:lint skill | frontmatter-validator, plugin-structure-validator |
| research-utilities | token count, file metrics, inventory, discover | file_metrics.py + plugin_validator.py | (none) |

## How the Router Works

The router reads `skills/the-rewrite-room/registry/routing-rules.yaml` and scores each workflow by:

1. Keyword matches in your task description
2. Source type signals (file, URL, git-diff) — 1.5x multiplier
3. Artifact target signals (CLAUDE.md, README.md, docs/) — 1.3x multiplier

The highest-scoring workflow is selected. If a second workflow scores above 30% confidence, a disambiguation note is shown. Use `--source-type` and `--artifact` flags for precision routing.

```bash
# Classify a description
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/router.py classify \
  "docs are stale after the refactor" --source-type git-diff

# List all registered workflows
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/router.py list
```

## Output Contract

Every workflow produces a STATUS block:

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [factual, 1-2 sentences]
ARTIFACTS:
  - path/to/output.md
VALIDATION:
  - validator-name: PASS|FAIL
NOTES: [only if needed]
```

`DONE` — all validators pass. `BLOCKED` — user action required. `FAILED` — output produced but failed validation.

## Adding New Workflows

See `skills/the-rewrite-room/references/registry-guide.md` for the step-by-step procedure to add workflows, validators, and adapter shims.
