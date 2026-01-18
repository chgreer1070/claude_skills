# Usage Examples

Concrete, real-world examples of using LiteLLM with llamafile and other providers.

## Example 1: Git Commit Message Generator

**Scenario**: Create a CLI tool that generates conventional commit messages from git diffs using a local llamafile server.

**Steps**:
1. Get staged git diff
2. Send to llamafile via LiteLLM
3. Parse and validate commit message format
4. Offer to create commit

**Code**:

```python
#!/usr/bin/env python3
"""Generate commit messages using local LLM via LiteLLM."""

import subprocess
import sys
from litellm import completion, APIConnectionError

def get_staged_diff() -> str:
    """Get diff of staged changes."""
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

def generate_commit_message(diff: str) -> str:
    """Generate commit message from diff using LiteLLM."""
    system_prompt = """Generate a concise conventional commit message.
Format: <type>: <description>
Types: feat, fix, docs, style, refactor, test, chore
Keep under 50 characters."""

    try:
        response = completion(
            model="llamafile/gemma-3-3b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate commit message:\n\n{diff}"},
            ],
            api_base="http://localhost:8080/v1",
            temperature=0.3,
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except APIConnectionError as e:
        print(f"Error: Cannot connect to llamafile at http://localhost:8080", file=sys.stderr)
        print("Make sure llamafile server is running", file=sys.stderr)
        sys.exit(1)

def main():
    diff = get_staged_diff()
    if not diff:
        print("No staged changes found")
        sys.exit(1)

    print("Generating commit message...")
    message = generate_commit_message(diff)
    print(f"\nSuggested message: {message}")

    if input("\nCreate commit? [y/N]: ").lower() == "y":
        subprocess.run(["git", "commit", "-m", message], check=True)
        print("Commit created!")

if __name__ == "__main__":
    main()
```

**Result**: Users can generate and create commits with `./commit-gen.py`, saving time on message formatting.

---

## Example 2: Code Review Assistant

**Scenario**: Review pull request changes and provide feedback using streaming for real-time output.

**Steps**:
1. Fetch PR diff from GitHub
2. Stream review feedback from LLM
3. Display suggestions as they're generated

**Code**:

```python
#!/usr/bin/env python3
"""Stream code review feedback from local LLM."""

import asyncio
import sys
from litellm import acompletion, APIConnectionError

async def stream_code_review(code_diff: str):
    """Stream code review feedback."""
    system_prompt = """You are a code reviewer. Analyze changes and provide:
1. Potential bugs
2. Security concerns
3. Performance issues
4. Style improvements
Be concise and actionable."""

    print("Code Review:\n" + "=" * 60)

    try:
        response = await acompletion(
            model="llamafile/mistralai/mistral-7b-instruct-v0.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review this code:\n\n{code_diff}"},
            ],
            api_base="http://localhost:8080/v1",
            temperature=0.2,
            max_tokens=500,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)

        print("\n" + "=" * 60)

    except APIConnectionError as e:
        print(f"\nError: {e.message}", file=sys.stderr)
        print(f"Provider: {e.llm_provider}", file=sys.stderr)
        sys.exit(1)

async def main():
    if len(sys.argv) != 2:
        print("Usage: review.py <file>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        code_diff = f.read()

    await stream_code_review(code_diff)

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: Real-time streaming code review feedback visible as the LLM generates it.

---

## Example 3: Multi-Provider Fallback

**Scenario**: Try local llamafile first, fall back to OpenAI if unavailable or slow.

**Steps**:
1. Attempt completion with llamafile
2. Catch timeout or connection errors
3. Fall back to OpenAI API
4. Track which provider was used

**Code**:

```python
#!/usr/bin/env python3
"""Multi-provider completion with fallback logic."""

import os
from typing import Tuple
from litellm import completion, APIConnectionError, Timeout

def generate_with_fallback(prompt: str) -> Tuple[str, str]:
    """Try llamafile first, fall back to OpenAI."""

    # Try local llamafile
    try:
        print("Attempting local llamafile...")
        response = completion(
            model="llamafile/gemma-3-3b",
            messages=[{"role": "user", "content": prompt}],
            api_base="http://localhost:8080/v1",
            timeout=10.0,  # Short timeout for local
        )
        return response.choices[0].message.content, "llamafile"

    except (APIConnectionError, Timeout) as e:
        print(f"Local failed: {e.message}")
        print("Falling back to OpenAI...")

        # Fall back to OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set for fallback")

        response = completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0,
        )
        return response.choices[0].message.content, "openai"

def main():
    prompt = "Explain quantum computing in one sentence"
    result, provider = generate_with_fallback(prompt)

    print(f"\nProvider used: {provider}")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

