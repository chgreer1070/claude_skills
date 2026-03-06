#!/usr/bin/env node
/**
 * UserPromptSubmit hook — injects pending background task notifications.
 *
 * On each user message, checks .claude/notifications/ for pending JSON files.
 * If any exist, formats them as additionalContext and moves them to processed/.
 * Zero cost when no notifications are pending (fast fs check, no API calls).
 */

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const notifDir = path.join(projectDir, '.claude', 'notifications');

if (!fs.existsSync(notifDir)) {
  process.exit(0);
}

const files = fs
  .readdirSync(notifDir)
  .filter((f) => f.endsWith('.json'))
  .sort();

if (files.length === 0) {
  process.exit(0);
}

const processedDir = path.join(notifDir, 'processed');
if (!fs.existsSync(processedDir)) {
  fs.mkdirSync(processedDir, { recursive: true });
}

const parts = [];

for (const file of files) {
  const filePath = path.join(notifDir, file);
  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    // Skip malformed files but don't leave them to re-fire
    fs.renameSync(filePath, path.join(processedDir, file));
    continue;
  }

  // Archive immediately — only fires once
  fs.renameSync(filePath, path.join(processedDir, file));

  if (data.type === 'timeout') {
    parts.push(
      `BACKGROUND TASK TIMEOUT\n` +
        `PR: #${data.pr} (${data.repo})\n` +
        `Bot: ${data.bot}\n` +
        `Message: ${data.message}`,
    );
  } else if (data.type === 'review') {
    parts.push(
      `BACKGROUND TASK COMPLETE — COPILOT REVIEW POSTED\n` +
        `PR: #${file.match(/pr(\d+)/)?.[1] ?? 'unknown'}\n` +
        `State: ${data.state}\n` +
        `Author: ${data.user}\n` +
        `URL: ${data.url}\n` +
        `Submitted: ${data.submitted_at}\n\n` +
        `--- Review Body ---\n${data.body}\n--- End Review Body ---`,
    );
  } else if (data.type === 'comment') {
    parts.push(
      `BACKGROUND TASK COMPLETE — BOT COMMENT POSTED\n` +
        `PR: #${file.match(/pr(\d+)/)?.[1] ?? 'unknown'}\n` +
        `Author: ${data.user}\n` +
        `URL: ${data.url}\n` +
        `Created: ${data.created_at}\n\n` +
        `--- Comment Body ---\n${data.body}\n--- End Comment Body ---`,
    );
  } else {
    parts.push(`BACKGROUND TASK NOTIFICATION\n${JSON.stringify(data, null, 2)}`);
  }
}

if (parts.length === 0) {
  process.exit(0);
}

const context =
  `=== BACKGROUND TASK NOTIFICATIONS (${parts.length}) ===\n\n` +
  parts.join('\n\n---\n\n') +
  '\n\n=== END NOTIFICATIONS ===';

console.log(JSON.stringify({ additionalContext: context }));
