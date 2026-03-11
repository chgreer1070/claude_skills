---
name: Fix irritation command false positives — remove agent-control words from correction phrases
description: The _CORRECTION_PHRASES constant was defined in the architecture spec and implemented verbatim without validating the phrases against real session JSONL data. Words like "stop", "undo", "revert", "don't", "no," appear in ordinary conversational user messages in contexts unrelated to frustration. No analysis of actual session data was done before or during implementation to verify that each phrase reliably signals user frustration when it appears in a user-role record. Before fixing the phrase list, sample real session JSONL files and examine how each phrase actually appears in context. The fix should be driven by observed data, not a revised guess at a better list.
metadata:
  topic: fix-irritation-command-false-positives-remove-agent-control-
  source: User feedback — 2026-03-11
  added: '2026-03-11'
  priority: P1
  type: Bug
  status: open
---