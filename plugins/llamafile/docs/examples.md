# Usage Examples

Concrete examples for integrating llamafile into applications and workflows.

## Example 1: Basic Server Setup and Testing

**Scenario**: You want to set up a local LLM server for development and verify it works correctly.

**Steps**:

1. Download and prepare llamafile binary and model
2. Start the server in the background
3. Test the API with curl
4. Verify health endpoint

**Code**:

```bash
# Download llamafile binary
curl -L -o llamafile https://github.com/mozilla-ai/llamafile/releases/download/0.9.3/llamafile-0.9.3
chmod 755 llamafile

# Download a small model for testing
curl -L -o qwen-0.6b.gguf \
  https://huggingface.co/Mozilla/Qwen3-0.6B-gguf/resolve/main/Qwen3-0.6B-Q4_K_M.gguf

# Start server
./llamafile --server \
    -m qwen-0.6b.gguf \
    --nobrowser \
    --port 8080 \
    --host 127.0.0.1 &

# Wait for server to start
sleep 10

# Test health endpoint
curl http://localhost:8080/health

# Test chat completions
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local",
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ],
    "temperature": 0.3,
    "max_tokens": 50
  }'
```

**Result**: Local LLM server running and responding to API requests at http://localhost:8080/v1

---

## Example 2: LiteLLM Integration with Fallback

**Scenario**: Use llamafile as primary LLM with automatic fallback to cloud provider if local server is unavailable.

**Steps**:

1. Configure LiteLLM with llamafile as primary model
2. Set up cloud provider as fallback
3. Implement connection retry logic
4. Handle API errors gracefully

**Code**:

```python
import litellm
from litellm import completion
from litellm.exceptions import APIError, ServiceUnavailableError
import time

def get_completion(prompt: str, use_local: bool = True) -> str:
    """Get LLM completion with automatic fallback."""

    if use_local:
        try:
            response = completion(
                model="llamafile/gemma-3-3b",
                messages=[{"role": "user", "content": prompt}],
                api_base="http://localhost:8080/v1",
                temperature=0.3,
                max_tokens=500,
                timeout=30
            )
            return response.choices[0].message.content

        except (APIError, ServiceUnavailableError, TimeoutError) as e:
            print(f"Local LLM unavailable: {e}")
            print("Falling back to cloud provider...")
            # Fall through to cloud provider

    # Cloud provider fallback
    response = completion(
        model="gpt-4o-mini",  # Or claude-3-haiku-20240307
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    return response.choices[0].message.content


# Usage
if __name__ == "__main__":
    prompt = "Explain the difference between lists and tuples in Python"

    # Try local first
    result = get_completion(prompt, use_local=True)
    print(result)
```

**Result**: Seamless LLM access with cost-effective local inference and reliable cloud fallback.

---

## Example 3: OpenAI SDK with Llamafile for Commit Messages

**Scenario**: Create a commit message generator tool using llamafile and OpenAI SDK.

**Steps**:

1. Read git diff output
2. Send to llamafile via OpenAI SDK
3. Format as conventional commit message
4. Validate output

**Code**:

```python
#!/usr/bin/env python3
"""Generate commit messages using local LLM."""

import subprocess
import sys
from openai import OpenAI

def get_git_diff() -> str:
    """Get staged changes from git."""
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout


def generate_commit_message(diff: str) -> str:
    """Generate commit message from diff using llamafile."""
    client = OpenAI(
        base_url="http://localhost:8080/v1",
        api_key="sk-no-key-required"
    )

    prompt = f"""Generate a conventional commit message for this diff.
Format: <type>: <description>

Types: feat, fix, docs, style, refactor, test, chore

Keep under 50 characters. Use imperative mood.

Diff:
{diff}

Commit message:"""

    response = client.chat.completions.create(
        model="local",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )

    return response.choices[0].message.content.strip()


def main():
    """Main entry point."""
    try:
        diff = get_git_diff()
        if not diff:
            print("No staged changes found")
            sys.exit(1)

        message = generate_commit_message(diff)
        print(f"Suggested commit message:\n{message}")

        # Optionally: git commit -m "$message"

    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Usage**:

```bash
# Stage changes
git add src/utils.py

# Generate commit message
./generate_commit.py
# Output: feat: add caching to API requests
```

**Result**: AI-powered commit messages using local LLM, no cloud API required.

---

## Example 4: Background Process Management

**Scenario**: Integrate llamafile as a managed background service for an application.

**Steps**:

1. Create process manager class
2. Implement health checking with retry logic
3. Handle graceful shutdown
4. Log server output

**Code**:

```python
import subprocess
import time
import signal
import httpx
from pathlib import Path
from typing import Optional

