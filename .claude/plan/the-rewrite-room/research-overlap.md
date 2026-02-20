# Overlap Analysis & Deduplication Plan

Research date: 2026-02-20
Researcher: RESEARCHER 4 — Overlap Analysis & Taxonomy Classification

---

## Trigger Space Overlaps

### Overlap 1: "audit" trigger — drift-audit vs. audit-skill-lifecycle vs. audit-agent-lifecycle

Three components respond to audit-like triggers and produce audit reports:

- `plugins/plugin-creator/skills/audit-skill-lifecycle/SKILL.md`
  Trigger: "auditing skill coherence", "validating skill workflow", "finding semantic gaps", "auditing plugin before marketplace submission"
  Output: audit-report-{slug}.md, call-graph-{slug}.md, patterns.md, recommendations.md in `.claude/audits/`

- `plugins/plugin-creator/skills/audit-agent-lifecycle/SKILL.md`
  Trigger: "auditing agent lifecycle", "checking agent capabilities", "finding dead agents", "validating agent contract alignment"
  Output: agent-audit-report-{slug}.md, agent-dependency-graph-{slug}.md, patterns.md, agent-recommendations.md in `.claude/audits/`

- `plugins/development-harness/agents/doc-drift-auditor.md`
  Trigger: "audits documentation accuracy against actual implementation", git history analysis
  Output: `.claude/reports/DOCUMENTATION_DRIFT_AUDIT.md`

The first two overlap heavily on "audit plugin before marketplace submission" — a user requesting that phrase could receive either. They are differentiated by target type (skill workflows vs. agent execution capability) but share the word "audit" in both their descriptions and their output contract (markdown report to `.claude/audits/`).

The doc-drift-auditor overlaps with the taxonomy category drift-audit (category 3) but operates as a development-harness agent, not a standalone skill. It covers code↔docs divergence via git forensics, which is distinct from skill-lifecycle and agent-lifecycle audits (which audit skill/agent design coherence, not code drift).

### Overlap 2: "documentation sync" trigger — add-doc-updater vs. doc-drift-auditor vs. ensure-complete

- `plugins/plugin-creator/skills/add-doc-updater/SKILL.md`
  Trigger: "Add doc sync to {skill}", "Automate documentation updates for {skill}", "This skill needs to wrap {external docs}"
  Scope: OUTBOUND sync — downloads upstream docs into a skill's references/ directory. Creates a Python sync script.

- `plugins/development-harness/agents/doc-drift-auditor.md`
  Trigger: "Audits documentation accuracy against actual implementation"
  Scope: INBOUND audit — checks that existing docs match actual code state.

- `plugins/plugin-creator/skills/ensure-complete/SKILL.md`
  Trigger: "validate refactoring completeness", "check for documentation drift"
  Scope: Partial overlap — Phase 3 of ensure-complete explicitly delegates a "documentation audit" step (runs doc-drift-auditor). This makes ensure-complete a consumer of doc-drift-auditor, not a duplicate.

The add-doc-updater and doc-drift-auditor operate on opposite directions: one pulls external docs in; the other detects when internal docs have drifted from code. They are not duplicates — they serve different intents and produce different outputs.

### Overlap 3: "prompt optimization" trigger — prompt-optimization-claude-45 vs. optimize-claude-md vs. contextual-ai-documentation-optimizer (agent)

- `plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md`
  Trigger: "reviewing, creating, or improving system prompts, CLAUDE.md configurations, or Skill files"
  Output: Inline transformed content. Reference-only skill (knowledge, principles, examples). Does not write files.

- `.claude/skills/optimize-claude-md/SKILL.md`
  Trigger: "improving prompt effectiveness, reducing token waste, rewriting instructions for LLM consumption, or enhancing files with latest Claude Code features"
  Output: Orchestration workflow — measures baseline metrics, delegates to @contextual-ai-documentation-optimizer, runs independent verification, produces before/after report. Writes optimized files after user approval.

- `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer` (agent, not a SKILL.md)
  Trigger: Invoked by optimize-claude-md and by DOC_IMPROVE tasks in refactor workflows
  Output: Optimized file content + CoVe verification. Enables prompt-optimization-claude-45 skill internally.

These three form a delegation chain: optimize-claude-md (orchestrator skill) → contextual-ai-documentation-optimizer (agent) → prompt-optimization-claude-45 (knowledge reference skill). The trigger space for optimize-claude-md and prompt-optimization-claude-45 overlaps on "improving CLAUDE.md / SKILL.md files", but they are at different levels — one is a knowledge reference, the other is an executable workflow.

### Overlap 4: "summarize" trigger — summarizer (router) vs. file-summarization vs. url-summarization vs. image-summarization vs. CLAUDE.md summarization rules

