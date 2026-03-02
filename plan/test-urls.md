# Test URLs and Expected Content Structure

This document defines the four test URLs used for is-fast validation, including detailed breakdown of expected structural elements that will be extracted.

---

## Test URL 1: Skill Frontmatter Schema

**URL**: https://raw.githubusercontent.com/Jamie-BitFlight/claude_skills/main/.claude/docs/SKILL.md

**Why This URL**: Demonstrates is-fast's ability to:
- Extract tables with semantic content (field names, data types, descriptions)
- Preserve inline code markers and type annotations
- Handle nested property documentation
- Extract YAML example blocks verbatim

### Expected Content Structure

#### Table 1: Frontmatter Fields Reference

Expected location: Main schema documentation section

Expected columns (5):
1. `Field` — Frontmatter key name
2. `Type` — Data type (string, string[], object, etc.)
3. `Required` — Yes/No indicator
4. `Description` — Field purpose (1-3 sentences)
5. `Default` — Default value or "N/A"

Expected rows (minimum 8):
- `name` | `string` | Yes | Skill name used in activation | N/A
- `description` | `string` | Yes | Human-readable description | N/A
- `version` | `string` | No | Semantic version string | latest
- `frontmatter` | `object` | No | Metadata structure | `{}`
- `hooks` | `object[]` | No | Event-driven triggers | `[]`
- `tags` | `string[]` | No | Search/categorization tags | `[]`
- `dependencies` | `string[]` | No | Required other skills | `[]`
- `context` | `string` | No | Execution context (fork, inherit) | inherit

Expected inline markup:
- Type annotations: `` `string` ``, `` `string[]` ``, `` `object` ``
- Field references: `` `hooks` ``, `` `frontmatter` ``
- Example values: `` `{}` ``, `` `[]` ``

#### Code Block 1: Example Frontmatter YAML

Expected location: After table, in "Example" section

Expected structure: Multi-line YAML block with:
- Key structure matching table above
- Comments explaining each section
- At least 2-3 hooks examples with matcher conditions
- Example dependencies list

Expected preservation:
- YAML syntax exact (colons, dashes, indentation)
- Comments with `#` character preserved
- Nested structure clear (indentation preserved)
- No ANSI color codes or syntax highlighting markup

Example (verbatim):
```
name: my-skill
description: "Example skill for documentation"
version: "1.0.0"
tags: [example, documentation]
hooks:
  - type: PostToolUse
    matcher: "Write|Edit"
    # Only trigger on file changes
    command: "validate"
```

#### Table 2: Hooks Types Reference (if present)

Expected columns (3-4):
- `Hook Type` — Event name (PostToolUse, SubagentStop, etc.)
- `Triggers` — When this hook fires
- `Matcher Support` — Pattern matching available? (yes/no)
- `Use Case` — Example use

Expected rows (minimum 3):
- PostToolUse events, SubagentStop events, etc.

### Validation Checklist for URL 1

- [ ] Table 1: All 5 columns present and named exactly
- [ ] Table 1: All 8+ rows extracted (count rows)
- [ ] Table 1: No cell truncation (check longest description column)
- [ ] Type annotations: Backticks preserved (`` `string` ``, not `string`)
- [ ] Code block: YAML indentation preserved exactly
- [ ] Code block: Comments with `#` preserved
- [ ] Code block: No ANSI color codes injected
- [ ] If Table 2 present: All columns and rows extracted
- [ ] No "Here's an example" summaries in place of actual code
- [ ] No field descriptions paraphrased or shortened

---

## Test URL 2: Docker Compose Specification

**URL**: https://docs.docker.com/reference/compose-file/

**Why This URL**: Demonstrates is-fast's ability to:
- Extract large schema documentation with many tables
- Handle code examples in YAML format with complex nesting
- Preserve technical property names and type constraints
- Extract version notes and breaking change callouts

### Expected Content Structure

#### Table 1: Services Block Properties (main table)

Expected location: "services" section or similar

Expected columns (5-6):
1. `Property` — Configuration key name (e.g., `build`, `environment`, `ports`)
2. `Type` — Data type (string, object, array, etc.)
3. `Required` — Yes/No
4. `Default` — Default value
5. `Description` — Property purpose
6. (Optional) `Since` — Version introduced

