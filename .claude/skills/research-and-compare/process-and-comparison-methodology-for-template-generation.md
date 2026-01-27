# Research + Comparison Methodology (With References)

This document is an AI-facing **process spec** for doing cross-domain comparison research and synthesizing reusable comparison templates (or executing a one-off comparison) with **bounded scope**, **evidence traceability**, and **explicit comparability rules**.

---

## 1) When to use this process

Use this process when asked to:

- Compare two methodologies/frameworks/systems/products/theories.
- Build or improve a reusable comparison template or rubric.
- Produce a decision matrix, evaluation rubric, or “best for / avoid if” recommendation set.
- Do multi-domain research where web sources are required and some sources may be paywalled/blocked.

---

## 2) Core principles (non-negotiable)

- **Fit-for-purpose first**: define the decision the comparison must enable before selecting criteria.
- **Evidence > priors**: treat training priors as hypotheses; ground claims in sources.
- **Comparability is a first-class constraint**: do not compare metrics produced under different protocols unless explicitly normalized; otherwise mark **NOT_COMPARABLE**.
- **Bounded extension**: explicitly cap domain expansion and declare stopping criteria to avoid “comparison paralysis”.
- **Traceability**: every non-trivial claim must be linkable to a source (URL/doc/test) or explicitly marked as assumption/unknown.

---

## 3) Tooling workflow (including MCP + fallbacks)

### 3.1 Primary web workflow

1. **Locate candidate sources** using standard web search.
2. **Fetch primary documents** (methodology pages, rubrics, scoring systems, changelogs) rather than secondary summaries.
3. **Extract comparison mechanics**:
   - how criteria are chosen,
   - how weighting works,
   - what evidence protocols ensure comparability,
   - how recommendations are produced (picks, tiers, disqualifiers),
   - how scope is framed (who it’s for, out of scope),
   - how updates/changelogs are handled.
4. **Synthesize** into:
   - universal domains,
   - domain-specific patterns,
   - question archetypes,
   - bounded self-extension rules.

### 3.2 Handling blocked sources / scraping failures

If direct fetch fails (403/paywall/JS-heavy):

- Prefer MCP tooling that can retrieve the page content reliably (e.g., Firecrawl MCP).
- If an important site is blocklisted by the scraper provider, **do not fabricate**. Either:
  - find an equivalent primary source elsewhere, or
  - record the gap explicitly (“blocked by provider; unable to verify”), and proceed with other sources.

### 3.3 Evidence hygiene

- Record **access date** for every URL.
- Record **version/date** when comparing fast-moving targets (framework versions, rubric editions, test-bench versions).
- If methodology indicates “only compare within same script/protocol”, adopt that rule in the comparison template.

---

## 4) Source selection rubric (to avoid domain bias)

When building a universal template, sample at least:

- **Consumer product testing**: “how we test”, scoring methods, lab + real-world evaluation.
- **Decision matrices / selection frameworks**: criteria selection + weighting + aggregation mechanics.
- **Business methodologies**: “when to use” framing, change-management implications, org/coordination costs.
- **Academic/peer-review rubrics**: mixed scoring, “not all criteria must be strong”, sufficiency gates.
- **Technical frameworks**: explicit bias management, ecosystem/tooling axes, benchmarking caveats.

Prefer primary documents that contain the mechanics (process), not just opinions.

---

## 5) Extraction template (how to read a comparison methodology)

For each source, extract the following fields:

- **Domain**: consumer_product | technical_framework | business_methodology | academic_rubric | decision_matrix | other
- **Purpose**: what decision it enables
- **Scope framing**: “who it’s for”, “what it excludes”
- **Criteria selection mechanism**: how criteria are generated/refined; include/exclude rules
- **Evidence protocol**: lab tests, real-world tests, expert input, surveys, benchmarks; comparability rules
- **Aggregation method**:
  - narrative only,
  - weighted average,
  - rubric levels,
  - baseline comparison (-1/0/+1),
  - disqualifying thresholds
- **Output form**: top pick/runner-up, tiers, matrix winner, persona mapping, etc.
- **Tradeoff handling**: explicit tradeoffs vs forced single score
- **Update mechanism**: changelogs, edition updates, “what to look forward to”
- **Anti-bias measures**: disclosure, neutrality statements, separation of monetization/editorial, etc.
- **Notable patterns to generalize**: concise bullets
- **Citation**: URL + access date (+ edition/version when relevant)

---

## 6) Synthesis procedure (Stage 1 -> Stage 2)

### 6.1 Build a pattern library

Create a table of extracted patterns and cluster them into:

