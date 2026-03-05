# Batch Mode Workflow

Processing multiple URLs in parallel via `--batch`.

---

## URL Parsing

Extract URLs from the `--batch` argument. Input format:

```text
/research-curator --batch https://url1.com https://url2.com https://url3.com
```

Parse all tokens after `--batch` that match `https?://` as target URLs. Non-URL tokens are ignored with a warning.

---

## Wave Spawning

The following diagram is the authoritative procedure for batch wave spawning. Execute steps in the exact order shown, including branches, decision points, and stop conditions.

```mermaid
flowchart TD
    Start(["Parse deduplicated URLs from --batch"]) --> Count{"How many URLs remain after duplicate check?"}
    Count -->|"1 to 5 — fits in one wave"| Wave1["Spawn all URLs as Wave 1<br>up to 5 parallel @research-curator agents via Agent tool"]
    Count -->|"6 to 10 — fits in two waves"| W1a["Spawn Wave 1 — first 5 URLs<br>up to 5 parallel @research-curator agents"]
    Count -->|"11 or more — requires three or more waves"| WNa["Spawn Wave 1 — URLs 1 through 5<br>up to 5 parallel @research-curator agents"]
    Wave1 --> Collect["Collect structured results from all agents<br>(status, file path, category, key findings)"]
    W1a --> W1aDone["Wait for all Wave 1 agents to complete"]
    W1aDone --> W2a["Spawn Wave 2 — remaining URLs<br>up to 5 parallel @research-curator agents"]
    W2a --> Collect
    WNa --> WNaDone["Wait for current wave to complete"]
    WNaDone --> QMore{"More URLs remaining?"}
    QMore -->|"Yes — advance to next batch of 5"| WNa
    QMore -->|"No — all URLs processed"| Collect
    Collect --> Results{"Did any agent return status: failed?"}
    Results -->|"No — all succeeded"| README["Update ./research/README.md<br>add all new entries to category tables"]
    Results -->|"Yes — one or more failed"| Partial["Update ./research/README.md<br>with successful entries only<br>Report each failure with reason to user"]
    README --> Finalize(["Lint, commit, push — batch complete"])
    Partial --> Finalize
```

**Wave size**: Maximum 5 concurrent @research-curator agents per wave.

**Sequential waves**: Wait for all agents in current wave to complete before spawning next wave. This prevents overwhelming MCP tool rate limits.

---

## Error Handling

- **Individual failure**: Log the error, continue with remaining URLs. Do not abort the batch.
- **Agent timeout**: If an agent does not return within reasonable time, mark as failed and continue.
- **Duplicate detection**: Before spawning, check if `./research/` already contains an entry for the URL's resource. If found, skip with info message suggesting `--rerun` instead.

---

## Progress Reporting

After each wave completes, report:

```text
Wave N complete: M/N succeeded
  ✓ category/resource-name.md — created
  ✓ category/resource-name.md — created
  ✗ https://failed-url.com — error: [reason]
```

After all waves:

```text
Batch complete: X/Y total succeeded
Files created: [list]
README updated: Yes
```

---

## Post-Batch Actions

These happen ONCE after all waves complete (not per-entry):

1. Update `./research/README.md` with all new entries
2. Run `uv run prek run --files` on README and all new entry files
3. Commit all changes in a single commit
4. Push to current branch