- `plugins/summarizer/skills/summarizer/SKILL.md` — router skill, dispatches to type-specific strategies
- `plugins/summarizer/skills/file-summarization/SKILL.md` — file strategy
- `plugins/summarizer/skills/url-summarization/SKILL.md` — URL strategy
- `plugins/summarizer/skills/image-summarization/SKILL.md` — image strategy
- `plugins/summarizer/skills/multi-source-synthesis/SKILL.md` — reduce step after individual summaries
- `plugins/summarizer/skills/agent-result-relay/SKILL.md` — relay rules (not a summarizer, prevents lossy re-summarization)

All five summarizer sub-skills share the "summarize" keyword trigger in their descriptions. The router (summarizer/SKILL.md) is the single entry point; the others are dispatched to by it. The CLAUDE.md global instruction also contains summarization rules (the 5000-char threshold decision flow). This creates a possible ambiguity where the CLAUDE.md global instruction and the summarizer plugin both respond to "summarize this file."

The CLAUDE.md global instruction is a standing rule applied to all sessions; the summarizer plugin provides the deep implementation. They are not duplicates but could produce inconsistent behavior if the global rule routes differently than the plugin's decision tree.

### Overlap 5: "audit skill completeness" vs. "plugin-assessor" (agent) vs. "assessor" (skill)

- `plugins/plugin-creator/skills/audit-skill-completeness/SKILL.md`
  Trigger: "auditing skill quality", "checking marketplace readiness", "evaluating skill completeness score"
  Output: `completeness-report-{skill-slug}.md` in `.claude/audits/`

- `plugins/plugin-creator/skills/assessor/SKILL.md` (not read in full but referenced in CLAUDE.md as the refactoring assessment entry point)
  Trigger: "Analyze plugin structure and create refactoring task files"

- `plugins/plugin-creator/agents/plugin-assessor.md` (agent)
  Trigger: "Analyze plugins for structure, frontmatter, schema compliance, and quality"

These three share the trigger space of "analyze/assess plugin quality". The audit-skill-completeness skill scores against 8 specific Anthropic-derived completeness categories; the assessor produces a refactoring task file; the plugin-assessor agent produces a detailed assessment report. The overlap is real but differentiated by outcome: completeness score vs. refactor plan vs. quality report.

---

## Output Contract Overlaps

### Shared contract: markdown audit report to `.claude/audits/`

These components all write markdown reports to `.claude/audits/`:

- `audit-skill-lifecycle` → `audit-report-{slug}.md`, `call-graph-{slug}.md`, `patterns.md`, `recommendations.md`
- `audit-agent-lifecycle` → `agent-audit-report-{slug}.md`, `agent-dependency-graph-{slug}.md`, `patterns.md`, `agent-recommendations.md`
- `audit-skill-completeness` → `completeness-report-{skill-slug}.md`

The `patterns.md` file is explicitly shared between the two lifecycle audits. This is intentional by design — they append to a shared pattern catalog.

### Shared contract: structured markdown summary with YAML frontmatter

All four summarizer sub-skills (file, url, image, multi-source) produce identical output structure:

- YAML frontmatter (source_type, source_path, method, confidence, word counts)
- Summary, What Was Found, What Was NOT Found, Uncertain, Sources sections

This is intentional — they are implementations of the same output contract defined in `../summarizer/templates/structured.md`.

### Shared contract: STATUS/ARTIFACTS/RISKS response format

`doc-drift-auditor` returns STATUS: DONE with ARTIFACTS listing and RISKS section. This matches the development-harness subagent-contract format defined in the subagent-contract skill.

---

## Shared Validator Usage

### `plugin_validator.py` — invoked by multiple components

- `plugins/plugin-creator/skills/lint/SKILL.md` — direct invocation wrapper
- `plugins/plugin-creator/CLAUDE.md` workflow 5 — used in validate-plugin workflow
- `plugins/plugin-creator/skills/ensure-complete/SKILL.md` — Phase 1 re-runs plugin assessment
- `plugins/plugin-creator/skills/add-doc-updater/SKILL.md` — Phase 3 runs `prek` (which includes frontmatter validation)
- `plugins/plugin-creator/skills/audit-skill-completeness/SKILL.md` — uses `plugin_validator.py --check` to measure token count

Multiple skills use plugin_validator.py as a quality gate. No deduplication needed here — this is appropriate shared infrastructure.

### Fidelity rules reference — shared across summarizer sub-skills

All summarizer sub-skills reference `../summarizer/references/fidelity-rules.md`. This is correct shared-reference architecture. No duplication.

### `prek run` — holistic-linting and multiple refactor workflows

