# LiteLLM Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Unified Python interface for calling 100+ LLM APIs using consistent OpenAI format. Provides standardized exception handling, retry/fallback logic, and cost tracking across multiple providers.

## Features

- **Unified API** - Single `completion()` function for all LLM providers
- **Llamafile Integration** - Direct support for local llamafile servers
- **Exception Mapping** - All provider errors map to OpenAI exception types
- **Retry Logic** - Built-in retry with configurable attempts
- **Streaming Support** - Sync and async streaming for all providers
- **Cost Tracking** - Automatic usage and cost calculation
- **Multi-Provider** - OpenAI, Anthropic, Google, AWS Bedrock, local servers

## Installation

### Prerequisites

- Claude Code version 2.1+
- Python 3.11+
- LiteLLM package: `pip install litellm` or `uv add litellm`
- (Optional) Running llamafile server for local LLM inference

### Install Plugin

```bash
# Method 1: Using cc plugin install (if published to marketplace)
cc plugin install litellm

# Method 2: Manual installation
cp -r plugins/litellm ~/.claude/plugins/litellm
cc plugin reload
```

## Quick Start

```python
import litellm

# Call any LLM using OpenAI format
response = litellm.completion(
    model="llamafile/mistralai/mistral-7b-instruct-v0.2",
    messages=[{"role": "user", "content": "Summarize this diff"}],
    api_base="http://localhost:8080/v1",
    temperature=0.2,
    max_tokens=80,
)

print(response.choices[0].message.content)
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | litellm | Unified LLM API interface with llamafile integration, exception handling, retry logic | Activated automatically by Claude when working with LLM APIs |

## Usage

### Skills

The litellm plugin provides one comprehensive skill that activates automatically when:

- Calling LLM APIs from Python code
- Connecting to llamafile or local LLM servers
- Switching between OpenAI/Anthropic/local providers
- Implementing retry/fallback logic for LLM calls
- Code imports litellm or uses `completion()` patterns

Claude automatically applies this skill when detecting relevant patterns in your requests.

[View detailed Skills Reference →](./docs/skills.md)

## Configuration

### Llamafile Connection

```python
import os

# Set base URL for llamafile server
os.environ["LLAMAFILE_API_BASE"] = "http://localhost:8080/v1"
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `LLAMAFILE_API_BASE` | Llamafile server endpoint | `http://localhost:8080/v1` |
| `LITELLM_LOG` | Enable debug logging | `INFO` or `DEBUG` |

[View detailed Configuration Reference →](./docs/configuration.md)

## Examples

### Async Streaming with Llamafile

```python
from litellm import acompletion
import asyncio

async def stream_response():
    response = await acompletion(
        model="llamafile/gemma-3-3b",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        api_base="http://localhost:8080/v1",
        stream=True,
    )

    async for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

asyncio.run(stream_response())
```

### Exception Handling

```python
import litellm
import openai

try:
    response = litellm.completion(
        model="llamafile/gemma-3-3b",
        messages=[{"role": "user", "content": "Hello"}],
        api_base="http://localhost:8080/v1",
        timeout=30.0,
    )
except openai.APITimeoutError as e:
    print(f"Timeout: {e}")
except litellm.APIConnectionError as e:
    print(f"Connection failed: {e.message}")
    print(f"Provider: {e.llm_provider}")
```

[View more examples →](./docs/examples.md)

## Troubleshooting

### Connection Issues

**Problem**: `APIConnectionError` when calling llamafile

**Solutions**:
- Verify llamafile server is running: `curl http://localhost:8080/v1/models`
- Check port number (default is 8080, not 8000)
- Ensure API base includes `/v1` suffix
- Do NOT add `/chat/completions` to `api_base` (LiteLLM adds this automatically)

### Model Routing Issues

**Problem**: Model not recognized or wrong provider used

**Solutions**:
- Always use `llamafile/` prefix for llamafile models
- Example: `model="llamafile/gemma-3-3b"` (not just `"gemma-3-3b"`)
- Verify model name matches your llamafile server configuration

### Timeout Errors

**Problem**: Requests timing out with large context

**Solutions**:
- Increase timeout: `timeout=60.0`
- Reduce `max_tokens` parameter
- Enable streaming for long responses: `stream=True`
- Add retry logic: `num_retries=3`

## Contributing

Contributions to improve LiteLLM integration patterns, add new provider examples, or enhance documentation are welcome.

## License

MIT

## Credits

**Plugin Author**: Claude Code Skills Repository

**LiteLLM**: [BerriAI/litellm](https://github.com/BerriAI/litellm)

## Related Skills

- **llamafile** - Activate using `Skill(command: "llamafile")` for llamafile server setup and management
- **uv** - Activate using `Skill(command: "uv")` for Python dependency management
