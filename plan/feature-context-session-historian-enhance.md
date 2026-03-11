# Feature Context: Session Historian — Four New Query Commands

## Document Metadata

- **Generated**: 2026-03-11
- **Input Type**: simple_description
- **Source**: Feature request — enhance session_query.py with `errors`, `tools`, `irritation`, `current-path` commands
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Enhance session_query.py (at `.claude/skills/session-historian/scripts/session_query.py`) with four new query commands:

1. `errors` — query sessions for tool errors (JSONL records where `message.content[].is_error: true`)
2. `tools` — list tools used in a session with counts and success/failure breakdown
3. `irritation` — detect user irritation signals: correction phrases in user messages + repeated identical tool calls (stuck loops)
4. `current-path` — resolve and return the current session's JSONL file path to the agent (using `CLAUDE_SESSION_ID` env var + `~/.claude/projects/<encoded-cwd>/` path pattern; report clearly when not found)

Constraints:
- Use direct Python file I/O / JSONL parsing (NOT Agent SDK as primary mechanism)
- Build on existing session_query.py infrastructure: `_iter_records()`, `_extract_text()`, `_is_noise()`, DuckDB index, Rich/raw output
- No new external dependencies beyond what session_query.py already uses

Key files:
- `.claude/skills/session-historian/scripts/session_query.py`
- `.claude/skills/session-historian/SKILL.md`

---

## Core Intent Analysis

### WHO (Target Users)

Claude Code agents (orchestrators and subagents) that need to introspect the current or past session's error rate, tool usage patterns, and conversation health signals. The `current-path` command is specifically agent-facing — it resolves the live session file for real-time analysis.

### WHAT (Desired Outcome)

Four new Typer commands added to the existing `session_query.py` CLI that expose four distinct views of JSONL session data:

1. A filtered view of tool error records from a session
2. A per-tool usage count table with success vs. failure columns
3. A heuristic analysis of user frustration signals (phrase-based + stuck-loop detection)
4. A path resolver that maps the live `CLAUDE_SESSION_ID` to a filesystem path and returns it

### WHEN (Trigger Conditions)

- `errors`: After a session with suspected tool failures; during debugging of agent behavior
- `tools`: When reviewing what tools an agent used and whether they succeeded
- `irritation`: During post-session retrospectives; as a quality signal for agent behavior audits
- `current-path`: When an agent (running inside a session) needs to point another tool at the live JSONL file for real-time analysis — called programmatically, not interactively

### WHY (Problem Being Solved)

The existing commands (`list`, `messages`, `search`, `show`) provide content retrieval but no behavioral analysis. The new commands expose:

- Error density (are tool failures concentrated in a session?)
- Tool diversity and failure rate (what broke and how often?)
- Interaction quality signals (is the user correcting the agent repeatedly?)
- Self-awareness for live sessions (can the agent find its own transcript?)

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: `_iter_records()` — JSONL parsing foundation

- **Location**: `.claude/skills/session-historian/scripts/session_query.py:108-130`
- **Relevance**: All four new commands parse JSONL records. This function is the shared entry point. It returns `list[dict]` of all valid records from a given path.
- **Reusable**: Directly. All new commands iterate records from this function.

#### Pattern 2: `_scan_records()` — per-record dispatch loop

- **Location**: `.claude/skills/session-historian/scripts/session_query.py:238-276`
- **Relevance**: Shows the established pattern for inspecting `rec.get("type")`, `rec.get("message", {}).get("content")`, and timestamps. The `errors` and `tools` commands follow this same dispatch structure.
- **Reusable**: The loop body pattern is directly reusable; `_scan_records` itself is not called by new commands (they need different extraction logic).

#### Pattern 3: `cmd_messages()` — session-ID-to-file lookup via DuckDB

- **Location**: `.claude/skills/session-historian/scripts/session_query.py:498-549`
- **Relevance**: Shows how to look up a session by ID prefix from the DuckDB index (`file_path` column in `sessions` table), then parse the referenced JSONL file. The `errors`, `tools`, and `irritation` commands need the same lookup.
- **Reusable**: The `session_id == "last"` branch, the `LIKE ?` query pattern, and the `file_path` retrieval logic are all directly reusable.

#### Pattern 4: `cmd_show()` — Rich table + raw output pattern

- **Location**: `.claude/skills/session-historian/scripts/session_query.py:652-709`
- **Relevance**: Shows how commands emit either Rich-formatted output (default) or plain text (`--raw`). The `tools` command especially needs a table; `errors` and `irritation` follow the same output pattern.
- **Reusable**: The `--raw` flag pattern, `stdout.print()` vs `print()` branching, and Rich `Table` construction.

#### Pattern 5: JSONL schema — tool use records

- **Location**: `.claude/skills/session-historian/SKILL.md:129-139`
- **Relevance**: Documents that tool use blocks appear inside `message.content` as `{type: "tool_use", ...}` blocks in assistant records. Tool results appear as records with `toolUseResult` key. The `tools` and `errors` commands must inspect these structures.
- **Reusable**: The `toolUseResult` skip pattern from `_scan_records` (line 259) is the inverse of what `errors` needs.

