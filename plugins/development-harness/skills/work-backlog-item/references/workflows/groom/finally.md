# Groom: Finally

Runs after every groom workflow exit — whether the outcome is Groomed, Blocked, Skipped, Drift, or Error. This is cleanup, not error handling.

## Steps

1. **Sync state**: call `mcp__plugin_dh_backlog__backlog_sync(flush_only=true)` to export current state to JSONL. This ensures any status changes (blocked, groomed) are persisted regardless of how the workflow exited.

2. **Report terminal state**: emit a one-line summary to the caller with the outcome:

   | Outcome | Report |
   |---|---|
   | Groomed | `Grooming complete for <item_ref/>. Item is ready for planning.` |
   | Blocked (RT-ICA) | `Grooming blocked for <item_ref/>: unresolved MISSING conditions.` |
   | Blocked (validation) | `Grooming blocked for <item_ref/>: required sections missing after 3 attempts.` |
   | Blocked (error) | `Grooming blocked for <item_ref/>: {error summary}. Backlog item created for the issue.` |
   | Skipped | `Skipped <item_ref/>: {skip reason}.` |
   | Drift | `Drift check complete for <item_ref/>. See drift section in item.` |

3. **Return control**: the groom workflow is done. Control returns to the caller — either the SKILL.md router (if groom was the target route) or the work workflow's `prepare.md` (if groom ran as a prerequisite for the work route).