class LlamafileServer:
    """Manage llamafile server lifecycle."""

    def __init__(
        self,
        llamafile_path: Path,
        model_path: Path,
        port: int = 8080,
        host: str = "127.0.0.1"
    ):
        self.llamafile_path = llamafile_path
        self.model_path = model_path
        self.port = port
        self.host = host
        self.process: Optional[subprocess.Popen] = None
        self.base_url = f"http://{host}:{port}"

    def start(self, timeout: int = 60) -> None:
        """Start llamafile server."""
        if self.is_running():
            print("Server already running")
            return

        cmd = [
            str(self.llamafile_path),
            "--server",
            "-m", str(self.model_path),
            "--nobrowser",
            "--port", str(self.port),
            "--host", self.host,
            "--ctx-size", "4096",
            "--threads", "8",
        ]

        print(f"Starting llamafile server on {self.base_url}")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self._wait_for_ready(timeout)
        print("Server ready")

    def _wait_for_ready(self, timeout: int) -> None:
        """Wait for server to respond to health checks."""
        url = f"{self.base_url}/health"
        start = time.time()

        while time.time() - start < timeout:
            if self.process and self.process.poll() is not None:
                raise RuntimeError("Server process terminated unexpectedly")

            try:
                response = httpx.get(url, timeout=2)
                if response.status_code == 200:
                    return
            except httpx.RequestError:
                pass

            time.sleep(1)

        raise TimeoutError(f"Server did not start within {timeout} seconds")

    def is_running(self) -> bool:
        """Check if server is running and responsive."""
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def stop(self) -> None:
        """Stop llamafile server gracefully."""
        if not self.process:
            return

        print("Stopping llamafile server...")
        self.process.send_signal(signal.SIGTERM)

        try:
            self.process.wait(timeout=10)
            print("Server stopped")
        except subprocess.TimeoutExpired:
            print("Forcing server shutdown...")
            self.process.kill()
            self.process.wait()

        self.process = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Usage
if __name__ == "__main__":
    llamafile = Path("./llamafile")
    model = Path("./gemma-3-3b.gguf")

    with LlamafileServer(llamafile, model) as server:
        print(f"Server running at {server.base_url}")

        # Use the server
        import litellm
        response = litellm.completion(
            model="llamafile/gemma-3-3b",
            messages=[{"role": "user", "content": "Hello!"}],
            api_base=f"{server.base_url}/v1"
        )
        print(response.choices[0].message.content)

    # Server automatically stopped when exiting context
```

**Result**: Reliable server lifecycle management with automatic startup, health checking, and graceful shutdown.

---

## Example 5: Configuration-Driven Application

**Scenario**: Build an application that reads llamafile configuration from a file and manages server lifecycle.

**Steps**:

1. Define configuration schema
2. Load settings from TOML file
3. Initialize llamafile server based on config
4. Use configuration for API calls

**Code**:

Configuration file (`~/.config/myapp/config.toml`):

```toml
[ai]
model = "llamafile/gemma-3-3b"
temperature = 0.3
max_tokens = 500

[llamafile]
binary_path = "/home/user/.local/bin/llamafile"
model_path = "/home/user/.local/share/myapp/models/gemma-3-3b.gguf"
port = 8080
host = "127.0.0.1"
api_base = "http://127.0.0.1:8080/v1"

[llamafile.server_args]
ctx_size = 4096
n_gpu_layers = 99
threads = 8
cont_batching = true
parallel = 4
```

Application code:

```python
#!/usr/bin/env python3
"""Application using configuration-driven llamafile."""

import tomli
import litellm
from pathlib import Path
from typing import Any

