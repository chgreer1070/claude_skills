#!/usr/bin/env node
'use strict';

/**
 * TaskCompleted hook — reminds the orchestrator to clean up kage-bunshin
 * tmux sessions when a task is marked complete.
 *
 * Scope: plugin (development-harness)
 * Fires on: TaskCompleted (no matcher)
 * Action: non-blocking — emits systemMessage listing active worktree sessions
 *
 * Test:
 *   echo '{"hook_event_name":"TaskCompleted"}' | node ./hooks/task-completed-kage-bunshin-reminder.cjs
 */

const { execFileSync } = require('node:child_process');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  input += chunk;
});
process.stdin.on('end', () => {
  // Parse stdin — exit cleanly on failure
  try {
    JSON.parse(input || '{}');
  } catch {
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  // List tmux sessions — suppress stderr so hook never leaks noise
  let rawSessions = '';
  try {
    rawSessions = execFileSync('tmux', ['list-sessions', '-F', '#{session_name}'], {
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 3000,
    }).toString('utf8');
  } catch {
    // tmux not running or not installed — no sessions to report
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  // Filter to kage-bunshin worktree sessions (pattern: *_worktree-*)
  const sessions = rawSessions
    .split('\n')
    .map((s) => s.trim())
    .filter((s) => s.includes('_worktree-'));

  if (sessions.length === 0) {
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  // Build reminder message
  const sessionList = sessions.map((s) => `  - ${s}`).join('\n');
  const message = [
    `Kage-bunshin worktree sessions still running (${sessions.length}):`,
    sessionList,
    '',
    'Clean up with:',
    sessions
      .map((s) => {
        // Extract the --name value: everything after the last _worktree- prefix
        const match = s.match(/_worktree-(.+)$/);
        const name = match ? match[1] : s;
        return `  uv run spawn.py kill --name ${name}`;
      })
      .join('\n'),
    '',
    'Or review all sessions: uv run spawn.py list',
  ].join('\n');

  const output = {
    systemMessage: message,
  };

  process.stdout.write(JSON.stringify(output));
  process.exit(0);
});
