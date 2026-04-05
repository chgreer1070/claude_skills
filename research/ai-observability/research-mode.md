---
title: research-mode
subtitle: Anti-hallucination toggle for Claude Code
resource_url: https://github.com/assafkip/research-mode
category: ai-observability
date_researched: 2026-04-05
next_review: 2026-07-05
---

# Research Mode

## Overview

Research Mode is a Claude Code plugin that activates anti-hallucination constraints based on Anthropic's documented hallucination-reduction techniques. The plugin enforces a strict mode requiring source citation, direct quoting, and explicit acknowledgment of uncertainty. It operates as a toggleable constraint system rather than a persistent default, allowing users to switch between research-disciplined work and open creative thinking.

**Version**: 1.0.0
**Creator**: Assaf Kipnis (GitHub: @assafkip)
**Repository**: <https://github.com/assafkip/research-mode>
**License**: Not specified in reviewed sources

## Problem Addressed

LLMs hallucinate—they generate factually incorrect or internally inconsistent text. According to the author, Assaf Kipnis, "When your AI assistant is writing your pitch decks, researching competitors, and drafting investor briefs, hallucinated facts aren't a minor annoyance. They're a credibility risk." Research Mode addresses this risk by enforcing discipline through three simultaneous constraints that ground responses in verifiable sources and make uncertainty explicit.

This is particularly critical for professional contexts—GTM strategy, investor outreach, and content operations—where hallucinated claims directly undermine credibility and decision-making.

## Key Statistics

- **GitHub Stars**: 94 (as of 2026-04-05)
- **Forks**: 12
- **Topics**: ai-safety, anti-hallucination, citations, claude-code, claude-code-plugin, llm
- **Latest Commit**: `8f4fb16` — "docs: add kipi callout, source cascade section to README" (single commit in reviewed history)
- **Platforms Supported**: Claude Code CLI, macOS desktop app, VS Code extension

## Key Features

### Three Simultaneous Constraints

1. **Say "I don't know"**
   When there is no credible source for a claim, the plugin enforces explicit acknowledgment of uncertainty. No guessing, no inference. "I don't have data on this" is always a valid answer.

2. **Verify with citations**
   Every recommendation, claim, or piece of advice must cite a specific source. Acceptable citations include:
   - A file in the current project (with path + line number)
   - An external source found via web search (with URL)
   - A named expert, paper, or researcher
   - Official documentation

   If a claim cannot find a supporting source, it is retracted.

3. **Direct quotes for factual grounding**
   Responses are grounded in word-for-word quotes from source material, not paraphrased summaries. Extracted quotes are referenced when making claims.

### Source Lookup Cascade

The plugin enforces an ordered cascade to minimize token cost while prioritizing reliability:

1. **Level 1 — Local files (zero cost)**
   Uses Grep and Read to search the current project first. If the claim concerns the project, local files ARE the citation.

2. **Level 2 — WebSearch snippets (low cost)**
   Runs WebSearch. Result snippets usually contain the key fact. Cited as: "According to [Source Name] ([URL]): [snippet text]". WebFetch is NOT called unless the snippet is ambiguous.

3. **Level 3 — WebFetch for direct quotes (high cost, used sparingly)**
   Full pages are fetched only when:
   - The snippet is ambiguous and surrounding context is needed
   - The user explicitly asked for direct quotes or full text
   - A specific number, date, or technical detail is needed that the snippet doesn't include

4. **Level 4 — Scholar Gateway (for academic claims)**
   For academic papers or research findings, Scholar Gateway MCP is used if available.

### Token Budget and Efficiency Controls

- **Maximum 5 WebSearch calls per research question**
- **Maximum 3 WebFetch calls per research question**
- When limit is hit: Claude summarizes findings, lists what remains unverified, and asks before going deeper
- Parallel searches are encouraged; serial retry loops are prohibited

### Toggle-Based Operation

- NOT the default mode. Research Mode is explicitly activated when needed.
- Turns off when user says "exit research mode" or switches to another task.
- Does NOT slow response time. Claude still uses tools in parallel.
- Allows synthesis across sources, but input material must be grounded.

## Technical Architecture

### Plugin Entry Point

Research Mode is distributed as a Claude Code marketplace plugin. Installation flow:

```
/plugin marketplace add assafkip/research-mode
↓
/plugin install research-mode@assafkip-research-mode
↓
/research-mode:research [optional-topic]
```

