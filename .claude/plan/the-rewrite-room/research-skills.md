# Skill Inventory

Skills relevant to authoring, documentation, summarization, prompt optimization, formatting, and drift detection.

---

## plugin-creator:add-doc-updater

- Path: plugins/plugin-creator/skills/add-doc-updater/SKILL.md
- Category: documentation-sync
- Tools: (inherits from orchestrator — delegates to @python-cli-architect, @python-code-reviewer)
- Model: sonnet
- Purpose: Orchestrates adding an automated documentation sync pipeline to any Claude skill. Creates a Python script that downloads upstream docs, processes markdown for AI consumption (removes Hugo shortcodes, transforms links), enforces a configurable cooldown period, and integrates the updater into the skill's SKILL.md execution protocol.
- Triggers: "Add doc sync to {skill}", "Automate documentation updates for {skill}", "This skill needs to wrap {external docs}", adding auto-updating reference documentation to plugins or skills.
- Has References: yes — `references/doc-updater-template.md` (the substitutable 6-variable prompt template for delegating implementation)
- Has Scripts: no

---

## python3-development:pypi-readme-creator

- Path: plugins/python3-development/skills/pypi-readme-creator/SKILL.md
- Category: authoring
- Tools: (none specified in frontmatter)
- Model: (none specified)
- Purpose: Generate professional, PyPI-compliant README files in Markdown or reStructuredText that render correctly on PyPI, GitHub, GitLab, and BitBucket. Covers format selection strategy, essential content sections, writing style principles, format-specific syntax, pyproject.toml configuration, and pre-publish validation with twine.
- Triggers: Creating README for Python packages, preparing for PyPI publication, README renders incorrectly on PyPI, choosing between README.md and README.rst, running twine check, configuring readme field in pyproject.toml.
- Has References: yes — `references/markdown-template.md`, `references/rst-template.rst`, `references/sphinx-readme-example.md`
- Has Scripts: no

---

## prompt-optimization-claude-45:prompt-optimization-claude-45

- Path: plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md
- Category: prompt-optimization
- Tools: (none specified in frontmatter)
- Model: (none specified)
- Purpose: Optimize CLAUDE.md files and Agent Skills for Claude Code CLI using Anthropic's official prompt engineering best practices. Transforms negative prohibitions into positive patterns, adds motivations, structures with headings, provides concrete examples, and applies compression techniques for context window efficiency. Includes a verification checklist and length targets by document type.
- Triggers: Reviewing, creating, or improving system prompts, CLAUDE.md configurations, or skill files. Transforming negative instructions into positive patterns.
- Has References: no (references directory not found)
- Has Scripts: no

---

## plugin-creator:lint

- Path: plugins/plugin-creator/skills/lint/SKILL.md
- Category: formatting-validation
- Tools: (command executes plugin_validator.py via shell; loads ERROR_CODES.md reference)
- Model: (none specified)
- Purpose: Run the plugin validator script on a skill, agent, or plugin directory. Reports token complexity, broken links, frontmatter issues, and structural problems. User-invocable shortcut that executes `plugin_validator.py $ARGUMENTS` and loads the ERROR_CODES reference.
- Triggers: Checking skill quality, validating before commit, diagnosing validator warnings. Pass the path as an argument.
- Has References: no (references directory not found; ERROR_CODES.md is in scripts/ of the plugin)
- Has Scripts: no (delegates to `${CLAUDE_PLUGIN_ROOT}/scripts/plugin_validator.py`)

---

## plugin-creator:refactor-plugin

- Path: plugins/plugin-creator/skills/refactor-plugin/SKILL.md
- Category: other (plugin lifecycle / structural refactoring orchestration)
- Tools: (inherits — orchestrates agents: refactor-planner, refactor-executor, refactor-validator)
- Model: (none specified)
- Purpose: Start a complete plugin refactoring workflow — analyzes plugin structure, creates a refactoring plan with tasks, and guides through execution. Phases: Assessment → Design → Planning → Execution → Validation. Handles skill splits, agent optimizations, documentation improvements, doc-updater additions, and orphan resolution.
- Triggers: "Refactor {plugin-name} plugin", "Analyze plugin for refactoring", "Create refactoring plan for {plugin}", plugin exceeds token threshold.
- Has References: no
- Has Scripts: no

