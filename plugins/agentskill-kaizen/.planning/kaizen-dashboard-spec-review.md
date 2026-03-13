# Kaizen Dashboard Redesign Spec -- Review

**Reviewer**: Senior Code Reviewer (orchestrator)
**Date**: 2026-03-12
**Documents reviewed**:
1. `kaizen-dashboard-redesign-spec.md` (architecture spec)
2. `kaizen-dashboard-db-schema.md` (DuckDB schema)
3. `kaizen-dashboard-views.md` (Panel component specs)
4. `kaizen-dashboard-testing.md` (test strategy)

**Current codebase verified**:
- `mcp/dashboard.py` -- existing sentiment dashboard (4 tabs, CSV-based)
- `mcp/server.py` -- existing MCP server (PEP 723 deps, no `duckdb` in deps)

---

## What Was Done Well

The spec represents a genuine architectural shift from a sentiment chart gallery to a findings-driven forensic browser. The core abstraction -- `information + context -> action -> outcome` with intervention edges -- is well-defined and consistently threaded through all four documents. Specific strengths:

- **ADR discipline**: Five architectural decisions are documented with context, decision, rationale, and consequences. ADR-002 (separate ingestion script) correctly identifies the Tornado IOLoop blocking risk that would result from in-dashboard analysis.
- **C4 diagrams**: Context and container diagrams provide clear system boundaries. The read-only dashboard / write-only ingestion split is visually explicit.
- **Query patterns**: Every dashboard view has SQL queries in the schema doc, making the data contract between `db.py` and `dashboard.py` unambiguous.
- **Current state accuracy**: The spec correctly describes the existing dashboard (4 tabs: Session Timeline, Session Heatmap, Distribution, Hot Spots), the CSV polling pattern (5-second interval), the `FastListTemplate` usage, and the daemon thread hosting model. Verified against `mcp/dashboard.py`.
- **Interface-first design**: `KaizenDB` is specified as signatures with type annotations before any implementation. Filter dataclasses (`FindingFilter`, `SessionFilter`) are well-structured.

---

## Critical Issues (Must Fix)

### C1. `duckdb` missing from `server.py` PEP 723 dependencies

**File**: `kaizen-dashboard-redesign-spec.md`, Section 8 (Distribution Architecture)

The spec states: "Dependencies for the dashboard (`panel`, `hvplot`, `holoviews`, `bokeh`, `duckdb`) are already declared in `mcp/server.py`'s PEP 723 metadata block. The `duckdb` dependency needs to be added there."

Verified against `mcp/server.py` lines 1-15: the PEP 723 block declares `fastmcp`, `pm4py`, `pandas`, `prefixspan`, `scikit-learn`, `panel`, `hvplot`, `holoviews`, `bokeh`. No `duckdb`.

The sentence says `duckdb` is "already declared" and then contradicts itself by saying it "needs to be added." This is confusing. The spec should state clearly: **`duckdb>=1.0.0` must be added to `mcp/server.py`'s PEP 723 dependencies as a prerequisite step.** This is a blocking dependency for the entire redesign.

### C2. `findings.fix_id` creates a 1:1 relationship but `fixes.finding_id` already creates 1:many

**File**: `kaizen-dashboard-db-schema.md`, `findings` table (line 48) and `fixes` table (line 148)

The `findings` table has `fix_id TEXT` (FK to `fixes.fix_id`), and the `fixes` table has `finding_id TEXT NOT NULL` (FK to `findings.finding_id`). This creates a bidirectional FK:

- `findings.fix_id -> fixes.fix_id` (one finding points to one fix)
- `fixes.finding_id -> findings.finding_id` (one fix points to one finding)

The ER diagram in the spec (`kaizen-dashboard-redesign-spec.md`, line 272) shows `findings ||--o{ fixes : "resolved by"` -- meaning one finding can have **many** fixes. But `findings.fix_id` can only hold one value, creating a contradiction.

If a finding can be resolved by multiple fixes (e.g., a hook that was ineffective, then a CLAUDE.md update that worked), the `findings.fix_id` column should be removed. The relationship is already navigable via `fixes.finding_id`. The Findings Browser query (schema doc, line 228) already JOINs `findings -> fixes` via `f.fix_id = fx.fix_id`, which would only return one fix per finding.

**Recommendation**: Remove `findings.fix_id`. Update the Findings Browser query to use a subquery or lateral join against `fixes WHERE finding_id = f.finding_id ORDER BY applied_at DESC LIMIT 1` to get the most recent fix. This preserves the "most recent fix status" display while supporting multiple fix attempts per finding.

### C3. Ingestion script parsing is underspecified