Expected rows (minimum 10):
```
build | object|string | No | (based on context) | Build configuration or image name
cap_add | string[] | No | [] | Linux capabilities to add
cap_drop | string[] | No | [] | Linux capabilities to drop
container_name | string | No | (none) | Container name override
depends_on | object|string[] | No | {} | Service dependencies
environment | object|string[] | No | {} | Environment variables
...
```

Expected inline markup:
- Code references: `` `build` ``, `` `services` ``
- Type arrays: `string[]`, `object[]`
- Nested paths: `` `services.build.args` ``

#### Code Block 1: Basic Service Definition

Expected location: "Example" section or "Getting Started"

Expected structure: YAML with:
```yaml
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    environment:
      NGINX_HOST: example.com
      NGINX_PORT: 80
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
```

Expected preservation:
- YAML syntax exact (colons, dashes, quotes around strings)
- Indentation structure clear (2-space indentation common)
- Comments if present preserved
- Multiline strings with proper quoting

#### Code Block 2: Advanced Service with Build Context

Expected location: "build" section or similar

Expected structure: Showing `build` object with:
- `context` — directory path
- `dockerfile` — filename
- `args` — build arguments
- `target` — multi-stage target

Example pattern:
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
      args:
        BUILD_ENV: production
      target: final
```

#### Callouts/Warnings (non-table text)

Expected: Paragraphs explaining:
- Deprecated properties and replacements
- Version-specific behavior
- Performance implications
- Network modes and restrictions

Expected preservation:
- Original warning text not summarized
- Specific version numbers preserved (e.g., "Docker Compose v2.0+")
- Links to related sections (URL or "see X section")

### Validation Checklist for URL 2

- [ ] Main services table: All columns present (5-6)
- [ ] Main table: Minimum 10 rows extracted (not summarized to 5)
- [ ] Code Block 1: YAML syntax exact with indentation preserved
- [ ] Code Block 2: Advanced example complete (build context shown)
- [ ] Nested property paths: `` `services.build.args` `` format preserved
- [ ] Callout text: Warnings not paraphrased, specific versions intact
- [ ] Type arrays: `string[]` notation preserved (not written as "array of strings")
- [ ] No "Compose allows you to..." summaries in place of property tables
- [ ] Environment variable examples: Exact values shown (not "[variables]")
- [ ] Line breaks in YAML preserved (not collapsed to single line)

---

## Test URL 3: Packer HCL Schema

**URL**: https://developer.hashicorp.com/packer/docs/templates/hcl_templates

**Why This URL**: Demonstrates is-fast's ability to:
- Extract scenario-specific documentation (use cases, when to use X)
- Preserve multi-line HCL code blocks with exact syntax
- Extract configuration block types and their properties
- Maintain comments and inline documentation within code

### Expected Content Structure

#### Table 1: Configuration Block Types

Expected location: Overview or "Building Blocks" section

Expected columns (4-5):
1. `Block Type` — datasource, variable, local, build, required_plugins
2. `Purpose` — What does this block do?
3. `Required` — Is this required? (yes/no)
4. `Example` — Brief usage pattern
5. (Optional) `Documentation Link` — Where to learn more

Expected rows (minimum 5):
```
datasource | Fetch data from external sources (AMIs, images, etc.) | No | data "ami" {...}
variable | Input variables and templates | No | variable "ami_id" {...}
local | Local values computed during runtime | No | locals { ami = data.aws... }
build | Builder blocks defining image construction | Yes | build { sources = ... }
required_plugins | Declare plugin dependencies | No | required_plugins { ... }
```

#### Code Block 1: Variable Declaration with Scenario

Expected location: "Variables" or "Input Configuration" section

Expected context: Paragraph explaining "For parameterized builds, define input variables like this:"

Expected structure: HCL variable block with:
- Type declaration
- Default value
- Validation rules if present
- Inline comments

Example (verbatim expected):
```hcl
variable "region" {
  type        = string
  description = "AWS region for build"
  default     = "us-east-1"
  sensitive   = false
}

variable "instance_type" {
  type = string
  # Validate instance type is in allowed list
  validation {
    condition     = contains(["t3.micro", "t3.small"], var.instance_type)
    error_message = "Instance type not supported"
  }
}
```

Expected preservation:
- HCL syntax exact (equal signs, curly braces, square brackets)
- Comments with `#` preserved
- String quotes preserved
- Indentation structure (2-space standard)
- Multi-line strings if present

#### Code Block 2: Build Block with Multiple Sources

Expected location: "Builders" or "Build Configuration" section

