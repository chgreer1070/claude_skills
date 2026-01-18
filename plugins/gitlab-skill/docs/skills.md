# Skills Reference

The gitlab-skill plugin provides comprehensive expertise for GitLab CI/CD pipelines, GitLab Flavored Markdown documentation, and local testing workflows.

## gitlab-skill

**Location**: `skills/gitlab-skill/SKILL.md`

**Description**: The model must apply when tasks involve .gitlab-ci.yml configuration, GitLab Flavored Markdown (GLFM) syntax, gitlab-ci-local testing, CI/CD pipeline optimization, GitLab CI Steps composition, Docker-in-Docker workflows, or GitLab documentation creation. Triggers include modifying pipelines, writing GitLab README/Wiki content, debugging CI jobs locally, implementing caching strategies, or configuring release workflows.

**User Invocable**: Yes (default)

**Allowed Tools**: Inherits from session

**Model**: Inherits from session

### When to Use

The skill automatically activates when:
- Editing `.gitlab-ci.yml` files
- Writing GitLab README or Wiki documentation
- Testing CI pipelines locally with gitlab-ci-local
- Implementing caching or optimization strategies
- Configuring Docker-in-Docker workflows
- Using glab CLI for pipeline operations
- Debugging CI/CD job failures

### Capability Domains

#### Domain 1: CI/CD Pipeline Configuration

**Triggers**:
- Task involves .gitlab-ci.yml file
- Pipeline performance optimization required
- Caching strategy implementation needed
- Conditional job execution configuration
- Secret/environment variable management
- Docker-in-Docker (dind) workflow setup
- Pipeline job failure troubleshooting
- GitLab CI Steps composition for reusable workflow units

**Key Constraints**:
- Validate .gitlab-ci.yml syntax before committing
- Implement caching for dependencies to minimize build time
- Use masked variables for sensitive data
- Define timeout limits for all jobs
- Test pipelines locally with gitlab-ci-local before pushing
- Use .gitlab-ci.yml include feature for modular configurations
- Optimize job dependencies to prevent unnecessary execution

**Reference Files**:
- [pipeline-optimization.md](../skills/gitlab-skill/references/pipeline-optimization.md) - Caching strategies, job parallelization
- [common-patterns.md](../skills/gitlab-skill/references/common-patterns.md) - Reusable configuration examples
- [ci-steps/index.md](../skills/gitlab-skill/references/ci-steps/index.md) - GitLab CI Steps documentation

**Validation Checklist**:
- [ ] Syntax validated against GitLab CI schema
- [ ] Jobs and stages use descriptive names, logical organization
- [ ] Caching configured for dependencies
- [ ] Secrets masked, environment variables secured
- [ ] Conditional execution prevents unnecessary resource consumption
- [ ] Artifacts configured with appropriate expiration
- [ ] Timeout limits defined per job
- [ ] Pipeline tested locally with gitlab-ci-local
- [ ] Pipeline architecture documented

#### Domain 2: GitLab Flavored Markdown (GLFM)

**Triggers**:
- Writing README files for GitLab projects
- Creating GitLab Wiki pages
- API documentation with GitLab syntax highlighting
- User guides requiring collapsible sections
- Process flow diagrams with Mermaid
- Changelogs with GitLab issue/MR references

**GLFM Syntax Features**:
- Alert blocks: `[!note]`, `[!tip]`, `[!important]`, `[!caution]`, `[!warning]`
- Collapsible sections: `<details><summary>` syntax
- Mermaid diagrams for visualizations
- Task lists with completion tracking
- GitLab references: #issue, !MR, @user
- Table of contents generation
- Math expressions support
- Color chips for design documentation

**Critical Syntax Rules**:
1. Alert types MUST be lowercase: `[!note]` not `[!Note]` or `[!NOTE]`
2. `<details><summary>` MUST be single line: `<details><summary>Text</summary>` not multi-line
3. No markdown syntax inside `<summary>` tags - use HTML equivalents (`<code>`, `<strong>`)
4. Validate rendering with validate-glfm.py script before finalizing

**Reference Files**:
- [glfm-syntax.md](../skills/gitlab-skill/references/glfm-syntax.md) - Complete syntax guide, examples, common mistakes

**Validation Checklist**:
- [ ] Alert blocks use lowercase syntax: `[!note]`, `[!tip]`, `[!important]`, `[!caution]`, `[!warning]`
- [ ] Collapsible sections use single-line `<details><summary>` format
- [ ] No markdown syntax in `<summary>` tags
- [ ] Mermaid diagrams used for process flows
- [ ] Table of contents present for documents >100 lines
- [ ] GitLab references used: #issue, !MR, @user
- [ ] Code blocks have language specifiers
- [ ] Heading hierarchy consistent (no skipped levels)
- [ ] Rendered output validated with validate-glfm.py

#### Domain 3: Local Pipeline Testing

**Triggers**:
- Testing .gitlab-ci.yml changes before push
- Debugging pipeline job failures locally
- Validating release workflows without actual release creation
- Testing specific jobs/stages in isolation
- Verifying conditional job execution logic
- Checking artifact generation and dependencies

**Setup Procedure**:

```bash
# 1. Install gitlab-ci-local globally
npm install -g gitlab-ci-local

# 2. Configure authentication tokens
# Edit $HOME/.gitlab-ci-local/variables.yml

# 3. Set project-specific variables
# Create .gitlab-ci-local-variables.yml in project root

# 4. Execute job locally
gitlab-ci-local <job-name>
```

**Common Operations**:

```bash
gitlab-ci-local --list                    # List all jobs
gitlab-ci-local --preview                 # Preview parsed configuration
gitlab-ci-local --stage test              # Run specific stage
gitlab-ci-local --needs release           # Run with dependencies
gitlab-ci-local --timestamps job-name     # Debug with timestamps
```

