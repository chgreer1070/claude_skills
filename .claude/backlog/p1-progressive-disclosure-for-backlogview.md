---
name: Progressive disclosure for backlog_view
description: 'backlog_view MCP tool returns full section content by default, producing responses that exceed context limits (53k+ observed for issue #965 with groomed content). Callers need item metadata and section inventory without content, then the ability to expand specific sections on demand. Success: default view is compact (metadata + section names with entry counts), sections expandable via regex or glob pattern in the show parameter.'
metadata:
  topic: progressive-disclosure-for-backlogview
  source: 'Session observation — backlog_view returned 53k+ for issue #965 during 2026-03-21 session'
  added: '2026-03-22'
  priority: P1
  type: Refactor
  status: open
  issue: '#987'
  last_synced: '2026-03-22T12:23:12Z'
  groomed: '2026-03-22'
---

## RT-ICA

<div><sub>2026-03-22T12:20:12Z</sub>

RT-ICA Snapshot: Progressive disclosure for backlog_view
Goal: Make backlog_view return compact metadata by default, with section content expandable on demand via regex/glob.
Conditions:
1. Current backlog_view response structure and parameters | Status: DERIVABLE | Read server.py implementation
2. Existing show and limit parameters on backlog_view | Status: AVAILABLE | Tool schema shows: show (all/last/first/struck/N), since (ISO date), offset, limit
3. How section content is assembled in backlog_view | Status: DERIVABLE | Read the view implementation in operations.py
4. What metadata fields callers need in compact view | Status: AVAILABLE | title, priority, status, issue, plan, groomed, sections list with entry counts
AVAILABLE count: 2
DERIVABLE count: 2
MISSING count: 0
</div>

## Groomed (2026-03-22)

### Impact Radius

<div><sub>2026-03-22T12:21:11Z</sub>

### Recommended Approach

<div><sub>2026-03-22T12:22:23Z</sub>

### Implementation Scope

<div><sub>2026-03-22T12:22:37Z</sub>

### Success Criteria

<div><sub>2026-03-22T12:22:47Z</sub>

## Success Criteria

### Phase 1 Validation (Implementation Complete)

- [ ] New model `ViewItemResultCompact` defined in backlog_core/models.py with all required fields
- [ ] `backlog_view()` parameter `include_content: bool = True` added to server.py schema
- [ ] Routing logic implemented: `include_content=True` returns `ViewItemResult`, `include_content=False` returns `ViewItemResultCompact`
- [ ] `_build_sections_metadata()` accepts `include_content` parameter; skips entry assembly when False
- [ ] All 15 existing tests pass without modification (backward compatibility validated)
- [ ] New tests added:
  - `test_backlog_view_compact_mode_omits_body()` — PASS
  - `test_backlog_view_compact_mode_includes_sections_metadata()` — PASS
  - `test_backlog_view_default_includes_content()` — PASS
- [ ] `backlog-mcp-validator` agent runs and passes (no shape change on defaults)
- [ ] `test_scenarios.py` scenario C1 (compact view pagination) passes

### Phase 2 Validation (Skills Adoption)

- [ ] End-to-end test: `work-backlog-item` skill successfully matches items using compact view initial call
- [ ] End-to-end test: `add-new-feature` context injection works with compact view
- [ ] End-to-end test: `groom-backlog-item` skill continues working (default full-content call)
- [ ] SKILL.md documentation updated for backlog/SKILL.md, work-backlog-item/SKILL.md, add-new-feature/SKILL.md
- [ ] No regression in user-facing workflows: `/work-backlog-item`, `/add-new-feature`, `/groom-backlog-item` all function normally

### Phase 3 Validation (Future Optimization)

- [ ] Server-side optimization applied: `_build_sections_metadata()` with `include_content=False` skips entry loop
- [ ] Response size for compact view verified: < 2K tokens for groomed items (was 53K+)
- [ ] Performance test added: measure response time reduction for large backlog items
- [ ] All tests continue passing

### Definition of Done

**Phase 1 must be complete AND all Phase 1 validation gates pass before code is merged.**
**Phase 2 adoption may proceed in parallel with Phase 1 (no blocking dependency).**
**Phase 3 is deferred (optional future optimization).**