def load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from TOML file."""
    with open(config_path, "rb") as f:
        return tomli.load(f)


def start_llamafile_from_config(config: dict[str, Any]) -> None:
    """Start llamafile server using configuration."""
    import subprocess

    lf_config = config["llamafile"]
    server_args = lf_config.get("server_args", {})

    cmd = [
        lf_config["binary_path"],
        "--server",
        "-m", lf_config["model_path"],
        "--nobrowser",
        "--port", str(lf_config["port"]),
        "--host", lf_config["host"],
    ]

    # Add optional server arguments
    if "ctx_size" in server_args:
        cmd.extend(["--ctx-size", str(server_args["ctx_size"])])
    if "n_gpu_layers" in server_args:
        cmd.extend(["--n-gpu-layers", str(server_args["n_gpu_layers"])])
    if "threads" in server_args:
        cmd.extend(["--threads", str(server_args["threads"])])
    if server_args.get("cont_batching"):
        cmd.append("--cont-batching")
    if "parallel" in server_args:
        cmd.extend(["--parallel", str(server_args["parallel"])])

    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_completion(prompt: str, config: dict[str, Any]) -> str:
    """Get completion using configuration."""
    ai_config = config["ai"]
    lf_config = config["llamafile"]

    response = litellm.completion(
        model=ai_config["model"],
        messages=[{"role": "user", "content": prompt}],
        api_base=lf_config["api_base"],
        temperature=ai_config["temperature"],
        max_tokens=ai_config["max_tokens"]
    )

    return response.choices[0].message.content


def main():
    """Main entry point."""
    # Load configuration
    config_path = Path.home() / ".config" / "myapp" / "config.toml"
    config = load_config(config_path)

    # Start server (if not running)
    # In production, check if server is already running first
    import time
    start_llamafile_from_config(config)
    time.sleep(10)  # Wait for startup

    # Use the configured LLM
    result = get_completion("Explain Python decorators", config)
    print(result)


if __name__ == "__main__":
    main()
```

**Result**: Flexible, configuration-driven application that adapts to different environments and user preferences.

---

## Example 6: GPU-Accelerated Server for High Throughput

**Scenario**: Configure llamafile for maximum performance with GPU acceleration and concurrent request handling.

**Steps**:

1. Verify GPU availability
2. Start server with GPU offloading
3. Enable continuous batching for concurrency
4. Test with parallel requests

**Code**:

```bash
# Check GPU availability
nvidia-smi  # For NVIDIA GPUs
# or
rocm-smi   # For AMD GPUs

# Start high-performance server
./llamafile --server \
    -m ./mistral-7b.gguf \
    --nobrowser \
    --port 8080 \
    --host 127.0.0.1 \
    --ctx-size 8192 \
    --n-gpu-layers 99 \
    --threads 16 \
    --threads-batch 16 \
    --cont-batching \
    --parallel 8 \
    --mlock
```

Test parallel requests:

```python
#!/usr/bin/env python3
"""Test concurrent requests to llamafile."""

import asyncio
import httpx
import time

async def make_request(client: httpx.AsyncClient, prompt: str) -> str:
    """Make async API request."""
    response = await client.post(
        "http://localhost:8080/v1/chat/completions",
        json={
            "model": "local",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200
        },
        timeout=60.0
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]


async def test_concurrent_requests(n_requests: int = 10):
    """Test concurrent request handling."""
    async with httpx.AsyncClient() as client:
        prompts = [f"Count from 1 to {i}" for i in range(1, n_requests + 1)]

        start = time.time()
        results = await asyncio.gather(
            *[make_request(client, prompt) for prompt in prompts]
        )
        elapsed = time.time() - start

        print(f"Completed {n_requests} requests in {elapsed:.2f} seconds")
        print(f"Average: {elapsed/n_requests:.2f} seconds per request")

        for i, result in enumerate(results, 1):
            print(f"\nRequest {i}: {result[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_concurrent_requests(10))
```

**Result**: High-throughput local LLM server capable of handling multiple concurrent requests efficiently.

---

## Example 7: Embeddings Generation

**Scenario**: Use llamafile to generate embeddings for semantic search or similarity comparisons.

**Steps**:

1. Start server with embeddings enabled
2. Generate embeddings via API
3. Compare embeddings with cosine similarity

**Code**:

```bash
# Start server with embeddings support
./llamafile --server \
    -m ./gemma-3-3b.gguf \
    --nobrowser \
    --port 8080 \
    --host 127.0.0.1 \
    --embedding
```

Generate and compare embeddings:

```python
#!/usr/bin/env python3
"""Generate and compare embeddings using llamafile."""

import httpx
import numpy as np
from typing import List

def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text."""
    response = httpx.post(
        "http://localhost:8080/v1/embeddings",
        json={"model": "local", "input": [text]},
        timeout=30
    )
    data = response.json()
    return data["data"][0]["embedding"]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr))


# Example usage
texts = [
    "The cat sat on the mat",
    "A feline rested on the rug",
    "The weather is sunny today",
]

embeddings = [get_embedding(text) for text in texts]

# Compare similarity
sim_01 = cosine_similarity(embeddings[0], embeddings[1])
sim_02 = cosine_similarity(embeddings[0], embeddings[2])

print(f"Similarity between text 0 and 1: {sim_01:.3f}")  # High (similar meaning)
print(f"Similarity between text 0 and 2: {sim_02:.3f}")  # Low (different topics)
```

**Result**: Local embeddings generation for semantic search, clustering, and similarity tasks.

---

## Common Patterns

### Pattern: Check Server Before Starting

```python
import httpx

def is_llamafile_running(port: int = 8080) -> bool:
    """Check if llamafile server is already running."""
    try:
        response = httpx.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except httpx.RequestError:
        return False

# Usage
if not is_llamafile_running():
    # Start server
    pass
else:
    print("Server already running")
```

### Pattern: Retry with Exponential Backoff

```python
import time
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Any:
    """Retry function with exponential backoff."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2

# Usage with llamafile API
result = retry_with_backoff(
    lambda: litellm.completion(
        model="llamafile/gemma-3-3b",
        messages=[{"role": "user", "content": "Hello"}],
        api_base="http://localhost:8080/v1"
    )
)
```

### Pattern: Environment-Based Configuration

```python
import os

def get_llamafile_config():
    """Get llamafile configuration from environment."""
    return {
        "api_base": os.getenv("LLAMAFILE_API_BASE", "http://localhost:8080/v1"),
        "model": os.getenv("LLAMAFILE_MODEL", "llamafile/gemma-3-3b"),
        "temperature": float(os.getenv("LLAMAFILE_TEMPERATURE", "0.3")),
        "max_tokens": int(os.getenv("LLAMAFILE_MAX_TOKENS", "500")),
    }

# Usage
config = get_llamafile_config()
response = litellm.completion(
    model=config["model"],
    api_base=config["api_base"],
    messages=[{"role": "user", "content": "Hello"}],
    temperature=config["temperature"],
    max_tokens=config["max_tokens"]
)
```
