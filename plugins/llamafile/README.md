# Llamafile Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Run LLMs locally with Mozilla Llamafile - a cross-platform executable that provides OpenAI-compatible APIs for GGUF models without requiring cloud services.

## Features

- **Local LLM Inference** - Run language models entirely offline without cloud API dependencies
- **OpenAI-Compatible API** - Drop-in replacement for OpenAI API using local models
- **Cross-Platform** - Single executable works on macOS, Windows, Linux, and BSD systems
- **GPU Acceleration** - Support for CUDA, Metal, and Vulkan for faster inference
- **Zero Configuration** - Simple command-line interface with sensible defaults
- **Model Management** - Guidance for selecting and downloading GGUF models from Hugging Face
- **Integration Examples** - Ready-to-use code for LiteLLM, OpenAI SDK, and direct HTTP access

## Installation

### Prerequisites

- **Operating System**: macOS, Windows, Linux, FreeBSD, OpenBSD, NetBSD
- **Architecture**: AMD64 or ARM64
- **Disk Space**: 500MB - 5GB depending on model size
- **RAM**: 4GB minimum, 8GB+ recommended
- **Optional**: CUDA, Metal, or Vulkan for GPU acceleration

### Install Plugin

```bash
# Method 1: Using cc plugin install (if published to marketplace)
cc plugin install llamafile

# Method 2: Manual installation
git clone https://github.com/your-org/llamafile-plugin ~/.claude/plugins/llamafile
cc plugin reload
```

### Download Llamafile Binary

```bash
# Download llamafile v0.9.3
curl -L -o llamafile https://github.com/mozilla-ai/llamafile/releases/download/0.9.3/llamafile-0.9.3
chmod 755 llamafile
```

### Download GGUF Model

```bash
# Recommended: Gemma 3 3B (balanced speed/quality, ~2GB)
curl -L -o gemma-3-3b.gguf \
  https://huggingface.co/Mozilla/gemma-3-3b-it-gguf/resolve/main/gemma-3-3b-it-Q4_K_M.gguf
```

## Quick Start

Start a local LLM server and make an API call:

```bash
# Start llamafile server
./llamafile --server -m gemma-3-3b.gguf --nobrowser --port 8080 --host 127.0.0.1

# Test with curl (in another terminal)
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local",
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "temperature": 0.3,
    "max_tokens": 200
  }'
```

## Capabilities

| Type  | Name       | Description                                       | Invocation                       |
| ----- | ---------- | ------------------------------------------------- | -------------------------------- |
| Skill | llamafile  | Configure and manage Mozilla Llamafile for local LLM inference | `@llamafile` or automatic |

## Usage

### Skill: llamafile

The llamafile skill provides comprehensive guidance for:

- **Installation**: Download llamafile binary and GGUF models
- **Server Configuration**: Start llamafile with optimal performance settings
- **API Integration**: Use LiteLLM, OpenAI SDK, or direct HTTP requests
- **Server Management**: Process management and health checking
- **Troubleshooting**: Common issues and performance optimization

**When to Use**: The skill activates automatically when you mention:
- Setting up local LLM inference without cloud APIs
- Running GGUF models locally
- Building offline/air-gapped AI tools
- Troubleshooting local LLM server connections

**Manual Activation**:

```
@llamafile
```

or

```
Skill(command: "llamafile")
```

## Configuration

This plugin does not require additional configuration. All llamafile server settings are managed via command-line flags.

### Recommended Server Configuration

```bash
# Basic server (localhost only)
./llamafile --server \
    -m /path/to/model.gguf \
    --nobrowser \
    --port 8080 \
    --host 127.0.0.1

# Performance-optimized (GPU acceleration)
./llamafile --server \
    -m /path/to/model.gguf \
    --nobrowser \
    --port 8080 \
    --host 127.0.0.1 \
    --ctx-size 4096 \
    --n-gpu-layers 99 \
    --threads 8 \
    --cont-batching \
    --parallel 4
```

## Examples

### Example 1: Using LiteLLM with Llamafile

**Scenario**: Integrate llamafile with LiteLLM for unified LLM provider interface.

```python
import litellm

response = litellm.completion(
    model="llamafile/gemma-3-3b",  # MUST use llamafile/ prefix
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    api_base="http://localhost:8080/v1",  # MUST include /v1 suffix
    temperature=0.3,
    max_tokens=200
)

print(response.choices[0].message.content)
```

**Key Points**:
- Model name requires `llamafile/` prefix
- API base URL must include `/v1` suffix
- No API key required (any placeholder works)

### Example 2: Using OpenAI SDK

**Scenario**: Use OpenAI Python SDK with llamafile for local inference.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",  # Include /v1
    api_key="sk-no-key-required"  # Any value works
)

