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
- typecheck: `{typecheck command} {files}` or `(none)` for non-typed languages
- test: `{test command}`
- standards: /{plugin}:{standards-skill}
- live_validation: `{command that exercises the delivery surface through the real runtime path, not via test imports}`
  # Must invoke the actual runtime entry point (CLI binary, MCP tool call, HTTP endpoint, library require)
  # Examples
  #   MCP server:   uv run fastmcp call --command "uv run python scripts/run_server.py" --target health_check --input-json '{}'
  #   CLI tool:     uv run mytool --version
  #   Web service:  curl -sf <http://localhost:3000/health>
  #   Library:      ruby -e "require './lib/mylib'; puts MyLib::VERSION"
  #   Web (browser required): agent-browser
  # When absent, feature-verifier flags this as a gap in the verification report

## Project Detection

- markers: {config files that identify this language}
- source-patterns: {glob patterns for source files}
- test-patterns: {glob patterns for test files}

## Process Flow Override

(none — uses default harness flow)
