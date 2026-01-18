# Usage Examples

Concrete, real-world examples of using the gitlab-skill plugin for CI/CD pipeline configuration, GLFM documentation, and local testing.

## Example 1: Optimize Node.js Pipeline with Caching

**Scenario**: A Node.js project has a slow CI pipeline that reinstalls dependencies on every job, taking 5+ minutes per run.

**Steps**:

1. Ask Claude to optimize the pipeline for caching:
   ```
   Optimize our .gitlab-ci.yml to cache npm dependencies
   ```

2. Claude (with gitlab-skill) analyzes the existing configuration:
   ```yaml
   # Before optimization
   test:
     stage: test
     script:
       - npm install
       - npm test
   ```

3. Claude implements caching with proper keys:
   ```yaml
   # After optimization
   .node_cache: &node_cache
     cache:
       key:
         files:
           - package-lock.json
       paths:
         - node_modules/
       policy: pull

   .node_cache_push: &node_cache_push
     cache:
       key:
         files:
           - package-lock.json
       paths:
         - node_modules/
       policy: push

   install:
     stage: .pre
     script:
       - npm ci
     <<: *node_cache_push

   test:
     stage: test
     script:
       - npm test
     <<: *node_cache
     needs:
       - install

   lint:
     stage: test
     script:
       - npm run lint
     <<: *node_cache
     needs:
       - install
   ```

4. Test locally before pushing:
   ```bash
   gitlab-ci-local test
   ```

**Result**: Pipeline execution time reduced from 5 minutes to 1.5 minutes. Dependencies cached based on package-lock.json hash, ensuring consistent environments.

**Key Techniques Applied**:
- Cache key based on package-lock.json for automatic invalidation
- Separate install job with push policy
- Test jobs use pull policy for cache reuse
- YAML anchors for DRY configuration

---

## Example 2: Create Professional GitLab README with GLFM Alerts

**Scenario**: Create a README.md for a Python library with GitLab-specific alert blocks and collapsible installation instructions.

**Steps**:

1. Ask Claude to create documentation:
   ```
   Create a README.md with installation instructions, usage examples, and important security notes
   ```

2. Claude (with gitlab-skill) writes GLFM-compliant documentation:

```markdown
# Python Configuration Parser

A lightweight, type-safe configuration parser for Python applications.

> [!note]
> This library requires Python 3.9 or higher for full type annotation support.

## Installation

<details>
<summary>Install via pip</summary>

```bash
pip install config-parser
```
</details>

<details>
<summary>Install from source</summary>

```bash
git clone https://gitlab.com/org/config-parser.git
cd config-parser
pip install -e .
```
</details>

## Quick Start

```python
from config_parser import load_config

config = load_config("config.yaml")
print(config.database.host)
```

> [!important]
> Always validate configuration files before deploying to production. Use `config.validate()` to check for required fields and type mismatches.

## Security

> [!warning]
> Never commit configuration files containing secrets to version control. Use GitLab CI/CD variables or external secret managers for sensitive data.

> [!caution]
> This library loads YAML files using `safe_load()` by default. Custom loaders may introduce security risks.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines. Report issues at !1 or mention @maintainer for urgent security concerns.
```

3. Validate GLFM rendering:
   ```bash
   uv run --with requests scripts/validate-glfm.py --file README.md
   ```

4. Review rendered HTML output to confirm alert blocks display correctly.

**Result**: Professional README with properly rendered alert blocks, collapsible sections, and GitLab-specific references.

**Key GLFM Features Used**:
- Lowercase alert syntax: `[!note]`, `[!important]`, `[!warning]`, `[!caution]`
- Single-line `<details><summary>` tags (no markdown inside)
- GitLab references: !MR, @user
- Code blocks with language specifiers

---

## Example 3: Debug Failed CI Job Locally

**Scenario**: A Docker build job fails in GitLab CI with cryptic error messages. Need to debug interactively without polluting git history with test commits.

**Steps**:

1. Configure gitlab-ci-local authentication:
   ```bash
   # Create $HOME/.gitlab-ci-local/variables.yml
   GITLAB_TOKEN: glpat-xxxxxxxxxxxxx
   ```

