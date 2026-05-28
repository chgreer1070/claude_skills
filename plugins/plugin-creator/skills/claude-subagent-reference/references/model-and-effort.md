# Model and Effort Configuration

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Choose a model (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/model-config.md> (accessed 2026-05-28)

## Model field

The `model` frontmatter field accepts:

| Value | Behavior |
|:------|:---------|
| `sonnet` | Latest Sonnet model — daily coding tasks. On Anthropic API: Sonnet 4.6. On Bedrock/Vertex: Sonnet 4.5 |
| `opus` | Latest Opus model — complex reasoning. On Anthropic API: Opus 4.7. On Bedrock/Vertex: Opus 4.6 |
| `haiku` | Fast, efficient model for simple tasks |
| Full model ID | e.g., `claude-opus-4-7`, `claude-sonnet-4-6` — pins a specific version |
| `inherit` | Same model as the main conversation (default when field is omitted) |

## Model resolution order

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Choose a model (accessed 2026-05-28)

When Claude invokes a subagent, the model resolves in this order (first match wins):

1. `CLAUDE_CODE_SUBAGENT_MODEL` environment variable
2. Per-invocation `model` parameter Claude passes when delegating
3. Subagent definition's `model` frontmatter field
4. Main conversation's model

## CLAUDE_CODE_SUBAGENT_MODEL

SOURCE: <https://code.claude.com/docs/en/env-vars.md> (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/model-config.md> § Environment variables (accessed 2026-05-28)

Overrides the model for ALL subagents and agent teams, regardless of per-invocation parameters and frontmatter:

```bash
export CLAUDE_CODE_SUBAGENT_MODEL=haiku
```

Set to `inherit` to restore normal model resolution:

```bash
export CLAUDE_CODE_SUBAGENT_MODEL=inherit
```

---

## Effort field

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Supported frontmatter fields (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/model-config.md> § Adjust effort level (accessed 2026-05-28)

The `effort` field overrides the session effort level when this specific subagent is active:

```yaml
effort: high
```

Available levels depend on the model:

| Model | Supported levels |
|:------|:----------------|
| Opus 4.7 | `low`, `medium`, `high`, `xhigh`, `max` |
| Opus 4.6, Sonnet 4.6 | `low`, `medium`, `high`, `max` |

If you set a level the model does not support, Claude Code falls back to the highest supported level at or below the one you set.

### Effort level guidance

| Level | When to use |
|:------|:------------|
| `low` | Latency-sensitive, scoped, non-intelligence-sensitive tasks |
| `medium` | Cost-sensitive work that can trade some intelligence |
| `high` | Standard implementation, file editing, test writing |
| `xhigh` | Best results for most coding and agentic tasks (recommended default on Opus 4.7) |
| `max` | Deep reasoning — may show diminishing returns; session-only (not persistable in settings) |

### Precedence

`CLAUDE_CODE_EFFORT_LEVEL` env var > frontmatter `effort` > session level

The environment variable takes precedence over the frontmatter `effort` field. Frontmatter effort applies only when the subagent is active, overriding the session level.

## CLAUDE_CODE_EFFORT_LEVEL

SOURCE: <https://code.claude.com/docs/en/env-vars.md> (accessed 2026-05-28)

Set the effort level for all models globally:

```bash
export CLAUDE_CODE_EFFORT_LEVEL=high
```

Valid values: `low`, `medium`, `high`, `xhigh`, `max`, or `auto` (model default).

This variable takes precedence over all other effort configuration including `/effort` command and the `effortLevel` setting.