**Result**: Seamless fallback to cloud provider when local server is unavailable.

---

## Example 4: Batch Processing with Retry

**Scenario**: Process multiple documents with retry logic for transient failures.

**Steps**:
1. Load documents to process
2. Process each with LiteLLM
3. Retry failed requests
4. Track success/failure metrics

**Code**:

```python
#!/usr/bin/env python3
"""Batch document processing with retry logic."""

import asyncio
from typing import List, Dict
from litellm import acompletion, APIConnectionError, RateLimitError

async def summarize_document(doc: str, doc_id: int) -> Dict:
    """Summarize a single document with retry."""

    for attempt in range(3):
        try:
            response = await acompletion(
                model="llamafile/gemma-3-3b",
                messages=[
                    {"role": "system", "content": "Summarize in 2-3 sentences."},
                    {"role": "user", "content": doc},
                ],
                api_base="http://localhost:8080/v1",
                temperature=0.3,
                max_tokens=150,
                num_retries=2,  # Built-in retry
            )

            return {
                "doc_id": doc_id,
                "status": "success",
                "summary": response.choices[0].message.content.strip(),
                "attempts": attempt + 1,
            }

        except RateLimitError:
            if attempt < 2:
                wait_time = 2 ** attempt
                print(f"Rate limited on doc {doc_id}, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            raise

        except APIConnectionError as e:
            print(f"Failed doc {doc_id} attempt {attempt + 1}: {e.message}")
            if attempt < 2:
                await asyncio.sleep(1)
                continue

            return {
                "doc_id": doc_id,
                "status": "failed",
                "error": str(e),
                "attempts": attempt + 1,
            }

async def batch_summarize(documents: List[str]) -> List[Dict]:
    """Process documents concurrently with rate limiting."""
    # Process in batches of 5 to avoid overwhelming server
    batch_size = 5
    results = []

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        tasks = [
            summarize_document(doc, i + idx)
            for idx, doc in enumerate(batch)
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

        # Brief pause between batches
        if i + batch_size < len(documents):
            await asyncio.sleep(0.5)

    return results

async def main():
    # Sample documents
    documents = [
        "Quantum computing uses quantum mechanics to process information...",
        "Machine learning is a subset of artificial intelligence...",
        "Blockchain is a distributed ledger technology...",
        # ... more documents
    ]

    print(f"Processing {len(documents)} documents...")
    results = await batch_summarize(documents)

    # Print statistics
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful

    print(f"\nResults:")
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")

    # Show successful summaries
    for result in results:
        if result["status"] == "success":
            print(f"\nDoc {result['doc_id']} (attempts: {result['attempts']}):")
            print(f"  {result['summary']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: Robust batch processing with automatic retries and rate limiting handling.

---

## Example 5: Embeddings for Semantic Search

**Scenario**: Generate embeddings for documents and perform semantic search.

**Steps**:
1. Generate embeddings for document corpus
2. Store embeddings with metadata
3. Embed search query
4. Find most similar documents

**Code**:

```python
#!/usr/bin/env python3
"""Semantic search using LiteLLM embeddings."""

import os
import numpy as np
from typing import List, Tuple
from litellm import embedding
from numpy.linalg import norm

os.environ["LLAMAFILE_API_BASE"] = "http://localhost:8080/v1"