**File**: `kaizen-dashboard-redesign-spec.md`, Section 5 (Data Architecture), items 1-3

The ingestion script is described as parsing `.planning/kaizen/analysis-*.md` files, but:

1. **No markdown format is defined.** The spec says it uses "the output format defined in the transcript-analysis skill (severity, evidence, frequency, recommendation type)" but does not include or reference that format. Without a concrete markdown schema (headings, YAML frontmatter, structured sections), two implementers would parse differently.

2. **Intervention extraction heuristics are vague.** "Scans JSONL transcripts for `[Request interrupted by user]`, tool denials, direct corrections, and compact boundaries" -- how is a "direct correction" detected? How is a "compact boundary that follows an investigation sequence" identified? These are classification problems that need defined rules.

3. **State transition construction is the hardest part and gets one paragraph.** "For each assistant turn, creates a `(context_summary, action, outcome)` triple" -- `context_summary` requires NLP-level summarization of the preceding user turn + active tools/files. The spec does not specify whether this is extractive (first N chars), template-based, or LLM-generated.

**Recommendation**: Add a companion document `kaizen-dashboard-ingestion-spec.md` that defines:
- The expected markdown output format from transcript-analysis (with an example)
- The intervention detection rules (regex patterns, JSONL field names, classification logic)
- The context summarization strategy (extractive vs template)
- Edge cases: what happens with empty sessions, sessions with no tool calls, sessions with only system messages

---

## Important Issues (Should Fix)

### I1. `state_transitions` graph model conflates two different visualizations

**File**: `kaizen-dashboard-views.md`, Tab 2 (Interventions), lines 86-151

The Intervention Flow tab has two modes:
- **Aggregate**: Nodes are tool names, edges are weighted by cross-session frequency
- **Per-Session**: Shows one session's flow

In Aggregate mode, `action_tool` becomes the node identity. But `state_transitions` stores individual triples `(context -> action -> outcome)` where the same tool appears in different contexts. The aggregate query (schema doc, line 274) groups by `action_tool, outcome` -- this loses the **context** dimension entirely. The graph becomes "Read -> success (500 times), Read -> intervention (20 times)" which tells you Read sometimes triggers interventions, but not **what context** leads to Read triggering interventions.

The core abstraction is `information + context -> action -> outcome`. The aggregate view collapses it to `action -> outcome`, losing half the value.

**Recommendation**: The aggregate graph should use `(context_type, action_tool)` pairs as nodes, or provide a "group by context" toggle. Alternatively, make the aggregate view a Sankey diagram: `context_type -> action_tool -> outcome`, which preserves all three dimensions.

### I2. No `FOREIGN KEY` constraints in the schema DDL

**File**: `kaizen-dashboard-db-schema.md`, all table definitions

The schema comments describe FK relationships (`-- FK to sessions.session_id`, `-- FK to findings.finding_id`, etc.) but the DDL does not declare `FOREIGN KEY` constraints. DuckDB supports foreign keys. Without them:
- The ingestion script can insert orphaned records (e.g., `finding_evidence` rows referencing nonexistent `finding_id` values)
- No cascade behavior on deletes (when re-ingesting, stale child records persist)

**Recommendation**: Add `FOREIGN KEY` constraints to the DDL. DuckDB enforces them on insert. This is especially important for `fix_measurements.fix_id -> fixes.fix_id` and `finding_evidence.finding_id -> findings.finding_id` where orphans would produce wrong visualizations.

### I3. `Tabulator pagination='remote'` does not work without a server-side data source

**File**: `kaizen-dashboard-views.md`, Findings Browser (line 60), Session Explorer (line 236)

The spec calls for `pagination='remote'` and `page_size=50` on multiple Tabulators. Panel's `pagination='remote'` requires a server-side data source (a callback or a Dask/Vaex DataFrame). If `KaizenDB.findings()` returns a full pandas DataFrame and that DataFrame is passed directly to Tabulator, then `pagination='remote'` will silently fall back to client-side pagination -- loading the full DataFrame into the browser DOM anyway.

For true server-side pagination, the Tabulator would need a callback-based value source (e.g., `pn.widgets.Tabulator(value=callback, pagination='remote')`) or the KaizenDB methods would need to accept `offset`/`limit` parameters.

**Recommendation**: Either:
1. Change to `pagination='local'` (simpler, acceptable up to ~5000 rows)
2. Add `offset: int | None` and `limit: int | None` parameters to `KaizenDB.findings()` and `.sessions()`, and wire Tabulator's page-change event to re-query with the correct offset/limit

### I4. HoloViews `Graph` does not natively support directed edges

