# Node.js Hook Authoring Guide

> This guide covers Node.js hook scripts specifically. Claude Code hooks are language-agnostic — any executable works. See [hooks-python.md](./hooks-python.md) for Python hooks.

## Table of Contents

- [File Extension — Never Use Plain .js](#file-extension--never-use-plain-js)
- [Script Header](#script-header)
- [Read stdin](#read-stdin)
- [execFileSync over execSync](#execfilesync-over-execsync)
- [Timeout Discipline](#timeout-discipline)
- [Exit Codes](#exit-codes)
- [stdout — JSON Only](#stdout--json-only)
- [stderr — Error Messages Only](#stderr--error-messages-only)
- [Complete Templates](#complete-templates)
  - [Blocking — PreToolUse exit 2](#blocking--pretooluse-exit-2)
  - [Permission Decision](#permission-decision)
  - [Context Injection — SessionStart](#context-injection--sessionstart)
  - [Task Verification — Stop and SubagentStop](#task-verification--stop-and-subagentstop)
  - [Binary Availability Check](#binary-availability-check)
- [Anti-Patterns](#anti-patterns)

---

## File Extension — Never Use Plain .js

Name every Node.js hook script with an explicit extension — `.cjs` or `.mjs`. Never use plain `.js`.

**Why:** Plain `.js` inherits its module type from the nearest `package.json` `"type"` field. A `.js` file in a project with `"type": "module"` is treated as ESM; in a project without that field it is CommonJS. Using `.js` for a hook script causes a module type mismatch error if the project's `"type"` field conflicts with the script's actual syntax. Explicit extensions override `package.json` entirely and load correctly regardless of project type:

- `.mjs` — forces ESM resolution (`import` syntax). **Preferred default for new Node.js scripts written from scratch.**
- `.cjs` — forces CommonJS resolution (`require()` syntax). Use when `require()` is needed (e.g., existing hooks that already use CommonJS).

New Node.js hooks written from scratch: default to `.mjs`. Existing hooks in this repo use CommonJS (`require()`) → keep `.cjs`.

```text
hooks/validate-bash.cjs     ← correct — explicit CommonJS, works in any project
hooks/validate-bash.mjs     ← correct — explicit ESM, works in any project
hooks/validate-bash.js      ← wrong — module type depends on package.json "type"
```

Use lowercase names with hyphens to match the event or purpose:

```text
hooks/pre-bash-validator.cjs
hooks/session-context.cjs
hooks/stop-checker.cjs
```

---

## Script Header

Every hook script starts with these two lines:

```javascript
#!/usr/bin/env node
'use strict';
```

Line 1 — shebang: tells the shell to execute this file with `node` from PATH. Required for direct invocation (e.g., `chmod +x` and `./hooks/myhook.cjs`).

Line 2 — strict mode: prevents silent variable hoisting bugs and reserved word conflicts. Place immediately after the shebang with no blank line between them.

Follow the header with a doc comment:

```javascript
#!/usr/bin/env node
'use strict';

/**
 * PreToolUse hook — blocks dangerous shell patterns.
 * Scope: plugin
 * Fires on: PreToolUse, matcher: Bash
 *
 * Test:
 *   echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | node ./hooks/pre-bash-validator.cjs
 */
```

---

## Read stdin

Claude Code delivers hook input as JSON on stdin. Read it with `readFileSync('/dev/stdin')` inside a `try/catch`. Exit 0 on parse failure — never crash on bad input.

```javascript
let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}
```

Why `readFileSync('/dev/stdin')` and not `process.stdin`: the synchronous read is simpler and avoids async stream handling in short-lived scripts. The `try/catch` catches both read errors and JSON parse errors in one block.

Extract fields after the parse:

```javascript
const toolName = inputData.tool_name ?? '';
const toolInput = inputData.tool_input ?? {};
const hookEvent = inputData.hook_event_name ?? '';
```

---

## execFileSync over execSync

When calling external binaries, use `execFileSync` with an array of arguments. Never pass a command string to `execSync`.

```javascript
const { execFileSync } = require('node:child_process');

// Correct
execFileSync('git', ['status', '--short'], {
  stdio: ['ignore', 'pipe', 'ignore'],
  timeout: 3000,
});

// Wrong — shell injection risk
const { execSync } = require('node:child_process');
execSync(`git status ${userInput}`);
```

**Why execFileSync:**

- No shell interpolation — each argument is passed directly to the OS `exec` call
- User-supplied values in args cannot escape into shell metacharacters
- `execSync` with a string spawns a shell (`/bin/sh -c "..."`), which evaluates the string

**stdio suppression:** Always pass `{ stdio: ['ignore', 'pipe', 'ignore'] }` unless you need stdout from the child. The third element suppresses child stderr, preventing it from leaking into hook output.

---

## Timeout Discipline

Set `timeout` in every `execFileSync` call and in `hooks.json`. Never rely on defaults.

| Operation type | Timeout |
|---|---|
| Local binary check (which, git status) | 3000 ms |
| Filesystem read or stat | 5000 ms |
| Network operations | Do not implement in hooks |

```javascript
// Local binary — 3000ms
execFileSync('which', ['prettier'], {
  stdio: ['ignore', 'pipe', 'ignore'],
  timeout: 3000,
});

// Filesystem operation — 5000ms
const { statSync } = require('node:fs');
// (statSync is synchronous — no timeout parameter, but keep the threshold in mind)
```

In `hooks.json`, set `timeout` in seconds:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/validate-bash.cjs",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Note: `hooks.json` timeout is in seconds. `execFileSync` timeout option is in milliseconds.

---

## Exit Codes

| Exit code | Meaning | Effect |
|---|---|---|
| 0 | Success or non-blocking issue | Claude proceeds normally |
| 1 | Script error | Logged, non-blocking |
| 2 | Blocking error | Claude sees stderr message; tool call or action is blocked |

Use exit 2 to block a tool call and surface an error to Claude:

```javascript
if (isDangerous) {
  process.stderr.write(`Blocked: command matches dangerous pattern\n`);
  process.exit(2);
}
process.exit(0);
```

Use exit 1 only for unrecoverable script failures (missing required dependency, corrupt input after retrying). Most error conditions should exit 0 (non-blocking) or exit 2 (blocking with a message).

---

## stdout — JSON Only

Write JSON to stdout using `console.log(JSON.stringify(output))`. Never write raw text to stdout in hooks that return structured output.

```javascript
const output = {
  hookSpecificOutput: {
    hookEventName: 'PreToolUse',
    permissionDecision: 'allow',
    permissionDecisionReason: 'Read-only operation auto-approved',
  },
  suppressOutput: true,
};
console.log(JSON.stringify(output));
process.exit(0);
```

**Why:** Claude Code parses stdout as JSON when the hook produces structured output. Raw text on stdout in a JSON-producing hook causes a parse error and the hook is ignored.

For hooks that only block or allow (exit code only, no JSON decision), produce no stdout.

---

## stderr — Error Messages Only

Write to stderr only when the exit code is 2 (blocking) or when producing debug output:

```javascript
// Blocking — write reason to stderr, then exit 2
process.stderr.write(`Blocked: ${reason}\n`);
process.exit(2);
```

Claude receives stderr content when a hook exits with code 2. This message is shown in the session.

Do not write debug logging to stderr in production hooks. It will appear in Claude's context on any exit 2 and adds noise.

---

## Complete Templates

These templates use CommonJS (`require()`) syntax — save them as `.cjs`. For new scripts written from scratch, prefer `.mjs` and replace `require(...)` with `import ... from '...'`.

### Blocking — PreToolUse exit 2

Blocks a tool call and shows an error to Claude.

```javascript
#!/usr/bin/env node
'use strict';

/**
 * PreToolUse hook — blocks dangerous rm patterns.
 * Scope: plugin
 * Fires on: PreToolUse, matcher: Bash
 *
 * Test:
 *   echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | node ./hooks/block-rm-rf.cjs
 */

let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}

const toolName = inputData.tool_name ?? '';
const toolInput = inputData.tool_input ?? {};

if (toolName !== 'Bash') {
  process.exit(0);
}

const command = toolInput.command ?? '';
const DANGEROUS = /\brm\s+-[^-]*r[^-]*f|\brm\s+--recursive/i;

if (DANGEROUS.test(command)) {
  process.stderr.write(`Blocked: recursive force delete detected in: ${command}\n`);
  process.exit(2);
}

process.exit(0);
```

Wire in `hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/block-rm-rf.cjs",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Permission Decision

Returns a JSON `permissionDecision` to auto-approve or auto-deny without the user seeing a dialog.

```javascript
#!/usr/bin/env node
'use strict';

/**
 * PreToolUse hook — auto-approves reads on documentation files.
 * Scope: plugin
 * Fires on: PreToolUse, matcher: Read
 *
 * Test:
 *   echo '{"hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"README.md"}}' | node ./hooks/auto-approve-docs.cjs
 */

let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}

const toolName = inputData.tool_name ?? '';
const toolInput = inputData.tool_input ?? {};

if (toolName !== 'Read') {
  process.exit(0);
}

const filePath = toolInput.file_path ?? '';
const DOC_EXTENSIONS = /\.(md|mdx|txt|json|yaml|yml)$/i;

if (DOC_EXTENSIONS.test(filePath)) {
  const output = {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'allow',
      permissionDecisionReason: 'Documentation file — auto-approved for read',
    },
    suppressOutput: true,
  };
  console.log(JSON.stringify(output));
  process.exit(0);
}

process.exit(0);
```

Wire in `hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/auto-approve-docs.cjs",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Context Injection — SessionStart

Injects context into the session. stdout is added to Claude's context when the event is `SessionStart`.

```javascript
#!/usr/bin/env node
'use strict';

/**
 * SessionStart hook — injects project environment context.
 * Scope: plugin
 * Fires on: SessionStart, matcher: startup|resume
 *
 * Test:
 *   echo '{"hook_event_name":"SessionStart","source":"startup"}' | node ./hooks/session-context.cjs
 */

let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}

const nodeVersion = process.version;
const cwd = process.cwd();
const nodeEnv = process.env.NODE_ENV ?? 'development';

const contextText = [
  `Node version: ${nodeVersion}`,
  `NODE_ENV: ${nodeEnv}`,
  `Working directory: ${cwd}`,
].join('\n');

const output = {
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: `<project-context>\n${contextText}\n</project-context>`,
  },
};

console.log(JSON.stringify(output));
process.exit(0);
```

Wire in `hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-context.cjs",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Task Verification — Stop and SubagentStop

Exit 2 forces Claude to continue working. Exit 0 allows Claude to stop.

```javascript
#!/usr/bin/env node
'use strict';

/**
 * Stop hook — verifies a task marker file exists before allowing Claude to stop.
 * Scope: plugin
 * Fires on: Stop (no matcher)
 *
 * Test:
 *   echo '{"hook_event_name":"Stop","stop_hook_active":false}' | node ./hooks/verify-complete.cjs
 */

const { existsSync } = require('node:fs');
const { join } = require('node:path');

let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}

// Prevent infinite loop — if hook is already active, allow stop
if (inputData.stop_hook_active === true) {
  process.exit(0);
}

const projectDir = process.env.CLAUDE_PROJECT_DIR ?? process.cwd();
const markerPath = join(projectDir, '.task-complete');

if (!existsSync(markerPath)) {
  process.stderr.write(`Task not complete: ${markerPath} not found. Continue working.\n`);
  process.exit(2);
}

process.exit(0);
```

Wire in `hooks.json` (Stop has no matcher):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/verify-complete.cjs",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

For `SubagentStop`, change `hook_event_name` in the test and the `hookEventName` in the output (if producing JSON). The exit code behavior is identical.

### Binary Availability Check

Check whether a binary is available before running it. Use `execFileSync('which', [binary])` with a 3000 ms timeout.

```javascript
#!/usr/bin/env node
'use strict';

/**
 * PostToolUse hook — runs prettier after Write/Edit if available.
 * Scope: plugin
 * Fires on: PostToolUse, matcher: Write|Edit
 *
 * Test:
 *   echo '{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"src/index.ts"}}' | node ./hooks/format-on-write.cjs
 */

const { execFileSync } = require('node:child_process');

let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}

const toolInput = inputData.tool_input ?? {};
const filePath = toolInput.file_path ?? toolInput.new_file_path ?? '';

if (!filePath) {
  process.exit(0);
}

function binaryAvailable(binary) {
  try {
    execFileSync('which', [binary], {
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 3000,
    });
    return true;
  } catch {
    return false;
  }
}

if (!binaryAvailable('prettier')) {
  // prettier not installed — silently skip
  process.exit(0);
}

try {
  execFileSync('prettier', ['--write', filePath], {
    stdio: ['ignore', 'pipe', 'ignore'],
    timeout: 5000,
  });
} catch {
  // Format failure is non-blocking
  process.exit(0);
}

process.exit(0);
```

Wire in `hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/format-on-write.cjs",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## Anti-Patterns

### Wrong extension for Node.js scripts

```text
hooks/validate-bash.js
```

```text
hooks/validate-bash.cjs
```

Plain `.js` causes module type mismatch errors. See [File Extension — Never Use Plain .js](#file-extension--never-use-plain-js) for the full rule and rationale.

---

### execSync with string command

```javascript
// Wrong
const { execSync } = require('node:child_process');
execSync(`git log --oneline ${userInput}`);
```

```javascript
// Correct
const { execFileSync } = require('node:child_process');
execFileSync('git', ['log', '--oneline', userInput], {
  stdio: ['ignore', 'pipe', 'ignore'],
  timeout: 3000,
});
```

`execSync` with a string spawns a shell. User input in the string can inject shell metacharacters. `execFileSync` with an args array passes each argument directly to the OS — no shell expansion.

---

### stderr leak from child process

```javascript
// Wrong — child stderr goes to hook stderr
execFileSync('binary', ['arg'], { stdio: 'inherit' });
```

```javascript
// Correct — child stderr suppressed
execFileSync('binary', ['arg'], {
  stdio: ['ignore', 'pipe', 'ignore'],
  timeout: 3000,
});
```

`stdio: 'inherit'` passes child stdout and stderr through to the hook process. On exit 2, anything in stderr is shown to Claude. Suppress child stderr unless you specifically intend to surface it.

---

### Raw text to stdout in a JSON hook

```javascript
// Wrong
console.log('Auto-approved');
process.exit(0);
```

```javascript
// Correct
const output = {
  hookSpecificOutput: {
    hookEventName: 'PreToolUse',
    permissionDecision: 'allow',
    permissionDecisionReason: 'Auto-approved',
  },
  suppressOutput: true,
};
console.log(JSON.stringify(output));
process.exit(0);
```

Claude Code expects JSON on stdout when the hook returns a structured decision. Raw text causes a parse failure and the hook decision is ignored.

---

### No try/catch on stdin parse

```javascript
// Wrong — crashes on bad input
const inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
```

```javascript
// Correct — exits cleanly on bad input
let inputData;
try {
  inputData = JSON.parse(require('node:fs').readFileSync('/dev/stdin', 'utf8'));
} catch {
  process.exit(0);
}
```

If Claude Code sends malformed JSON or no input, the uncaught exception produces an exit 1 (error), which is logged as a script failure. Exit 0 on parse failure is the correct non-blocking behavior.

---

### Missing timeout on execFileSync

```javascript
// Wrong — hangs indefinitely if binary stalls
execFileSync('git', ['fetch']);
```

```javascript
// Correct
execFileSync('git', ['fetch'], {
  stdio: ['ignore', 'pipe', 'ignore'],
  timeout: 3000,
});
```

Hooks run synchronously in the Claude Code event loop. A stalled child process blocks the entire hook. Always set `timeout`.

---

### Deleting hooks-json when unused

```text
(no hooks/hooks.json file)
```

```json
{ "hooks": {} }
```

An absent `hooks.json` in a plugin directory signals an incomplete plugin structure. Keep the file with an empty hooks object.

---

## Sources

- [Hooks Reference](https://code.claude.com/docs/en/hooks.md) (accessed 2026-01-28)
- [Hooks Guide](https://code.claude.com/docs/en/hooks-guide.md) (accessed 2026-01-28)
- [Plugin Components Reference](https://code.claude.com/docs/en/plugins-reference.md#hooks) (accessed 2026-01-28)
- Patterns derived from `plugin-creator:hook-creator` agent mandatory constraints (2026-03-01)
- Patterns derived from `plugin-creator:hooks-patterns` skill code examples (2026-03-01)
