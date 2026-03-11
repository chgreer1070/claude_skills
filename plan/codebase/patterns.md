# Session-Historian Codebase Patterns

Source files analyzed:
- `.claude/skills/session-historian/scripts/session_query.py`
- `pyproject.toml`
- `plugins/frustration-analyzer/agents/frustration-analyst.md`
- `plugins/frustration-analyzer/agents/batch-detector.md`

---

## 1. Imports in session_query.py

### PEP 723 inline script metadata (lines 1–8)

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=1.0.0",
#     "typer>=0.21.0"
# ]
# ///
```

### Standard library imports (lines 19–29)

```python
from __future__ import annotations

import hashlib
import json
import operator
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
```

### Third-party imports (lines 31–37)

```python
import duckdb
import typer
from rich import box
from rich.console import Console
from rich.measure import Measurement
from rich.panel import Panel
from rich.table import Table
```

No `anthropic`, `httpx`, `subprocess`, or any external API call imports exist anywhere in the file. There are zero HTTP calls or subprocess invocations.

---

## 2. Python Version Target

- PEP 723 metadata: `requires-python = ">=3.11"`
- `pyproject.toml` project: `requires-python = ">=3.11"`
- `pyproject.toml` ruff: `target-version = "py311"`

Target is **Python 3.11+**.

---

## 3. `_CORRECTION_PHRASES` constant (lines 71–82)

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

A module-level tuple of 10 lowercase phrases. Matched case-insensitively against `content.lower()`.

---

## 4. Irritation matcher (lines 1046–1050)

```python
lower = content.lower()
for phrase in _CORRECTION_PHRASES:
    if phrase in lower:
        results.append((ts, phrase, content[:200]))
        break  # one signal per message is enough
```

- Iterates `_CORRECTION_PHRASES` with `phrase in lower` (substring match)
- Appends at most one tuple per message (`break` after first match)
- Excerpt is truncated to first 200 chars of the raw content

---

## 5. `_collect_correction_phrases` — full function (lines 1024–1051)

**Signature:**

```python
def _collect_correction_phrases(records: list[dict]) -> list[tuple[str, str, str]]:
```

**What it receives:** `records` — a `list[dict]` of parsed JSONL records from a session file (as returned by `_iter_records`).

**What it returns:** `list[tuple[str, str, str]]` — each tuple is `(timestamp, matched_phrase, excerpt)`:

| Index | Field | Type | Description |
|-------|-------|------|-------------|
| 0 | `timestamp` | `str` | ISO timestamp from `rec["timestamp"]`, empty string if absent |
| 1 | `matched_phrase` | `str` | The first phrase from `_CORRECTION_PHRASES` that matched |
| 2 | `excerpt` | `str` | First 200 characters of the message text |

**Filter logic:**
- Skips records where `type != "user"` or `"toolUseResult" in rec`
- Skips records where `_is_noise(content)` is True
- At most one tuple per message (first matched phrase only)

---

## 6. `cmd_irritation` — full command (lines 1106–1176)

**Signature:**

```python
@app.command("irritation")
def cmd_irritation(
    session_id: Annotated[str, typer.Argument(...)] = "last",
    raw: Annotated[bool, typer.Option("--raw", ...)] = False,
) -> None:
```

**Output shape — rich mode (default):**

```text
Irritation Signals — {session_id}

Correction Phrases ({N} found)
── {date}  {phrase}
{excerpt}

Stuck Tool Loops ({N} detected)
── {date}  {tool_name}  x{count}  {input_hash}
```

**Output shape — `--raw` mode:**

Tab-separated lines, two record types:

```text
phrase\t{date}\t{phrase}\t{single_line_excerpt}
loop\t{date}\t{tool_name}\t{count}\t{input_hash}
```

Where `date` is `ts[:19].replace("T", " ")` (e.g. `2026-03-11 14:22:05`).

**Exit behavior:**
- Exit 0 with stderr message when no signals detected
- Exit 1 when session not found

---

## 7. `_collect_stuck_loops` — supporting function (lines 1054–1103)

**Signature:**

```python
def _collect_stuck_loops(records: list[dict]) -> list[tuple[str, str, int, str]]:
```

**Returns:** `list[tuple[str, str, int, str]]` — each tuple is `(first_timestamp, tool_name, count, input_hash)`.

Threshold: `_STUCK_LOOP_THRESHOLD = 3` (module-level constant, line 84).

---

## 8. `anthropic` in pyproject.toml

`anthropic>=0.80.0` is present in `[dependency-groups] dev` — it is a **dev dependency only**, not a runtime dependency of the project or any script.

The script's own PEP 723 metadata declares only `duckdb>=1.0.0` and `typer>=0.21.0`. `anthropic` is not available to `session_query.py` at runtime via `uv run --script`.

---

## 9. Frustration-analyzer batch-detector pattern

**Agent:** `plugins/frustration-analyzer/agents/batch-detector.md`
**Model:** `haiku`
**Tools:** `Read`, `Write` only — no MCP tools, no HTTP, no subprocess

### Input format (batch JSONL)

Each line of the input batch file is a JSON object:

```json
{ "file": "<source session path>", "line_index": <integer>, "text": "<user message text>" }
```

### Detection criteria

The agent reads each entry's `text` field and flags it if it contains a **strong emotional reaction aimed at the AI assistant**:

- Direct insults or profanity directed at assistant
- Accusations of not listening, ignoring instructions, or being useless
- Sarcasm or mockery clearly aimed at assistant
- Expressions of disbelief at repeated/obvious failure
- Escalated corrections (elevated tone or repeated emphasis)
- Arguments with the assistant

Does NOT flag: neutral corrections, questions without emotional charge, self-directed frustration, mild disappointment.

### Output files

**`{batch_path}.flags.json`:**

```json
{
  "source_batch": "<path to batch JSONL>",
  "flags": [
    { "file": "<source session path>", "line_index": <integer>, "text": "<message text>" }
  ],
  "count": <integer>
}
```

**`{batch_path}.flags.txt`:**

```text
[<basename of source session file>:<line_index>] "<message text>"
```

Empty file if no flags.

### Stage 2 delegation pattern (from frustration-analyst.md)

```text
Task: Detect emotional user reactions in this batch file.
Batch file: /tmp/rtfp-batch-{session_stem}.jsonl
Subagent type: frustration-analyzer:batch-detector

Read the batch file. Each entry has {file, line_index, text}.
Identify entries containing strong emotional reactions aimed at the AI assistant.
Write output to {batch_file}.flags.json and {batch_file}.flags.txt.
Report the count of flagged messages.
```

One subagent per batch file, spawned in parallel.

---

## 10. External API calls

There are **zero** external API calls (HTTP, subprocess, MCP) in `session_query.py`. The file uses:
- `duckdb` — local embedded database
- `typer` / `rich` — CLI and display
- Standard library only for all other operations

The frustration-analyzer `batch-detector` agent similarly uses only `Read`/`Write` tools — no API calls.