**File**: `kaizen-dashboard-redesign-spec.md`, ADR-003 (line 409); `kaizen-dashboard-views.md`, Tab 2 (line 129)

The spec selects `hv.Graph` for the state machine visualization and describes "directed" edges with arrow indicators. HoloViews `Graph` renders undirected edges by default. Directed edges require either:
- Custom Bokeh glyphs (arrow heads) added via hooks
- Using `hv.Sankey` instead (which is inherently directional)
- Dropping to raw Bokeh `GraphRenderer` with `ArrowHead` decorations

ADR-003 excludes NetworkX as "overkill" but HoloViews `Graph` actually uses NetworkX internally for layout computation (`nx.spring_layout`, `nx.kamada_kawai_layout`, etc.). The dependency is implicit via HoloViews.

**Recommendation**: Acknowledge in ADR-003 that directed edge rendering requires Bokeh-level customization (arrow glyphs via `hv.Graph.opts(hooks=[...])`) or evaluate `hv.Sankey` for the aggregate view. Add a spike task to prototype directed edge rendering before committing to `hv.Graph`.

### I5. `sentiment` table timestamp is `TEXT` while all other tables use `TIMESTAMP WITH TIME ZONE`

**File**: `kaizen-dashboard-db-schema.md`, `sentiment` table (line 196) vs all other tables

The `sentiment` table declares `timestamp TEXT` while every other table uses `TIMESTAMP WITH TIME ZONE`. The spec notes this table "already exists" and the schema is "shown for completeness." However, the dashboard will query across tables (e.g., correlating sentiment with intervention timestamps). Joining `TEXT` timestamps against `TIMESTAMP WITH TIME ZONE` requires casting, which is error-prone and prevents DuckDB's timestamp-aware optimizations.

**Recommendation**: Add a migration step to `ingest-findings.py` that casts the sentiment `timestamp` column to `TIMESTAMP WITH TIME ZONE` (DuckDB can do this with `ALTER TABLE sentiment ALTER COLUMN timestamp TYPE TIMESTAMP WITH TIME ZONE`). Or create a view that casts on read if the existing table cannot be altered (due to `sentiment-score.py` still writing to it).

### I6. No idempotency strategy for the ingestion script

**File**: `kaizen-dashboard-redesign-spec.md`, Section 5 (Data Architecture)

The spec says the ingestion script is "the single writer" and can be "run on a schedule or on-demand." But there is no discussion of:
- What happens when the script is run twice on the same data?
- Are UUIDs deterministic (content-addressed) or random?
- Is there an upsert strategy or does the script truncate and reload?

If UUIDs are random, running the script twice creates duplicate rows. If the script truncates tables first, `fixes` and `fix_measurements` (which are populated separately over time) would be destroyed.

**Recommendation**: Define the idempotency contract explicitly. Suggested approach: content-addressed UUIDs (hash of `dimension + title + session_id` for findings, hash of `session_id + sequence_index` for transitions) with `INSERT OR REPLACE` semantics. The `fixes` and `fix_measurements` tables should be excluded from bulk re-ingestion.

---

## Suggestions (Nice to Have)

### S1. Add a "Last Ingested" indicator to the dashboard chrome

ADR-002 consequences note: "Need a 'last ingested' timestamp visible in the dashboard." The views spec (`kaizen-dashboard-views.md`) does not show where this appears in the UI. The health endpoint response includes `last_ingested`, but the user needs to see it in the dashboard itself -- not via `curl`.

**Recommendation**: Add a `pn.pane.Markdown` or `pn.indicators.String` in the `FastListTemplate` header or sidebar showing "Data as of: {last_ingested}". Wire it to the periodic callback.

### S2. Cross-tab navigation implementation approach needs more specificity

**File**: `kaizen-dashboard-views.md`, Cross-Tab Navigation section (line 385)

The spec says: "use `pn.state.location` or shared reactive values (`pn.rx()`) to communicate selection state between tabs." These are two different approaches with different trade-offs:
- `pn.state.location` uses URL parameters (bookmarkable, but requires serialization)
- `pn.rx()` uses in-memory reactive state (simpler, but lost on page refresh)

**Recommendation**: Pick one. `pn.rx()` is likely the right choice since this is a single-page app with no bookmarking requirement. Document the shared state variables (e.g., `selected_session_id`, `selected_finding_id`, `selected_fix_id`) as part of the component design.

### S3. Test fixtures could use a factory pattern

**File**: `kaizen-dashboard-testing.md`, Test Directory Structure (line 22)

SQL INSERT fixture files (`sample_findings.sql`, etc.) are rigid. If the schema changes, every fixture file must be updated manually.

