#!/usr/bin/env node
'use strict';

/**
 * Stop hook — checks after every orchestrator turn whether any kage-bunshin
 * child sessions are sitting idle (❯ prompt visible). If idle sessions exist,
 * emits a systemMessage reminding the orchestrator to read or stop them.
 *
 * Scope: plugin (development-harness)
 * Fires on: Stop (no matcher)
 * Action: non-blocking — emits systemMessage listing idle sessions with commands
 *
 * Test:
 *   echo '{"hook_event_name":"Stop","stop_hook_active":false}' | node ./hooks/stop-kage-bunshin-idle-check.cjs
 */

const { execFileSync } = require('node:child_process');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  input += chunk;
});
process.stdin.on('end', () => {
  // Parse stdin — exit cleanly on failure
  let data = {};
  try {
    data = JSON.parse(input || '{}');
  } catch {
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  // Avoid infinite loops — if stop hook is already active, do nothing
  if (data.stop_hook_active) {
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

  // Capture last 5 lines of each session and check for idle prompt (❯)
  const idleSessions = [];
  for (const session of sessions) {
    let paneContent = '';
    try {
      paneContent = execFileSync('tmux', ['capture-pane', '-p', '-J', '-t', session, '-S', '-5'], {
        stdio: ['ignore', 'pipe', 'ignore'],
        timeout: 2000,
      }).toString('utf8');
    } catch {
      // Session may have ended between list and capture — skip it
      continue;
    }

    // Find the last non-empty line and check for idle prompt
    const lines = paneContent.split('\n').filter((l) => l.trim().length > 0);
    const lastLine = lines[lines.length - 1] || '';
    if (lastLine.includes('❯')) {
      idleSessions.push(session);
    }
  }

  if (idleSessions.length === 0) {
    // All sessions are working — no reminder needed
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  // Build reminder message for idle sessions
  const spawn = `${process.env.CLAUDE_PLUGIN_ROOT || '.'}/skills/kage-bunshin/scripts/spawn.py`;
  const sessionList = idleSessions.map((s) => `  - ${s}`).join('\n');
  const commands = idleSessions
    .map((s) => {
      const match = s.match(/_worktree-(.+)$/);
      const name = match ? match[1] : s;
      return `  uv run ${spawn} read --name ${name}  # read output\n  uv run ${spawn} stop --name ${name}  # graceful Ctrl-C shutdown`;
    })
    .join('\n');

  const message = [
    `Kage-bunshin sessions idle (❯ prompt) — ${idleSessions.length} finished:`,
    sessionList,
    '',
    'Read output and stop when done:',
    commands,
  ].join('\n');

  process.stdout.write(JSON.stringify({ systemMessage: message }));
  process.exit(0);
});
