#!/usr/bin/env node
const { execSync } = require('node:child_process');

try {
  const whichCmd = process.platform === 'win32' ? 'where' : 'which';
  execSync(`${whichCmd} dasel`, { stdio: 'ignore' });
  const output = execSync('dasel --version', { encoding: 'utf-8' }).trim();
  // Parse version from output like "dasel version v3.2.2"
  const versionMatch = output.match(/v?(\d+\.\d+\.\d+)/);
  const version = versionMatch ? versionMatch[1] : output;
  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        dasel: { installed: true, version },
      },
    }),
  );
} catch {
  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        dasel: { installed: false, message: 'dasel not found. Run /dasel:setup to install.' },
      },
    }),
  );
}
