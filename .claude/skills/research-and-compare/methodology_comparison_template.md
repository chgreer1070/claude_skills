# Methodology Comparison Template (Universal, AI-Reasoning Oriented)

Use this template to systematically compare **any two items** (methodologies, frameworks, systems, products, theories, organizations, etc.) while staying **fit-for-purpose**, **evidence-grounded**, and **bounded** (no infinite scope creep).

---

## 0) Comparison Header (fill first)

- **Item A**: {{A_NAME}}
- **Item B**: {{B_NAME}}
- **Comparison category** (choose): {{consumer_product | technical_framework | business_methodology | academic_theory | process/tooling | other}}
- **Decision posture** (choose): {{choose_one | recommend_ranked | describe_tradeoffs_only | decide_for_each_persona}}
- **Audience**: {{who_will_use_this}}
- **Primary decision to enable**: {{decision_question}}
- **Stakes / cost of wrong choice**: {{low | medium | high}} (why: {{...}})
- **Time budget**: {{minutes_or_hours}}
- **Evidence constraint**: {{high_rigor_required | moderate | low (qualitative OK)}}
- **Non-negotiables (hard constraints)**: {{list}}

---

## 1) Pre-Comparison Reflection (MANDATORY; produces the “tailored rubric”)

This section is a **gating step**: you must tailor the template before evaluating.

### 1.1 Fit-for-purpose framing (stop generic comparisons)

- **What problem exists in the world that this comparison must resolve?**
  - {{...}}
- **Who experiences the problem and in what context(s)?**
  - {{...}}
- **What does “success” mean in observable terms?**
  - {{success_signals}}
- **What does “failure” look like (costly mistakes)?**
  - {{failure_modes}}
- **What is out of scope?**
  - {{explicit_non_goals}}

### 1.2 Assumptions and boundary conditions (write them down or they’ll leak)

- **Assumptions you are making** (each must be testable / falsifiable):
  - {{assumption_1}} (evidence needed to validate: {{...}})
  - {{assumption_2}} (evidence needed to validate: {{...}})
- **Boundary conditions / constraints** (time, money, regulatory, environment, compatibility, team skills):
  - {{...}}

### 1.3 Evidence plan (how you will ground claims)

Pick the evidence types you will use and how you will ensure comparability.

- **Primary evidence sources** (select + list):
  - {{published_docs/specs | official docs | lab tests | benchmarks | case studies | surveys | expert interviews | peer review | standards/regulators | direct experimentation}}
- **Comparability rules** (to avoid apples-to-oranges):
  - Only compare metrics measured under comparable conditions (same protocol/version where possible).
  - If not comparable, explicitly mark the comparison cell as **NOT_COMPARABLE** and explain why.
- **Version / time window** (important for fast-moving domains):
  - A version/date: {{...}}
  - B version/date: {{...}}

### 1.4 Scoring stance (quant + qual without forcing fake numbers)

Choose one:

- **Narrative-only** (no numeric scoring). Use when criteria are inherently qualitative or evidence is sparse.
- **Hybrid** (numeric scores only for criteria with measurable evidence; narrative for the rest).
- **Weighted decision matrix** (numeric). Use when you must pick one option and can justify weights.

Selected stance: {{narrative_only | hybrid | weighted_matrix}}

If using a matrix:

- **Scale**: {{1-3 | 1-5 | 1-9 | baseline -1/0/+1 | other}}
- **Weighting method**: {{distribute_100_points | 1-10 importance | pairwise | none}}
- **Rule**: Higher score must always mean “more desirable” (reword criteria if needed: “low cost” not “cost”).

### 1.5 Tailored domain set (select essentials, then extend)

#### Essential domains (must cover, but may be “N/A with justification”)

Select the minimum set that directly drives the decision (usually 5–9):

- [ ] Fit to use-cases / “Who it’s for”
- [ ] Core approach / mechanism / workflow
- [ ] Effectiveness / outcomes (primary success signals)
- [ ] Costs (total cost, not just sticker price) + constraints
- [ ] Risks / failure modes + mitigations
- [ ] Adoption / learning curve / switching or migration cost
- [ ] Maintainability / operability (ongoing effort)

Chosen essentials: {{list}}

#### Optional universal domains (include only if decision-relevant)

