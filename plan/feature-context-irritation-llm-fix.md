# Feature Context: Irritation LLM Fix

## Document Metadata

- **Generated**: 2026-03-11
- **Input Type**: simple_description
- **Source**: Feature request — fix irritation command false positives by replacing `_CORRECTION_PHRASES` substring matching with LLM judgment
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Fix irritation command false positives in `session_query.py` by replacing `_CORRECTION_PHRASES` substring matching with LLM judgment.

The `irritation` command in `.claude/skills/session-historian/scripts/session_query.py` uses a `_CORRECTION_PHRASES` tuple with bare-token entries ("stop", "undo", "revert", "don't", "no,") and a `if phrase in lower` substring matcher (lines 1046–1050, first match fires). This produces false positives: "don't use tabs", "stop after step 3", "revert to the original approach" all incorrectly trigger the irritation counter.

Replace `_CORRECTION_PHRASES` and the substring matcher with LLM judgment — the same pattern used by the frustration-analyzer plugin's batch-detector (`plugins/frustration-analyzer/agents/frustration-analyst.md`). A Claude API call reads each user message and decides whether it is a genuine correction/frustration signal directed at the AI assistant.

---

## Core Intent Analysis

### WHO (Target Users)

Developers and users running the `irritation` command via the session-historian CLI to audit their Claude Code sessions for genuine friction signals. The fix is internal — end users see the same CLI interface, improved accuracy.

### WHAT (Desired Outcome)

The `irritation` command accurately identifies messages where the user expressed genuine correction or frustration directed at the AI assistant, and does not fire on neutral instructions that happen to contain bare tokens like "stop", "don't", or "revert".

### WHEN (Trigger Conditions)

Any time a user runs `session_query.py irritation [session_id]` on a session that contains messages with words from `_CORRECTION_PHRASES` used in non-irritation contexts (e.g., task instructions, workflow descriptions).

### WHY (Problem Being Solved)

Substring matching on bare tokens produces systematic false positives. "don't use tabs", "stop after step 3", and "revert to the original approach" are neutral workflow instructions — not irritation signals — but the current matcher counts them as irritation. This corrupts the irritation metric, making it unreliable for session analysis.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: `_CORRECTION_PHRASES` substring matcher

- **Location**: `.claude/skills/session-historian/scripts/session_query.py:71–82` (constant definition), `:1046–1050` (matcher loop)
- **Relevance**: This is the exact code being replaced. The constant defines 10 bare tokens; the loop does `if phrase in lower` with first-match-breaks.
- **Reusable**: The surrounding record iteration logic (`_collect_correction_phrases` function, lines ~1028–1051) is preserved — only the inner matching logic changes.

Observed constant (lines 71–82):

```python
_CORRECTION_PHRASES = (
    "that's wrong",
    "no,",
    "stop",
    "undo",
    "revert",
    "don't",
    "not what i asked",
    "wrong",
    "incorrect",
    "that's not",
)
```

Observed matcher (lines 1046–1050):

```python
lower = content.lower()
for phrase in _CORRECTION_PHRASES:
    if phrase in lower:
        results.append((ts, phrase, content[:200]))
        break  # one signal per message is enough
```

#### Pattern 2: `frustration-analyzer` batch-detector LLM judgment

- **Location**: `plugins/frustration-analyzer/agents/batch-detector.md`
- **Relevance**: This agent is the reference implementation for LLM-based frustration detection. It uses semantic criteria — not substring matching — to decide whether a user message contains a strong emotional reaction aimed at the AI assistant.
- **Reusable**: The detection criteria defined in `batch-detector.md` lines 20–50 directly model what the new LLM call should evaluate. The distinction between flagged patterns (accusations of not listening, escalated corrections, sarcasm aimed at the assistant) and non-flagged patterns (neutral corrections, mild disappointment) maps exactly to this feature's requirements.

Key detection criteria from `batch-detector.md`:

Flag: accusations of not listening, escalated corrections (elevated tone or repeated emphasis), sarcasm aimed at assistant, arguments with the assistant.

Do not flag: neutral corrections ("please try again"), questions without emotional charge, self-directed frustration, mild disappointment without escalation.

#### Pattern 3: `cmd_irritation` output shape

