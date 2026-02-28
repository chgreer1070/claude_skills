---
name: verify
description: Rigorous self-assessment checklist before marking any task as complete. Use when about to claim task completion, before final commit, when user asks "is it done?", or when transitioning from implementation to reporting. Prevents premature completion claims by requiring evidence for every assertion.
user-invocable: true
---
# Verification Protocol

**Workflow Reference**: See [Master Workflow](./../../knowledge/workflow-diagrams/master-workflow.md) for how this skill fits into the verification stage of the agentic workflow.

**STOP.** You are NOT done yet. Generate this checklist and provide **EVIDENCE** for every item.

---

## 1. Task Type & Strategy

- [ ] **Type:** FIX / FEATURE / REFACTOR / DOCS / INVESTIGATION
- [ ] **Strategy:** Executable verification vs. Static verification?

---

## 2. The "WORKS" Check

<!-- Converted from prose branch instruction: "Choose A or B based on task type" -->

```mermaid
flowchart TD
    Start(["Begin WORKS Check -- Section 2"]) --> Q{"Task type?"}
    Q -->|"Executable code -- compiled, scripted, or CLI-run"| A1["Execution check<br>Terminal output showing successful run<br>(exit code 0 is NOT enough)"]
    Q -->|"Static asset -- docs, configs, analysis"| B1["Accuracy check<br>Verified against source code or schema?"]
    A1 --> A2["Real data check<br>Ran changed code path against real data<br>not just read the diff?"]
    A2 --> A3["Regression check<br>Evidence that existing tests still pass?"]
    A3 --> A4["Edge case check<br>Evidence of testing failure scenarios?"]
    A4 --> AEvidence["Record code evidence<br>execution output, real data test,<br>test results, edge case result"]
    B1 --> B2["Clarity check<br>Follows the established format?"]
    B2 --> B3["Validity check<br>Links and references resolve?"]
    B3 --> BEvidence["Record static evidence<br>accuracy check method,<br>format standard, link validation method"]
    AEvidence --> Done(["WORKS Check complete -- proceed to Section 3"])
    BEvidence --> Done
```

### A. For Code (Executable)

- [ ] **Execution:** Terminal output showing successful run? (Exit code 0 is NOT enough)
- [ ] **Real data:** Ran the changed code path against real data, not just read the diff?
- [ ] **Regression:** Evidence that existing tests still pass?
- [ ] **Edge Cases:** Evidence of testing failure scenarios?

```text
EVIDENCE:
- Execution output: [paste actual output]
- Real data test: [command run, input used, output observed]
- Test results: [paste test output]
- Edge case tested: [describe scenario and result]
```

### B. For Static Assets (Docs, Configs, Analysis)

- [ ] **Accuracy:** Verified against source code/schema?
- [ ] **Clarity:** Does it follow the established format?
- [ ] **Validity:** Do links/references resolve?

```text
EVIDENCE:
- Accuracy check: [how verified]
- Format compliance: [standard followed]
- Links validated: [method used]
```

---

## 3. The "FIXED" Check

For bug fixes specifically:

- [ ] **Reproduction:** Did I observe the pre-fix state?
- [ ] **Resolution:** Does the original problem NO LONGER occur?

```text
EVIDENCE:
- Pre-fix behavior: [what was observed]
- Post-fix behavior: [what is now observed]
- Regression test added: [yes/no, location]
```

---

## 4. Quality Gates

- [ ] Pre-commit hooks passed?
- [ ] Linting passed? (Necessary, but not sufficient)
- [ ] Type checking passed? (if applicable)

```text
EVIDENCE:
- Pre-commit: [output or "not configured"]
- Linting: [tool and result]
- Type check: [tool and result]
```

---

## 5. Honesty Check

- [ ] Did I verify the _full scope_?
- [ ] Am I distinguishing between "should work" and "verified to work"?
- [ ] **Destination check:** Did I read the target state after writing? (Tool output claiming success is not evidence — the state of the destination is.)
- [ ] Can I answer YES to: "I have VALIDATED this output in its intended context"?

---

## The Golden Rule

**If you cannot demonstrate it working in practice with evidence, it is NOT done.**

| Claim           | Required Evidence                                        |
| --------------- | -------------------------------------------------------- |
| "Code works"    | Terminal output showing execution against real data      |
| "Tests pass"    | Actual test output, not assumption                       |
| "Bug fixed"     | Before/after comparison                                  |
| "Data synced"   | Read the destination after writing — not the tool output |
| "Docs accurate" | Cross-reference with source                              |
| "Config valid"  | Validation command output                                |

---

## Quick Reference

```text
VERIFICATION SUMMARY:
Task Type: [FIX/FEATURE/REFACTOR/DOCS/INVESTIGATION]
Works Check: [PASS/FAIL] - Evidence: ___
Fixed Check: [PASS/FAIL/N/A] - Evidence: ___
Quality Gates: [PASS/FAIL] - Evidence: ___
Honesty Check: [PASS/FAIL]

VERDICT: [COMPLETE / NOT COMPLETE - reason]
```
