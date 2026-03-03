#!/usr/bin/env node
/**
 * Cross-platform npx launcher for MCP server config.
 *
 * Uses child_process shell: true so Node.js picks the correct
 * shell per platform:
 *   - Linux/macOS: /bin/sh  → finds 'npx' on PATH
 *   - Windows:     cmd.exe  → finds 'npx.cmd' automatically
 *
 * Usage in .mcp.json:
 *   "command": "node",
 *   "args": ["./scripts/npx-run.cjs", "-y", "<package>", ...]
 */
const { spawnSync } = require('node:child_process');
const result = spawnSync('npx', process.argv.slice(2), {
  stdio: 'inherit',
  shell: true,
});
process.exit(result.status ?? 1);