- **Universal domains** (appear across multiple source categories)
- **Category-specific domains** (strongly tied to one domain type)
- **Question archetypes** (reusable prompts)
- **Aggregation archetypes** (narrative, hybrid, weighted, rubric-level)
- **Scope-setting archetypes** (personas, “who it’s for”, “out of scope”, disqualifiers)

### 6.2 Rank domains by frequency + decision relevance

Assign each candidate domain:

- **frequency**: how often it appears across categories
- **decision criticality**: how often it flips conclusions in practice

Use this to define:

- an **essential** set (default-on),
- an **optional** set,
- and a **bounded extension** mechanism (cap new domains; require justification).

### 6.3 Implement bounded self-extension (anti-paralysis)

In the final template:

- Require a **pre-comparison reflection** that tailors domains to context.
- Cap new domain generation (e.g., max 5).
- Add explicit **stopping criteria** (“ready to compare” vs “needs more evidence”).

---

## 7) Quality gates before claiming “done”

- **Coverage**: essentials are answered or explicitly marked unknown with impact.
- **Comparability**: apples-to-oranges comparisons are marked NOT_COMPARABLE.
- **Bias disclosure**: if sources are stakeholder-authored (e.g., “Vue vs others”), label as such.
- **Sensitivity** (if numeric): vary top weights ±20%; note if the winner flips.
- **Traceability**: every non-trivial claim maps to a citation or is flagged assumption.

---

## 8) Reference set used to derive the methodology (primary sources)

Consumer testing / review methodology:

1. Wirecutter, “The Anatomy of a Wirecutter Guide” (guide structure, trust framing, picks taxonomy). `https://www.nytimes.com/wirecutter/blog/anatomy-of-a-guide/` (accessed 2026-01-27)
2. Wirecutter, “Wirecutter’s Secret to Making Great Picks: Obsessive Spreadsheeting” (comparison tables, weighted attributes, institutional memory). `https://www.nytimes.com/wirecutter/blog/comparison-tables/` (accessed 2026-01-27)
3. Consumer Reports Data Intelligence, “Rating Methods” (category-dependent criteria/weighting, reliability/satisfaction components, privacy/security inclusion). `https://data.consumerreports.org/rating-methods/` (accessed 2026-01-27)
4. PCMag, “How We Test Everything We Review” (repeatable scripts, comparability constraint across methodology changes, rating scale semantics, ethics separation). `https://www.pcmag.com/about/how-we-test-everything-we-review` (accessed 2026-01-27)
5. Good Housekeeping (UK), “How the Good Housekeeping Institute Approved seal really works” (home-context rubric: design/ease/performance/instructions; pass/fail endorsement gate). `https://www.goodhousekeeping.com/uk/consumer-advice/a563956/how-good-housekeeping-institute-approved-really-works/` (accessed 2026-01-27)
6. RTINGS, “Test Benches and Scoring System” (tests -> weighted usage ratings; versioned test benches; explicit score interpretation bands; price not part of scores). `https://www.rtings.com/company/test-benches-and-scoring-system` (accessed 2026-01-27)
7. RTINGS, “Scoring Function Overhaul” (measurement-to-score mapping method; transparency and change control). `https://www.rtings.com/company/scoring-function-overhaul` (accessed 2026-01-27)

Decision matrices / selection frameworks: 8. ASQ, “What is a Decision Matrix?” (criteria brainstorming, include/exclude, weighting, baseline scoring variants; scale direction guidance). `https://asq.org/quality-resources/decision-matrix` (accessed 2026-01-27)

Business methodology comparisons / selection framing: 9. Atlassian, “Project management intro: Agile vs. waterfall methodologies” (advantages/disadvantages; risk timing; change cost; coordination structure). `https://www.atlassian.com/agile/project-management/project-management-intro` (accessed 2026-01-27) 10. Lucidchart, “Lean vs. Six Sigma: Determining the Right Method for Your Business” (selection by goal type; principles; implementation pathways 5S vs DMAIC; hybridization). `https://lucidchart.com/blog/lean-vs-six-sigma` (accessed 2026-01-27)

Formal rubrics / peer review: 11. NIST Baldrige, “Award Criteria” (context section + evaluation rubrics; trends + comparisons requirements; process vs results rubrics). `https://www.nist.gov/baldrige/baldrige-award/award-criteria` (accessed 2026-01-27) 12. NIH Grants, “Simplified Peer Review Framework” (criteria reorganized into factors; mixed scoring types; “not all categories must be strong”). `https://grants.nih.gov/policy-and-compliance/policy-topics/peer-review/simplifying-review/framework` (accessed 2026-01-27)

Technical framework self-comparison: 13. Vue.js (Vue 2 docs), “Comparison with Other Frameworks” (explicit bias management; mixed objective/subjective axes; update solicitation). `https://vuejs.org/v2/guide/comparison.html` (accessed 2026-01-27)