**Go/No-Go Gate Before Merge:**
- Every validation item in Phase 1 section shows [ ✅ DONE ]
- Zero test failures
- Zero agent validation failures
- User-facing workflows tested end-to-end
</div>


## Implementation Scope

### Files to Modify

**Core Implementation (2 files)**

1. **backlog_core/models.py**
   - Add `ViewItemResultCompact` Pydantic model with fields:
     - All metadata: `title`, `priority`, `issue`, `plan`, `file_path`, `groomed`, `status`, `number`, `state`
     - Compact sections: `sections_metadata: List[SectionMetadata]` where `SectionMetadata = {"name": str, "num_entries": int, "num_struck": int}`

2. **backlog_core/server.py**
   - Modify `backlog_view()` function signature to add `include_content: bool = True` parameter
   - Update tool schema documentation: "When `include_content=False`, returns section metadata only (name, entry counts) without full entry content. Default `True` preserves current behavior."
   - Routing logic: return `ViewItemResult` if `include_content=True`, return `ViewItemResultCompact` if `False`

**Operations Layer (1 file)**

3. **backlog_core/operations.py**
   - Modify `_build_sections_metadata()` to accept an `include_content: bool` parameter
   - When `include_content=False`, skip the entry assembly loop; return only `{"name": str, "num_entries": int, "num_struck": int}` per section
   - Call site: update `ViewBacklog` class method to pass parameter through

**Test Updates (2 files)**

4. **plugins/development-harness/tests/test_backlog_core_server.py**
   - Add new test: `test_backlog_view_compact_mode_omits_body()` — verify `include_content=False` returns `ViewItemResultCompact` without `body` key
   - Add new test: `test_backlog_view_compact_mode_includes_sections_metadata()` — verify section names and entry counts present
   - Add new test: `test_backlog_view_default_includes_content()` — verify default `include_content=True` maintains current behavior
   - Update existing test: `test_backlog_view_success_returns_item_detail()` — add assertion that default includes `body` key (documents current contract)

5. **plugins/development-harness/tests/test_scenarios.py**
   - Add new scenario: Scenario C1 (compact view pagination) — `backlog_view(..., include_content=False, offset=0, limit=5)` and verify no pagination side effects
   - Update scenarios S1072-S1128 (resolve workflow): no change needed (continue using defaults)

### Skill and Agent Updates (Non-blocking, Phase 2)

6. **plugins/development-harness/skills/work-backlog-item/SKILL.md** (Phase 2 only)
   - Document updated matching strategy: "First call uses `include_content=False` to retrieve metadata for title/state matching. If Strategy 3 (content-based matching) is needed, second call uses default `include_content=True`."
   - No code changes to skill itself; this is documentation of the capability available to sub-agents

7. **plugins/development-harness/skills/add-new-feature/SKILL.md** (Phase 2 only)
   - Document that agent context injection can use `include_content=False` for efficiency
   - No code changes required

### Documentation Updates (1 file)

8. **plugins/development-harness/skills/backlog/SKILL.md**
   - Update tool description for `backlog_view`: "View a single backlog item. By default returns full content; pass `include_content=False` for metadata-only response (section names and entry counts without content)."
   - Add parameter documentation for new `include_content` parameter

### No Changes Required

- **groom-backlog-item** skill: continues using defaults; no modification needed
- **backlog-mcp-validator** agent: validates default behavior (unchanged); no changes needed
- **backlog_list()** and other tools: unaffected
- Implementation-manager hooks: unaffected
</div>


## Recommended Approach

Start with **Option A (non-breaking addition)** deployed in two phases. This approach minimizes deployment risk while creating the foundation for future optimization.

### Phase 1: Add Metadata-Only Response Path

Add a new response model `ViewItemResultCompact` containing:
- All metadata fields: `title`, `priority`, `issue`, `plan`, `file_path`, `groomed`, `status`, `number`, `state`
- Compact sections: `sections_metadata: List[{"name": str, "num_entries": int, "num_struck": int}]` (section names and counts only, no entry content)

Modify `backlog_view()` to return the existing `ViewItemResult` (unchanged) for backward compatibility. Add an optional parameter:
- `include_content: bool = True` (default maintains current behavior; set to False returns compact view)

When `include_content=False`:
- Return `ViewItemResultCompact` (same metadata fields, but `sections_metadata` instead of full `sections`)
- Callers can iterate section names and counts without loading entry content

