# Post-Planning Output (Steps 4.5 + 4.5a)

<!-- NOTE: This file is only loaded in interactive mode (see plan.md Step 4.5).
     Auto mode routes directly back to start.md steps 6–8 without loading this file. -->

## Interactive mode (Step 4.5)

```text
Backlog item "{title}" is now planned.

- Plan: accessible via `sam_plan(action='read', plan="{slug}")` MCP tool
- To execute:      /implement-feature {slug}
- To check status: /implementation-manager status . {slug}
- To close when done: /work-backlog-item close {title}
```

**Do NOT close the GitHub Issue directly.** Do NOT include `Fixes #N`, `Closes #N`, or `Resolves #N` in task-level commit messages or PR bodies — issue closure is handled exclusively by `/complete-implementation` in its final commit step. Only use `/work-backlog-item resolve` for post-merge verification and local bookkeeping. Use `/work-backlog-item close` only for dismissals (duplicate, out_of_scope, etc.). Never call `mcp__plugin_dh_backlog__backlog_resolve` before the PR has merged.
