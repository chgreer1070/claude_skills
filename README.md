# Claude Skills Repository

Claude Code Marketplace plugin with 22 plugins extending Claude's capabilities.

## Installation

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install {plugin-name}@jamie-bitflight-skills
```

## Plugins

### Python Development
| Plugin | Description |
|--------|-------------|
| [python3-development](./plugins/python3-development/) | Python project workflows, testing, async |
| [async-python-patterns](./plugins/async-python-patterns/) | asyncio, concurrent programming |
| [uv](./plugins/uv/) | Astral's uv package manager |
| [hatchling](./plugins/hatchling/) | Hatchling build system |
| [toml-python](./plugins/toml-python/) | pyproject.toml handling |
| [pypi-readme-creator](./plugins/pypi-readme-creator/) | PyPI README generation |

### Code Quality and Git
| Plugin | Description |
|--------|-------------|
| [holistic-linting](./plugins/holistic-linting/) | Coordinated linting |
| [pre-commit](./plugins/pre-commit/) | Git commit hooks |
| [commitlint](./plugins/commitlint/) | Commit message validation |
| [conventional-commits](./plugins/conventional-commits/) | Conventional commit format |
| [clang-format](./plugins/clang-format/) | C/C++ formatting |

### Documentation and CI/CD
| Plugin | Description |
|--------|-------------|
| [mkdocs](./plugins/mkdocs/) | MkDocs with Material theme |
| [gitlab-skill](./plugins/gitlab-skill/) | GitLab CI/CD |

### AI and LLM Tools
| Plugin | Description |
|--------|-------------|
| [fastmcp-creator](./plugins/fastmcp-creator/) | MCP server building |
| [litellm](./plugins/litellm/) | LLM API integration |
| [llamafile](./plugins/llamafile/) | Local LLM inference |
| [prompt-optimization-claude-45](./plugins/prompt-optimization-claude-45/) | CLAUDE.md optimization |

### Agent Orchestration
| Plugin | Description |
|--------|-------------|
| [agent-orchestration](./plugins/agent-orchestration/) | Sub-agent delegation |
| [verification-gate](./plugins/verification-gate/) | Pre-action verification |
| [brainstorming-skill](./plugins/brainstorming-skill/) | Idea generation |
| [story-based-framing](./plugins/story-based-framing/) | Pattern storytelling |

### System
| Plugin | Description |
|--------|-------------|
| [xdg-base-directory](./plugins/xdg-base-directory/) | XDG paths |

## Development

```bash
claude --plugin-dir ./plugins/{plugin-name}
```
