# Backlog MCP: Timestamped Entry Blocks for Section Content

**Backlog item:** #583
**Date:** 2026-03-10
**Status:** Approved

## Problem

When agents add or update sections on backlog items via `backlog_update`/`backlog_groom` (section + content parameters), there is no record of when each piece of content was written. Multiple updates to the same section silently replace previous content with no audit trail.

## Solution

Wrap every piece of section content in timestamped, addressable blocks. Entries are never deleted — they are struck through with a reason and collapsed.

## Entry Block Data Model

### Active entry format

```html
<div><sub>{ISO-8601-UTC}</sub>

Markdown content here.
</div>
```

### Struck entry format

```html
<div><sub>{ISO-8601-UTC}</sub>
<details><summary>struck: {ISO-8601-UTC} — {reason}</summary>

Original content preserved.
</details>
</div>
```

### Parsing

- Single regex: `<div><sub>([^<]+)</sub>` extracts entry ID
- Struck detection: presence of `<details><summary>struck:` inside the div
- Duplicate timestamp handling: at parse/display time, assign `-0`, `-1` suffixes in document order. No pre-check at write time.
- Entry IDs are the ISO timestamp string from the `<sub>` tag

### Legacy migration

On first append to a section with unwrapped content:

1. Wrap existing text in `<div><sub>{added_date}T00:00:00Z</sub>` block (date from item's `added` metadata)
2. Append the new entry with current timestamp

## API Changes

### Parameters removed

- `groomed_content` from both `backlog_update` and `backlog_groom`

### Parameters added to `backlog_update` and `backlog_groom`

- `entry_id` (optional str) — target a specific block for overwrite. If unique across issue, `section` not required.
- `replace_section` (optional bool, default False) — strike all existing entries in the section, append content as new block.
- `reason` (optional str) — required when `replace_section=True`. The reason existing entries are being struck.

### `backlog_view` changes

- `offset` / `limit` — now operate on entry count, not lines. Breaking change replacing line-based pagination.
- Response adds per-section metadata:

```json
{
  "sections": {
    "Decision": {
      "num_entries": 3,
      "num_struck": 1,
      "entries": [
        {"id": "2026-03-10T22:18:04Z", "struck": false, "content": "full content..."},
        {"id": "2026-03-10T22:18:04Z-1", "struck": true, "content": "struck content..."},
        {"id": "2026-03-11T14:30:00Z", "struck": false, "content": "full content..."}
      ]
    }
  }
}
```

### New tool: `backlog_strike_entry`

```text
backlog_strike_entry(selector, entry_id, reason)
```

Wraps the entry's content in `<details><summary>struck: {timestamp} — {reason}</summary>` block. Entry stays in place, skipped by active pagination counts.

### Behavior matrix

| Parameters | Action |
|---|---|
| `section` + `content` | Append new timestamped entry to section |
| `section` + `content` + `entry_id` | Overwrite that entry within the section |
| `entry_id` + `content` (no section) | Overwrite entry by ID anywhere in issue |
| `section` + `content` + `replace_section=True` + `reason` | Strike all existing entries with reason, append content as new entry |

## Entry Block Parser/Writer

### New module: `backlog_core/entry_blocks.py`

**`wrap_entry(content: str) -> str`** — wraps content in `<div><sub>{now}</sub>\n\n{content}\n</div>`

**`strike_entry(entry_html: str, reason: str) -> str`** — preserves `<sub>` timestamp, wraps content in `<details><summary>struck: {now} — {reason}</summary>...</details>`

**`parse_entries(section_body: str, show: str | int | None = "all", since: str | None = None) -> list[Entry]`**

`show` accepts:

- `"all"` — every entry (active + struck)
- `"last"` — most recent active entry
- `"first"` — oldest active entry
- `"struck"` — only struck entries
- Positive int (e.g. `5`) — first N active entries from the span
- Negative int (e.g. `-5`) — last N active entries from the span

`since` filters the span start — only entries at or after that datetime are considered before `show` is applied.

Example: `parse_entries(body, show=-3, since="2026-03-10")` returns the 3 most recent active entries since March 10th.

**`rewrite_section(existing_body, new_content, entry_id, replace, reason, added_date) -> str`** — orchestrates append/overwrite/replace_section/strike operations. Returns full section body text.

### Legacy detection

If section body contains no `<div><sub>` patterns, the entire body is legacy content. On first append, wrap it with `<div><sub>{added_date}T00:00:00Z</sub>`.

## `backlog_pull` Entry-Aware Merge

### Merge rules

1. Parse both sides into entry lists using `parse_entries(body, show="all")`
2. Build a dict keyed by entry ID from each side
3. Merge:
   - Entry exists only on one side — keep it
   - Entry exists on both sides, one is struck — keep the struck version (strike is intentional)
   - Entry exists on both sides, both active — keep the version with more content (longer)
   - Entry exists on both sides, both struck — keep the one with the later struck timestamp
4. Reassemble entries in chronological order by entry ID

### Diff output

Git-diff style at the entry block level with full content:

```text
### Decision
  <div><sub>2026-03-10T08:00:00Z</sub>

Unchanged entry content here.
</div>
- <div><sub>2026-03-10T12:00:00Z</sub>

Local version of content.
</div>
+ <div><sub>2026-03-10T12:00:00Z</sub>

Remote version with more detail and additional context.
</div>
  <div><sub>2026-03-10T22:18:04Z</sub>

Another unchanged entry.
</div>
+ <div><sub>2026-03-11T14:30:00Z</sub>

New entry only on remote.
</div>
```

- Unchanged entries: space prefix
- Differs between sides: `-` for local, `+` for remote
- Only on one side: `+` or `-` accordingly

### `backlog_pull` parameter additions

- `dry_run` (existing) — now produces entry-level diff string instead of just counts
- `diff` (new bool, default False) — apply the merge AND return the diff string alongside the result

### Modes

- `dry_run=True` — parse both sides, compute diff, return diff string without writing
- `diff=True` — apply merge, return diff string alongside result
- Both False (default) — apply merge, return counts only (entry-aware)

## Affected Files

### New file

- `backlog_core/entry_blocks.py` — `wrap_entry()`, `strike_entry()`, `parse_entries()`, `rewrite_section()`, diff generation

### Modified files

- `backlog_core/server.py` — remove `groomed_content` param, add `entry_id`, `replace_section`, `reason` params to update/groom. Add `backlog_strike_entry` tool. Update `backlog_view` pagination to entry-based. Add `diff` param to `backlog_pull`.
- `backlog_core/operations.py` — wire entry block functions into `update_item()`, `groom_item()`, `view_item()`, `pull_items()`. New `strike_entry()` operation.
- `backlog_core/parsing.py` — add entry block regex patterns
- `backlog_core/models.py` — add `Entry` model, update `ViewItemResult` with sections/entries metadata
- `scripts/backlog.py` — CLI parity: update `groom`, `update`, `view`, `pull` commands. Add `strike-entry` command. Remove `--groomed-content` flag.
- Tests — update existing tests for changed signatures, add tests for entry block parsing/writing/striking/merging/diffing

### Not changed

- `backlog_add` — new items start empty, no entry blocks at creation
- `backlog_close`, `backlog_resolve` — operate on item-level status, not section content
- `backlog_sync` — pushes local content to GitHub; entry blocks are already in the file content, written as-is