- [ ] Safety / harm / privacy / security
- [ ] Reliability / robustness / quality control
- [ ] Performance / efficiency / speed (define metric!)
- [ ] Scalability (define scale dimension!)
- [ ] Compatibility / interoperability / integration surface
- [ ] Ecosystem / support / community / vendor stability
- [ ] Governance / accountability / transparency / ethics
- [ ] Evidence quality / auditability / reproducibility
- [ ] Future outlook (roadmap, update cadence, deprecation risk)

Chosen optional domains: {{list}}

#### Domain-specific extensions (self-expand, but bounded)

Generate **at most {{MAX_NEW_DOMAINS:=5}} new domains**. Each must include:

- why it is decision-critical,
- what evidence would resolve it,
- and which existing domain it refines or replaces.

New domains:

- {{domain_new_1}}: why {{...}}; evidence {{...}}; relates to {{...}}
- {{domain_new_2}}: why {{...}}; evidence {{...}}; relates to {{...}}

### 1.6 Stopping criteria (prevent comparison paralysis)

You may stop extending/collecting when ALL are true:

- The chosen essentials are answered with **decision-grade** evidence (or explicitly marked as unknown with impact).
- Adding another domain would not change the recommendation for the target audience(s) (or would be pure “nice to know”).
- Remaining unknowns are either:
  - low-impact, or
  - blocked by unavailable evidence, or
  - would require a different project (e.g., new experiments).

Stop decision: {{READY_TO_COMPARE | NEEDS_MORE_EXTENSION | NEEDS_MORE_EVIDENCE}}

---

## 2) Comparison Map (one-screen orientation)

### 2.1 One-sentence summaries (avoid wordy drift)

- **A in one sentence**: {{...}}
- **B in one sentence**: {{...}}

### 2.2 “Best for” and “avoid if” (persona anchors)

- **A best for**: {{persona/use-case}}
- **A avoid if**: {{persona/use-case}}
- **B best for**: {{persona/use-case}}
- **B avoid if**: {{persona/use-case}}

### 2.3 Non-negotiables check

- If either fails a hard constraint, mark it **DISQUALIFIED** and explain:
  - A: {{PASS | FAIL}} (why: {{...}})
  - B: {{PASS | FAIL}} (why: {{...}})

---

## 3) Domain Worksheets (repeat per selected domain)

For each domain below, fill:

- **Definition** (what the domain means _in this comparison_),
- **Questions** (use the starter set; add specialized ones),
- **Evidence** (sources + comparability),
- **Findings** (A vs B),
- **Tradeoffs** (what improves, what worsens),
- **Verdict** (optional score + confidence).

### 3.1 Fit to use-cases / “Who it’s for”

- **Definition**: {{...}}
- **Starter questions**
  - What user/problem context is each optimized for?
  - What usage scenarios are common, and which are edge cases?
  - Where does each become the wrong tool?
- **Specialize**
  - Add 3 scenario questions specific to {{A_NAME}}/{{B_NAME}}:
    - {{...}}
- **Evidence**
  - {{...}}
- **Findings**
  - A: {{...}}
  - B: {{...}}
- **Tradeoffs**
  - {{...}}
- **Verdict**
  - {{A_better | B_better | depends}}; confidence {{low|med|high}}

### 3.2 Core approach / mechanism / workflow

- **Starter questions**
  - What are the core primitives/steps?
  - Where are decisions made (centralized vs distributed; human vs system)?
  - What must be true for the approach to work (preconditions)?
  - What is the typical failure mode when assumptions are violated?
- **Specialize**
  - {{...}}
- **Evidence / Findings / Tradeoffs / Verdict**
  - {{...}}

### 3.3 Effectiveness / outcomes (primary success signals)

- **Starter questions**
  - What measurable or observable outcomes matter?
  - How do we measure them (protocol)? What counts as “good enough”?
  - How sensitive are outcomes to context (team skill, environment, scale)?
  - What are known ceiling/floor effects?
- **Specialize**
  - Define 3 outcome metrics and thresholds:
    - Metric 1: {{...}} threshold {{...}}
    - Metric 2: {{...}} threshold {{...}}
    - Metric 3: {{...}} threshold {{...}}
- **Evidence / Findings / Tradeoffs / Verdict**
  - {{...}}

### 3.4 Costs (total cost) + constraints

