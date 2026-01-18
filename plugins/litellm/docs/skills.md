# Skills Reference

The litellm plugin provides one comprehensive skill for unified LLM API integration across 100+ providers with special focus on llamafile integration.

## litellm

**Location**: `skills/litellm/SKILL.md`

**Description**: When calling LLM APIs from Python code. When connecting to llamafile or local LLM servers. When switching between OpenAI/Anthropic/local providers. When implementing retry/fallback logic for LLM calls. When code imports litellm or uses completion() patterns.

**User Invocable**: Yes

**Allowed Tools**: All (default)

**Model**: Inherits from current model

### When to Use

Use this skill when:

- Integrating with multiple LLM providers through a single interface
- Routing requests to local llamafile servers using OpenAI-compatible endpoints
- Implementing retry and fallback logic for LLM calls
- Building applications requiring consistent error handling across providers
- Tracking LLM usage costs across different providers
- Converting between provider-specific APIs and OpenAI format
- Deploying LLM proxy servers with unified configuration
- Testing applications against both cloud and local LLM endpoints

### Activation

This skill activates automatically when Claude detects:

- Python code importing `litellm`
- Usage of `completion()` or `acompletion()` patterns
- Mentions of llamafile integration
- Questions about LLM API providers
- Exception handling for LLM calls
- Retry/fallback logic implementation

Manual activation:

```
@litellm
or
Skill(command: "litellm")
```

### Core Capabilities

#### Provider Support

LiteLLM provides unified access to 100+ LLM providers:

- **Cloud Providers**: OpenAI, Anthropic, Google Gemini, Azure OpenAI, AWS Bedrock
- **Local Servers**: llamafile, Ollama, LocalAI, vLLM, LM Studio
- **Unified Format**: All requests use OpenAI message format
- **Exception Mapping**: All provider errors map to OpenAI exception types

#### Llamafile Integration

Special support for llamafile servers with OpenAI-compatible endpoints:

**Model Naming Convention**:
```python
model = "llamafile/mistralai/mistral-7b-instruct-v0.2"
model = "llamafile/gemma-3-3b"
```

**API Base Configuration**:
```python
api_base = "http://localhost:8080/v1"
```

**Critical Requirements**:
- MUST include `llamafile/` prefix for model names
- MUST include `/v1` suffix in `api_base`
- Do NOT add endpoint paths like `/chat/completions` (LiteLLM handles routing)
- Default llamafile port is 8080

#### Exception Handling

All exceptions inherit from OpenAI exception types for compatibility:

| Status Code | Exception Type | Inherits from | Use Case |
|-------------|----------------|---------------|----------|
| 400 | `BadRequestError` | `openai.BadRequestError` | Invalid request parameters |
| 400 | `ContextWindowExceededError` | `litellm.BadRequestError` | Token limit exceeded |
| 401 | `AuthenticationError` | `openai.AuthenticationError` | API key issues |
| 404 | `NotFoundError` | `openai.NotFoundError` | Invalid model/endpoint |
| 408 | `Timeout` | `openai.APITimeoutError` | Request timeout |
| 429 | `RateLimitError` | `openai.RateLimitError` | Rate limiting |
| 500 | `APIConnectionError` | `openai.APIConnectionError` | Connection failures |
| 503 | `ServiceUnavailableError` | `openai.APIStatusError` | Service down |

**Exception Attributes**:
- `status_code`: HTTP status code
- `message`: Error description
- `llm_provider`: Provider that raised the exception

#### Retry and Fallback

Built-in retry logic with configurable attempts:

```python
response = litellm.completion(
    model="llamafile/gemma-3-3b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:8080/v1",
    num_retries=3,      # Retry 3 times on failure
    timeout=30.0,       # 30 second timeout per attempt
)
```

#### Streaming Support

Both synchronous and asynchronous streaming:

```python
# Async streaming
from litellm import acompletion

response = await acompletion(
    model="llamafile/gemma-3-3b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:8080/v1",
    stream=True,
)

async for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Common Patterns

#### Connection Verification

```python
import litellm
from litellm import APIConnectionError

def verify_llamafile_connection(api_base: str = "http://localhost:8080/v1") -> bool:
    """Check if llamafile server is running."""
    try:
        litellm.completion(
            model="llamafile/test",
            messages=[{"role": "user", "content": "test"}],
            api_base=api_base,
            max_tokens=1,
        )
        return True
    except APIConnectionError:
        return False
```

#### Async Service Class

```python
from litellm import acompletion, APIConnectionError
import asyncio

class AIService:
    """LiteLLM wrapper with llamafile routing."""

    def __init__(self, model: str, api_base: str, temperature: float = 0.3):
        self.model = model
        self.api_base = api_base
        self.temperature = temperature

    async def generate_response(self, system_prompt: str, user_input: str) -> str:
        """Generate response using LLM."""
        try:
            response = await acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                api_base=self.api_base,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except APIConnectionError as e:
            raise RuntimeError(f"Failed to connect: {e.message}")
```

### Common Pitfalls

1. **Missing `llamafile/` prefix** - Without prefix, LiteLLM won't route to correct provider
2. **Wrong port** - Llamafile uses 8080 by default, not 8000
3. **Missing `/v1` suffix** - API base must end with `/v1`
4. **Adding extra paths** - Do NOT use `http://localhost:8080/v1/chat/completions`
5. **API key requirement** - No API key needed for local llamafile

### Related Skills

- **llamafile** - `Skill(command: "llamafile")` for server setup and management
- **uv** - `Skill(command: "uv")` for Python dependency management

### References

- [LiteLLM Documentation](https://docs.litellm.ai/) - Main documentation portal
- [Llamafile Provider Docs](https://docs.litellm.ai/docs/providers/llamafile) - Provider-specific guide
- [Exception Mapping](https://docs.litellm.ai/docs/exception_mapping) - Complete exception reference
- [GitHub Repository](https://github.com/BerriAI/litellm) - Source code and examples
- [Completion Streaming](https://docs.litellm.ai/docs/completion/stream) - Streaming guide

**Documentation Version**: Verified against LiteLLM main branch (accessed 2025-01-15)
