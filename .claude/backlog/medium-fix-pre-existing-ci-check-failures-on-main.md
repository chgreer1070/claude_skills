---
name: Fix pre-existing CI check failures on main
description: "6 CI checks fail on main (and all PRs) due to pre-existing issues:\n\n1. Python/Ruff: DOC201/ANN401/S202/PLR0911 in gh/, research-curator/, session-historian/, agentskill-kaizen/, plugin-creator/, uv/ scripts\n2. Python/ty: unresolved gitlab imports + mix_stderr arg removed in newer click (gh tests, plugin-creator conftest)\n3. Python/Tests: CliRunner mix_stderr (~30 ERRORs in plugin-creator) + panel.extension missing in agentskill-kaizen\n4. JSON/Prettier: plugins/agentskill-kaizen/.mcp.json and plu"
metadata:
  topic: fix-pre-existing-ci-check-failures-on-main
  source: Not specified
  added: '2026-02-26'
  priority: medium
  type: Bug
  status: open
  issue: '#281'
---