#!/usr/bin/env node
/**
 * SessionStart hook — reminds about backlog workflow tooling.
 * The backlog is managed via /work-backlog-item and GitHub Issues.
 */

const output = {
  additionalContext: `<backlog-context>
Backlog workflow: use /work-backlog-item to browse, plan, and track items.
GitHub integration: /work-backlog-item setup-github (first-time setup of labels, milestone, project).
Reference: .claude/skills/work-backlog-item/SKILL.md
</backlog-context>`,
};

console.log(JSON.stringify(output));