Expected context: "To define image construction with multiple source types:"

Expected structure: Build block with:
- Sources list (multiple image types)
- Provisioners (shell commands, file copies)
- Post-processors (artifact generation)

Example (verbatim expected):
```hcl
build {
  name = "example"
  sources = [
    "source.amazon-ebs.linux",
    "source.amazon-ebs.windows"
  ]

  provisioner "shell" {
    inline = [
      "echo Building {{.SourceAmiName}}",
      "apt-get update",
      "apt-get install -y curl"
    ]
  }

  post-processor "manifest" {
    output = "manifest.json"
  }
}
```

Expected preservation:
- Multi-line arrays with proper bracketing
- String interpolation: `{{.SourceAmiName}}` exact
- Nested provisioner/post-processor blocks
- Inline command arrays with proper escaping

#### Scenario-Specific Documentation Sections

Expected location: Multiple sections throughout

Expected patterns:
- "To use this feature for X scenario, configure Y like this..."
- "Common use case: Building Z images, which requires..."
- "Warning: This approach is not recommended when..."
- "For advanced users: To customize the build process, X can be..."

Expected preservation:
- Exact wording of scenario descriptions (not paraphrased)
- Specific examples tied to scenarios (not generic)
- All examples for a scenario (not just first one)
- Warnings with specific conditions preserved

### Validation Checklist for URL 3

