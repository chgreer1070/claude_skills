# Configuration Reference

This document covers environment variables, configuration files, and setup patterns for LiteLLM integration.

## Environment Variables

### Llamafile Configuration

| Variable | Purpose | Example | Required |
|----------|---------|---------|----------|
| `LLAMAFILE_API_BASE` | Llamafile server endpoint | `http://localhost:8080/v1` | No (can pass in code) |
| `LITELLM_LOG` | Enable debug logging | `INFO`, `DEBUG` | No |

**Usage**:

```python
import os

os.environ["LLAMAFILE_API_BASE"] = "http://localhost:8080/v1"
os.environ["LITELLM_LOG"] = "DEBUG"
```

### Cloud Provider API Keys

| Provider | Environment Variable | Required For |
|----------|---------------------|--------------|
| OpenAI | `OPENAI_API_KEY` | OpenAI models |
| Anthropic | `ANTHROPIC_API_KEY` | Claude models |
| Google | `GOOGLE_API_KEY` | Gemini models |
| AWS | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Bedrock models |
| Azure | `AZURE_API_KEY`, `AZURE_API_BASE` | Azure OpenAI |

**Note**: Local llamafile servers do NOT require API keys.

## Configuration Files

### TOML Configuration Pattern

For application-level configuration:

```toml
# ~/.config/myapp/config.toml
[ai]
model = "llamafile/gemma-3-3b"
api_base = "http://localhost:8080/v1"
temperature = 0.3
max_tokens = 200
timeout = 30.0
num_retries = 3
```

**Loading Configuration**:

```python
import tomllib
from pathlib import Path

config_path = Path.home() / ".config" / "myapp" / "config.toml"
with open(config_path, "rb") as f:
    config = tomllib.load(f)

ai_config = config["ai"]
model = ai_config["model"]
api_base = ai_config["api_base"]
```

### YAML Configuration for Proxy Deployment

For LiteLLM proxy servers:

```yaml
# config.yaml
model_list:
  - model_name: commit-polish-model
    litellm_params:
      model: llamafile/gemma-3-3b
      api_base: http://localhost:8080/v1
      temperature: 0.3
      max_tokens: 200

  - model_name: code-review-model
    litellm_params:
      model: llamafile/mistralai/mistral-7b-instruct-v0.2
      api_base: http://localhost:8081/v1
      temperature: 0.2
      max_tokens: 500

general_settings:
  master_key: your_secret_key_here
```

**Starting Proxy**:

```bash
litellm --config config.yaml
```

### JSON Configuration

For programmatic configuration:

```json
{
  "model": "llamafile/gemma-3-3b",
  "api_base": "http://localhost:8080/v1",
  "temperature": 0.3,
  "max_tokens": 200,
  "timeout": 30.0,
  "num_retries": 3
}
```

## API Base URL Configuration

### Correct URL Format

```python
# ✅ Correct - ends with /v1
api_base = "http://localhost:8080/v1"

# ❌ Wrong - missing /v1
api_base = "http://localhost:8080"

# ❌ Wrong - includes endpoint path
api_base = "http://localhost:8080/v1/chat/completions"
```

### Multiple Server Configuration

When running multiple llamafile servers:

```python
SERVERS = {
    "fast": "http://localhost:8080/v1",    # Fast small model
    "accurate": "http://localhost:8081/v1", # Larger model
    "embedding": "http://localhost:8082/v1" # Embedding model
}

# Use based on task
response = litellm.completion(
    model="llamafile/gemma-3-3b",
    api_base=SERVERS["fast"],
    messages=[{"role": "user", "content": "Quick question"}],
)
```

## Model Selection Patterns

### Model Naming Convention

All llamafile models MUST use the `llamafile/` prefix:

```python
# ✅ Correct
model = "llamafile/mistralai/mistral-7b-instruct-v0.2"
model = "llamafile/gemma-3-3b"
model = "llamafile/sentence-transformers/all-MiniLM-L6-v2"

# ❌ Wrong - missing prefix
model = "gemma-3-3b"
model = "mistral-7b-instruct-v0.2"
```

### Dynamic Model Selection

```python
from typing import Literal

ModelType = Literal["fast", "balanced", "accurate"]

MODEL_CONFIGS = {
    "fast": {
        "model": "llamafile/gemma-3-3b",
        "api_base": "http://localhost:8080/v1",
        "max_tokens": 100,
    },
    "balanced": {
        "model": "llamafile/mistralai/mistral-7b-instruct-v0.2",
        "api_base": "http://localhost:8080/v1",
        "max_tokens": 200,
    },
    "accurate": {
        "model": "llamafile/meta-llama/llama-3-8b-instruct",
        "api_base": "http://localhost:8081/v1",
        "max_tokens": 500,
    },
}

def get_completion(prompt: str, model_type: ModelType = "balanced"):
    config = MODEL_CONFIGS[model_type]
    return litellm.completion(
        messages=[{"role": "user", "content": prompt}],
        **config
    )
```