### Existing Infrastructure

**DuckDB index** (`~/.claude/kaizen/session-index.duckdb`): Contains `sessions` table with `file_path` and `session_id` columns. New commands that accept a session ID argument use the same `SELECT file_path FROM sessions WHERE session_id LIKE ?` lookup pattern established in `cmd_messages()`.

**Dependencies already declared** (PEP 723 inline metadata, lines 3-8): `duckdb>=1.0.0`, `typer>=0.21.0`. Rich is imported as a transitive dependency of typer. No new dependencies needed for any of the four commands.

**`PROJECTS_DIR`** (`~/.claude/projects`): The filesystem root where all session files live, in subdirectories named by the encoded CWD slug. The `current-path` command derives its lookup path from this constant plus the `CLAUDE_SESSION_ID` env var.

### Code References

- `.claude/skills/session-historian/scripts/session_query.py:49-51` — `PROJECTS_DIR`, `CACHE_DIR`, `DB_PATH` path constants
- `.claude/skills/session-historian/scripts/session_query.py:108-130` — `_iter_records()` JSONL parser
- `.claude/skills/session-historian/scripts/session_query.py:58-65` — `_NOISE_PREFIXES` — user messages starting with these are skip targets
- `.claude/skills/session-historian/scripts/session_query.py:259` — `"toolUseResult" not in rec` guard — records WITH this key are tool results, not user messages
- `.claude/skills/session-historian/scripts/session_query.py:279-338` — `_index_file()` — shows DuckDB upsert pattern; not called by new commands but shows session_id = `path.stem`
- `.claude/skills/session-historian/SKILL.md:133-139` — JSONL schema: `type: "tool_use"` inside `message.content`, `toolUseResult` key marks tool result records

---

## Use Scenarios

### Scenario 1: Agent debugs a session with suspected stuck loops

**Actor**: Orchestrator agent, post-task
**Trigger**: Agent suspects it ran the same tool repeatedly without progress
**Goal**: Confirm whether a specific session contains repeated identical tool calls
**Expected Outcome**: `irritation <session-id>` returns a report listing: correction phrases found in user messages (with timestamps), and any tool calls repeated 3+ times consecutively (with the tool name and repeat count)

### Scenario 2: Agent queries its own live session file

**Actor**: Orchestrator agent, mid-session
**Trigger**: User asks "how many errors have occurred in this session so far?"
**Goal**: Agent needs the path to the current JSONL file to pass to `errors` or read directly
**Expected Outcome**: `current-path` prints the absolute path to the live JSONL file, or prints a clear "not found" message with the session ID and searched path

### Scenario 3: Post-session tool usage review

**Actor**: Developer reviewing a session retrospectively
**Trigger**: Wants to understand which tools were called and how often they failed
**Goal**: See a breakdown of tool names, call counts, and success/failure counts
**Expected Outcome**: `tools <session-id>` prints a Rich table with columns: Tool Name, Total Calls, Successes, Failures — sorted by total calls descending

### Scenario 4: Quality audit for tool errors in a project

**Actor**: Developer or agent performing a session quality audit
**Trigger**: Investigating whether a particular session had elevated error rates
**Goal**: List all tool error records from a session with timestamps and error content
**Expected Outcome**: `errors <session-id>` lists each error record with timestamp, tool name (if detectable), and the error content — supports `--raw` output for piping

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | `is_error` field location is not documented in SKILL.md JSONL schema. The request says `message.content[].is_error: true` but this needs verification against actual JSONL records. | `errors` command may use wrong field path if schema differs |
| 2 | Behavior | `irritation` correction phrases — the specific phrases to detect are not listed in the request (e.g., "no", "wrong", "that's not what I", "stop"). The command needs a phrase list. | Command behavior undefined without a curated phrase list |
| 3 | Behavior | `irritation` stuck-loop threshold — what count of repeated identical tool calls constitutes a "stuck loop"? Request says "repeated identical" but gives no count threshold. | Threshold affects false positive rate |
| 4 | Scope | `tools` command — "identical tool call" identity definition: same tool name only, or same tool name + same input? | Affects stuck-loop detection in `irritation` |
| 5 | Integration | `current-path` — the encoded-CWD directory name format: does it match the `project_slug` in `sessions` table, or is it derived independently? The slug format uses hyphens to encode `/home/user/repos/project` as `home-user-repos-project`. | Determines whether DuckDB can assist or pure filesystem glob is needed |
| 6 | User | `current-path` — is the output intended for agent consumption (raw path only, no formatting) or human display? | Affects whether `--raw` flag is needed or whether raw-by-default is correct |
| 7 | Scope | `errors` and `tools` — should they require `session_id` as a mandatory argument, or support `last` like `messages`/`show` do? | Consistency with existing command API |

---

## Questions Requiring Resolution

### Q1: `is_error` field path in JSONL records