2. Create project-specific variables:
   ```bash
   # Create .gitlab-ci-local-variables.yml
   DOCKER_REGISTRY: registry.gitlab.com
   CI_REGISTRY_USER: my-user
   ```

3. Run the failing job locally:
   ```bash
   gitlab-ci-local build-docker --timestamps
   ```

4. Claude identifies the issue from local output:
   ```
   ERROR: /bin/sh: line 1: docker: command not found
   ```

5. Claude fixes the .gitlab-ci.yml to use correct service:
   ```yaml
   # Before
   build-docker:
     stage: build
     script:
       - docker build -t myapp .

   # After
   build-docker:
     stage: build
     image: docker:latest
     services:
       - docker:dind
     variables:
       DOCKER_TLS_CERTDIR: "/certs"
     script:
       - docker build -t myapp .
   ```

6. Re-test locally:
   ```bash
   gitlab-ci-local build-docker
   ```

7. Verify artifacts created:
   ```bash
   ls -la .gitlab-ci-local/artifacts/
   ```

**Result**: Issue identified and fixed in under 10 minutes without any CI pipeline runs. Docker build now succeeds both locally and in GitLab CI.

**Key Techniques Applied**:
- Local testing with gitlab-ci-local
- Timestamp debugging for pinpointing failures
- Docker-in-Docker service configuration
- Artifact verification

---

## Example 4: Implement Multi-Stage Pipeline with GitLab CI Steps

**Scenario**: Build a reusable CI/CD pipeline using GitLab CI Steps for testing, building, and deploying a microservice.

**Steps**:

1. Ask Claude to create a modular pipeline:
   ```
   Create a .gitlab-ci.yml using GitLab CI Steps for test, build, and deploy stages
   ```

2. Claude (with gitlab-skill) references CI Steps documentation and creates:

