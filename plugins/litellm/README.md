# LiteLLM

Unified Python interface for calling 100+ LLM APIs using consistent OpenAI format. Provides standardized exception handling, retry/fallback logic, and cost tracking across multiple providers including llamafile, Ollama, OpenAI, Anthropic, and more.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install litellm@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/litellm
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [litellm](./skills/litellm/SKILL.md) | When calling LLM APIs from Python code. When connecting to llamafile or local LLM servers. When switching between OpenAI/Anthropic/local providers. When implementing retry/fallback logic for LLM calls. When code imports litellm or uses completion() patterns. |

## Quick Start

Connect to a local llamafile server using LiteLLM's unified interface:

```python
import litellm

response = litellm.completion(
    model="llamafile/mistralai/mistral-7b-instruct-v0.2",
    messages=[{"role": "user", "content": "Summarize this code change"}],
    api_base="http://localhost:8080/v1",
    temperature=0.2,
    max_tokens=80,
)

print(response.choices[0].message.content)
```

**Key Points:**
- Use `llamafile/` prefix for llamafile models
- API base must end with `/v1` suffix
- No API key required for local llamafile
- All exceptions inherit from OpenAI exception types

For detailed usage including async/streaming, exception handling, embeddings, and proxy configuration, see the [litellm skill documentation](./skills/litellm/SKILL.md).

## License

See repository root for license information.