- **Category**: Behavior
- **Gap**: The request states `message.content[].is_error: true` but the SKILL.md JSONL schema does not document this field. Tool error records may use a different structure (e.g., `toolUseResult` records with an error flag, or `type: "tool_result"` with `is_error` as a top-level content block field).
- **Question**: Can you confirm the exact JSON path for tool errors? Is it `record["message"]["content"][N]["is_error"]`, or is it in the `toolUseResult` key, or somewhere else? A sample JSON snippet would resolve this.
- **Options**:
  - A) `message.content[N].is_error: true` (as stated in request)
  - B) Records with `toolUseResult` key where `toolUseResult.is_error: true`
  - C) Both A and B apply to different record types
- **Why It Matters**: The `errors` command iterates the wrong field path if this is wrong, producing zero results silently.
- **Resolution**: _pending_

### Q2: Irritation phrase list

- **Category**: Behavior
- **Gap**: No phrase list is specified for correction-phrase detection.
- **Question**: Should the phrase list be hard-coded in the script (if so, provide the list), or should it be a configurable parameter (e.g., `--phrases` option or a config file)?
- **Options**:
  - A) Hard-code a default list (e.g., "no,", "wrong", "that's not", "stop", "you already", "I said", "not what I asked", "undo") — user can extend later
  - B) Accept `--phrases` argument with defaults
- **Why It Matters**: Without a phrase list the command cannot be implemented.
- **Resolution**: _pending_

### Q3: Stuck-loop threshold for irritation detection

- **Category**: Behavior
- **Gap**: "Repeated identical tool calls" — no count threshold given.
- **Question**: At what consecutive repeat count does a tool call sequence become a "stuck loop"? And is "identical" defined as same tool name only, or same tool name + same input arguments?
- **Options**:
  - A) 3+ consecutive calls to the same tool name = stuck loop; identity = tool name only
  - B) 3+ calls to same tool name + same input hash = stuck loop
  - C) Different threshold (specify)
- **Why It Matters**: A threshold of 2 produces many false positives; threshold of 5 misses real loops.
- **Resolution**: _pending_

### Q4: `current-path` output mode

- **Category**: User
- **Gap**: Unclear whether output should be agent-consumption-optimized (raw path only, no color) or human-friendly (Rich formatting with context).
- **Question**: Should `current-path` default to raw path output (just the absolute path string, nothing else), or should it use Rich formatting like other commands?
- **Options**:
  - A) Raw by default (no Rich, just the path on stdout) — optimal for agent piping
  - B) Rich formatted with context, `--raw` flag available
- **Why It Matters**: If agents parse the output for the path, Rich markup will break the parse.
- **Resolution**: _pending_

### Q5: `last` shorthand and session ID argument style

- **Category**: Integration
- **Gap**: Existing commands `messages` and `show` support `last` as a session ID. It's not stated whether new commands should follow the same convention.
- **Question**: Should `errors`, `tools`, and `irritation` all support `last` as a session ID shorthand (matching the existing API convention)?
- **Options**:
  - A) Yes — all session-ID-accepting commands support `last`
  - B) Only some commands need it (specify which)
- **Why It Matters**: Consistency with the existing CLI API.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Add `errors` command that reads a session's JSONL file (via DuckDB path lookup or direct path), iterates records, and returns those where `message.content[].is_error` is true — with timestamp, tool name, and error content.
2. Add `tools` command that iterates all assistant records in a session, extracts `type: "tool_use"` blocks, correlates with subsequent tool result records, and emits a per-tool usage table (name, total calls, successes, failures) in Rich table or raw format.
3. Add `irritation` command that scans user messages for correction phrases and scans assistant records for repeated consecutive identical tool calls — emitting a structured report of detected signals.
4. Add `current-path` command that reads `CLAUDE_SESSION_ID` from environment, maps it to a filesystem path under `~/.claude/projects/`, and returns the path (or a clear not-found message with diagnostics).
5. All new commands reuse `_iter_records()`, `_open_db()`, `_extract_text()`, and the existing `session_id LIKE ?` DuckDB lookup pattern.
6. No new `pyproject.toml` dependencies introduced — all four commands use only `duckdb`, `typer`, `rich`, `pathlib`, `os`, `re`, and `json` (all already present).

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design (`python-cli-design-spec` agent)

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-11_

### Design Refinements

1. **All gaps resolved by architect spec**: The five open questions in the Gap Analysis section were resolved during architecture design rather than needing user input. The resolutions: `is_error` field is at `record["message"]["content"][N]["is_error"]` (option A); phrase list was hard-coded in spec (option A); stuck-loop threshold is 3 with name+input-hash identity (option B); `current-path` defaults to raw (option A); all session-ID-accepting commands support `"last"` shorthand.
   - Recorded in: `plan/tasks-6-session-historian-enhance.md`, Discovered During Implementation

2. **Extraction helpers pattern emerged**: All four new commands follow a "command orchestrates helpers" pattern rather than embedding extraction logic inline. This is the established pattern for testability in this file and should be documented as convention for future command additions.
   - Recorded in: `plan/tasks-6-session-historian-enhance.md`, Discovered During Implementation

3. **No-truncation policy applies to error content**: The feature context was silent on whether error content should be truncated in display. The "No Invented Limits" repository policy resolved this — full content is shown in Rich output, consistent with all other display in the file.
   - Recorded in: `plan/tasks-6-session-historian-enhance.md`, Discovered During Implementation
