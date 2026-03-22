# Feature Context: Progressive Disclosure for backlog_view

**Issue**: [#987](https://github.com/Jamie-BitFlight/claude_skills/issues/987)
**Status**: in-progress
**Priority**: P1
**Type**: refactor

---

## Problem Statement

The `backlog_view` MCP tool returns full section content (entry bodies, timestamps, all metadata) by default. For heavily-groomed backlog items, this produces responses exceeding 53,000 characters -- observed on issue #965 during a 2026-03-21 session. This volume consumes a large portion of the agent's context window on a single tool call, leaving insufficient context for the agent's actual task.

SOURCE: Session observation, 2026-03-21. Verified against `backlog_core/server.py` and `backlog_core/operations.py` -- `ViewItemResult` includes unrestricted `body` field and `_build_sections_metadata()` returns full entry content with no default truncation.

### Current State

The tool already provides partial progressive disclosure at the section level:

- Each section in the `sections` dict includes `num_entries` and `num_struck` counts
- But entries always include full `content` -- there is no way to retrieve counts without content
- Existing `show`, `offset`, and `limit` parameters control pagination of entries but do not suppress content

SOURCE: Fact-check against operations.py line 1370 -- entry dicts contain `{id, struck, content}` unconditionally.

### Root Cause

The tool was designed for a single use case (read everything) and later gained pagination parameters (`show`, `offset`, `limit`, `since`). But the response model (`ViewItemResult`) has no mode that returns metadata without content. Callers that only need item title, priority, status, and section inventory must still receive the full body.

---

## Desired Outcome

Callers can retrieve backlog item metadata and section inventory (section names, entry counts) without receiving full entry content. Full content remains available on demand. Existing callers continue working without modification.

### Success Indicators

- Default response preserves current behavior (no breaking change)
- A compact response mode exists that returns metadata + section names with entry counts, without entry content
- Compact response size is under 2K tokens for groomed items (vs 53K+ currently for full response)
- All existing tests pass without modification
- Consuming skills and agents function normally

---

## Stakeholders

### Direct Consumers (call `backlog_view` in code or skill logic)

| Consumer | What it needs from backlog_view | Needs full content? |
|---|---|---|
| `groom-backlog-item` skill | Full body to parse Impact Radius file paths | Yes -- body-to-paths extraction depends on entry content |
| `work-backlog-item` skill | Title, issue number, state for matching; full body only for Strategy 3 (semantic fallback) | Sometimes -- metadata sufficient for primary matching |
| `add-new-feature` skill | Title, priority, plan for agent context injection | No -- metadata fields sufficient |
| `backlog-mcp-validator` agent | Response dict shape validation | Yes -- validates full response structure |
| `backlog-item-groomer` agent | Full item for completeness assessment | Yes -- assesses section content |

SOURCE: Skill files at `plugins/development-harness/skills/{groom-backlog-item,work-backlog-item,add-new-feature}/SKILL.md`; agents at `.claude/agents/{backlog-mcp-validator,backlog-item-groomer}.md`.

### Indirect Consumers (reference `backlog_view` in documentation)

Seven SKILL.md files and one agent file reference `backlog_view` in documentation or tool inventories: `backlog/SKILL.md`, `work-milestone/SKILL.md`, `groom-milestone/SKILL.md`, `complete-implementation/SKILL.md`, `work-backlog-item/SKILL.md`, `add-new-feature/SKILL.md`. These are documentation-only references -- none assert specific response shape.

### Test Surface

- `test_backlog_core_server.py`: 6+ test functions assert on response dict keys including `body` and `sections`
- `test_scenarios.py`: pagination scenarios (18, 23, S1072-S1128) exercise `backlog_view` with `offset`/`limit`

SOURCE: Issue #987 groomed content, "Tests Asserting on Response Shape" section.

---

## Risks

### Backward Compatibility

The primary risk is breaking existing callers. Any change to default response shape will fail:

- 8+ test assertions on `body` and `sections` keys
- `groom-backlog-item` body parsing
- `backlog-mcp-validator` shape validation

Mitigation constraint: the default behavior must remain unchanged. Compact mode must be opt-in.

### Cascading Workflow Breakage

`groom-backlog-item` is called by `groom-milestone`. If the groom skill breaks, milestone planning breaks. `work-backlog-item` is a top-level user-facing skill. These are high-traffic paths.

### Parameter Semantics Overlap

The tool already has `show`, `offset`, `limit`, and `since` parameters. Adding a new parameter for content inclusion creates a question of how it interacts with existing parameters. For example: does `show="last"` with compact mode return the last entry's metadata without content, or is it an error? These interactions need explicit design.

### Response Model Divergence

If compact mode returns a different model structure than full mode, callers that switch between modes must handle two response shapes. This adds complexity to consuming code and documentation.

---

## Open Questions

1. **Parameter naming**: Should the compact mode be controlled by a boolean (`include_content`), an enum (`response_format`), or by extending the existing `show` parameter semantics?

2. **Interaction with existing pagination**: How should `offset`, `limit`, `since`, and `show` behave when content is suppressed? Should they be ignored, produce an error, or still filter the section inventory?

3. **Section-level expansion**: Should callers be able to request content for specific sections (e.g., "give me metadata for all sections but full content for 'Recommended Approach'")? Or is it all-or-nothing (compact vs full)?

4. **Body field in compact mode**: Should the compact response omit the `body` key entirely, or include it as an empty string? Omitting it changes the response shape; including it as empty preserves shape but may mislead callers into thinking the item has no body.

5. **Validator update timing**: The `backlog-mcp-validator` agent validates response shapes. When should it be updated -- simultaneously with the server change, or after Phase 1 is stable?

6. **Token budget target**: The 2K token target for compact responses -- is this a hard requirement or a guideline? What if section metadata alone exceeds 2K for items with many sections?

---

## Constraints

- **No breaking changes to defaults**: Existing callers must work without modification when using current parameter values
- **Backward-compatible response shape**: Default `backlog_view()` call must return the same dict keys as today
- **Test stability**: All 15 existing tests must pass without modification after Phase 1
- **MCP schema compliance**: New parameters must be valid FastMCP parameter types with proper descriptions