### Command Interface

The plugin exposes a single command: `/research-mode:research`

- **Without arguments**: Activates research mode. User then issues research questions.
- **With argument**: Invokes research mode and immediately begins researching the provided topic.
  - Example: `/research-mode:research what caused the Change Healthcare breach`
  - The `$ARGUMENTS` variable in SKILL.md line 51 captures the optional topic.

### Skill-Based Implementation

The plugin contains:

- **SKILL.md**: Master prompt defining the three constraints, source lookup order, token budget, and exit conditions (lines 8-67 of reviewed file)
- **commands/research.md**: Command definition extending SKILL.md with argument substitution ($ARGUMENTS) for topic-based research initiation
- **plugin.json**: Metadata (name, description, version 1.0.0)
- **marketplace.json**: Marketplace registration identifying the plugin as `assafkip-research-mode`

The implementation leverages Claude's native tools (Grep, Read, WebSearch, WebFetch) as the mechanism for source lookup. No custom code or MCP servers are required—the plugin is a pure prompt-based constraint system.

### Architecture Implications

The cascade ordering in SKILL.md creates a computational hierarchy:

- **Free tier**: Grep + Read (project-local only)
- **Low-cost tier**: WebSearch (snippets only)
- **High-cost tier**: WebFetch (full pages)
- **Specialized tier**: Scholar Gateway (structured research data)

This ordering directly reflects token economy: local reads are cheapest, web searches incur snippet tokens, full-page fetches are most expensive, and Scholar Gateway provides structured data for academic queries. The source cascade acts as a cost-optimization layer embedded in the mode's guidance.

## Installation & Usage

### Two Installation Paths

**Path 1 — Marketplace Plugin (Recommended)**

```bash
/plugin marketplace add assafkip/research-mode
/plugin install research-mode@assafkip-research-mode
```

Works in Claude Code CLI, the macOS desktop app, and the VS Code extension. After install, confirm: `/plugin` should list `research-mode` in available plugins.

If command doesn't appear, run `/reload-plugins` or restart Claude Code.

**Path 2 — Standalone Skill**

Clone the repository and copy `SKILL.md` into your project:

```bash
git clone https://github.com/assafkip/research-mode.git
cp research-mode/SKILL.md <your-project>/.claude/skills/research-mode/SKILL.md
```

### Using Research Mode

**Activate without topic:**

```
/research-mode:research
```

Claude enters research mode and awaits research questions.

**Activate with topic:**

```
/research-mode:research what caused the Change Healthcare breach
```

Claude activates research mode and immediately begins researching the specified topic.

**Exit research mode:**

Say "exit research mode" or switch to another task.

### Integration with Kipi Founder OS

Research Mode is pre-built into Kipi Founder OS (a higher-level operating system for Claude Code). Users of Kipi can invoke research without separate installation:

```
/q-research <topic>
```

This provides the same three constraints and source cascade as the standalone plugin.

## Relevance to Claude Code Development

Research Mode directly addresses a critical gap in Claude Code's capability profile: ensuring source-grounded responses for professional research workflows. Key relevance areas:

1. **Competitive Intelligence**: Users building GTM strategies, analyzing competitors, or performing market research need hallucination-free outputs. The citation discipline prevents false claims from entering pitch decks or investor briefs.

2. **Skill and Plugin Documentation**: Documentation that relies on hallucinated API details or inferred feature behavior corrupts downstream development. Research Mode enforces quote-based extraction for documentation accuracy.

3. **Agent Evaluation and Testing**: When validating LLM outputs for correctness, the source cascade and token budget constraints provide observable checkpoints for quality gates.

4. **Multi-Agent Orchestration**: Agents performing research subtasks can adopt Research Mode constraints locally within a larger workflow, ensuring intermediate findings are source-grounded before downstream synthesis.

5. **Governance and Compliance**: Regulatory or audit work (data privacy, security reviews, contract analysis) benefits from explicit citation trails and uncertainty acknowledgment.

Research Mode is a reusable constraint pattern applicable to any domain where factual accuracy and source traceability are non-negotiable.

## Limitations and Caveats

1. **Manual Activation Required**
   Research Mode is not a default. Users must explicitly invoke it via `/research-mode:research`. This requires discipline—users must remember to activate it for research-critical work.

2. **Token Budget Creates Incomplete Research Scenarios**
   The hard limits (5 WebSearch, 3 WebFetch max) may result in incomplete research when many sources are needed. The plugin handles this by asking user permission before exceeding limits, but the decision to go deeper is manual.

