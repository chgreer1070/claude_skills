Your name and current agent-id is: AGENT_ID_HERE

Describe your capabilities in 2-4 sentences. Cover: what you do, what inputs you accept, what outputs you produce, and any key constraints or specializations that distinguish you from a general-purpose agent. Keep the entire description on a single line — no newlines.

After writing your description, run this exact command (replace `CAPABILITIES_HERE` with your description — escape any single quotes in the description as `'\''`):

```bash
node $CLAUDE_PLUGIN_ROOT/scripts/update-agent-map.mjs --name "AGENT_ID_HERE" --capabilities 'CAPABILITIES_HERE'
```

Confirm success by reporting: `Updated agent-map.db`

If the Bash tool is unavailable, return only the capabilities text so the orchestrator can write it.
