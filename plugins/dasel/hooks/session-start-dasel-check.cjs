#!/usr/bin/env node
/**
 * Check whether dasel v3 is installed and report its version.
 * Fires on: SessionStart
 * Action: non-blocking — injects dasel status into session context
 */

'use strict';

const { execFileSync } = require('node:child_process');

const EXEC_OPTS = { stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000 };

function checkDasel() {
  const whichBin = process.platform === 'win32' ? 'where' : 'which';

  try {
    execFileSync(whichBin, ['dasel'], EXEC_OPTS);
  } catch {
    return {
      installed: false,
      message: 'dasel not found. Run /dasel:setup to install.',
    };
  }

  try {
    const raw = execFileSync('dasel', ['version'], EXEC_OPTS).toString().trim();
    const match = raw.match(/(\d+\.\d+\.\d+)/);
    const version = match ? match[1] : raw;
    return { installed: true, version };
  } catch {
    return {
      installed: false,
      message: 'dasel found on PATH but version check failed. Run /dasel:setup.',
    };
  }
}

let _input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  _input += chunk;
});
process.stdin.on('end', () => {
  const result = checkDasel();
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        dasel: result,
      },
    }),
  );
  process.exit(0);
});