def get_embedding(text: str) -> np.ndarray:
    """Get embedding vector for text."""
    response = embedding(
        model="llamafile/sentence-transformers/all-MiniLM-L6-v2",
        input=[text],
    )
    return np.array(response.data[0]["embedding"])

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between vectors."""
    return np.dot(a, b) / (norm(a) * norm(b))

def build_index(documents: List[str]) -> List[Tuple[str, np.ndarray]]:
    """Build embedding index for documents."""
    print(f"Building index for {len(documents)} documents...")
    index = []

    for doc in documents:
        embedding_vec = get_embedding(doc)
        index.append((doc, embedding_vec))

    return index

def search(query: str, index: List[Tuple[str, np.ndarray]], top_k: int = 3) -> List[Tuple[str, float]]:
    """Search for most similar documents."""
    query_embedding = get_embedding(query)

    # Calculate similarities
    results = []
    for doc, doc_embedding in index:
        similarity = cosine_similarity(query_embedding, doc_embedding)
        results.append((doc, similarity))

    # Sort by similarity and return top k
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

def main():
    # Sample document corpus
    documents = [
        "Python is a high-level programming language known for readability",
        "Machine learning models can predict outcomes from data",
        "Git is a distributed version control system",
        "Docker containers provide isolated application environments",
        "SQL is used for managing relational databases",
    ]

    # Build embedding index
    index = build_index(documents)

    # Perform searches
    queries = [
        "version control",
        "artificial intelligence",
        "database queries",
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        results = search(query, index)

        for doc, similarity in results:
            print(f"  {similarity:.3f} - {doc[:60]}...")

if __name__ == "__main__":
    main()
```

**Result**: Semantic search finds conceptually similar documents even without exact keyword matches.

---

## Example 6: Context-Aware Chat Application

**Scenario**: Build a chat application that maintains conversation history and uses streaming.

**Steps**:
1. Maintain conversation history
2. Stream responses for real-time feedback
3. Handle context window limits
4. Implement stop sequences

**Code**:

```python
#!/usr/bin/env python3
"""Interactive chat application with streaming."""

import asyncio
from typing import List, Dict
from litellm import acompletion

class ChatSession:
    """Manage chat conversation with LLM."""

    def __init__(self, system_prompt: str, max_history: int = 10):
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        """Add message to history."""
        self.messages.append({"role": role, "content": content})

        # Keep only recent messages to avoid context limits
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    async def send(self, user_message: str) -> str:
        """Send message and get streaming response."""
        self.add_message("user", user_message)

        # Build message list with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.messages,
        ]

        response = await acompletion(
            model="llamafile/gemma-3-3b",
            messages=messages,
            api_base="http://localhost:8080/v1",
            temperature=0.7,
            max_tokens=300,
            stream=True,
        )

        # Collect streamed response
        full_response = []
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response.append(content)

        print()  # Newline after stream
        response_text = "".join(full_response)
        self.add_message("assistant", response_text)

        return response_text

async def main():
    chat = ChatSession(
        system_prompt="You are a helpful coding assistant. Provide concise, practical advice.",
        max_history=8,
    )

    print("Chat started. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            print("Assistant: ", end="", flush=True)
            await chat.send(user_input)
            print()

        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: Interactive chat application with streaming responses and conversation history management.

---

## Example 7: Provider Cost Comparison

**Scenario**: Compare cost and performance across different providers for the same task.

**Steps**:
1. Define task and test cases
2. Run on multiple providers
3. Track tokens, latency, and cost
4. Generate comparison report

**Code**:

```python
#!/usr/bin/env python3
"""Compare costs across LLM providers."""

import time
from typing import Dict, List
from litellm import completion

def benchmark_provider(model: str, prompt: str, **kwargs) -> Dict:
    """Benchmark a single provider."""
    start_time = time.time()

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        elapsed = time.time() - start_time
        usage = response.usage

        return {
            "model": model,
            "status": "success",
            "tokens_total": usage.total_tokens,
            "tokens_prompt": usage.prompt_tokens,
            "tokens_completion": usage.completion_tokens,
            "latency": elapsed,
            "response": response.choices[0].message.content[:100],
        }

    except Exception as e:
        return {
            "model": model,
            "status": "failed",
            "error": str(e),
        }

def main():
    prompt = "Write a Python function to calculate factorial recursively"

    # Define providers to test
    providers = [
        {
            "model": "llamafile/gemma-3-3b",
            "api_base": "http://localhost:8080/v1",
        },
        {
            "model": "gpt-4o-mini",
            # Uses OPENAI_API_KEY from environment
        },
        {
            "model": "claude-3-5-haiku-20241022",
            # Uses ANTHROPIC_API_KEY from environment
        },
    ]

    print("Running benchmarks...\n")
    results = []

    for provider in providers:
        print(f"Testing {provider['model']}...")
        result = benchmark_provider(prompt=prompt, **provider)
        results.append(result)

    # Print comparison table
    print("\n" + "=" * 80)
    print(f"{'Model':<40} {'Tokens':<10} {'Latency':<10} {'Status':<10}")
    print("=" * 80)

    for result in results:
        if result["status"] == "success":
            print(
                f"{result['model']:<40} "
                f"{result['tokens_total']:<10} "
                f"{result['latency']:.2f}s{'':<6} "
                f"{result['status']:<10}"
            )
        else:
            print(f"{result['model']:<40} {'N/A':<10} {'N/A':<10} {result['status']:<10}")

    print("=" * 80)

if __name__ == "__main__":
    main()
```

**Result**: Comparison table showing tokens, latency, and success rate across providers.

---

## Related Documentation

- [Skills Reference](./skills.md) - Detailed skill documentation
- [Configuration Reference](./configuration.md) - Environment and setup
- [README](../README.md) - Plugin overview

## References

- [LiteLLM Documentation](https://docs.litellm.ai/) - Official documentation
- [LiteLLM Examples](https://github.com/BerriAI/litellm/tree/main/cookbook) - Cookbook examples
- [Streaming Guide](https://docs.litellm.ai/docs/completion/stream) - Streaming documentation