### Phase 2: Consume Compact View in Skills

Update three consuming skills to prefer compact view initially, then fetch full content only when needed:

1. **work-backlog-item**: On first call, use `include_content=False` to retrieve metadata for title/state matching. If full body is needed for content-based matching (Strategy 3), make a second call with `include_content=True`.

2. **add-new-feature**: Use `include_content=False` for issue context injection (title, priority, plan are sufficient); no second call needed.

3. **groom-backlog-item**: Continue using default (full content); already parses body for Impact Radius extraction. No skill change needed for Phase 1.

### Phase 3 (Future): Optimize Response Generation

Once Phase 1 and 2 are deployed and stable:
- Modify `_build_sections_metadata()` to skip entry content assembly when `include_content=False`
- This reduces server-side computation and response size for heavily-groomed items from 53K+ to ~2K tokens

### Risk Mitigation

- **No breaking changes**: All existing callers continue working with current default behavior
- **Staged rollout**: Phase 1 adds code, Phase 2 adopts it (in skills), Phase 3 optimizes server
- **Test validation**: All 15 existing tests pass without modification (backward compat); new tests added for compact mode
- **Validator clean**: `backlog-mcp-validator` agent continues passing (no response shape change on default calls)
</div>


## Systems Calling backlog_view

### Skill Delegation Points (3 skills call backlog_view)

1. **groom-backlog-item** (`plugins/development-harness/skills/groom-backlog-item/SKILL.md:158`)
   - Calls: `mcp__plugin_dh_backlog__backlog_view(selector="{title}")`
   - Purpose: Retrieve full item to extract file paths from Impact Radius sections
   - Impact: Receives FULL body content to parse Impact Radius, parse code/doc/config file paths
   - Downstream: Uses paths to route file changes to affected components
   - Regression risk: HIGH — body-to-paths extraction will break if response structure changes

2. **work-backlog-item** (`plugins/development-harness/skills/work-backlog-item/SKILL.md:100-172`)
   - Calls: `mcp__plugin_dh_backlog__backlog_view(selector="{selector}")`
   - Purpose: Match backlog item by title, issue number, or URL; extract issue state
   - Strategy 3 call: `backlog_list()` + `backlog_view(selector)` for semantic matching fallback
   - Impact: Receives full item including issue state, priority, description, groomed sections
   - Downstream: Decision branching on issue state (open vs closed); title/type/topic comparison
   - Regression risk: MEDIUM — expects full body for content-based matching; can accept metadata-only if metadata preserved

3. **add-new-feature** (`plugins/development-harness/skills/add-new-feature/SKILL.md:70-329`)
   - Calls: `backlog_view(selector="#{issue}")` (6 occurrences in agent context)
   - Purpose: Inject issue context into agent prompts for planning
   - Impact: Receives full item details to populate `{issue}`, `{title}`, `{work_type}` into agent context
   - Downstream: Used as human-readable context in planning agent system prompts
   - Regression risk: LOW — used for display/context only; tolerates metadata-only response if `title` field preserved

### Tests Asserting on Response Shape (15 test cases)

**Test file: `plugins/development-harness/tests/test_backlog_core_server.py`**
- `test_backlog_view_success_returns_item_detail()` — asserts dict keys: title, priority, issue, plan, file_path, body, sections
- `test_backlog_view_passes_pagination_params()` — validates offset/limit forwarding
- `test_backlog_view_backlog_error_returns_error_key()` — error handling
- `test_backlog_view_show_numeric_string_converts_to_int()` — parameter type coercion
- `test_backlog_view_show_non_numeric_string_passed_as_str()` — string passthrough
- Signature tests: `test_backlog_view_show_string_int_conversion()` — inspect.signature validation

**Test file: `plugins/development-harness/tests/test_scenarios.py`**
- Scenario 18 (offset/limit): `backlog_view(..., offset=0, limit=5)` validates pagination
- Scenario 23 (error): `backlog_view(selector="...")` with non-existent item
- Scenario S1072-S1128 (resolve workflow): `backlog_view` called to read item state during resolve

**Regression risk:** MEDIUM — 8 assertions on `body` and `sections` keys; 5+ on full response structure. Tests will fail if response dict structure changes.

### Agent Delegation (2 agents reference backlog_view)