---

## holistic-linting:holistic-linting

- Path: plugins/holistic-linting/skills/holistic-linting/SKILL.md
- Category: formatting-validation
- Tools: (inherits — guides orchestrators to delegate; sub-agents run ruff, mypy, pyright, markdownlint, etc.)
- Model: (none specified)
- Purpose: Prevent Claude from completing tasks without running quality checks. Provides automatic format-lint-resolve pipelines: orchestrators delegate immediately to linting-root-cause-resolver agent; sub-agents format then lint then resolve before marking tasks done. Includes comprehensive linter detection by scanning project config files and a knowledge base of 933+ ruff rules, mypy error codes, and 65+ bandit security checks.
- Triggers: Running linters, fixing ruff/mypy/bandit errors, ensuring code quality before completion, resolving linting issues systematically, after any Edit/Write operation.
- Has References: yes — `references/rules/ruff/index.md`, `references/rules/mypy/index.md`, `references/rules/bandit/index.md`, `references/pre-existing-issues-protocol.md`
- Has Scripts: yes — `scripts/detect_hook_tool.py`, `scripts/install_agents.py`, `scripts/lint_orchestrator.py`, `scripts/discover_linters.py`

---

## holistic-linting:holistic-linting-orchestrator

- Path: plugins/holistic-linting/skills/holistic-linting-orchestrator/SKILL.md
- Category: formatting-validation
- Tools: (inherits — orchestrator delegation only; reads reports via Read tool)
- Model: (none specified)
- Purpose: Orchestrator-specific delegation workflows for linting. Guides orchestrators on when and how to delegate to linting-root-cause-resolver and post-linting-architecture-reviewer agents. Enforces the principle that orchestrators must NOT pre-gather linting data before delegating — agents discover and run linters themselves.
- Triggers: Orchestrating linting tasks, delegating quality checks, reading linting resolution reports, after implementation work is complete.
- Has References: no (references directory not found)
- Has Scripts: no

---

## agentskill-kaizen:transcript-analysis

- Path: plugins/agentskill-kaizen/skills/transcript-analysis/SKILL.md
- Category: drift-audit
- Tools: Read, Grep, Glob, mcp__plugin_agentskill-kaizen_kaizen-duckdb__execute_query
- Model: (none specified)
- Purpose: Analyze Claude Code JSONL session transcripts to detect anti-patterns, inefficiencies, user frustration, and workflow improvement opportunities. Covers 10 analysis dimensions (tool misuse, repeated errors, user frustration signals, missing tooling, subagent delegation patterns, shortest path analysis, red herring detection, system process interruptions, missing hooks, DuckDB SQL querying) and PM4Py process mining methodology.
- Triggers: Analyzing Claude Code session transcripts, reviewing agent performance, finding anti-patterns or tool misuse, detecting user frustration signals, mining workflow patterns, running kaizen analysis, debugging agent behavior, session forensics.
- Has References: yes — `references/jsonl-schema.md` (JSONL field paths by record type), `references/duckdb-queries.md` (SQL query patterns for transcript analysis)
- Has Scripts: no

---

## agentskill-kaizen:kaizen-improvement

- Path: plugins/agentskill-kaizen/skills/kaizen-improvement/SKILL.md
- Category: drift-audit
- Tools: (inherits)
- Model: (none specified)
- Purpose: Transform transcript analysis findings from `.planning/kaizen/` into actionable improvements — hooks, agent prompt patches, skill refinements, CLAUDE.md updates, and automation scripts. Scores improvements by frequency × impact, automation potential, blast radius, and implementation cost. Produces draft proposals or (with --install flag) writes hooks directly to settings.
- Triggers: "Generate hooks from findings", "improve agent", "fix anti-pattern", "kaizen improvement", "generate hook proposals", "create improvement plan". Prerequisite: analysis findings exist in `.planning/kaizen/`.
- Has References: yes — `references/improvement-templates.md`, `references/hook-patterns.md`
- Has Scripts: no

---

## agentskill-kaizen:meta-inspector