- **Starter questions**
  - What are one-time vs ongoing costs (money, time, effort)?
  - What hidden costs exist (tooling, training, compliance, maintenance)?
  - Which costs scale with usage/size?
- **Specialize**
  - Build a mini TCO breakdown table:
    - {{...}}
- **Evidence / Findings / Tradeoffs / Verdict**
  - {{...}}

### 3.5 Risks / failure modes + mitigations

- **Starter questions**
  - What can go wrong (top 5 failure modes)?
  - How detectable are failures (early vs late)?
  - What are mitigations and their costs?
  - What is the “blast radius” if it fails?
- **Specialize**
  - Add domain-specific harms (safety/privacy/ethics/regulatory) if applicable:
    - {{...}}
- **Evidence / Findings / Tradeoffs / Verdict**
  - {{...}}

### 3.6 Adoption / learning curve / switching or migration

- **Starter questions**
  - What skills/prereqs are required?
  - Time-to-first-success vs time-to-mastery?
  - Migration path and compatibility with existing assets?
  - Lock-in risk and exit costs?
- **Evidence / Findings / Tradeoffs / Verdict**
  - {{...}}

### 3.7 Maintainability / operability (ongoing effort)

- **Starter questions**
  - What does “operate” mean here (run, govern, audit, support)?
  - What are routine tasks and their frequency?
  - Observability/diagnostics: how do you know it’s working?
  - How are changes introduced safely?
- **Evidence / Findings / Tradeoffs / Verdict**
  - {{...}}

### 3.x Additional selected domains

Copy this block per domain you selected in 1.5:

#### {{DOMAIN_NAME}}

- **Definition**: {{...}}
- **Starter questions**:
  - {{...}}
- **Specialize**:
  - {{...}}
- **Evidence**:
  - {{...}}
- **Findings**:
  - A: {{...}}
  - B: {{...}}
- **Tradeoffs**:
  - {{...}}
- **Verdict**:
  - {{...}}

---

## 4) Decision Matrix (optional; only if you chose it in 1.4)

### 4.1 Criteria list and weights

- Criteria must be:
  - decision-relevant,
  - non-overlapping where possible,
  - worded so “higher = more desirable”.

| Criterion | Definition in this context |  Weight | Evidence type | Notes   |
| --------- | -------------------------- | ------: | ------------- | ------- |
| {{c1}}    | {{...}}                    | {{...}} | {{...}}       | {{...}} |
| {{c2}}    | {{...}}                    | {{...}} | {{...}}       | {{...}} |

### 4.2 Scoring table

| Criterion | Weight | A score | B score | Rationale + citations |
| --------- | -----: | ------: | ------: | --------------------- |
| {{c1}}    | {{w1}} |  {{a1}} |  {{b1}} | {{...}}               |
| {{c2}}    | {{w2}} |  {{a2}} |  {{b2}} | {{...}}               |

### 4.3 Sensitivity check (required for numeric decisions)

- Re-run mentally with:
  - weights shifted ±20% on the top 3 criteria,
  - pessimistic assumptions for weakest-evidence criteria.

Result stability:

- **Stable winner**: {{yes|no}}
- **If not stable, what drives flips?**: {{...}}

---

## 5) Outputs (produce something actionable)

### 5.1 Recommendation (choose a format)

Pick one:

- **Single winner**: {{A|B}} (because {{top_reasons}})
- **Ranked**: 1) {{...}} 2) {{...}} 3) {{...}}
- **Best-for personas**: {{persona -> pick mapping}}
- **Tradeoff-only** (no winner): {{...}}

### 5.2 “Flaws but not dealbreakers”

- A: {{...}}
- B: {{...}}

### 5.3 Worth considering (near-misses / niche fits)

- {{option}}: {{why}}

### 5.4 The competition (explicitly excluded options/domains)

- Excluded domains (and why): {{...}}
- Excluded alternatives (and why): {{...}}

### 5.5 What to look forward to (update triggers)

- What would make you revisit this comparison?
  - new version/release, new evidence, changed constraints, new regulation, etc.
- Next review date: {{...}}

---

## 6) Evidence Log (traceability)

List each non-trivial claim with its evidence.

| Claim   | Evidence         | Date / version | Confidence | Notes |
| ------- | ---------------- | -------------- | ---------- | ----- | ------ | ------- |
| {{...}} | {{url/doc/test}} | {{...}}        | {{low      | med   | high}} | {{...}} |
