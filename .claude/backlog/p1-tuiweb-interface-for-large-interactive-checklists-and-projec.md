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
  last_synced: '2026-03-05T04:24:48Z'
---