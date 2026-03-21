# Feature Context: Convert Backlog Files from Hybrid Markdown to Pure YAML

## Problem Statement

Local backlog files (`.claude/backlog/*.md`) use a hybrid format: YAML frontmatter delimited by `---` fences, plus a markdown body below the closing `---`. This creates several problems:

1. **Two parsing systems required** -- The I/O layer uses `python-frontmatter` with a `ruamel.yaml` handler (`frontmatter_utils.py`) to parse the YAML frontmatter, then separate regex-based parsing (`parsing.py`) to extract `## Section` blocks and `**Field**: value` pairs from the markdown body. Two independent parsing systems for one file format means two independent failure modes.

2. **Lossy round-trip** -- The `python-frontmatter` library treats the body as an opaque string. Structured data in the body (sections like `## Groomed`, `## Fact-Check`, `## RT-ICA`, subsections like `### Priority`, `### Impact`, entry blocks wrapped in `<div><sub>timestamp</sub>...</div>`) is stored as raw markdown text. Reading structured data back out requires regex extraction (`extract_sections()`, `extract_groomed_section()`, `ENTRY_RE`, `STRUCK_RE`). Writing structured data back requires string concatenation and regex substitution (`append_or_replace_section()`, `rewrite_section()`).

3. **Fragile section manipulation** -- Adding, replacing, or merging sections uses regex patterns that must handle edge cases: sections at end-of-file vs mid-file, subsections nested under `## Groomed`, headings with suffixes like `## Groomed (2026-03-12)`, entries with duplicate timestamps. Each edge case is a regex branch in `parsing.py` and `entry_blocks.py`.

4. **Type information lost in body** -- The frontmatter has typed fields (strings, nested dicts). The body is untyped markdown. The `BacklogItem` model stores the body as `raw_body: str`, and any structured content within it must be re-parsed on every access. Entry blocks (`Entry` model with `id`, `content`, `struck`, `struck_reason`, `struck_at`) exist as parsed objects only transiently during `parse_entries()` calls -- they are never persisted in a structured format.

5. **Merge complexity** -- `merge_sections()` compares local and GitHub bodies section-by-section using `extract_sections()`, keeping the longer version per section. This "longer wins" heuristic is lossy. Entry-aware merging in `entry_blocks.py` (`generate_diff()`) operates on regex-parsed entry blocks. Both would be simpler with structured data.

## Desired Outcome

When done:

- Local backlog files use `.yaml` extension and are pure YAML (no `---` frontmatter delimiters, no markdown body)
- All currently-in-body sections (Groomed, Fact-Check, RT-ICA, Issue Classification) become typed YAML fields
- Entry blocks become YAML list-of-objects with typed fields (`id`, `content`, `struck`, `struck_reason`, `struck_at`) instead of `<div><sub>` HTML wrappers parsed by regex
- The `python-frontmatter` library is no longer needed for backlog file I/O -- `ruamel.yaml` handles the entire file directly
- `BacklogItem` model fields map 1:1 to YAML keys (no `raw_body` string requiring re-parsing)
- GitHub Issue bodies remain markdown (backward compatible -- the GitHub sync layer converts between YAML local format and markdown issue body format)
- `parse_item_file()` becomes a YAML load + Pydantic model construction (no regex)
- Section manipulation becomes dict/list operations (no regex substitution)

## Current Behavior Observations

### File format (observed from 3 sample files)

Frontmatter fields (YAML between `---` delimiters):

```yaml
name: 'item title'
description: 'description text or <div><sub>timestamp</sub> block'
metadata:
  topic: slug-string
  source: origin text
  added: 'YYYY-MM-DD'
  priority: P0|P1|P2|completed
  type: Feature|Bug|Refactor|Docs|Chore
  status: open|done|in-progress|needs-grooming
  issue: '#NNN'
  last_synced: 'ISO-8601'
  groomed: 'YYYY-MM-DD'
  plan: path/to/plan-file.md
```

Body sections (markdown below closing `---`):

- `## Groomed (YYYY-MM-DD)` with `### subsections` (Priority, Impact, Benefits, Expected Behavior, Desired Structure, Acceptance Criteria, Resources, Dependencies, Effort)
- `## Fact-Check` with timestamped entry blocks
- `## RT-ICA` with structured text
- `## Issue Classification` with timestamped entry blocks
- Entry blocks use `<div><sub>ISO-timestamp</sub>` HTML wrapper format

### I/O layer (`frontmatter_utils.py`)

- Uses `python-frontmatter` library with a custom `RuamelYAMLHandler` that delegates to `ruamel.yaml` in round-trip mode
- `load_frontmatter()` / `loads_frontmatter()` return `frontmatter.Post` objects with `.metadata` (dict) and `.content` (str body)
- `dump_frontmatter()` / `dumps_frontmatter()` serialize back with `---` delimiters
- `update_field()` is a load-modify-save helper for single frontmatter key updates
- Width set to `2147483647` to prevent ruamel.yaml from wrapping long scalars

### Parsing layer (`parsing.py`)

- `parse_item_file()` handles both "research-style" (name, description, metadata block) and "flat/legacy" frontmatter layouts
- `_parse_frontmatter()` uses `loads_frontmatter()` then extracts the nested `metadata` dict
- Body section operations: `extract_sections()`, `append_or_replace_section()`, `extract_groomed_section()`, `merge_sections()`, `reconstruct_body_from_sections()`
- Body field extraction: `extract_body_field_pairs()`, `parse_body_extra_fields()` for `**Key**: value` patterns before the first `## heading`