- `holistic-linting` skill delegates to agents that run `prek run`
- `add-doc-updater` Phase 3 runs `prek run --files {script-path}`
- Various Python development quality gates also run `prek run`

These are all correct uses of the shared pre-commit infrastructure.

---

## Canonical Workflow Candidates

### authoring

- **Canonical**: `plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md`
  Rationale: Pure knowledge reference skill covering rewrite, tone, structure, audience, positive framing, compression. No side effects. Usable inline or loaded by other skills/agents. Covers all five authoring taxonomy triggers.

- **Adapter shims needed**:
  - `.claude/skills/optimize-claude-md/SKILL.md` — already acts as an orchestration adapter that loads the canonical skill via the contextual-ai-documentation-optimizer agent. Keep as-is; it is not a duplicate but a workflow wrapper.
  - `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer` — internal agent adapter. Keep.

### documentation-sync

- **Canonical**: `plugins/plugin-creator/skills/add-doc-updater/SKILL.md`
  Rationale: Purpose-built for keeping docs aligned with upstream code changes. Defines a 5-phase workflow (implementation, code review, quality gates, validation, integration). Produces a Python sync script with cooldown enforcement. This is the only component in the repo that addresses outbound documentation sync.

- **Adapters**: None currently. The rewrite-room router should route "keep docs in sync with upstream", "automate doc updates", "doc sync pipeline" triggers here.

### drift-audit

- **Canonical**: `plugins/development-harness/agents/doc-drift-auditor.md`
  Rationale: Purpose-built for evidence-based comparison of docs vs. code. Uses git forensics, extracts actual implementation features, categorizes drift by severity (Critical/High/Medium/Low), cites file:line and commit SHAs. Produces structured DOCUMENTATION_DRIFT_AUDIT.md.

- **Adapters**: `plugins/plugin-creator/skills/ensure-complete/SKILL.md` already delegates to this agent as its Phase 3 documentation audit step. The rewrite-room router should route "docs out of date", "documentation drift", "docs don't match code", "implemented but undocumented" triggers here.

### prompt-optimization

- **Canonical**: `.claude/skills/optimize-claude-md/SKILL.md`
  Rationale: Full orchestration workflow — baseline measurement, delegation to @contextual-ai-documentation-optimizer, independent verification, before/after reporting. Covers CLAUDE.md, SKILL.md, agent definitions, reference files. Supports single file, skill directory, and plugin directory scopes. The prompt-optimization-claude-45 skill is a knowledge reference that this canonical workflow loads internally.

- **Adapters**:
  - `plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md` — knowledge reference, loaded by canonical workflow. Demote to reference role.
  - `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer` — implementation agent, invoked by canonical workflow.

### summarization

- **Canonical**: `plugins/summarizer/skills/summarizer/SKILL.md`
  Rationale: Router skill that dispatches to all type-specific strategies. Enforces fidelity rules. Coordinates multi-source synthesis and team-based summarization. All format selection and delegation logic lives here.

- **Sub-skills (not adapters — all remain active, invoked by canonical)**:
  - `plugins/summarizer/skills/file-summarization/SKILL.md`
  - `plugins/summarizer/skills/url-summarization/SKILL.md`
  - `plugins/summarizer/skills/image-summarization/SKILL.md`
  - `plugins/summarizer/skills/multi-source-synthesis/SKILL.md`
  - `plugins/summarizer/skills/agent-result-relay/SKILL.md`

### formatting-validation

- **Canonical**: `plugins/plugin-creator/skills/lint/SKILL.md`
  Rationale: Thin wrapper that runs `plugin_validator.py` on any skill, agent, or plugin path. Catches token complexity, broken links, frontmatter issues, and structural problems. Combined with `plugins/holistic-linting/skills/holistic-linting/SKILL.md` for code quality (ruff/mypy/bandit), these two cover GLFM, Markdown, YAML frontmatter constraints for the skill ecosystem.

  Note: There is no dedicated GLFM or Markdown formatting skill in the repository. The `holistic-linting` skill covers code file formatting (ruff, mypy); `plugin-creator:lint` covers plugin/skill structure validation. The rewrite-room may need to create a new formatting-validation workflow if GLFM-specific checks are required.

- **Adapters**: `plugins/holistic-linting/skills/holistic-linting-orchestrator/SKILL.md` for orchestrator-mode delegation to linting agents.

### research-utilities

