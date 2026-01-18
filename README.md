# Claude Skills Repository

A Claude Code Marketplace Plugin providing 22 specialized skills that extend Claude's capabilities with domain expertise, workflows, and best practices.

## Installation

```bash
# Install from marketplace
cc plugin install Jamie-BitFlight/claude_skills
```

Or clone and install locally:

```bash
git clone https://github.com/Jamie-BitFlight/claude_skills.git
cd claude_skills
./install.py
```

## Plugins

### Python Development

| Plugin | Description |
|--------|-------------|
| [python3-development](./plugins/python3-development/) | Python CLI applications with Typer, Rich, and modern patterns |
| [uv](./plugins/uv/) | Astral's uv - extremely fast Python package and project manager |
| [hatchling](./plugins/hatchling/) | Modern Python build backend (PEP 517/518/621/660) |
| [async-python-patterns](./plugins/async-python-patterns/) | asyncio, concurrent programming, async/await patterns |
| [toml-python](./plugins/toml-python/) | Reading/writing pyproject.toml with comment preservation |
| [pypi-readme-creator](./plugins/pypi-readme-creator/) | Creating PyPI-ready README files |

### Code Quality and Git

| Plugin | Description |
|--------|-------------|
| [holistic-linting](./plugins/holistic-linting/) | Comprehensive linting and formatting workflows |
| [pre-commit](./plugins/pre-commit/) | Automated code quality checks on git commit |
| [conventional-commits](./plugins/conventional-commits/) | Conventional commit message formatting |
| [commitlint](./plugins/commitlint/) | Commit message validation setup |
| [clang-format](./plugins/clang-format/) | C/C++ code formatting configuration |

### Documentation and CI/CD

| Plugin | Description |
|--------|-------------|
| [mkdocs](./plugins/mkdocs/) | MkDocs documentation with Material theme |
| [gitlab-skill](./plugins/gitlab-skill/) | GitLab CI/CD and GitLab Flavored Markdown |

### AI and LLM Tools

| Plugin | Description |
|--------|-------------|
| [fastmcp-creator](./plugins/fastmcp-creator/) | Build Model Context Protocol (MCP) servers |
| [litellm](./plugins/litellm/) | LiteLLM for unified LLM API access |
| [llamafile](./plugins/llamafile/) | Local LLM inference with llamafile |
| [prompt-optimization-claude-45](./plugins/prompt-optimization-claude-45/) | Optimize CLAUDE.md and skills for Claude Code |

### Agent Orchestration and Workflows

| Plugin | Description |
|--------|-------------|
| [agent-orchestration](./plugins/agent-orchestration/) | Scientific delegation framework for sub-agents |
| [verification-gate](./plugins/verification-gate/) | Pre-action verification checkpoints |
| [brainstorming-skill](./plugins/brainstorming-skill/) | Structured idea generation and exploration |
| [story-based-framing](./plugins/story-based-framing/) | Pattern/anti-pattern description for LLM detection |

### System Configuration

| Plugin | Description |
|--------|-------------|
| [xdg-base-directory](./plugins/xdg-base-directory/) | XDG Base Directory specification compliance |

## Usage

Skills activate automatically based on context, or explicitly:

```text
@uv
Help me set up a new Python project with dependencies
```

```text
@conventional-commits
Create a commit message for these changes
```

## Repository Structure

```text
claude_skills/
├── plugins/                    # 22 marketplace plugins
│   └── {plugin-name}/
│       ├── .claude-plugin/
│       │   └── plugin.json     # Plugin manifest
│       ├── skills/             # Skill definitions
│       ├── commands/           # Slash commands (optional)
│       ├── agents/             # Sub-agents (optional)
│       └── README.md           # Plugin documentation
├── .claude/                    # Local Claude Code configuration
│   ├── agents/                 # Repository agents
│   ├── commands/               # Repository commands
│   └── skills/                 # Repository skills
├── sessions/                   # cc-sessions framework
└── install.py                  # Local installation script
```

## Creating New Skills

Use the skill-creator skill to create new skills:

```text
@skill-creator
Create a new skill for Kubernetes deployment patterns
```

After creating skills, run the installation script:

```bash
./install.py
```

## Local Development

```bash
# Run pre-commit checks
uv run pre-commit run --all-files

# Install pre-commit hooks
uv run pre-commit install
```

## License

See individual plugin directories for license information.