### Entry block layer (`entry_blocks.py`)

- `ENTRY_RE` regex: `<div><sub>([^<]+)</sub>\s*(.*?)</div>` (dotall)
- `STRUCK_RE` regex: `<details><summary>struck:\s*(\S+)\s*—\s*(.*?)</summary>\s*(.*?)</details>` (dotall)
- `parse_entries()` returns `list[Entry]` from section body text
- `rewrite_section()` handles append, replace (strike all + append), and entry-id-targeted overwrite
- `strike_entry()` wraps content in collapsed `<details>` HTML
- `generate_diff()` produces git-diff style output for entry-level merge
- Duplicate timestamp handling: suffixes `-0`, `-1` in document order

### Data model (`models.py`)

- `BacklogItem`: 22 fields, all defaulting to empty/falsy. `raw_body: str` holds the entire markdown body as a string.
- `Entry`: 6 fields (`id`, `content`, `struck`, `struck_reason`, `struck_at`, `raw`). Only exists as transient parse output -- never persisted in structured form in the file.
- `ViewItemResult`: enriched view model with `sections: dict[str, dict[str, object]]` for section metadata

### GitHub sync layer (`github.py`, `operations.py`)

- `build_issue_body_from_file()` passes `item.raw_body` through to GitHub when `## Groomed` is present
- `build_issue_body()` constructs markdown from `BacklogItem` fields (Story, Description, Acceptance Criteria, Files, Context sections)
- `merge_sections()` merges GitHub issue body back into local body by section (longer wins)
- Entry block merge rules exist in `entry_blocks.py` for `backlog_pull` operations
- `update_item_metadata()` in `operations.py` uses `load_frontmatter()` / `dumps_frontmatter()` for field updates

### Save operations (`operations.py`)

- `update_item_metadata()` loads frontmatter, updates keys in `.metadata` dict, writes back via `dumps_frontmatter()`
- Item creation (`add_item()`) uses `build_backlog_frontmatter()` which constructs a `frontmatter.Post` object and serializes it
- Section updates go through `append_or_replace_section()` which operates on the body string

## Environment Constraints

1. **GitHub Issue bodies must remain markdown** -- GitHub renders markdown in issue bodies. The sync layer (`github.py`) must convert between local YAML format and markdown issue body format. This is already partially true (the `build_issue_body()` function constructs markdown from model fields), but `build_issue_body_from_file()` currently passes the raw markdown body through directly.

2. **`ruamel.yaml` is the YAML library** -- per `.claude/rules/yaml-toml-libraries.md`, never use `pyyaml`. The existing `RuamelYAMLHandler` already uses `ruamel.yaml` in round-trip mode. Pure YAML files would use `ruamel.yaml` directly without the `python-frontmatter` wrapper.

3. **Backward compatibility during migration** -- Approximately 90+ backlog files exist in `.claude/backlog/`. A migration script is needed to convert `.md` files to `.yaml`. The system should handle both formats during a transition period, or the migration must be atomic.

4. **Entry block format preservation** -- Entry blocks carry audit trail semantics (timestamped, struck-not-deleted). The YAML representation must preserve all entry block fields: `id` (timestamp), `content`, `struck` (bool), `struck_reason`, `struck_at`. The `raw` field on `Entry` can be dropped since the YAML structure IS the canonical representation.

5. **Consumers of `BacklogItem.raw_body`** -- Any code that reads `raw_body` and applies regex extraction must be updated. This includes `build_issue_body_from_file()`, `view_result_from_local_item()` (sets `result.body = item.raw_body`), and MCP server tools that return body content.

6. **File naming convention** -- Current files use priority prefix: `p0-slug.md`, `p1-slug.md`, `ideas-slug.md`, `completed-slug.md`. The new format changes extension to `.yaml` but the prefix convention can remain.

7. **`backlog_pull` merge logic** -- Currently merges at the section level (local vs GitHub). With YAML, merging becomes dict/list merging, which is structurally cleaner but the merge rules (entry-level: struck wins, longer active wins) still need implementation.

## Questions for Resolution

1. **Migration strategy** -- Atomic (convert all files in one commit) or gradual (support both `.md` and `.yaml` during transition)? Atomic is simpler but creates a large diff. Gradual adds complexity to parsing/discovery code.

2. **Body sections as top-level keys or nested structure?** -- Should `## Groomed` become `groomed_sections:` (a dict of subsection names to entry lists), or should each subsection become a top-level key like `groomed_priority:`, `groomed_impact:`, etc.?

3. **Entry block YAML representation** -- Should entries be a list of objects under their section key, or should the section value be the latest entry's content (with history in a separate `_history` key)?

4. **`ViewItemResult.body` and MCP tool responses** -- These currently return markdown body text. Should they return YAML text, or should the response format remain markdown (generated from YAML on read)?

5. **`description` field dual use** -- Currently `description` in frontmatter can contain either plain text OR a `<div><sub>` entry block (observed in sample file `p2-backlog-add-status-field-to-backlogitem-model.md` where `description` starts with `<div><sub>2026-03-12T02:09:48Z</sub>`). Should `description` be plain text only, with entry-wrapped descriptions migrated to a separate field?
