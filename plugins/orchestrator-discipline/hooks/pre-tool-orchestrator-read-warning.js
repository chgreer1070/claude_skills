#!/usr/bin/env node
/**
 * PreToolUse hook: warns when the orchestrator reads source/config files.
 *
 * The orchestrator should NOT read files it will not Edit/Write in the same turn.
 * Pass file paths to agents instead — agents have fresh context, orchestrator does not.
 *
 * Fires on: Read, Grep tool calls targeting source/config/test files
 * Action: injects additionalContext reminder (non-blocking)
 *
 * Non-blocking by design — legitimate reads (reading a file you ARE about to edit)
 * are not disrupted. The reminder surfaces the decision point.
 */

const SOURCE_FILE_EXTENSIONS =
  /\.(py|toml|yaml|yml|js|ts|jsx|tsx|json|cfg|ini|env|sh|bash|go|rs|rb|java|c|cpp|h|hpp)$/i;
const TEST_PATH_PATTERN = /\/(tests?|spec|__tests?__)\/|test_[^/]+\.(py|js|ts)$/i;

/**
 * @param {string} filePath
 * @returns {boolean}
 */
function isSourceOrConfigFile(filePath) {
  if (!filePath) return false;
  return SOURCE_FILE_EXTENSIONS.test(filePath) || TEST_PATH_PATTERN.test(filePath);
}

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  input += chunk;
});
process.stdin.on('end', () => {
  let data = {};
  try {
    data = JSON.parse(input);
  } catch {
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  const toolName = data.tool_name || '';
  const toolInput = data.tool_input || {};

  let targetPath = '';
  if (toolName === 'Read') {
    targetPath = toolInput.file_path || '';
  } else if (toolName === 'Grep') {
    targetPath = toolInput.path || '';
  } else {
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  if (!isSourceOrConfigFile(targetPath)) {
    process.stdout.write(JSON.stringify({}));
    process.exit(0);
  }

  const output = {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext: `<orchestrator-read-warning>
CONTEXT WINDOW CHECK: You are about to read a source/config file as the orchestrator.

File: ${targetPath}

BEFORE PROCEEDING — ask yourself:
1. Will you Edit or Write this file in this same turn? If YES: proceed.
2. Are you reading it to understand before delegating? If YES: STOP.
   Pass the file path to the agent instead. Agents have fresh context.
   You do not.

RULE: NEVER read source code, config, or test files unless you will Edit/Write them this turn.
Pass paths to agents — they perform their own verification.

ANTI-PATTERN: "Let me understand the patterns to scope the delegation"
CORRECT: Write the path into the delegation prompt. Delegate first.
</orchestrator-read-warning>`,
    },
  };

  process.stdout.write(JSON.stringify(output));
  process.exit(0);
});