## Timeout Configuration

### Request-Level Timeout

```python
response = litellm.completion(
    model="llamafile/gemma-3-3b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:8080/v1",
    timeout=30.0,  # 30 seconds per request
)
```

### Global Timeout

```python
import litellm

# Set global timeout for all requests
litellm.timeout = 60.0
```

### Streaming with Timeout

```python
from litellm import acompletion
import asyncio

async def stream_with_timeout():
    try:
        response = await asyncio.wait_for(
            acompletion(
                model="llamafile/gemma-3-3b",
                messages=[{"role": "user", "content": "Long explanation"}],
                api_base="http://localhost:8080/v1",
                stream=True,
            ),
            timeout=60.0  # Overall timeout for stream
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
    except asyncio.TimeoutError:
        print("Stream timed out")
```

## Retry Configuration

### Basic Retry

```python
response = litellm.completion(
    model="llamafile/gemma-3-3b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:8080/v1",
    num_retries=3,      # Retry up to 3 times
    timeout=30.0,       # Timeout per attempt
)
```

### Custom Retry Logic

```python
import litellm
from litellm import APIConnectionError
import time

def completion_with_backoff(max_attempts: int = 5, **kwargs):
    """Completion with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return litellm.completion(**kwargs)
        except APIConnectionError as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
```

## Logging Configuration

### Enable LiteLLM Logging

```python
import litellm
import logging

# Enable verbose logging
litellm.set_verbose = True

# Configure logging level
logging.basicConfig(level=logging.DEBUG)
```

### Custom Log Handler

```python
import litellm
import logging

# Create custom logger
logger = logging.getLogger("litellm")
logger.setLevel(logging.INFO)

# Add file handler
file_handler = logging.FileHandler("litellm.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Enable verbose mode
litellm.set_verbose = True
```

## Cost Tracking Configuration

### Enable Cost Tracking

```python
import litellm

# Enable cost tracking
litellm.success_callback = ["cost_tracking"]

response = litellm.completion(
    model="llamafile/gemma-3-3b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:8080/v1",
)

# Access cost information
print(f"Tokens used: {response.usage.total_tokens}")
```

### Custom Cost Tracking

```python
import litellm
from typing import Dict, Any

def track_usage(kwargs: Dict[str, Any], response: Any, start_time: float, end_time: float):
    """Custom usage tracking callback."""
    print(f"Model: {kwargs['model']}")
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"Duration: {end_time - start_time:.2f}s")

# Register callback
litellm.success_callback = [track_usage]
```

## Port Configuration Reference

| Service | Default Port | Endpoint |
|---------|--------------|----------|
| Llamafile | 8080 | `http://localhost:8080/v1` |
| Ollama | 11434 | `http://localhost:11434` |
| LocalAI | 8080 | `http://localhost:8080/v1` |
| vLLM | 8000 | `http://localhost:8000/v1` |
| LM Studio | 1234 | `http://localhost:1234/v1` |

## Security Considerations

### Local Development

```python
# ✅ Safe for local development
api_base = "http://localhost:8080/v1"
```

### Production Deployment

```python
# Use HTTPS for production
api_base = os.getenv("LLAMAFILE_API_BASE", "https://llm-server.internal/v1")

# Validate environment variables
assert api_base.startswith("https://"), "Production must use HTTPS"
```

### API Key Management

```python
import os
from pathlib import Path

# Never hardcode API keys
# ❌ Wrong
api_key = "sk-1234567890abcdef"

# ✅ Correct - use environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")

# Or load from secure credential store
# ✅ Correct - use dotenv
from dotenv import load_dotenv
load_dotenv(Path.home() / ".config" / "myapp" / ".env")
api_key = os.getenv("OPENAI_API_KEY")
```

## References

- [LiteLLM Configuration](https://docs.litellm.ai/docs/set_keys) - Official configuration guide
- [Proxy Server Setup](https://docs.litellm.ai/docs/proxy/quick_start) - Proxy deployment guide
- [Logging and Debugging](https://docs.litellm.ai/docs/debugging) - Debug configuration
- [Cost Tracking](https://docs.litellm.ai/docs/completion/cost_tracking) - Usage tracking guide
