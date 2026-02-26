---
name: Validate carbonyl Terminal Browser
description: "Test carbonyl on host with proper TTY and network access.\n**Validation
  steps**:\n- Test basic: `npx -y carbonyl --no-sandbox https://example.com`\n- Test
  with tmux: `tmux new-session -d -s carbonyl 'npx -y carbonyl --no-sandbox https://example.com'`\n\
  - Test screenshot capture: Can we grab terminal output as image?\n- Test text extraction:
  Can we pipe output or capture rendered text?\n- Compare JS rendering quality with
  other tools\n**Blocked on 2026-02-05**: Needs TTY (Inappropriate ioctl for device),
  DNS also blocked\n\n---"
metadata:
  topic: validate-carbonyl-terminal-browser
  source: Session experimentation 2026-02-05
  added: '2026-02-05'
  priority: P2
  type: Feature
  status: open
---