```yaml
spec:
  inputs:
    environment:
      default: staging

---

steps:
  - name: run-tests
    step: gitlab.com/steps/pytest@1
    inputs:
      test_path: tests/
      coverage: true
      pytest_args: "-v --junit-xml=report.xml"

  - name: build-docker-image
    step: gitlab.com/steps/docker-build@1
    inputs:
      dockerfile: Dockerfile
      context: .
      tags:
        - $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
        - $CI_REGISTRY_IMAGE:latest
    needs:
      - run-tests

  - name: deploy-to-k8s
    step: gitlab.com/steps/kubectl-apply@1
    inputs:
      manifest: k8s/${{ inputs.environment }}.yaml
      namespace: ${{ inputs.environment }}
    needs:
      - build-docker-image
    rules:
      - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

3. Test the pipeline configuration:
   ```bash
   glab ci lint --include-jobs
   ```

4. Run specific step locally:
   ```bash
   gitlab-ci-local run-tests
   ```

**Result**: Modular, maintainable pipeline using official GitLab CI Steps. Steps are versioned, tested by GitLab, and reusable across projects.

**Key CI Steps Features Used**:
- Input parameters for environment customization
- Needs dependencies for job orchestration
- Official GitLab steps for common tasks
- Rules for conditional execution

---

## Example 5: Automate Token Management for Release Publishing

**Scenario**: Release jobs fail with `401 Unauthorized` when uploading artifacts because `CI_JOB_TOKEN` lacks permissions.

**Steps**:

1. Run the setup command:
   ```
   /setup-ci-publish-token
   ```

2. Claude executes the command, which:
   - Creates project access token `ci-publish-token`
   - Adds CI variable `CI_PUBLISH_TOKEN` (protected + masked)
   - Configures token with `api` and `write_repository` scopes

3. Update .gitlab-ci.yml to use the new token:
   ```yaml
   release:
     stage: deploy
     image: alpine:latest
     before_script:
       - apk add --no-cache glab
       - |
         if [ -n "${CI_PUBLISH_TOKEN}" ]; then
           glab auth login --hostname ${CI_SERVER_HOST} --token ${CI_PUBLISH_TOKEN}
         else
           glab auth login --hostname ${CI_SERVER_HOST} --job-token ${CI_JOB_TOKEN}
         fi
     script:
       - |
         glab release create "${CI_COMMIT_TAG}" \
           --name "Release ${CI_COMMIT_TAG}" \
           --notes-file CHANGELOG.md \
           --assets-links name="Binary",url="${CI_PROJECT_URL}/-/jobs/${CI_JOB_ID}/artifacts/raw/dist/app" \
           --assets-links name="Checksums",url="${CI_PROJECT_URL}/-/jobs/${CI_JOB_ID}/artifacts/raw/dist/checksums.txt"
     rules:
       - if: $CI_COMMIT_TAG
     only:
       - tags
   ```

4. Test on protected branch (token is protected):
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

5. Verify release created with artifacts attached.

**Result**: Automated release publishing with proper authentication. Token automatically rotates before expiry.

**Key Features Used**:
- Protected CI variables for security
- Masked variables to hide token in logs
- Conditional authentication (falls back to CI_JOB_TOKEN if token unavailable)
- Automatic token rotation handling

---

## Example 6: Validate GLFM Before Committing

**Scenario**: Ensure documentation renders correctly in GitLab before pushing changes.

**Steps**:

1. Write or modify GLFM documentation in README.md

2. Validate syntax:
   ```bash
   uv run --with requests scripts/validate-glfm.py --file README.md
   ```

3. Claude (with gitlab-skill) runs validation and identifies issues:
   ```
   WARNING: Alert block uses uppercase '[!NOTE]' - should be '[!note]'
   ERROR: <summary> tag spans multiple lines - must be single line
   ```

4. Claude fixes the issues:
   ```markdown
   <!-- Before -->
   > [!NOTE]
   > This is a note

   <details>
   <summary>
   **Installation Instructions**
   </summary>
   ```

   ```markdown
   <!-- After -->
   > [!note]
   > This is a note

   <details>
   <summary>Installation Instructions</summary>
   ```

5. Re-validate:
   ```bash
   uv run --with requests scripts/validate-glfm.py --file README.md --output preview.html
   ```

6. Review preview.html in browser to confirm rendering

**Result**: Documentation renders perfectly in GitLab. No surprises after push.

**Key Validation Features Used**:
- Syntax validation via GitLab API
- HTML preview generation
- Automatic GITLAB_TOKEN loading
- Verbose debugging mode

---

## Example 7: Monitor Pipeline Status with glab CLI

**Scenario**: Check pipeline status without leaving terminal during active development.

**Steps**:

1. Validate before committing:
   ```bash
   glab ci lint --include-jobs
   ```

2. Commit and push:
   ```bash
   git add .gitlab-ci.yml
   git commit -m "feat: add caching for npm dependencies"
   git push
   ```

3. Monitor pipeline status:
   ```bash
   # Quick status check
   glab ci status --compact

   # List recent pipelines
   glab ci list --per-page 3
   ```

   Output:
   ```
   State          IID        Ref     Created
   (running)    #1254280   (#5)   feat/caching    (30 seconds ago)
   (success)    #1254276   (#4)   main            (1 minute ago)
   (failed)     #1254271   (#3)   main            (15 minutes ago)
   ```

4. Get detailed job information:
   ```bash
   glab ci get
   ```

   Output:
   ```
   # Pipeline:
   id:       1254280
   status:   success
   source:   push
   ref:      feat/caching
   sha:      c3f955e...
   yaml Errors:

   # Jobs:
   install:  success  (45s)
   test:     success  (23s)
   lint:     success  (18s)
   build:    success  (1m 12s)
   ```

5. If failures occur, use non-interactive commands for automation:
   ```bash
   if ! glab ci status --compact; then
     echo "Pipeline failed! Check details:"
     glab ci get
     exit 1
   fi
   ```

**Result**: Complete pipeline monitoring without browser context switching. Non-interactive commands work perfectly in CI/CD and automation scripts.

**Key glab Features Used**:
- CI linting before push
- Non-interactive status checking
- Pipeline and job listing
- Detailed job inspection
- Exit codes for scripting

---

[← Back to README](../README.md)