1. **backlog-mcp-validator** (`.claude/agents/backlog-mcp-validator.md`)
   - Purpose: Validate MCP server against CLI; calls `backlog_view` as part of validation suite
   - Calls: `backlog_view(selector=...)` to retrieve item and check response dict shape
   - Regression risk: HIGH — this is a validator; any shape change will be caught and reported as a failure

2. **backlog-item-groomer** (`.claude/agents/backlog-item-groomer.md`)
   - Purpose: Produce groomed content; discovers related skills, agents, dependencies
   - Uses: `backlog_view` to retrieve full item during grooming assessment
   - Regression risk: MEDIUM — used to assess item completeness; tolerates metadata-only if critical fields preserved

### Documentation References (8 docs mention backlog_view)

1. **SKILL.md (backlog/SKILL.md:56-58)** — documents backlog_view as "View a single backlog item in detail. Supports pagination for long bodies."
2. **backlog/SKILL.md:203-217** — lists backlog_view among available tools
3. **add-new-feature/SKILL.md:329** — states {title} comes from `backlog_view(selector="#{issue}")`
4. **work-milestone/SKILL.md:145-233** — lists backlog_view as tool used by spawned sessions to self-discover item content
5. **groom-milestone/SKILL.md:86-88** — lists backlog_view in tool inventory
6. **complete-implementation/SKILL.md:94-95** — shows example backlog_view call
7. **work-backlog-item/SKILL.md:100-411** — extensive documentation of matching strategy with backlog_view calls

**Regression risk:** LOW-MEDIUM — most are reference documentation; none assert specific response shape. Updating SKILL.md docs is straightforward.

## Impact Checklist (5-Question Framework)

### Q1: What systems will break?

**High impact (code-level breaks):**
- `groom-backlog-item` skill: body parsing will fail if `body` key is removed or structure changes
- `test_backlog_core_server.py`: 8 test assertions on `body` and `sections` keys will fail
- `test_scenarios.py`: pagination tests assert on returned body length

**Medium impact (functional breaks):**
- `work-backlog-item` skill: semantic matching uses full body for content comparison; would need fallback
- `backlog-mcp-validator` agent: response validation will report shape changes as errors

**Low impact (display-only breaks):**
- `add-new-feature` context injection: graceful if title/priority still present
- Documentation: easily updated once change is finalized

### Q2: What new behaviors are consumers expecting?

All current callers expect **full body content by default**. None expect compact metadata. Progressive disclosure is a NEW feature, not a requirement of existing consumers.

**Consumers' actual needs (inferred):**
- Skills need: `title`, `issue`, `priority`, `plan`, `file_path`, `sections` (metadata + section headers, not content)
- Body content is needed only by: `groom-backlog-item` (parsing) and `test_scenarios.py` (pagination testing)
- All other callers can tolerate metadata-only response

### Q3: What's the minimal change that preserves backward compatibility?

**Option A: Expand current response**
- Current tool returns: `{title, priority, issue, plan, file_path, body, sections, messages, warnings}`
- Add new field: `sections_metadata: {name, entry_count, has_content}` (list, no body content)
- Callers receive both full `body` AND compact `sections_metadata` in same call
- Tests pass unchanged; no behavior breaking

**Option B: Add optional response mode**
- New parameter: `response_format="full"` (default) or `response_format="compact"`
- `full` (default): current behavior, backward compatible
- `compact`: returns only metadata (title, issue, priority, sections_metadata) without body
- Callers opt-in to compact mode; existing code unaffected

**Option C: Token-aware default (my recommendation)**
- Change default behavior: return metadata-only + section headers
- Response grows only if caller explicitly requests: `include_body=true`
- **Breaking change:** skills calling groom-backlog-item and tests fail immediately
- **Benefit:** forces explicit intent; surfaces which callers truly need body

### Q4: What testing strategy catches regressions?

**Required tests:**
- `test_backlog_view_metadata_only_default()` — verify default response omits body
- `test_backlog_view_full_response_with_include_body()` — verify `include_body=true` returns body
- `test_backlog_view_pagination_with_body()` — pagination only works with `include_body=true`
- `test_groom_backlog_item_receives_full_body()` — skill delegation test; ensures groom-backlog-item calls with `include_body=true`
- `test_work_backlog_item_matches_on_metadata()` — matching strategy tolerates metadata-only initial call
- `test_add_new_feature_context_injection()` — agent context population works with metadata-only response

