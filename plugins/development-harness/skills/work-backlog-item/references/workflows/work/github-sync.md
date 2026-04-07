# GitHub Issue Sync (Steps 2.2–2.4)

> **Repository**: OWNER/REPO is discovered via `discover_repo()` from `backlog_core.models`. Use MCP tools for all GitHub operations — no `gh` CLI required.

## Step 2.2: GitHub Issue Sync

After extracting item fields, check for an existing linked issue:

1. Search the matched item for `**Issue**: #N` field.
2. If found: issue already linked. Run:

   ```text
   MCP: backlog_view(selector="#N")
   ```

   Report the issue state. If open, proceed. If closed, warn the user before re-opening planning.

3. If not found AND priority is P0 or P1: offer to create a GitHub Issue:

   ```text
   This P1 item has no linked GitHub issue. Create one? (yes/no)
   ```

   If yes, proceed to Step 2.3.
   If no, skip GitHub sync; the per-item file remains the only local record.

4. If not found AND priority is P2 or Ideas: do not prompt; skip GitHub sync silently.

## Step 2.3: Create GitHub Issue

Call the `mcp__plugin_dh_backlog__backlog_update` tool with `selector="{title}"`.

The tool creates the issue automatically when the item lacks one and writes `issue: '#N'` back to the per-item file frontmatter. Check the returned dict for an `error` key.

## Step 2.4: Set In-Progress Label

Call the `mcp__plugin_dh_backlog__backlog_update` tool with `selector="{title}"` and `status="in-progress"`. Check the returned dict for an `error` key.

If the item is in a milestone with other issues, also run `milestone start` to bulk-transition all open milestone issues to in-progress:

```text
MCP: backlog_update(selector="{title}", status="in-progress")
```

> **Note**: Bulk milestone start (transitioning all issues in a milestone) is not yet available as a single MCP tool call. Use `backlog_list_issues(milestone="{milestone_title}")` to enumerate milestone issues, then `backlog_update` each one individually.
