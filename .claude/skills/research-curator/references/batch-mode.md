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

```mermaid
flowchart TD
    Start([Parse URLs from --batch]) --> Count{How many URLs?}
    Count -->|1-5| Wave1[Spawn all as Wave 1 — up to 5 parallel @research-curator agents]
    Count -->|6-10| Split1[Wave 1: first 5 URLs<br>Wave 2: remaining URLs]
    Count -->|11+| SplitN[Wave 1: URLs 1-5<br>Wave 2: URLs 6-10<br>Wave N: remaining]
    Wave1 --> Collect[Collect results from all agents]
    Split1 --> W1[Execute Wave 1]
    W1 --> W1Done[Wait for Wave 1 completion]
    W1Done --> W2[Execute Wave 2]
    W2 --> Collect
    SplitN --> WN[Execute waves sequentially, 5 agents per wave]
    WN --> Collect
    Collect --> Results{Any failures?}
    Results -->|All succeeded| README[Update README with all new entries]
    Results -->|Some failed| Partial[Update README with successful entries<br>Report failures to user]
    README --> Finalize[Lint, commit, push]
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
