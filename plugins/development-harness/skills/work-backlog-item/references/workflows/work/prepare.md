# Work: Prepare (Phase 3)

Groom if needed, run RT-ICA gate, check feasibility.

## Step 3.1: Auto-Groom (if needed)

**Trigger:** always — runs for both groomed and ungroomed items.

- **Ungroomed** (`groomed` absent or empty): run the grooming workflow via `references/workflows/groom/start.md`.
- **Groomed** (`groomed` = date string): run two-phase staleness check before consuming
  cached content. Phase 1 detects functional commits on Impact Radius files since the groom
  date. Phase 2 classifies drift as FUNCTIONAL_DRIFT (re-groom), SUPERSEDED (close), or
  COSMETIC_ONLY (proceed).

Load [groom-check.md](./groom-check.md) for
staleness detection procedure, groomed-content retrieval, groom skill invocation, and continuation.

## Step 3.2: RT-ICA Gate

**Trigger:** RT-ICA result absent, stale (>7 days), or item updated since last run.

Load [rt-ica-gate.md](./rt-ica-gate.md) for staleness policy, freshness flowchart, and BLOCKED handling.

## Step 3.3: RT-ICA Date Stamp

After `dh:rt-ica` completes (or the existing result is confirmed fresh), write a parseable `Date:` header to the RT-ICA section before storing the result:

```text
RT-ICA Final: {item title}
Date: {YYYY-MM-DD}
Goal: {same as snapshot}
```

The `Date:` header is required for the freshness check in Step 3.2. If the RT-ICA result was retrieved from cache and already contains a `Date:` header, skip this step.

## Step 3.4: Feasibility Gate

**Trigger:** RT-ICA returned APPROVED (Step 3.2) and RT-ICA Date Stamp written (Step 3.3).

Load [feasibility-gate.md](./feasibility-gate.md) and evaluate all 4 criteria (technical feasibility, effort proportionality, blast radius, prior attempt check).

**BLOCKED at feasibility gate stops the workflow** — do not proceed to Phase 4. Report the BLOCKED output contract from the reference file and stop.

**PASS** → proceed to `plan.md` (Step 4.1) with the feasibility assessment appended to the feature request.
