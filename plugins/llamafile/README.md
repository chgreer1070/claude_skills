# Llamafile

Configure and manage Mozilla Llamafile - running LLMs locally with OpenAI-compatible APIs. Provides setup, server configuration, API integration, and troubleshooting guidance for local LLM inference.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install llamafile@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/llamafile
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [llamafile](./skills/llamafile/SKILL.md) | When setting up local LLM inference without cloud APIs. When running GGUF models locally. When needing OpenAI-compatible API from a local model. When building offline/air-gapped AI tools. When troubleshooting local LLM server connections. |

## Quick Start

**1. Download llamafile binary and model:**

```bash
# Download llamafile
curl -L -o llamafile https://github.com/mozilla-ai/llamafile/releases/download/0.9.3/llamafile-0.9.3
chmod 755 llamafile

# Download Gemma 3 3B model (recommended)
curl -L -o gemma-3-3b.gguf \
  https://huggingface.co/Mozilla/gemma-3-3b-it-gguf/resolve/main/gemma-3-3b-it-Q4_K_M.gguf
```

**2. Start server:**

```bash
./llamafile --server -m gemma-3-3b.gguf --nobrowser --port 8080 --host 127.0.0.1
```

**3. Use with LiteLLM:**

```python
import litellm

response = litellm.completion(
    model="llamafile/gemma-3-3b",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="http://localhost:8080/v1",  # Must include /v1
    temperature=0.3
)

print(response.choices[0].message.content)
```

**Critical details:**
- Llamafile uses port **8080** (not 8000)
- API base URL must include `/v1` suffix
- LiteLLM model name must have `llamafile/` prefix

For advanced configuration, GPU acceleration, embeddings, server management, and troubleshooting, see the [llamafile skill](./skills/llamafile/SKILL.md).

## License

Version 1.0.0