- **Location**: `.claude/skills/session-historian/scripts/session_query.py:1106–1159`
- **Relevance**: The command's output format (count + examples, with `--raw` tab-separated mode) must be preserved. The `phrases` list returned by `_collect_correction_phrases` is a `list[tuple[str, str, str]]` — `(timestamp, matched_phrase, excerpt)`. The LLM replacement must return the same shape.
- **Reusable**: Output rendering code (lines 1146–1159+) requires no changes.

### Existing Infrastructure

- `session_query.py` is a standalone script with PEP 723 inline metadata — it uses `uv run` and declares its own dependencies. Any `anthropic` SDK usage must be added to its inline `dependencies` block.
- The `_collect_correction_phrases` function (lines ~1028–1051) handles record filtering (skip non-user records, skip noise records) before reaching the matching logic. This filtering stays intact.
- The `_is_noise` function and `_extract_text` function at lines ~87+ handle pre-processing of records before they reach the matcher.
- Backlog item #607 covers tests for session-historian — this change must be communicated to that item.

### Code References

- `.claude/skills/session-historian/scripts/session_query.py:71–82` — `_CORRECTION_PHRASES` constant (to be removed)
- `.claude/skills/session-historian/scripts/session_query.py:1028–1051` — `_collect_correction_phrases` function (inner loop to be replaced)
- `.claude/skills/session-historian/scripts/session_query.py:1046–1050` — substring matcher (to be replaced with LLM call)
- `.claude/skills/session-historian/scripts/session_query.py:1106–1159` — `cmd_irritation` command (output shape preserved)
- `plugins/frustration-analyzer/agents/batch-detector.md:20–50` — reference detection criteria for LLM prompt

---

## Use Scenarios

### Scenario 1: Neutral instruction containing "stop"

**Actor**: Developer running session audit
**Trigger**: Session contains "stop after step 3, don't proceed further"
**Goal**: This message should NOT appear in irritation output
**Expected Outcome**: LLM identifies the message as a workflow instruction, not frustration. Irritation count unchanged.

### Scenario 2: Genuine correction with escalation

**Actor**: Developer running session audit
**Trigger**: Session contains "that's wrong, you keep doing the same thing, I've said this three times"
**Goal**: This message SHOULD appear in irritation output
**Expected Outcome**: LLM identifies escalated correction aimed at assistant. Count increments, excerpt included.

### Scenario 3: Bare "wrong" in non-irritation context

**Actor**: Developer reviewing a coding session
**Trigger**: Session contains "revert to the original approach, the new one is wrong"
**Goal**: This message should NOT fire as irritation
**Expected Outcome**: LLM identifies a neutral preference statement, not directed frustration at the assistant.

### Scenario 4: Raw output mode preserved

**Actor**: Script or automation consuming `session_query.py irritation --raw`
**Trigger**: Post-fix run of irritation command in raw mode
**Goal**: Tab-separated output format unchanged
**Expected Outcome**: Lines still follow `phrase\t<ts>\t<phrase>\t<excerpt>` format. The `<phrase>` field will now be an LLM-derived label or empty string — downstream consumers must tolerate this.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | What string goes in the `phrase` field of the output tuple when LLM detects irritation? The current output is the matched phrase token (e.g., "stop"). With LLM, no phrase was matched. | `--raw` output consumers and display code reference the phrase field. If empty or changed, callers may break. |
| 2 | Behavior | Per-message API calls vs batching — each message in the session triggers a call, or messages are batched into one call? | Cost, latency, and rate-limit behavior differ significantly. |
| 3 | Scope | `_CORRECTION_PHRASES` is also referenced in the docstring of `cmd_irritation` (line 1115–1116). Should this docstring be updated? | Minor but the docstring will be stale if the constant is removed. |
| 4 | Integration | Backlog item #607 (tests) must be informed of this change. Is this a blocker — must tests be updated before or after the fix? | If tests assert on specific phrase tokens in output, they will fail after the change. |
| 5 | Behavior | What happens when the Anthropic API is unavailable or rate-limited? Should the command fail fast, fall back to substring matching, or return an empty result with an error message? | Silent degradation vs loud failure. Debugging Protocol forbids silent fallback without explicit approval. |
| 6 | Scope | `_CORRECTION_PHRASES` is defined at module level (line 71). If removed entirely, any other callers in the file would break. Verified: only `_collect_correction_phrases` uses it. But the `pyproject.toml` or inline PEP 723 metadata may not include `anthropic` yet. | Dependency addition required. |

---

## Questions Requiring Resolution

### Q1: Output tuple `phrase` field with LLM detection

