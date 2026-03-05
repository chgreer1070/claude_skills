---
name: TUI/Web interface for large interactive checklists and project tree editing
description: "AskUserQuestion is limited to 3-5 questions per screen, which is insufficient when Claude needs to present large option sets to the user — e.g., filling in project templates with selective add/remove of components, displaying a project tree where the user can append or remove entries, or presenting screenshots and gathered images as selectable options for feedback.\n\nProblem: No mechanism exists for Claude to present a scrollable, interactive checklist or tree view where users can toggle items on/off, add custom entries, or browse visual options. Current workaround is multiple rounds of AskUserQuestion which is slow and loses context.\n\nSuccess looks like: Claude can present a project scaffold tree (or similar large structured list) in a TUI or web panel, the user can check/uncheck items, add new entries, remove unwanted ones, and submit the result back to Claude in a single interaction. Images/screenshots can be displayed as option cards.\n\nHow to verify: A skill or tool can render 20+ items in a single interactive view, user can modify the selection, and the result is returned to Claude as structured data.\n\nResearch first:\n? How does CopilotKit (research/agent-frameworks/copilotkit.md) handle agent-driven UI rendering and user feedback loops?\n? How does JSON Render (research/agent-frameworks/json-render.md) handle dynamic form/tree generation from agent output?\n? What TUI frameworks (textual, rich, blessed) support checkbox trees with real-time agent communication?"
metadata:
  topic: tuiweb-interface-for-large-interactive-checklists-and-projec
  source: User request
  added: '2026-03-05'
  priority: P1
  type: Feature
  status: open
  issue: '#437'
  last_synced: '2026-03-05T04:32:29Z'
  groomed: '2026-03-05'
---

## Fact-Check

**Claims checked**: 5
**VERIFIED**: 3 | **REFUTED**: 0 | **INCONCLUSIVE**: 2

| Claim | Verdict | Source |
|-------|---------|--------|
| No native Claude Code mechanism exists for scrollable, interactive checklist/tree views | VERIFIED | Claude Code tool inventory (AskUserQuestion, Bash, Read, Write, Edit) — no interactive TUI component exists SOURCE: Claude Code tool definitions, 2026-03-05 |
| CopilotKit handles agent-driven UI rendering and user feedback loops | VERIFIED | `useCopilotAction` render pattern, human-in-the-loop checkpoints, bi-directional state sync SOURCE: research/agent-frameworks/copilotkit.md (accessed 2026-02-23) |
| JSON Render handles dynamic form/tree generation from agent output | VERIFIED | Catalog+Zod schema system constrains AI to a defined component vocabulary; `defineCatalog` + `@json-render/shadcn` (39 pre-built components) covers interactive form generation SOURCE: research/agent-frameworks/json-render.md (accessed 2026-02-26) |
| AskUserQuestion is limited to 3-5 questions per screen | INCONCLUSIVE | The practical limitation on option count is observed behavior; the exact "3-5" number is not documented in official Claude Code sources. The broader claim (insufficient for 20+ items) is consistent with observed behavior. |
| TUI frameworks (textual, rich, blessed) support checkbox trees with real-time agent communication | INCONCLUSIVE | Textual (Textualize) has documented Checkbox and Tree widget support for interactive terminals. Rich is display-only (not interactive). Blessed is JavaScript (not Python). The claim bundles mismatched tools. "Real-time agent communication" mechanism is unspecified — no research file confirms IPC pattern. |

**Refuted claims**: None
**Inconclusive claims**: "3-5 questions limit" (unverified number); "textual, rich, blessed" bundle (rich is not interactive; blessed is JS)

## RT-ICA

**Goal**: Enable Claude to present 20+ items in a single interactive view where users can toggle, add, remove, and submit results as structured data in one round-trip.

**Conditions**:

1. Claude Code's AskUserQuestion is insufficient for 20+ item interactive selection | **AVAILABLE** | Observed behavior; item description documents the problem with sufficient specificity
2. Claude Code's Bash tool can launch external processes (TUI or web server) | **AVAILABLE** | Bash tool launches any shell command; a Python TUI or local HTTP server is launchable
3. A Python TUI framework (e.g., Textual) supports checkbox trees and tree editing | **DERIVABLE** | Textual has documented Checkbox and Tree widget support; specific checkbox-tree pattern requires research validation
4. A mechanism exists for returning structured JSON from the TUI/web UI back to Claude | **MISSING** | No research or design covers the IPC return path (stdout capture, temp file, local HTTP callback, etc.)
5. CopilotKit or json-render could serve as the web UI layer for a browser-based variant | **DERIVABLE** | Both frameworks support interactive component rendering; neither is purpose-built for CLI-to-browser round-trip
6. The solution integrates as a Claude Code skill/tool that can be invoked from any skill | **MISSING** | No integration contract defined (tool name, invocation API, return schema)
7. Images and screenshots can be displayed as selectable option cards | **MISSING** | No research covers image display in terminal or browser within a Claude Code skill context