**Reference Files**:
- [gitlab-ci-local-guide.md](../skills/gitlab-skill/references/gitlab-ci-local-guide.md) - Setup, authentication, troubleshooting

**Validation Checklist**:
- [ ] gitlab-ci-local installed and accessible
- [ ] Authentication tokens configured in $HOME/.gitlab-ci-local/variables.yml
- [ ] Project variables defined in .gitlab-ci-local-variables.yml
- [ ] Jobs execute locally without errors
- [ ] Artifacts present in .gitlab-ci-local/artifacts/
- [ ] Configuration validated with `--preview` flag

#### Domain 4: GitLab CLI (glab)

**Triggers**:
- Monitoring pipeline status from terminal
- Linting CI configuration before push
- Listing or inspecting pipelines and jobs
- Non-interactive CI/CD operations in scripts or automation

**Critical: Avoid Interactive Commands**

The `glab ci view` command launches an interactive TUI. Use non-interactive alternatives:

```bash
# INTERACTIVE (avoid in automation):
glab ci view                    # Opens interactive TUI

# NON-INTERACTIVE alternatives:
glab ci status --compact        # Quick pass/fail status
glab ci get                     # Pipeline details as text
glab ci list --per-page 5       # Recent pipelines table
```

**Linting CI Configuration**:

```bash
# Validate .gitlab-ci.yml syntax via GitLab API
glab ci lint

# Include job list in output
glab ci lint --include-jobs

# Simulate pipeline creation (dry run)
glab ci lint --dry-run --ref main
```

The lint command sends the local `.gitlab-ci.yml` to GitLab API for validation. This resolves `include:` directives from the remote repository, so included files must be committed and pushed for accurate validation.

**Pipeline Monitoring**:

```bash
# List recent pipelines with status
glab ci list --per-page 5

# Get current branch pipeline details
glab ci get

# Quick status check (exits non-zero on failure)
glab ci status --compact
```

**Common Workflow**:

```bash
# 1. Validate before commit
glab ci lint

# 2. Commit and push
git add . && git commit -m "message" && git push

# 3. Monitor pipeline
glab ci list --per-page 3
glab ci status --compact

# 4. On failure, get details
glab ci get
```

### Activation

The skill activates automatically - Claude decides when to apply based on task context.

**Manual activation** (if needed):

```
@gitlab-skill
```

Or via Skill tool:

```
Skill(command: "gitlab-skill")
```

### Hooks

No hooks configured.

### Execution Protocol

When the skill activates, it follows this sequence:

1. **Update documentation reference** (first step):
   ```bash
   uv run scripts/sync-gitlab-docs.py --working-dir .
   ```
   - Updates GitLab CI documentation from official repository
   - Respects 3-day cooldown (successful runs only)
   - Use `--force` flag to bypass cooldown if needed
   - Creates/updates Documentation Index in SKILL.md
   - Lock file: `.sync-gitlab-docs.lock` (gitignored)

2. Identify domain: CI/CD configuration, GLFM documentation, or local testing
3. Load domain-specific reference files for technical specifications
4. Apply domain constraints and validation rules
5. Execute domain-specific validation checklist
6. Validate output using appropriate tooling (gitlab-ci-local or validate-glfm.py)

### Quick Start Paths

**If task involves CI/CD pipeline:**
1. Load [pipeline-optimization.md](../skills/gitlab-skill/references/pipeline-optimization.md)
2. Review [common-patterns.md](../skills/gitlab-skill/references/common-patterns.md) for reusable configurations
3. Test locally with gitlab-ci-local before pushing

**If task involves GLFM documentation:**
1. Load [glfm-syntax.md](../skills/gitlab-skill/references/glfm-syntax.md)
2. Apply CRITICAL_SYNTAX_RULES during writing
3. Validate rendering with validate-glfm.py script

**If task involves local pipeline testing:**
1. Load [gitlab-ci-local-guide.md](../skills/gitlab-skill/references/gitlab-ci-local-guide.md)
2. Verify authentication configuration in $HOME/.gitlab-ci-local/
3. Execute pipeline locally, verify artifacts in .gitlab-ci-local/artifacts/

### Utility Scripts

#### validate-glfm.py

Python script validates GLFM rendering via GitLab Markdown API.

**Usage**:

```bash
# Validate markdown file
uv run --with requests ./scripts/validate-glfm.py --file README.md

# Validate inline markdown
uv run --with requests ./scripts/validate-glfm.py --markdown "> [!note]\n> Test alert"

# Save rendered HTML to file
uv run --with requests ./scripts/validate-glfm.py --file test.md --output rendered.html
```

**Capabilities**:
- Automatic GITLAB_TOKEN environment variable loading
- File or inline markdown input
- HTML output to stdout or file
- Verbose debugging mode (`--verbose`)
- Error handling with retry logic

#### sync-gitlab-docs.py

Python script synchronizes GitLab CI documentation from official repository.

**Usage**:

```bash
# Update documentation (respects 3-day cooldown)
uv run scripts/sync-gitlab-docs.py --working-dir .

# Force update (bypass cooldown)
uv run scripts/sync-gitlab-docs.py --working-dir . --force
```

### Documentation Index

The skill maintains an extensive index of official GitLab CI/CD documentation in SKILL.md (lines 356-603), covering:

- Get started with GitLab CI/CD
- Debugging CI/CD pipelines
- Caching examples
- Docker integration
- Environments and deployments
- Jobs and artifacts
- Pipeline configuration
- Runners
- Secrets management
- Variables
- YAML syntax reference

See [SKILL.md](../skills/gitlab-skill/SKILL.md#documentation-index) for the complete index.

---

[← Back to README](../README.md)
