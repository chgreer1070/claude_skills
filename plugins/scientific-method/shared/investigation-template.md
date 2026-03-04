# Unified Investigation Template

All investigation workflows produce outputs using this template. Sections 0–7 are filled before
execution. Sections 8–14 are filled during and after execution.

---

## 0 CONTEXT

```text
Goal:
System/Component:
Environment:
Baseline commit/build:
```

---

## 1 ISSUE STATEMENT

```text
Symptom:
Expected behavior:
Actual behavior:
Repro status: (reproduced | not reproduced | unknown)
Repro steps:
```

---

## 2 OBSERVATIONS

```text
O1:
  Snippet:
  Truncation: (none | TRUNCATED: total=<N>, shown=<M>, method=<head|tail|grep>)
  Evidence: [E#]

O2:
  Snippet:
  Evidence: [E#]
```

Rules:

- Raw signals only — no interpretation
- Prefer verbatim snippets over paraphrase
- Disclose truncation with total/shown counts and fingerprint

---

## 3 FACTS

```text
F1: Statement supported by evidence [E#]
F2: Statement supported by evidence [E#]
```

Rules:

- Must cite Evidence IDs
- No assumptions — only directly known items

---

## 4 HYPOTHESES

```text
H0 (Null): System behaves correctly; issue is external or environmental.

H1 (Alternative): [Specific causal mechanism]
```

Rules:

- Must be falsifiable
- Must reference facts
- State as: "If H1 is true, we would observe X"

---

## 5 PREDICTIONS

```text
If H1 is correct we should observe:

P1: [specific observable outcome]
P2: [specific observable outcome]
```

---

## 6 EXPERIMENT PLAN

```text
Path A:
  Test:
  Expected if H1:
  Expected if H0:

Path B:
  Test:
  Expected if H1:
  Expected if H0:
```

---

## 7 CONFOUNDING VARIABLES

```text
Possible confounds:
  - [caching, env vars, stale state, etc.]

Isolation plan:
  - [how each confound is controlled]
```

---

## 8 ACTIONS

```text
A1:
  Command/change:
  Location:
  Purpose:
  Evidence: [E#]
```

---

## 9 RESULTS

```text
R1:
  Observed outcome:
  Evidence: [E#]
```

---

## 10 CAUSALITY CHECK

See [causality-check.md](./causality-check.md) for classification rules.

```text
Link L1:
  Action: A#
  Result: R#
  Classification: (causal-supported | correlated-only | unrelated | unknown)
  Reason: (must reference evidence, not intuition)
  Falsification test:
```

---

## 11 CONCLUSION

```text
Decision: Reject H0 | Fail to Reject H0

Evidence: [cite E# items supporting decision]

Next step:
```

---

## 12 CHANGES

```text
Diff summary: <N> files, <N> insertions, <N> deletions [E#]

Key hunk:
  File:
  Before:
  After:
  Purpose:
```

---

## 13 VERIFICATION

```text
Verification command:
Result summary:
Evidence: [E#]
```

---

## 14 STATUS

Choose exactly one:

```text
status: unresolved
status: mitigated
status: resolved-verified
status: unknown
```

If `resolved-verified` — MUST include sections 13 (Verification) with evidence.