- Path: plugins/agentskill-kaizen/skills/meta-inspector/SKILL.md
- Category: research-utilities
- Tools: Read, Grep, Glob, mcp__plugin_agentskill-kaizen_kaizen-duckdb__execute_query
- Model: (none specified)
- Purpose: Data point extraction skill for pulling specific facts from large output files (agent transcripts, kaizen analysis reports, JSONL session files) without loading raw data into orchestrator context. Returns raw structured data — no analysis, interpretation, or recommendations. Uses DuckDB SQL for JSONL queries and Grep for markdown reports.
- Triggers: Orchestrator-invoked only (not user-invocable). Use when needing tool timings, query counts, error summaries, or any structured facts from large output files to prevent context pollution.
- Has References: yes — `references/extraction-patterns.md` (DuckDB SQL queries and Grep patterns for transcripts and kaizen reports)
- Has Scripts: no

---

## brainstorming-skill:brainstorming-skill

- Path: plugins/brainstorming-skill/skills/brainstorming-skill/SKILL.md
- Category: authoring
- Tools: (none specified)
- Model: (none specified)
- Purpose: Provides 30+ research-validated brainstorming patterns across 14 categories with exact prompt templates, output format specifications, and success metrics. Supports idea generation for products, features, content, strategic planning, and creative writing. Organized into perspective multiplication, constraint variation, inversion, analogical transfer, SCAMPER, scenario exploration, chain-of-thought, assumption challenge, competitive positioning, extreme scaling, and stakeholder empathy patterns.
- Triggers: Idea generation for products, features, or content; creative problem-solving; marketing campaigns; strategic planning; content creation; product feature ideation; business strategy; creative writing; QA test case brainstorming; breaking through creative blocks.
- Has References: yes — 18 reference files including `pattern-categories-and-documentation.md` (1,303 lines), `domain-specific-applications-and-variations.md`, `pattern-selection-guide.md`, `synthesis-what-makes-these-patterns-work.md`, `comprehensive-prompt-library-ready-to-use-templates.md`, `executive-summary.md`, and 12 source-specific research documents.
- Has Scripts: no

---

## conventional-commits:conventional-commits

- Path: plugins/conventional-commits/skills/conventional-commits/SKILL.md
- Category: formatting-validation
- Tools: (none specified)
- Model: (none specified)
- Purpose: Compose commit messages following the Conventional Commits v1.0.0 specification. Covers message structure, commit types and SemVer impact, specification rules, description best practices, breaking change notation, and integration with changelog generation tools (semantic-release, git-cliff, commitizen). Includes regex validation pattern and Python validation example.
- Triggers: Writing a git commit message, task completes and changes need committing, project uses semantic-release/commitizen/git-cliff, choosing between feat/fix/chore/docs types, indicating breaking changes, generating changelogs from commit history.
- Has References: no
- Has Scripts: no

---

## python3-development:mkdocs

- Path: plugins/python3-development/skills/mkdocs/SKILL.md
- Category: authoring
- Tools: (none specified)
- Model: (none specified)
- Purpose: Comprehensive guide for creating and managing MkDocs documentation projects with Material theme, including CLI command reference and mkdocs.yml configuration reference. NOTE: The SKILL.md body is a placeholder scaffold with TODO sections — content is not yet authored. The description accurately reflects the intent but the body has no substantive content.
- Triggers: Working with MkDocs projects including site initialization, mkdocs.yml configuration, Material theme customization, plugin integration, or building static documentation sites from Markdown files.
- Has References: no
- Has Scripts: no

---

## Notes on Excluded Skills

The following skills were examined but excluded as pure code-development skills with no documentation/authoring relevance:

- `python3-development:python3-review` — code review for Python, not docs
- `python3-development:snakepolish` — Python style/linting
- `python3-development:stinkysnake` — Python anti-pattern detection
- `holistic-linting:holistic-linting-resolver` — linting resolution sub-agent workflows (linting mechanics only)
- `bash-development:bash-lint` — bash linting only
- `plugin-creator:claude-plugins-reference-2026` — reference documentation (not authoring workflow)
- `agentskill-kaizen:kaizen-improvement` and `transcript-analysis` — retained above as drift-audit/research-utilities relevant to workflow quality
- All `perl-development:*` — language-specific, no doc relevance
- All `development-harness:*` — workflow scaffolding, no doc relevance