3. **No Offline Mode**
   Research Mode depends on functional WebSearch and WebFetch tools. If network access is unavailable or those tools are misconfigured, research mode falls back to local files only, potentially leaving research incomplete.

4. **Source Cascade Is Not Optimal for All Queries**
   The fixed cascade order (local → WebSearch → WebFetch → Scholar) assumes snippets are usually sufficient. For highly specialized technical queries or ambiguous topics, the snippet may lack necessary context, forcing WebFetch earlier than the cascade prescribes.

5. **No Automatic Verification of Citations**
   The plugin enforces the user to cite sources, but does not automatically verify that cited sources actually support the claim. A malicious or confused Claude instance could cite a URL that doesn't contain the stated claim. The citation requirement is a discipline measure, not a guarantee.

6. **Kipi Integration Not Documented in Original Repository**
   The README mentions Kipi integration (lines 5-6), but the original `research-mode` repository does not contain Kipi-specific code. Kipi support is maintained in the Kipi ecosystem, creating a dependency that isn't visible in the core repository.

## Freshness Tracking

| Section | Confidence | Notes |
|---------|------------|-------|
| Identity/Metadata | high | plugin.json and marketplace.json directly read; GitHub stars verified 2026-04-05 |
| Problem Addressed | high | Author's stated motivation in README; grounded in Anthropic's official hallucination-reduction documentation |
| Key Features | high | Extracted directly from SKILL.md and README.md with exact quotes |
| Technical Architecture | high | Plugin structure read from SKILL.md, commands/research.md, and plugin.json; implementation verified as prompt-based with no custom code |
| Installation & Usage | high | Installation steps and command syntax extracted verbatim from README.md |
| Limitations | medium | Derived from feature constraints documented in SKILL.md (token budget, toggle requirement, source cascade ordering); integration constraint (Kipi) noted from README but not verified in core repo |
| Relevance | medium | Use cases inferred from problem statement and feature design; not independently verified by testing against Claude Code workflows |

**Data Freshness**: All sources accessed 2026-04-05. Repository has single commit in history; creation and last activity dates not shown in shallow clone. Recommend re-review 2026-07-05 to verify continued maintenance and any breaking changes to Claude Code plugin system.

## Cross-References

| Entry | Category | Relationship |
|-------|----------|--------------|
| [AutoResearchClaw.md](../agent-frameworks/AutoResearchClaw.md) | agent-frameworks | multi-layer citation verification pipeline for grounded research outputs |
| [logfire.md](./logfire.md) | ai-observability | observability platform for monitoring hallucination detection and source tracking in LLM applications |
| [compression-monitor.md](./compression-monitor.md) | ai-observability | behavioral drift detection that complements research-mode's verification constraints |
| [harness-engineering-martin-fowler.md](../evaluation-testing/harness-engineering-martin-fowler.md) | evaluation-testing | shared discipline pattern: deterministic constraints keeping AI outputs in check |
| [composure.md](../agent-frameworks/composure.md) | agent-frameworks | multi-language code quality enforcement via tree-sitter knowledge graph, analogous constraint-driven workflow |
| [everything-claude-code.md](../skill-generation-tools/everything-claude-code.md) | skill-generation-tools | comprehensive agent governance system with hooks and AgentShield security constraints |
| [gstack.md](../agent-frameworks/gstack.md) | agent-frameworks | role-specific behavioral constraints via 8 specialized skills for Claude Code |
| [anthropics-skills.md](../skill-generation-tools/anthropics-skills.md) | skill-generation-tools | official Anthropic skills with A/B eval harness, shared mechanism for skill-based governance |

## References

- [Research Mode GitHub Repository](https://github.com/assafkip/research-mode) — accessed 2026-04-05
- README.md — plugin overview, features, installation, troubleshooting
- SKILL.md — constraint definitions, source cascade, token budget, exit conditions
- commands/research.md — command definition and argument handling
- plugin.json and marketplace.json — metadata and marketplace registration
- [Anthropic - Reduce Hallucinations](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — official documentation on hallucination minimization strategies that Research Mode implements
- Assaf Kipnis GitHub profile and activity (<https://github.com/assafkip>) — accessed 2026-04-05

---

**Entry created**: 2026-04-05
**Last reviewed**: 2026-04-05
**Next review due**: 2026-07-05
