# bash-development

Comprehensive Bash 5.1+ and POSIX shell development plugin with modular skills for scripting,
portability, testing, linting, logging, and version-specific features. Includes specialized
agents for script development and code auditing.

## What it does

Provides a complete toolkit for writing, testing, and auditing Bash scripts. Skills cover
version-specific features (5.1, 5.2, 5.3 changelogs with examples), portability between
POSIX and Bash, structured logging, and test design. Agents handle end-to-end script development
and security/quality auditing.

## Skills

- `bash-development` — Core Bash 5.1+ scripting guidance, patterns, and best practices
- `bash-51-features` — Bash 5.1 release features with practical examples (EPOCHSECONDS, redirection)
- `bash-52-features` — Bash 5.2 release features with practical examples (variable handling, readline)
- `bash-53-features` — Bash 5.3 release features with practical examples
- `bash-lint` — Linting rules and ShellCheck integration for Bash scripts
- `bash-logging` — Structured logging patterns for shell scripts
- `bash-portability` — Writing portable scripts that run on POSIX sh and Bash
- `bash-testing` — Testing strategies and frameworks for shell scripts

## Agents

- `bash-script-developer` — Writes new Bash scripts from requirements, applying modern Bash patterns
- `bash-script-auditor` — Reviews existing scripts for correctness, security, and portability issues

## Installation

```bash
/plugin install bash-development@jamie-bitflight-skills
```

## Usage

```text
/bash-development "write a deployment script that archives logs and rotates them daily"
/bash-development:bash-lint "audit my script for portability issues"
```