**Existing tests that WILL fail (need updating):**
- `test_backlog_view_success_returns_item_detail()` — assertion on `body` key presence
- `test_backlog_view_passes_pagination_params()` — pagination assertion on body structure
- 6 test_scenarios.py cases (offset/limit/pagination)

### Q5: What's the deployment risk?

**Risk level: MEDIUM-HIGH**

**Deployment blockers:**
1. `groom-backlog-item` skill is used by `groom-milestone` workflow; failing groom breaks milestone planning
2. `work-backlog-item` skill is a top-level user-facing skill; breaking it blocks user workflows
3. No feature flag to soften rollout (Option C requires immediate migration)

**Mitigation strategy:**
1. Start with Option A (non-breaking): add `sections_metadata` field alongside current `body`
2. Update consuming skills to prefer `sections_metadata` when available
3. Deploy in two phases: Phase 1 (add field), Phase 2 (optimize response generation to skip body when not requested)
4. Tests pass throughout both phases; no runtime breakage

**Go/no-go gates:**
- All 15 existing tests pass without modification (backward compat)
- New compact-metadata tests added and passing
- `groom-backlog-item` and `work-backlog-item` skills tested end-to-end
- No agent validation failures in `backlog-mcp-validator`
</div>

## Fact-Check

<div><sub>2026-03-22T12:21:40Z</sub>

## Fact-Check Results

**All 5 claims verified against source code (backlog_core/server.py and backlog_core/operations.py)**

### Claim 1: "backlog_view returns full section content by default"
✅ VERIFIED
- `ViewItemResult` model includes `body: str = ""` field holding the complete item body
- `_build_sections_metadata()` extracts each entry's full `"content"` field into the sections dict (line 1364)
- No default truncation applied

### Claim 2: "producing responses that exceed context limits (53k+)"
✅ PLAUSIBLE
- Tool returns unrestricted `body` (entire item text) plus full entry content for all entries in all sections
- Large backlog items with many timestamped entries easily exceed 53K characters
- No built-in size limit or default pagination

### Claim 3: "show parameter exists with values: all, last, first, struck, N"
✅ VERIFIED (with extension)
- Tool schema accepts: `"all"`, `"last"`, `"first"`, `"struck"`, positive integer N (first N active entries), negative integer (last N active), or section name string (case-insensitive)
- Source: server.py line 26 parameter definition + operations.py line 1335-1338

### Claim 4: "offset and limit parameters exist"
✅ VERIFIED
- `offset` (default 0): "Skip N entry blocks from body start (for pagination)"
- `limit` (default 0): "Show at most N entry blocks (0 = all, no truncation)"
- Both control pagination of the body's entry blocks
- Source: server.py function signature

### Claim 5: "Does backlog_view currently return section names and entry counts? Or only full content?"
✅ VERIFIED: Returns BOTH
- Each section in the `sections` dict includes:
  - `"num_entries"`: count of non-struck entries
  - `"num_struck"`: count of struck entries  
  - `"entries"`: list of full entry dicts with `{"id", "struck", "content"}`
- Progressive disclosure IS partially implemented at the section level (counts provided)
- BUT entries themselves always include full content — no way to get just the count or ID without the full content
- Source: operations.py line 1370
</div>

## RT-ICA

<div><sub>2026-03-22T12:23:12Z</sub>

RT-ICA Final: Progressive disclosure for backlog_view
Goal: Make backlog_view return compact metadata by default, with section content expandable on demand.
Conditions:
1. Current backlog_view response structure | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: fact-checker verified ViewItemResult includes unrestricted body field and _build_sections_metadata() returns full entry content (server.py, operations.py)
2. Existing show and limit parameters | Snapshot: AVAILABLE → Final: AVAILABLE | Citation: tool schema confirmed show (all/last/first/struck/N/section-name), since, offset, limit
3. How section content is assembled | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: fact-checker verified section metadata is built (entry counts) but content is always included — progressive disclosure partially exists
4. Compact view fields needed | Snapshot: AVAILABLE → Final: AVAILABLE | Citation: impact-analyst confirmed callers need title, priority, status, issue, plan, groomed, section names + entry counts
Decision: APPROVED
</div>