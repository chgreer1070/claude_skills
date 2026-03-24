#!/usr/bin/env node
'use strict';

/**
 * SessionEnd hook — gracefully stops all kage-bunshin tmux sessions when the
 * parent orchestrator session exits. Prevents orphaned sessions running with
 * no controller.
 *
 * Scope: plugin (development-harness)
 * Fires on: SessionEnd (no matcher)
 * Action: side effect — sends C-c to each session then force-kills stragglers
 *
 * Test:
 *   echo '{"hook_event_name":"SessionEnd","reason":"other"}' | node ./hooks/session-end-kage-bunshin-cleanup.cjs
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

  // List tmux sessions — suppress stderr
  let rawSessions = '';
  try {
    rawSessions = execFileSync('tmux', ['list-sessions', '-F', '#{session_name}'], {
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 3000,
    }).toString('utf8');
  } catch {
    // tmux not running or not installed — nothing to clean up
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

  // Send C-c to each session for graceful shutdown
  for (const session of sessions) {
    try {
      execFileSync('tmux', ['send-keys', '-t', session, 'C-c', ''], {
        stdio: ['ignore', 'pipe', 'ignore'],
        timeout: 2000,
      });
    } catch {
      // Session may have already exited — ignore
    }
  }

  // Wait up to 5 seconds for sessions to terminate naturally.
  // Poll at 500 ms intervals (10 checks × 500 ms = 5 s total).
  const deadline = Date.now() + 5000;
  let remaining = [...sessions];

  while (remaining.length > 0 && Date.now() < deadline) {
    // Busy-wait 500 ms using a synchronous spin — avoids setTimeout in a
    // stdin 'end' callback where the event loop may not pump again.
    const waitUntil = Date.now() + 500;
    while (Date.now() < waitUntil) {
      // spin
    }

    // Re-list sessions and filter down to those still alive
    let currentRaw = '';
    try {
      currentRaw = execFileSync('tmux', ['list-sessions', '-F', '#{session_name}'], {
        stdio: ['ignore', 'pipe', 'ignore'],
        timeout: 3000,
      }).toString('utf8');
    } catch {
      // tmux no longer has any sessions — all gone
      remaining = [];
      break;
    }

    const alive = new Set(
      currentRaw
        .split('\n')
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
    );
    remaining = remaining.filter((s) => alive.has(s));
  }

  // Force-kill any sessions that did not exit in time
  for (const session of remaining) {
    try {
      execFileSync('tmux', ['kill-session', '-t', session], {
        stdio: ['ignore', 'pipe', 'ignore'],
        timeout: 2000,
      });
    } catch {
      // Already gone — ignore
    }
  }

  process.stdout.write(JSON.stringify({}));
  process.exit(0);
});
