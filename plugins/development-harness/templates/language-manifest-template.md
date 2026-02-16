# Language Manifest: {Language Name}

## Role Fulfillment

- architect: @{plugin}:{agent-name}
- test-designer: @{plugin}:{agent-name}
- code-reviewer: @{plugin}:{agent-name}
- design-spec: @{plugin}:{agent-name}
- linting: /{plugin}:{skill-name}

## Quality Gates

- format: `{format command} {files}`
- lint: `{lint command} {files}`
- typecheck: `{typecheck command} {files}`
- test: `{test command}`
- standards: /{plugin}:{standards-skill}

## Project Detection

- markers: {config files that identify this language}
- source-patterns: {glob patterns for source files}
- test-patterns: {glob patterns for test files}

## Process Flow Override

(none — uses default harness flow)