- **Category**: Behavior
- **Gap**: When LLM detects irritation, the current `(timestamp, matched_phrase, excerpt)` tuple requires a `matched_phrase`. There is no matched phrase — the LLM made a holistic judgment.
- **Question**: What value should populate the `phrase` field in the output when LLM flags a message? Options: (A) a fixed label like `"llm-detected"`, (B) an LLM-generated short label summarizing the signal, (C) empty string `""`, (D) the first few words of the message.
- **Options**:
  - A) Fixed label `"llm-detected"` — backward-compatible, machine-parseable
  - B) LLM-generated label — more descriptive, variable length, higher token cost
  - C) Empty string — minimal change, may confuse `--raw` consumers
  - D) First N words of message — approximates old behavior without accuracy
- **Why It Matters**: The `--raw` output format uses this field as the second tab-separated column. Downstream scripts parsing raw output depend on this field being non-empty and stable.
- **Resolution**: _pending_

### Q2: Per-message calls vs batching

- **Category**: Behavior
- **Gap**: Sessions can have hundreds of user messages. Calling the Anthropic API once per message is expensive and slow. Batching all messages in one call is faster but requires a different prompt structure.
- **Question**: Should the LLM call be (A) one call per message, (B) one batch call with all user messages, or (C) chunked batches (e.g., 20 messages per call)?
- **Options**:
  - A) Per-message — simple prompt, high latency and cost on long sessions
  - B) Single batch call — one prompt with all messages, lower cost, requires structured JSON response
  - C) Chunked batches — balanced, most complex to implement
- **Why It Matters**: A long session with 200 user messages would make 200 API calls at ~$0.003 each = $0.60 per irritation query. Unacceptable for routine use.
- **Resolution**: _pending_

### Q3: API unavailability behavior

- **Category**: Behavior
- **Gap**: The Debugging Protocol prohibits silent fallback to substring matching without explicit approval. But the command must do something if the API is unavailable.
- **Question**: When the Anthropic API call fails (network error, rate limit, auth failure), should the command (A) fail loud with a clear error message and non-zero exit code, (B) warn and return empty phrase results (loops still work), or (C) fall back to substring matching with a visible warning?
- **Options**:
  - A) Fail loud — consistent with Debugging Protocol, no silent degradation
  - B) Warn + empty — partial results, loops still surface, but phrase signals silently absent
  - C) Fallback with warning — preserves old behavior under failure, labeled as fallback
- **Why It Matters**: Silent failures are prohibited. Option A is the Debugging Protocol default; C requires explicit user approval per the protocol.
- **Resolution**: _pending_

### Q4: Backlog item #607 sequencing

- **Category**: Integration
- **Gap**: Backlog item #607 covers tests for session-historian. If existing tests assert on specific matched phrase tokens, they will fail after this change.
- **Question**: Should tests in #607 be updated as part of this feature, before it, or after it? Should this feature create a sub-task on #607?
- **Options**:
  - A) Update tests as part of this feature — keeps tests green, adds LLM mock
  - B) Update tests after this feature — acceptable if #607 has no current passing tests on irritation
  - C) Block this feature on #607 — only if tests currently cover irritation
- **Why It Matters**: If tests pass now and this change breaks them without an update, CI fails.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Remove `_CORRECTION_PHRASES` constant from `session_query.py`.
2. Replace the substring matcher in `_collect_correction_phrases` with a Claude API call that evaluates each user message for genuine AI-directed correction or frustration.
3. LLM detection criteria match the semantics documented in `plugins/frustration-analyzer/agents/batch-detector.md` — flag escalated corrections, accusations, sarcasm aimed at assistant; do not flag neutral instructions or self-directed frustration.
4. False positives ("don't use tabs", "stop after step 3", "revert to the original approach") no longer trigger irritation.
5. True positives ("that's wrong", "not what i asked", "this is broken", "you're not listening") continue to trigger irritation.
6. Output shape `(timestamp, phrase_field, excerpt)` preserved — `phrase_field` value determined by Q1 resolution.
7. `--raw` tab-separated output format preserved.
8. API failure handling per Q3 resolution.
9. `anthropic` SDK added to `session_query.py` PEP 723 inline dependencies.
10. Backlog item #607 notified or updated per Q4 resolution.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section above.
2. Finalize Goals section with concrete behavior specs.
3. Proceed to RT-ICA assessment.
4. Then proceed to architecture design via `python-cli-design-spec` agent.
