---
name: Validate agent-browser for Web Automation
description: "Test agent-browser (Playwright-based) on host with unrestricted network
  and Playwright browsers installed.\n**Validation steps**:\n- Install browsers: `npx
  playwright install`\n- Test: `npx agent-browser open https://code.claude.com/docs/en/skills`\n\
  - Test: `npx agent-browser snapshot -i` (get element refs)\n- Test: `npx agent-browser
  get text body` (extract page text)\n- Verify snapshot/interact/re-snapshot workflow
  works\n- Document prerequisites for skill to function\n**Blocked on 2026-02-05**:
  Could not download Playwright browsers (DNS resolution failed, missing system libs)\n\
  **Skill location**: `.claude/skills/agent-browser/SKILL.md`"
metadata:
  topic: validate-agent-browser-for-web-automation
  source: Session experimentation 2026-02-05
  added: '2026-02-05'
  priority: P2
  type: Feature
  status: open
---
