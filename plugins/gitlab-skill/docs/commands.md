# Commands Reference

The gitlab-skill plugin provides a slash command for managing GitLab CI/CD publishing tokens.

## /setup-ci-publish-token

**Description**: Create GitLab project access token for CI/CD publishing and add as masked CI variable

**Arguments**: None

**Model**: Inherits from session

**Allowed Tools**: Inherits from session

### Usage

```
/setup-ci-publish-token
```

### Problem Solved

GitLab CI `CI_JOB_TOKEN` has limited permissions and cannot upload release assets, causing `401 Unauthorized` errors when using `glab release create` with file attachments.

### Solution

The command automatically:
1. Verifies your GITLAB_TOKEN has required permissions (api scope + Maintainer access)
2. Checks if `ci-publish-token` project access token exists
3. Checks if `CI_PUBLISH_TOKEN` CI/CD variable exists
4. Takes appropriate action based on current state

### Prerequisites

Before running the command, ensure:
- `GITLAB_TOKEN` environment variable set with `api` scope and Maintainer+ access to the project
- `jq` installed
- `glab` installed and authenticated
- Running from the git repository root

### Script Behavior

| Token Exists? | Token Valid? | Variable Exists? | Script Action |
|---------------|--------------|------------------|---------------|
| No | N/A | Any | Creates token and variable |
| Yes | Expired | Yes | Rotates token, updates variable |
| Yes | Valid | No | Rotates token to get value, creates variable |
| Yes | Valid | Yes | No action needed (already configured) |

### Examples

#### First-Time Setup

```bash
# Ensure GITLAB_TOKEN is set
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Run the command
/setup-ci-publish-token
```

**Output**:
```
INFO: Creating project access token 'ci-publish-token'...
INFO: Setting CI variable 'CI_PUBLISH_TOKEN'...
DONE: Token and variable created.
```

#### Already Configured

```bash
/setup-ci-publish-token
```

**Output**:
```
OK: Already configured. Token 'ci-publish-token' expires 2025-12-31.
```

#### Renew Expired Token

```bash
/setup-ci-publish-token
```

**Output**:
```
INFO: Token expired (2025-01-15). Rotating...
INFO: Updating CI variable 'CI_PUBLISH_TOKEN'...
DONE: Token rotated and variable updated.
```

### Output Messages

The script uses consistent prefixes:

- `ERROR:` - Fatal error, script exits with non-zero status
- `INFO:` - Progress information
- `DONE:` - Successful completion with changes made
- `OK:` - Successful completion, no changes needed

### Using the Token in CI/CD

Once created, use the token in your `.gitlab-ci.yml` or CI scripts:

#### Shell Script Example

```bash
PUBLISH_TOKEN="${CI_PUBLISH_TOKEN:-${GITLAB_TOKEN:-${GL_TOKEN:-}}}"
if [ -n "${PUBLISH_TOKEN}" ]; then
  glab auth login --hostname "${CI_SERVER_HOST}" --token "${PUBLISH_TOKEN}"
else
  glab auth login --hostname "${CI_SERVER_HOST}" --job-token "${CI_JOB_TOKEN}"
fi
```

#### Python Script Example

```python
import os

token = (os.environ.get("CI_PUBLISH_TOKEN") or
         os.environ.get("GITLAB_TOKEN") or
         os.environ.get("GL_TOKEN") or
         os.environ.get("CI_JOB_TOKEN"))
```

#### GitLab CI Example

```yaml
release:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache glab
    - glab auth login --hostname ${CI_SERVER_HOST} --token ${CI_PUBLISH_TOKEN}
  script:
    - |
      glab release create "v${CI_COMMIT_TAG}" \
        --name "Release ${CI_COMMIT_TAG}" \
        --notes "Release notes here" \
        --assets-links name="Binary",url="${CI_PROJECT_URL}/-/jobs/${CI_JOB_ID}/artifacts/raw/dist/app"
  rules:
    - if: $CI_COMMIT_TAG
  only:
    - tags
```

### Token Details

The script creates tokens with:
- **Name**: `ci-publish-token`
- **Access level**: Maintainer
- **Scopes**: `api`, `write_repository`
- **Duration**: 1 year (8760h)

The CI variable is created with:
- **Protected**: Yes (only available on protected branches)
- **Masked**: Yes (hidden in job logs)

### Arguments

This command takes no arguments.

### Related Agent

No dedicated agent for this command.

### Hooks

No hooks configured for this command.

### Troubleshooting

#### ERROR: The current GITLAB_TOKEN does not have the 'api' scope

**Cause**: Your personal access token needs the `api` scope.

**Solution**: Create a new token at Settings > Access Tokens with `api` scope enabled.

#### ERROR: The current GITLAB_TOKEN does not have Maintainer (40) or higher access

**Cause**: You need Maintainer or Owner role on the project to manage project access tokens and CI variables.

**Solution**: Request elevated permissions from a project owner, or have an owner run the command.

#### 401 Unauthorized errors persist after setup

**Possible causes**:
- Job not running on protected branch (the variable is protected)
- Token has expired
- CI script still using `CI_JOB_TOKEN` instead of `CI_PUBLISH_TOKEN`

**Solutions**:
- Verify the job runs on a protected branch
- Check token hasn't expired: `glab token list`
- Verify your CI script is using `CI_PUBLISH_TOKEN`, not `CI_JOB_TOKEN`

#### Variable not available in job

**Cause**: Protected variables only work on protected branches.

**Solution**: Verify the branch/tag is protected in Settings > Repository > Protected branches.

### Related Documentation

- [GitLab Project Access Tokens](https://docs.gitlab.com/user/project/settings/project_access_tokens/)
- [GitLab CI/CD Variables](https://docs.gitlab.com/ci/variables/)
- [glab token documentation](https://gitlab.com/gitlab-org/cli/-/blob/main/docs/source/token/index.md)

---

[← Back to README](../README.md)