**Decision**: APPROVED
**Missing inputs for planning**: (4) structured result return path (IPC mechanism), (6) skill integration contract and API, (7) image display mechanism

## Groomed (2026-03-05)

### Priority

8/10 — Unblocks large-scale interactive workflows that currently require 5+ sequential AskUserQuestion rounds. High impact on user experience for project scaffolding, template filling, and visual feedback loops. Currently no mechanism exists; workaround is slow and loses context across rounds.

### Impact

- Blocks: Any Claude Code skill that needs to present 20+ items for user selection/modification in a single interaction
- Bottleneck: Project template scaffolding, dependency selection, tree-based configuration, visual option browsing
- Affects: Skills built around structured decision-making (e.g., plugin-creator, project-init workflows)

### Benefits

- Single round-trip interaction for large option sets instead of 5+ sequential prompts
- Preserve full context across user selections
- Structured return value (JSON) integrates cleanly with Claude Code tools
- Enables visual feedback loops (screenshots, images as selectable cards)
- Foundation for interactive project tree editing workflows

### Expected Behavior

Claude can invoke an interactive UI component (TUI or web) from within a skill execution context. The component:
- Renders 20+ items in a scrollable view
- Allows user to toggle, add, remove, or reorder items
- Returns structured result (JSON or Python dict) to Claude automatically
- Blocks skill execution until user submits result (synchronous interaction model)
- Optionally displays images/screenshots as selectable cards alongside text options

### Desired Structure

A Claude Code skill or tool that acts as a bridge between Claude and an interactive UI system. Architecture decisions (TUI vs web, framework choice, IPC method) are open and will be determined during planning. Target outcome:
- **Tool invocation**: `Tool(tool: "interactive-select", items: [...], config: {...})` or `Skill(skill: "interactive-select", args: "...")`
- **Return contract**: Structured JSON result with selected items, added items, removed items, or reordered state
- **Integration**: Works from any skill context, returns data to Claude for further processing
- **State management**: No persistent state between invocations; each call is stateless

### Acceptance Criteria

1. Can render a list of 20+ items in a single view (not paginated via AskUserQuestion prompts)
2. User can toggle items on/off (checkbox interaction) without exiting the view
3. User can add custom entries to the list during interaction
4. User can remove entries from the list during interaction
5. Final result is returned to Claude as structured data (JSON dict or equivalent)
6. Result is deterministic and repeatable (same selections -> same output)
7. Interaction completes in under 30 seconds for typical 20-50 item lists
8. Tool/skill loads without external dependencies not already in Claude Code environment

### Questions for Human

- **Scope priority**: Would TUI (terminal-based, no browser) be acceptable, or is web UI required?
  - TUI enables faster integration but requires tmux/pty handling; web requires local HTTP server or WebSocket

- **Image support**: Must images/screenshots be displayed as option cards, or is text-only sufficient for first version?
  - Image support requires image loading and caching; adds complexity but unlocks visual feedback workflows

- **Return binding**: Should the result automatically resume skill execution, or does the skill need explicit code to parse and continue?
  - Automatic binding (tool blocks until result arrives) vs manual binding (skill polls for result) affects integration complexity

- **Persistence model**: Should the UI support "save and resume later" (with serialized state), or is session-scoped interaction sufficient?
  - Session-only is simpler; persistence enables multi-session workflows

### Resources

| Type | Item |
|------|------|
| Research | [CopilotKit](../../research/agent-frameworks/copilotkit.md) — React/TypeScript framework for agent-driven UI with bi-directional state sync |
| Research | [json-render](../../research/agent-frameworks/json-render.md) — Generative UI framework with catalog constraints and streaming support |
| Skill | agent-browser — existing skill for rendering and browser interaction |
| Prior work | plugins/development-harness/agents/service-docs-maintainer.md — example of complex UI workflows in SAM |

### Dependencies

- Depends on: None
- Blocks: Any P1/P2 items requiring interactive checklist workflows (future items, not yet backlogged)

### Blockers

None. RT-ICA decision is APPROVED. Missing inputs (IPC mechanism, skill integration contract, image display method) are planning-phase decisions, not prerequisites for grooming.

### Effort

Medium — Proof of concept (TUI with Textual + stdout capture) is achievable in 2-3 days. Full web UI variant (CopilotKit/json-render integration) requires Node.js setup and is 4-5 days. Image support adds 1-2 days. Integration as reusable skill adds 1-2 days. Effort scales with scope decisions.

### Issue Classification

**Type**: unbounded-design
**Rationale**: This is a capability gap with multiple valid implementation paths. No failure chain, no recurring defect, no missing guardrail. The problem is well-scoped but the solution space is open (TUI vs web vs hybrid).
**Analysis Method**: design-framing
**Scenario Target**: Claude needs to present 20+ item checklist/project tree for user selection → user completes interaction in one round-trip → structured result returned to Claude