- [ ] Block type table: All columns (4-5) present
- [ ] Block type table: All 5+ rows extracted
- [ ] Code Block 1: HCL syntax exact (type declaration, validation)
- [ ] Code Block 1: Comments preserved (# character)
- [ ] Code Block 2: Multi-line array syntax with brackets preserved
- [ ] Code Block 2: String interpolation `{{.SourceAmiName}}` exact
- [ ] Scenario descriptions: Exact wording preserved (not paraphrased)
- [ ] All examples for a scenario present (not summarized to one)
- [ ] Provisioner/post-processor blocks nested correctly
- [ ] Validation rules complete (condition and error_message both present)
- [ ] No "Here's how to build an image..." summaries replacing actual config
- [ ] No shorthand descriptions like "[shell commands]" in place of actual inline array

---

## Test URL 4: GitLab YAML Schema

**URL**: https://docs.gitlab.com/ee/ci/yaml/

**Why This URL**: Demonstrates is-fast's ability to:
- Handle deeply nested configuration key documentation
- Extract multiple examples per key
- Preserve version information and breaking changes
- Extract edge case documentation and gotchas

### Expected Content Structure

#### Table 1: Top-Level CI Configuration Keys

Expected location: Main CI reference section

Expected columns (4-5):
1. `Key` — Configuration key name (stages, variables, artifacts, etc.)
2. `Type` — Data type (string, array, object)
3. `Required` — Yes/No
4. `Description` — Purpose and behavior
5. (Optional) `Available Since` — GitLab version

Expected rows (minimum 12):
```
stages | string[] | No | Defines pipeline stages (default: [build, test, deploy])
variables | object | No | CI/CD variables available to all jobs
default | object | No | Default configuration for all jobs
include | string[] | No | Include external CI configuration files
artifacts | object | No | Artifacts to pass between jobs
cache | object | No | Cache files between job runs
image | string | No | Docker image for job execution
services | string[] | No | Service containers (databases, etc.)
...
```

#### Nested Key Table: `artifacts.*` Properties

Expected location: Subsection under "artifacts"

Expected structure:
```
Nested key: artifacts.reports

Type: object

Properties:
  coverage_report | object | No | Coverage report files
  junit | string|string[] | No | JUnit format test reports
  sast | string | No | SAST scan results
  ...
```

Expected format:
- Nested path notation: `` `artifacts.reports.coverage_report` ``
- Sub-properties with types and descriptions
- Relationships to other keys indicated

#### Code Block 1: Basic CI Configuration

Expected location: "Getting Started" or "Simple Example"

Expected structure: YAML pipeline with:
- `stages` definition
- Job definitions with stage assignment
- Variables and basic configuration

Example (verbatim expected):
```yaml
stages:
  - build
  - test
  - deploy

build_job:
  stage: build
  image: node:18
  script:
    - npm install
    - npm run build
  artifacts:
    paths:
      - dist/

test_job:
  stage: test
  image: node:18
  script:
    - npm run test
  coverage: '/Coverage: \d+\.\d+%/'

deploy_job:
  stage: deploy
  image: docker:latest
  script:
    - docker build -t app:latest .
    - docker push app:latest
```

#### Code Block 2: Advanced Configuration with Rules and Conditions

Expected location: "Advanced Configuration" or "Conditional Execution"

Expected structure: YAML with:
- Job rules with conditions
- If/unless logic for job execution
- Variable references
- Allow_failure and retry settings

Example (verbatim expected):
```yaml
deploy_production:
  stage: deploy
  image: ubuntu:22.04
  script:
    - ./deploy.sh production
  variables:
    ENVIRONMENT: production
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: always
    - if: '$CI_COMMIT_BRANCH =~ /^release\//'
      when: manual
    - when: never
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

#### Gotchas and Edge Cases Section

Expected location: Multiple places throughout document

Expected content:
- "Note: This behavior changed in GitLab 15.0..."
- "Gotcha: If you use both X and Y, Z will happen..."
- "Edge case: When running in parallel, ensure..."
- "Warning: This variable is not available in..."

Expected preservation:
- Specific version numbers ("GitLab 15.0", not "recent versions")
- Exact condition descriptions (not simplified)
- All edge cases listed (not just most common)

#### Breaking Changes and Deprecations

Expected location: Separate section or inline notes

Expected patterns:
- "Deprecated in GitLab X.Y: Use Z instead"
- "Removed in GitLab X.Y: Use Z as replacement"
- "Breaking change in GitLab X.Y: Y is now required for X"

Expected preservation:
- Version numbers exact
- Previous behavior documented
- Migration path clear

### Validation Checklist for URL 4

- [ ] Top-level keys table: All columns (4-5) present
- [ ] Top-level table: All 12+ keys extracted (not summarized)
- [ ] Nested key documentation: Paths like `` `artifacts.reports.coverage_report` `` exact
- [ ] Nested table: All sub-properties present
- [ ] Code Block 1: YAML syntax exact with indentation preserved
- [ ] Code Block 1: Multi-line script arrays preserved
- [ ] Code Block 1: Artifacts paths structure clear
- [ ] Code Block 2: Conditional rules with `if/when` logic preserved
- [ ] Code Block 2: Retry configuration with specific failure types intact
- [ ] Code Block 2: Nested `artifacts.reports` configuration complete
- [ ] Variable references: `$CI_COMMIT_BRANCH` notation preserved
- [ ] Gotchas section: Specific version numbers preserved (not "recent")
- [ ] Gotchas: All edge cases listed (not condensed to top 3)
- [ ] Breaking changes: Version numbers and migration paths clear
- [ ] No summaries replacing actual configuration examples
- [ ] No "[job rules]" or "[conditions]" in place of actual rule blocks
- [ ] Multiple examples per topic: all present (not reduced to one)

---

## Baseline Metrics Summary

This table summarizes expected extraction completeness for each URL:

| URL | Tables | Code Blocks | Lines Expected | Complexity | Markup Types |
|-----|--------|------------|-----------------|------------|--------------|
| Skill Schema | 2 | 1 YAML | 150-200 | Medium | Inline code, bold |
| Docker Compose | 2+ | 2-3 YAML | 300-400 | High | Code, lists, callouts |
| Packer HCL | 1 | 2-3 HCL | 250-350 | High | Code, comments, nesting |
| GitLab CI | 2+ | 2-3 YAML | 400-500 | Very High | Code, rules, callouts, warnings |

---

## Accessibility Confirmation

**As of 2026-03-02**, all four URLs were confirmed publicly accessible:
- No authentication required
- No client-side JavaScript rendering required for content access
- HTML source available via curl without special headers

---

## Notes for Validation Team

1. **Real pages used**: These are working documentation pages, not synthetic test cases. This ensures validation reflects real-world extraction scenarios.

2. **Version specificity**: Some URLs may change between validation runs (e.g., GitLab CI docs update frequently). Document the access date and any page structure changes discovered.

3. **Content verification**: Before extracting, manually visit each URL and confirm expected tables/code blocks are present. If page structure changed, update this document and checkpoint before proceeding.

4. **Markup variations**: Different pages may use different markup (e.g., GitHub-flavored markdown rendered as HTML). Adapt expectations if needed, but document changes.

5. **Baseline captures**: The raw curl outputs saved in `plan/baseline-outputs/` serve as the truth source. If disagreement arises on what "correct extraction" looks like, refer to curl output.
