---
description: Rules for orchestrators handling sub-agent results without lossy re-summarization. Activates when receiving agent output, relaying research results, passing data between agents, or combining agent findings. Prevents the failure mode where 'not found' becomes 'doesn't exist' and counts get dropped.
---
# Agent Result Relay

Rules for how orchestrators MUST handle sub-agent results to prevent information corruption in the relay chain.

## The Problem

When an orchestrator receives results from a sub-agent, three failure modes commonly corrupt information:

**Failure 1: Lossy Re-Summarization**

```text
Agent output:  "Found 7 items with details. 3 sources returned HTTP 403."
Orchestrator:  "Research complete. Found some items, the rest don't exist."
                                                    ^^^ CORRUPTED
```

**Failure 2: Count Dropping**

```text
Agent output:  "Analyzed 15 files: 12 pass validation, 2 have warnings, 1 has errors."
Orchestrator:  "Most files pass validation."
                ^^^ COUNTS LOST
```

**Failure 3: Status Escalation**

```text
Agent output:  "Unable to access 3 URLs (connection timeout)."
Orchestrator:  "3 URLs are not available."
               ^^^ "UNABLE TO ACCESS" ≠ "NOT AVAILABLE"
```

## Relay Rules

### Rule 1: Preserve Exact Counts

When an agent reports numbers, the orchestrator MUST relay those exact numbers.

| Agent Says | Orchestrator MUST Say | Orchestrator MUST NOT Say |
|------------|----------------------|--------------------------|
| "7 of 10 found" | "7 of 10 found" | "most found" |
| "3 errors, 2 warnings" | "3 errors, 2 warnings" | "several issues" |
| "12 files analyzed" | "12 files analyzed" | "files were analyzed" |
| "0 results" | "0 results found" | "nothing relevant" |

### Rule 2: Preserve Failure Reasons

When an agent reports failures, the orchestrator MUST relay the specific reason.

| Agent Says | Orchestrator MUST Say | Orchestrator MUST NOT Say |
|------------|----------------------|--------------------------|
| "HTTP 403 Forbidden" | "access denied (HTTP 403)" | "not available" |
| "Connection timeout" | "connection timed out" | "doesn't exist" |
| "File not found at path X" | "file not found at X" | "no such file" |
| "Rate limited, try later" | "rate limited" | "unavailable" |
| "3 sources not accessible" | "3 sources not accessible" | "3 sources don't exist" |

### Rule 3: Reference Files Instead of Re-Summarizing

When an agent wrote detailed results to a file, the orchestrator MUST reference the file rather than re-summarizing it.

**Required pattern**:

```text
Research complete. 7 of 10 items documented. 3 sources were inaccessible (connection timeout).
Full results: ./research-output.md
```

**Prohibited pattern**:

```text
Research complete. Here's a summary of the summary:
- Item 1 was about X
- Item 2 was about Y
[lossy re-interpretation of agent's already-summarized output]
```

### Rule 4: Relay Structure, Not Interpretation

When an agent returns structured output (STATUS, SUMMARY, ARTIFACTS, etc.), the orchestrator MUST preserve that structure.

**Agent returns**:

```text
STATUS: DONE
SUMMARY: Validated 15 plugins. 12 pass, 2 warnings, 1 critical error.
ARTIFACTS:
  - Report: ./validation-report.md
  - Critical: plugin-X has invalid manifest
WARNINGS:
  - plugin-Y: description exceeds 200 chars
  - plugin-Z: missing homepage field
```

**Orchestrator MUST relay**:

```text
Plugin validation complete. 12 of 15 pass, 2 warnings, 1 critical error.
Critical: plugin-X has invalid manifest.
Full report: ./validation-report.md
```

**Orchestrator MUST NOT relay**:

```text
Validation done. Most plugins are fine, a couple have minor issues.
```

### Rule 5: Distinguish Agent Conclusions from Agent Observations

When an agent reports both observations and conclusions, the orchestrator MUST clearly distinguish between them.

**Agent reports**:

```text
Observation: The config file does not contain a "timeout" field.
Conclusion: Using default timeout of 30s.
```

**Orchestrator relays**:

```text
Config has no "timeout" field; agent reports default of 30s will be used.
```

**Not**:

```text
Timeout is 30 seconds.
```

The distinction matters because the observation (no field) is verifiable, while the conclusion (default 30s) is the agent's interpretation.

## When to Summarize vs When to Relay

The orchestrator MAY summarize agent output ONLY when:

1. The user explicitly asked for a summary ("give me a quick overview")
2. Multiple agents returned results and the user needs a combined view
3. The agent output exceeds what the user needs for their immediate decision

Even when summarizing is appropriate, the orchestrator MUST:

- Preserve all counts
- Preserve all failure reasons
- Reference the full output file
- Not upgrade absence to nonexistence
- Include the "What Was NOT Found" category

## Checklist for Orchestrators

Before relaying agent results, verify:

- [ ] All numbers from agent output are preserved in relay
- [ ] All failure reasons are preserved (not generalized)
- [ ] File references are included if agent wrote output files
- [ ] "Not found" has not been upgraded to "doesn't exist"
- [ ] "Inaccessible" has not been upgraded to "unavailable" or "nonexistent"
- [ ] Structured sections (STATUS, ARTIFACTS, WARNINGS) are preserved
- [ ] Agent observations are distinguished from agent conclusions