response = client.chat.completions.create(
    model="local-model",
    messages=[{"role": "user", "content": "Write a haiku about coding"}],
    temperature=0.7,
    max_tokens=100
)

print(response.choices[0].message.content)
```

### Example 3: Background Server Management

**Scenario**: Start llamafile as a background process with health checking.

```python
import subprocess
import time
import httpx

def start_llamafile(llamafile_path: str, model_path: str) -> subprocess.Popen:
    """Start llamafile server as background process."""
    cmd = [
        llamafile_path, "--server",
        "-m", model_path,
        "--nobrowser",
        "--port", "8080",
        "--host", "127.0.0.1"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to be ready
    url = "http://127.0.0.1:8080/health"
    for _ in range(60):
        try:
            response = httpx.get(url, timeout=2)
            if response.status_code == 200:
                return process
        except httpx.RequestError:
            time.sleep(0.5)

    raise TimeoutError("Server did not start within 30 seconds")

# Usage
process = start_llamafile("./llamafile", "./gemma-3-3b.gguf")
```

See [examples documentation](./docs/examples.md) for more use cases.

## Troubleshooting

### Server Won't Start

**Check port availability:**

```bash
lsof -i :8080
kill $(lsof -t -i :8080)  # If port is in use
```

**Verify binary permissions:**

```bash
chmod 755 ./llamafile
```

### Connection Refused

**Common causes:**
1. Server not started with `--server` flag
2. Wrong port (8080 vs 8000)
3. Missing `/v1` in API URL
4. Server bound to 127.0.0.1 but accessing from another machine

**Test connectivity:**

```bash
curl http://localhost:8080/health
```

### API Errors

| Error              | Cause                | Solution                          |
| ------------------ | -------------------- | --------------------------------- |
| 404 Not Found      | Missing `/v1` in URL | Add `/v1` before endpoint path    |
| Connection refused | Server not running   | Start server with `--server` flag |
| Timeout            | Model loading slowly | Wait longer or use smaller model  |
| Invalid model      | Wrong model path     | Verify `-m` path to GGUF file     |

### Performance Issues

**Optimize inference speed:**
1. Use quantized models (Q4_K_M recommended)
2. Enable GPU acceleration: `--n-gpu-layers 99`
3. Increase threads: `--threads 8`
4. Enable continuous batching: `--cont-batching`
5. Reduce context size: `--ctx-size 2048`

## Recommended Models

| Model        | Size  | Use Case                | Download                                                      |
| ------------ | ----- | ----------------------- | ------------------------------------------------------------- |
| Gemma 3 3B   | ~2GB  | Balanced speed/quality  | [Mozilla/gemma-3-3b-it-gguf](https://huggingface.co/Mozilla/gemma-3-3b-it-gguf) |
| Qwen3-0.6B   | ~500MB | Fast, lower quality    | [Mozilla/Qwen3-0.6B-gguf](https://huggingface.co/Mozilla/Qwen3-0.6B-gguf)      |
| Mistral 7B   | ~4GB  | Higher quality, slower  | [Mozilla/Mistral-7B-gguf](https://huggingface.co/Mozilla/Mistral-7B-gguf)      |
| Llama 3.1 8B | ~5GB  | Best quality, slowest   | [Mozilla/Llama-3.1-8B-gguf](https://huggingface.co/Mozilla/Llama-3.1-8B-gguf)  |

## Related Resources

**Skills:**
- `litellm` - Unified interface for multiple LLM providers including llamafile

**External Tools:**
- [LiteLLM](https://docs.litellm.ai/) - Unified LLM provider interface
- [OpenAI Python SDK](https://github.com/openai/openai-python) - Official OpenAI client
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Underlying inference engine

**Documentation:**
- [Mozilla llamafile GitHub](https://github.com/mozilla-ai/llamafile)
- [Mozilla llamafile Documentation](https://mozilla-ai.github.io/llamafile/)
- [LiteLLM llamafile Provider](https://docs.litellm.ai/docs/providers/llamafile)

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `cc plugin validate .`
5. Submit a pull request

## License

This plugin documentation is provided as-is. Llamafile itself is licensed under Apache 2.0 by Mozilla.

## Credits

**Plugin Author**: Claude Code Skills Repository Contributors

**Llamafile**: Mozilla AI - [github.com/mozilla-ai/llamafile](https://github.com/mozilla-ai/llamafile)

**References**:
- [Mozilla llamafile Documentation](https://mozilla-ai.github.io/llamafile/)
- [LiteLLM llamafile Provider Guide](https://docs.litellm.ai/docs/providers/llamafile)
- [llama.cpp Server Documentation](https://github.com/ggml-org/llama.cpp/tree/master/examples/server)
