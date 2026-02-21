# Harness Engineering (Martin Fowler / Birgitta Böckeler)

**Research Date**: 2026-02-21
**Source URL**: <https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html>
**GitHub Repository**: N/A (article, no associated repository)
**Version at Research**: N/A (article, published 17 February 2026)
**License**: Copyright Martin Fowler (all rights reserved; article content)

---

## Overview

"Harness Engineering" is a memo by Birgitta Böckeler, a Distinguished Engineer at Thoughtworks, published as part of Martin Fowler's "Exploring Gen AI" series. It analyzes and contextualizes the concept of building deterministic and LLM-based infrastructure (a "harness") to constrain, guide, and verify AI coding agents during both code generation and maintenance. The article synthesizes insights from OpenAI's production experience with Codex agents, Mitchell Hashimoto's blog, and Chad Fowler's "Relocating Rigor" to argue that trustworthy AI-maintained codebases require deliberately constrained solution spaces—not unconstrained generation.

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| AI agents repeat mistakes and have no feedback loop for self-correction | Build a harness: programmatic tools (linters, structural tests, AGENTS.md) that prevent the agent from repeating known-bad behaviors |
| LLM-generated code decays over time due to inconsistent architectural adherence | Periodic "garbage collection" agents detect and fix inconsistencies; deterministic constraints enforce structure continuously |
| Trusting AI-generated code at scale requires wide flexibility, which reduces reliability | Constrain the solution space intentionally: specific architectural patterns, enforced module boundaries, and standardized structures increase reliability |
| Existing codebases are hard to retroactively harness | Harness design is most effective when designed from the start; retrofitting an existing codebase is comparable to running a static analyzer for the first time on an unchecked codebase |
| Context for AI agents degrades without maintenance | Continuously updated knowledge bases and dynamic context providers (observability data, browser navigation) supply fresh, accurate context |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| Article published | 17 February 2026 | 2026-02-21 |
| Author count | 1 (Birgitta Böckeler) | 2026-02-21 |
| Series article count | ~22 articles (Exploring Gen AI series) | 2026-02-21 |
| OpenAI harness codebase size cited | 1 million+ lines of code after 5 months | 2026-02-21 |
| OpenAI harness build duration cited | 5 months | 2026-02-21 |

---

## Key Features

### Core Harness Component Model (from OpenAI, interpreted by Böckeler)

- **Context Engineering**: Continuously maintained knowledge base embedded in the codebase; agents given dynamic context including observability data and browser navigation access
- **Architectural Constraints**: Enforced by both LLM agents and deterministic custom linters; structural tests enforce module boundaries and data shape contracts
- **Garbage Collection Agents**: Periodic agentic jobs that detect documentation inconsistencies and constraint violations, actively fighting entropy

### Harness as Forcing Function

- Teams use "no manually typed code" as a discipline to reveal where agents fail—each failure becomes a harness improvement task
- Iterative improvement loop: agent struggle signals missing tools, guardrails, or documentation; those gaps are closed by having the AI agent itself write the fix
- Harness components are the primary focus of engineering effort, not application feature code

### Conceptual Framework Contributions

- Böckeler introduces "harness" as a preferred term over alternatives (test harness, agent scaffolding, etc.) for tooling and practices that keep AI agents in check
- Proposes harnesses as the successor to service templates on "golden paths"—prebuilt harnesses for common application topologies
- Raises the distinction between pre-AI applications (where retrofitting may be cost-prohibitive) and post-AI applications (designed from the start for harness-based maintenance)
- Notes that what is good for human developers is repeatedly shown to be good for AI agents (usability of frameworks and SDKs)

### Constraints as a Design Principle

- Increasing AI autonomy requires decreasing solution space flexibility: specific architectural patterns, stable data structures, enforced module boundaries
- Convergence toward fewer tech stacks and topologies is predicted as a side effect of prioritizing "AI-friendliness" in stack selection
- Böckeler contrasts this with the industry hype that LLMs enable unlimited runtime flexibility

---

## Technical Architecture

The harness engineering pattern comprises three layers, based on Böckeler's categorization of the OpenAI team's approach:

