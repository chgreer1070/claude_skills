#!/usr/bin/env node
/**
 * SessionStart hook — reminds about backlog workflow tooling.
 * The backlog is managed via /work-backlog-item and GitHub Issues.
 */

const output = {
  additionalContext: `<backlog-context>
When you identify work needs multiple steps/jobs: create backlog items — don't just describe them.
- Create: create-backlog-item (or backlog add)
- Match/browse: work-backlog-item
- GitHub setup: work-backlog-item setup-github (first-time)
Reference: .claude/skills/work-backlog-item/SKILL.md
</backlog-context>`,
};

console.log(JSON.stringify(output));
