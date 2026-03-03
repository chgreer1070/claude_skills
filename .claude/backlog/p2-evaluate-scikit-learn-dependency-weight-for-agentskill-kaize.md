---
name: Evaluate scikit-learn dependency weight for agentskill-kaizen cluster_sessions tool
description: The `cluster_sessions` tool in `plugins/agentskill-kaizen/mcp/server.py` uses `scikit-learn` (`KMeans`, `CountVectorizer`) for session clustering. scikit-learn pulls in ~40MB of transitive dependencies (numpy, scipy, joblib, threadpoolctl). The typical use case is clustering dozens of sessions, not thousands. The Phase 1-2 research produced no durable artifact evaluating library choices — `scikit-learn` was assumed from the backlog without validation. Investigate whether a lighter alternative (e.g., `pyclustering`, stdlib-based implementation, or just `numpy` directly) would suffice for this scale, and whether the KMeans-on-bag-of-words approach is even appropriate for tool-call sequence similarity.
metadata:
  topic: evaluate-scikit-learn-dependency-weight-for-agentskill-kaize
  source: agentskill-kaizen MCP server review (2026-02-18)
  added: '2026-02-18'
  priority: P2
  type: Feature
  status: open
  issue: '#118'
  groomed: '2026-03-03'
---

## Story

As a **developer using Claude Code skills**, I want to **evaluate scikit-learn dependency weight for agentskill-kaizen cluster_sessions tool** so that **the tooling becomes more capable and complete**.

## Description

The `cluster_sessions` tool in `plugins/agentskill-kaizen/mcp/server.py` uses `scikit-learn` (`KMeans`, `CountVectorizer`) for session clustering. scikit-learn pulls in ~40MB of transitive dependencies (numpy, scipy, joblib, threadpoolctl). The typical use case is clustering dozens of sessions, not thousands. The Phase 1-2 research produced no durable artifact evaluating library choices — `scikit-learn` was assumed from the backlog without validation. Investigate whether a lighter alternative (e.g., `pyclustering`, stdlib-based implementation, or just `numpy` directly) would suffice for this scale, and whether the KMeans-on-bag-of-words approach is even appropriate for tool-call sequence similarity.

## Context

- **Source**: agentskill-kaizen MCP server review (2026-02-18)
- **Priority**: P2
- **Added**: 2026-02-18
- **Research questions**: What clustering approaches work for short categorical sequences? Is cosine similarity on bag-of-words tool vectors meaningful for workflow comparison? What lightweight Python clustering libraries exist that don't pull in scipy?

## Fact-Check

Claims checked: 5
VERIFIED: 3 | REFUTED: 0 | INCONCLUSIVE: 2

1. **VERIFIED** — `cluster_sessions` currently uses scikit-learn `KMeans` and `CountVectorizer` in `plugins/agentskill-kaizen/mcp/server.py`.
2. **VERIFIED** — scikit-learn is an explicit runtime dependency in the server script dependency block (`"scikit-learn>=1.0"`).
3. **VERIFIED** — current clustering is bag-of-tools text vectorization followed by KMeans, which mostly drops sequence order.
4. **INCONCLUSIVE** — dependency footprint is "~40MB"; no repository measurement artifact was found.
5. **INCONCLUSIVE** — real workload is "dozens of sessions, not thousands"; no telemetry or benchmark artifact was found.

Sources:

- `plugins/agentskill-kaizen/mcp/server.py`
- https://pypi.org/pypi/scikit-learn/json (retrieved 2026-03-03)
- https://pypi.org/pypi/pyclustering/json (retrieved 2026-03-03)

## RT-ICA

Goal: Produce an evidence-backed keep/replace/defer decision on scikit-learn usage for `cluster_sessions` at the expected workload scale.

Conditions:

1. Current clustering path and API surface are identifiable | Status: AVAILABLE | Info needed: None
2. Current dependency chain is identifiable | Status: AVAILABLE | Info needed: None
3. Clear "dependency weight" decision criteria exist (size/runtime/maintainability) | Status: MISSING | Info needed: explicit evaluation rubric
4. Representative workload profile exists | Status: MISSING | Info needed: sample-size and usage profile
5. Method-quality criteria for sequence similarity are defined | Status: MISSING | Info needed: quality rubric for clustering usefulness

Decision: APPROVED
Missing: Evaluation rubric, representative workload profile, sequence-quality rubric

## Issue Classification

**Type**: unbounded-design
**Rationale**: The item asks for comparative evaluation and method appropriateness without predefined thresholds for dependency budget, workload envelope, or output quality.
**Analysis Method**: design-framing
**Scenario Target**: Evaluate `cluster_sessions` dependency/method fit for small session sets -> provide an explicit keep/replace/defer decision with evidence

## Groomed (2026-03-03)

### Priority

6/10 — Valuable for dependency and method-fit quality, but not a confirmed production incident.

### Impact

- Potentially reduces dependency surface and install/runtime cost for `agentskill-kaizen`.
- Improves confidence that clustering output is meaningful for workflow comparison.

### Expected Behavior

A documented decision exists on whether `cluster_sessions` should keep scikit-learn or adopt a lighter/simpler approach, with explicit tradeoffs for dependency weight, quality of clustering signal, and expected session scale.

### Acceptance Criteria

1. Baseline is documented: current method, dependency chain, and observed clustering behavior.
2. Evaluation criteria are explicit and measurable (dependency footprint, runtime on representative session sets, output interpretability).
3. At least one lighter alternative is comparatively evaluated against the baseline.
4. Final decision records keep/replace/defer with rationale and known risks.
5. Remaining unknowns are captured as follow-up questions.

### Resources

| Type | Item |
|------|------|
| Files | `plugins/agentskill-kaizen/mcp/server.py` |
| Files | `plugins/agentskill-kaizen/tests/test_server.py` |
| Research | https://pypi.org/pypi/scikit-learn/json |
| Research | https://pypi.org/pypi/pyclustering/json |

### Issue Classification

**Type**: unbounded-design
**Rationale**: This is a framing and comparison problem (fitness-for-purpose under constraints), not a single traceable defect.
**Analysis Method**: design-framing
**Scenario Target**: Evaluate clustering approach and dependency weight for small-session workloads -> produce a bounded, evidence-backed direction