- **Canonical**: No single canonical. Three distinct utilities exist:

  1. Discovery/metrics: `plugins/plugin-creator/scripts/plugin_validator.py` (token counting, file metrics) — no SKILL.md wrapper beyond `plugin-creator:lint`
  2. Token counting: embedded in `plugin_validator.py` via TOKEN_WARNING_THRESHOLD and TOKEN_ERROR_THRESHOLD constants
  3. File metrics: `plugins/summarizer/skills/file-summarization/SKILL.md` references `$CLAUDE_PLUGIN_ROOT/scripts/file_metrics.py` for word count assessment

  The `plugins/agentskill-kaizen/skills/meta-inspector/SKILL.md` covers data-point extraction from agent transcripts and JSONL files (kaizen-specific, DuckDB-backed). This is a specialized research utility for kaizen analysis, not general-purpose.

- **Adapters**: The rewrite-room should route "count tokens in this file", "file word count", "how large is this skill" to the lint/validator workflow.

---

## Deduplication Plan

### Canonical workflows (one per category)

1. **authoring** → `plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md` (knowledge) + `.claude/skills/optimize-claude-md/SKILL.md` (executable workflow)
2. **documentation-sync** → `plugins/plugin-creator/skills/add-doc-updater/SKILL.md`
3. **drift-audit** → `plugins/development-harness/agents/doc-drift-auditor.md`
4. **prompt-optimization** → `.claude/skills/optimize-claude-md/SKILL.md` (orchestrator) → `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer` (agent) → `plugins/prompt-optimization-claude-45/skills/prompt-optimization-claude-45/SKILL.md` (knowledge)
5. **summarization** → `plugins/summarizer/skills/summarizer/SKILL.md` (router) → type-specific sub-skills
6. **formatting-validation** → `plugins/plugin-creator/skills/lint/SKILL.md` + `plugins/holistic-linting/skills/holistic-linting/SKILL.md`
7. **research-utilities** → `plugins/plugin-creator/scripts/plugin_validator.py` (token/metrics) + `plugins/summarizer/skills/file-summarization/SKILL.md` (file word count via file_metrics.py) + `plugins/agentskill-kaizen/skills/meta-inspector/SKILL.md` (kaizen data extraction)

### Adapter shims needed

- The `optimize-claude-md` skill is already an adapter over `prompt-optimization-claude-45`. No new shim needed — document this relationship explicitly in the rewrite-room router.
- The `ensure-complete` skill already delegates drift-audit to `doc-drift-auditor`. No new shim needed — the router simply routes "validate refactoring completeness" to `ensure-complete`, which handles the rest.
- The `audit-skill-lifecycle` and `audit-agent-lifecycle` skills overlap on "audit plugin for marketplace". The router should distinguish: if target is a skill/workflow graph → audit-skill-lifecycle; if target is agent execution capability → audit-agent-lifecycle; if target is docs vs. code → doc-drift-auditor.

### Shared references to consolidate

- `plugins/summarizer/references/fidelity-rules.md` — already properly shared. Referenced by all four summarizer sub-skills. No consolidation needed.
- `patterns.md` in `.claude/audits/` — shared between audit-skill-lifecycle and audit-agent-lifecycle by design. No consolidation needed.
- `plugins/summarizer/templates/structured.md` — shared output contract template. Already properly referenced by all summarizer sub-skills. No consolidation needed.

---

## Routing Signal Keywords

The following keywords and phrases signal each workflow category for use in the rewrite-room router:

### authoring

Keywords: rewrite, rephrase, tone, audience, style, clarity, structure this, improve this writing, make this more concise, positive framing, prohibition to directive, compress this, edit this prose, transform this text

### documentation-sync

Keywords: sync docs, doc sync, automate documentation, documentation updater, keep docs in sync, upstream docs, download docs, refresh docs, documentation pipeline, doc updater script, external documentation

### drift-audit

Keywords: drift, docs out of date, documentation drift, implemented but undocumented, documented but unimplemented, code changed but docs didn't, what's different between code and docs, verify documentation accuracy, git history divergence, docs don't match code

### prompt-optimization

Keywords: optimize CLAUDE.md, improve SKILL.md, agent definition quality, prompt effectiveness, reduce token waste, rewrite for AI, LLM instruction quality, front-load priorities, AI-facing documentation, skill description, agent description

### summarization

Keywords: summarize, tl;dr, give me the highlights, what's important, break down this, what does this code do, explain this file, describe this image, read and summarize, synthesize, combine these summaries, multi-source, merge findings

### formatting-validation

Keywords: validate frontmatter, check skill quality, lint plugin, token complexity, broken links, frontmatter issues, markdown format, YAML frontmatter, validate SKILL.md, plugin validation, frontmatter schema, check agent file

### research-utilities

Keywords: count tokens, file word count, how large is this skill, file metrics, data extraction, extract data points, how many sessions, tool timing, query counts, error summary from transcript