**Recommendation**: Consider Python factory functions (e.g., `make_finding(dimension="tool_misuse", severity="critical", ...)`) that generate INSERT statements or directly insert into in-memory DuckDB. This decouples test data from exact column ordering.

### S4. The `requires-python` upper bound in server.py conflicts with dashboard redesign timeline

**File**: `mcp/server.py` line 3 -- `requires-python = ">=3.11,<3.14"`

The existing server.py has `<3.14` as a Python upper bound, and there are `cpython-314` pycache files in the mcp directory. The spec does not address Python version constraints for the new code. The ingestion script spec (redesign-spec.md line 359) declares `requires-python = ">=3.11"` with no upper bound. Inconsistency between the server and the ingestion script may cause resolution conflicts when both are run via `uv run`.

**Recommendation**: Align Python version constraints across all PEP 723 scripts in the plugin.

### S5. Testing doc omits `duckdb` version pinning rationale

**File**: `kaizen-dashboard-testing.md`, Testing Stack (line 9)

The testing stack lists `duckdb>=1.0.0`. The ingestion script spec also uses `duckdb>=1.0.0`. For test reproducibility, consider pinning to a narrower range (e.g., `duckdb>=1.0.0,<2`) to avoid breaking changes in a hypothetical DuckDB 2.0.

---

## Consistency Check Across Documents

| Aspect | Spec | Schema | Views | Testing | Consistent? |
|--------|------|--------|-------|---------|-------------|
| Tab count | 5 | n/a | 5 | 5 (line 179) | Yes |
| Tab names | Findings, Intervention Flow, Fix Tracker, Sentiment, Session Explorer | n/a | Findings, Interventions, Fix Tracker, Sessions, Sentiment | n/a | **No** -- names differ |
| Table count | 8 | 8 | n/a | n/a | Yes |
| Polling interval | 30s | n/a | 30s | n/a | Yes |
| DuckDB read-only | Yes (sec 6, sec 10) | n/a | n/a | n/a | Yes |
| `dynamic=True` on Tabs | Yes (sec 10) | n/a | Yes (line 9) | n/a | Yes |
| Health endpoint fields | n/a | n/a | `db_path`, `db_exists`, `table_counts`, `last_ingested` | `db_path`, `db_exists`, `table_counts`, `last_ingested` | Yes |

### Tab naming inconsistency detail

The redesign spec (Section 4, line 117) uses: "Findings Browser", "Intervention Flow", "Fix Tracker", "Sentiment Signal", "Session Explorer".

The views spec table (line 12) uses: "Findings", "Interventions", "Fix Tracker", "Sessions", "Sentiment".

The container diagram (redesign spec, line 59-63) uses: "Findings Browser", "Intervention Flow", "Fix Tracker", "Sentiment Signal", "Session Explorer".

The view builder signatures (redesign spec, line 238-243) use: `_build_findings_tab`, `_build_flow_tab`, `_build_fix_tracker_tab`, `_build_sentiment_tab`, `_build_session_tab`.

These should be canonicalized. The views spec names are the ones users see in the tab bar -- those should be authoritative.

---

## Goal Alignment Assessment

**Does the spec deliver a findings browser with intervention flow visualization, or does it drift back toward analytics/charts?**

The spec delivers on the stated goal. The five tabs are structured around the forensic workflow:
1. **What broke?** -- Findings Browser
2. **How did it break?** -- Intervention Flow (state machine view)
3. **Did fixes work?** -- Fix Tracker (before/after measurement)
4. **What happened in a session?** -- Session Explorer (drill-down)
5. **Background signal** -- Sentiment (retained, compacted)

Sentiment is correctly demoted to a secondary signal (ADR-004). The Findings tab is the landing tab. The state machine abstraction is central to the Intervention Flow tab.

The one area where the spec could drift is the **Aggregate mode** of the Intervention Flow tab (issue I1 above). In aggregate mode, the graph becomes a tool-frequency chart rather than a forensic flow diagram. The per-session mode is the truly forensic view; the aggregate mode risks becoming "which tools fail most" analytics rather than "what context leads to failure."

---

## Summary of Findings

| Category | Count | IDs |
|----------|-------|-----|
| Critical (must fix) | 3 | C1, C2, C3 |
| Important (should fix) | 6 | I1, I2, I3, I4, I5, I6 |
| Suggestions | 5 | S1, S2, S3, S4, S5 |

**Blocking items before implementation can begin**: C1 (dependency), C2 (schema correctness), C3 (ingestion format definition). Of these, C3 is the largest -- the ingestion script is the pipeline that populates the entire database, and its parsing rules are currently underspecified.
