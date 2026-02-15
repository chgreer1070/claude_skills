# ARL Expert Panel — Framework Repository Manifest

Repository URLs and local clone paths for the six framework experts.
The orchestrator uses this manifest to clone missing repositories before running the panel.

## Repositories

| Expert | Local Path | GitHub URL |
| --- | --- | --- |
| bmad-expert | `../BMAD-METHOD/` | <https://github.com/bmad-code-org/BMAD-METHOD> |
| gastown-expert | `../gastown/` | <https://github.com/steveyegge/gastown> |
| gsd-expert | `../get-shit-done/` | <https://github.com/glittercowboy/get-shit-done> |
| octocode-expert | `../octocode-mcp/` | <https://github.com/bgauryy/octocode-mcp> |
| ralph-expert | `../ralph-orchestrator/` | <https://github.com/mikeyobrien/ralph-orchestrator> |
| sam-expert | `../stateless-agent-methodology/` | <https://github.com/bitflight-devops/stateless-agent-methodology> |

## URL Sources

All URLs verified from research files in this repository:

- bmad-expert: `research/agent-frameworks/bmad-method.md` (accessed 2026-02-01)
- gastown-expert: [`sam-vs-gastown.md`](https://github.com/bitflight-devops/stateless-agent-methodology/blob/main/.meta/v1_comparisons/sam-vs-gastown.md) (accessed 2026-01-26)
- gsd-expert: `research/agent-frameworks/get-shit-done.md` (accessed 2026-02-01)
- octocode-expert: `research/mcp-ecosystem/octocode-mcp.md` (accessed 2026-01-26)
- ralph-expert: [`sam-vs-ralph-loop-orchestrator.md`](https://github.com/bitflight-devops/stateless-agent-methodology/blob/main/.meta/v1_comparisons/sam-vs-ralph-loop-orchestrator.md) (accessed 2026-01-26)

## Clone Convention

Repositories are cloned as siblings of the current working directory (`../`).
The orchestrator runs `git clone <url> ../<dir-name>` for each missing repo.
SAM (`../stateless-agent-methodology/`) is a sibling repository. Clone from <https://github.com/bitflight-devops/stateless-agent-methodology> if missing.