```text
+-----------------------------------------------------------+
|                  AI Coding Agent (e.g., Codex)            |
+-----------------------------------------------------------+
          |                    |                   |
          v                    v                   v
+------------------+  +------------------+  +-------------------+
| Context Layer    |  | Constraint Layer |  | Entropy-Fighting  |
| - Knowledge base |  | - Custom linters |  | Agents (GC)       |
|   (curated docs) |  | - Structural     |  | - Doc consistency |
| - Observability  |  |   tests          |  | - Constraint      |
|   data access    |  | - Module boundary|  |   violation scan  |
| - Browser nav    |  |   enforcement    |  | - Periodic runs   |
+------------------+  +------------------+  +-------------------+
          |                    |                   |
          +--------+-----------+-------------------+
                   v
          +------------------+
          | Harness Feedback |
          | Loop             |
          | Agent fails -->  |
          | identify gap --> |
          | agent writes fix |
          +------------------+
```

The harness is not a single tool but a system of deterministic checks (linters, structural tests) and LLM-based agents (context providers, garbage collectors) working together. Deterministic components provide reliable guardrails; LLM agents handle semantic checks and adaptive maintenance.

---

## Installation & Usage

This is an article, not a software package. Key actionable patterns derived from the content:

**Assessing your current harness (from article's "What's your harness today?" section):**

- Audit existing pre-commit hooks: what behaviors do they enforce?
- Identify custom linter opportunities for architectural constraints
- Define explicit architectural constraints you want enforced
- Evaluate structural testing frameworks such as ArchUnit (Java) for boundary enforcement

**Harness improvement loop:**

```text
1. Observe agent mistake
2. Identify what is missing: tools, guardrails, documentation
3. Add the missing element to the harness (preferably via the agent itself)
4. Verify the agent no longer makes that class of mistake
5. Repeat
```

**Harness component checklist (derived from OpenAI case study):**

- AGENTS.md (or equivalent): behavioral instructions to prevent known failure modes
- Custom linters: encode architectural rules as static analysis
- Structural tests: enforce module boundaries and data shape contracts at build time
- Observability integration: give agents access to runtime data for self-diagnosis
- Garbage collection agents: schedule periodic consistency checks

---

## Relevance to Claude Code Development

### Applications

- Claude Code skill development benefits directly from harness thinking: CLAUDE.md files, pre-commit hooks, and validation scripts are components of a harness for Claude agents
- The iterative feedback loop (agent fails -> identify gap -> add to harness) maps directly to how Claude Code skills and AGENTS.md files should be maintained and improved
- The distinction between deterministic constraints (linters, structural tests) and LLM-based checks (garbage collection agents) informs how to layer Claude Code validation infrastructure

### Patterns Worth Adopting

- **Harness-first development**: when building new Claude Code workflows, define the harness (validation, structural tests, AGENTS.md constraints) before or alongside the workflow itself
- **Failure-as-signal**: when Claude Code makes a class of mistake, treat it as a gap in the harness rather than a one-off correction; fix the harness so the mistake cannot recur
- **Periodic entropy agents**: schedule or trigger agents to check for consistency violations in documentation, skill files, and manifest files (analogous to garbage collection agents)
- **Constraint engineering for reliability**: the article's argument that constrained solution spaces increase trustworthiness applies to Claude Code skill design—narrow scope with explicit constraints produces more reliable agent behavior than open-ended instructions

### Integration Opportunities

- The harness feedback loop could be formalized in Claude Code skill development: validation scripts (`validate_frontmatter.py`, `auto_sync_manifests.py`) are already harness components; extend them to catch more agent failure modes
- ArchUnit-style structural tests for skill file structure and cross-reference integrity would function as a harness for skill authoring agents
- The "harness as service template" concept suggests that Claude Code could offer pre-built harness configurations for common skill development patterns, analogous to the project's existing plugin structure

---

## References

- [Harness Engineering (Birgitta Böckeler, martinfowler.com)](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) (accessed 2026-02-21)
- [Exploring Generative AI series index (martinfowler.com)](https://martinfowler.com/articles/exploring-gen-ai.html) (accessed 2026-02-21)
- [Harness engineering: leveraging Codex in an agent-first world (OpenAI)](https://openai.com/index/harness-engineering/) (referenced in article; JavaScript-rendered, not directly accessible)
- [My AI Adoption Journey — Step 5: Engineer the Harness (Mitchell Hashimoto)](https://mitchellh.com/writing/my-ai-adoption-journey#step-5-engineer-the-harness) (accessed 2026-02-21)
- [Relocating Rigor (Chad Fowler, The Phoenix Architecture)](https://aicoding.leaflet.pub/3mbrvhyye4k2e) (accessed 2026-02-21)

---

## Freshness Tracking

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-21 |
| Version at Verification | N/A (article, published 17 February 2026) |
| Next Review Recommended | 2026-05-21 |

---

## Integration Opportunities

> Auto-generated by research-context-agent. Review before acting.

### Enhances Existing

| Target | Type | How |
|--------|------|-----|
| `plugins/development-harness/skills/development-harness/` | skill | The harness feedback loop concept (agent fails → identify gap → add to harness) maps directly onto the S6/S7 NEEDS_WORK/NOT_CERTIFIED loops; adding explicit harness-gap classification to those failure states would teach Claude to treat recurring failures as signals to extend the harness rather than one-off corrections. |
| `plugins/agentskill-kaizen/skills/kaizen-improvement/` | skill | The kaizen improvement skill already implements the harness improvement loop (transcript analysis → anti-pattern classification → hook/skill/CLAUDE.md fix), but the Böckeler article formalises the three harness layers (context, constraint, entropy-fighting). Adding explicit layer tagging to improvement proposals would let orchestrators route each finding to the correct fix type (hook for constraint violations, skill patch for context gaps, GC agent for entropy accumulation). |
| `plugins/agentskill-kaizen/skills/transcript-analysis/` | skill | Signal dimension 9 ("Missing Hooks") already detects corrections that recur 3+ times as hook candidates — this is identical to Böckeler's harness improvement trigger. Extend the output format to label each finding with its harness layer (context / constraint / entropy) so the kaizen-improvement skill can apply the correct fix type without re-classifying. |
| `.claude/agents/doc-drift-auditor.md` | agent | The doc-drift-auditor is a manual, on-demand agent; the article advocates periodic "garbage collection" agents that run on a schedule rather than being invoked ad hoc. Enhancing the agent's invocation documentation with scheduled trigger patterns (e.g., post-commit hook, weekly cron analogue) would implement the entropy-fighting layer of the harness model. |
| `plugins/holistic-linting/skills/holistic-linting/` | skill | The article argues linter error messages should be written as agent-readable remediation instructions, not bare error descriptions. The holistic-linting skill's rules knowledge base (ruff, mypy, bandit) currently documents rule intent and fix patterns for human-readable consumption; reframing each rule's resolution guidance as an explicit remediation instruction directed at the agent would align with the harness principle that constraints become guidance. |
| `plugins/verification-gate/skills/verification-gate/` | skill | The verification gate's four-checkpoint model is a deterministic constraint layer in harness terms. The article distinguishes deterministic checks (always-on, structural) from LLM-based checks (semantic, adaptive); documenting the verification gate explicitly as the constraint layer of this repository's harness (distinct from LLM-based kaizen analysis) would clarify where each belongs and prevent duplication of concerns across skills. |
| `.claude/hooks/session-start-backlog.js` | hook | This hook currently surfaces backlog item counts at session start (context layer). A harness-aligned extension would also inject a brief constraint-violation summary at session start — i.e., count of open harness gaps identified by kaizen analysis — so Claude begins each session aware of both backlog items and active constraint failures. |

### New Skill Candidates

- **harness-design**: A skill that teaches Claude to assess and design a repository's harness from scratch, following Böckeler's three-layer model (context layer, constraint layer, entropy-fighting agents). It would guide: auditing existing pre-commit hooks and linters as constraint components, identifying missing context documentation (CLAUDE.md gaps), and proposing garbage-collection agent schedules — producing a harness design document analogous to an AGENTS.md audit.

- **failure-as-signal**: A skill encoding the iterative harness improvement loop as a first-class workflow: when Claude makes a class of mistake, the skill triggers classification (which harness layer is missing?), drafts the harness addition (hook, linter rule, skill patch, or GC agent task), and writes it to `.planning/kaizen/improvements/` for review. This formalises the Böckeler feedback loop so it is repeatable rather than ad hoc.

### Cross-References

- Related research: `research/evaluation-testing/harness-engineering-openai.md` — The companion OpenAI engineering post by Ryan Lopopolo provides concrete implementation detail for each of Böckeler's three harness layers: the `docs/` structured repository as context layer, custom linters with agent-readable error messages as constraint layer, and recurring "doc-gardening" Codex tasks as entropy-fighting layer. Reading both together provides theory (Böckeler) and practice (Lopopolo).
- Related research: `research/evaluation-testing/codex-harness-openai.md` — Documents the Codex App Server's item/turn/thread protocol; relevant to the harness model because the bidirectional approval-pause-resume mechanism is an implementation of the human escalation decision the harness must make when constraints are unbound — mapping directly to the ARL touchpoint model in the development-harness plugin.
