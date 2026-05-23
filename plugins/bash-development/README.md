<p align="center">
  <img src="./assets/hero.png" alt="Bash Development" width="800" />
</p>

# bash-development

Complete Bash 5.1+ and POSIX shell development toolkit. Modular skills cover version-specific
features, portability, logging, linting, and testing. Specialized agents handle end-to-end
script development and security auditing.

## Problem

Writing reliable shell scripts means tracking feature availability across Bash versions,
choosing the right testing framework, setting up ShellCheck correctly, and deciding when to
use POSIX sh vs Bash. Without this plugin, Claude applies generic advice that may not match
your Bash version or portability requirements.

## Installation

```bash
/plugin install bash-development@jamie-bitflight-skills
```

## Quick Start

```text
/bash-development "write a deployment script that archives logs and rotates them daily"
/bash-development:bash-lint "check my script for shellcheck issues"
/bash-development:bash-portability "can this script run on sh?"
/bash-development:bash-testing "write tests for my validation functions"
```

## Skills

Each skill directory contains a `references/code-examples.md` file with extended runnable examples beyond what appears in the skill itself.

| Skill | What it provides |
|-------|-----------------|
| `bash-development` | Core patterns: script metadata, error handling, argument parsing, variable scoping, subshells |
| `bash-51-features` | Bash 5.1 features with examples — `EPOCHSECONDS`, `EPOCHREALTIME`, `SRANDOM`, nameref improvements |
| `bash-52-features` | Bash 5.2 features — readonly/unset improvements, array enhancements, readline integration |
| `bash-53-features` | Bash 5.3 features — in-shell `${ command; }` substitution, `REPLY` variable capture |
| `bash-lint` | ShellCheck integration: installation, common codes, suppression rules, portability flags |
| `bash-logging` | Structured logging functions with TTY detection and log level support |
| `bash-portability` | POSIX vs Bash feature matrix, shebang selection, portable conditional patterns |
| `bash-testing` | shunit2 and shellspec — framework selection, test structure, mocking, setup/teardown |

## Agents

### `bash-script-developer`

Writes new Bash scripts from requirements. Applies:

- Modern Bash 5.1+ idioms with ShellCheck compliance
- Proper error handling (`set -euo pipefail`, `trap` handlers)
- Structured logging and exit code conventions
- Function design with clear local variable scoping

**Example:** "Write a script that watches a directory for new files and processes them"

### `bash-script-auditor`

Reviews existing scripts and produces a scored assessment (0–10) weighted across:

- Security (25%) — command injection, path traversal, unsafe variable expansion
- Error handling (25%) — `set` options, trap handlers, exit codes
- Code organization (20%) — function design, modularity, readability
- Maintainability (20%) — naming, documentation, refactoring potential
- Performance (10%) — unnecessary subshells, inefficient loops

**Example:** "Audit `deploy.sh` for security and reliability issues"

## Reference

**Skill invocations trigger automatically** for Bash tasks: when you mention writing a `.sh`
script, ask about ShellCheck, or request portability help, the relevant skills activate.

To invoke a specific skill directly:

```text
/bash-development:bash-testing "write shunit2 tests for my parser"
/bash-development:bash-51-features "show EPOCHREALTIME examples"
```

To spawn an agent:

```text
@bash-development:bash-script-developer "create a backup rotation script"
@bash-development:bash-script-auditor "audit scripts/deploy.sh"
```

---

> **The Ancient Woe**
>
> *The despair of sending a vital decree with a messenger who trips over a single cobblestone, loses the letter, and sets the village on fire by accident.*

> **The Bard's Decree**
>
> *"Give me a courier of iron fortitude! One who knows the roads, anticipates the ambushes, and delivers the scroll unharmed through rain, wind, and the darkest nights!"*
