---
name: Audit tests that document bugs as 'limitations' — update after fixes
description: "During backlog MCP scenario testing (#328), a prior bugfix to _parse_frontmatter (preserving nested metadata dicts) caused test_parse_frontmatter_nested_meta_produces_empty_meta_dict to fail. The test explicitly asserted the buggy behavior (meta == {}) with a comment calling it a 'documented limitation'. This pattern — tests that enshrine bugs as expected behavior — can mask regressions and block fixes. Action: audit existing test suite for similar patterns where tests document current behavior as intentional limitations rather than testing correct behavior. Check for comments containing 'limitation', 'known issue', 'current behavior', 'workaround' that may be masking bugs."
metadata:
  topic: audit-tests-that-document-bugs-as-limitations-update-after-f
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: open
  issue: '#335'
  last_synced: '2026-03-01T13:21:03Z'
---