# Async Python Patterns

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Master Python asyncio, concurrent programming, and async/await patterns for building high-performance, non-blocking applications.

## Features

- **Comprehensive asyncio coverage** - Event loops, coroutines, tasks, futures, and async context managers
- **10+ battle-tested patterns** - From basic async/await to advanced producer-consumer implementations
- **Real-world applications** - Web scraping, database operations, WebSocket servers
- **Performance optimization** - Connection pooling, rate limiting, batch processing
- **Error handling guidance** - Timeouts, cancellation, exception management
- **Testing strategies** - pytest-asyncio integration and best practices

## Installation

### Prerequisites

- Claude Code 2.1+
- Python 3.7+ (for asyncio.run() and modern async features)

### Install Plugin

```bash
# Method 1: Using cc plugin install (if available in a marketplace)
cc plugin install async-python-patterns

# Method 2: Manual installation
git clone <repository-url> ~/.claude/plugins/async-python-patterns
cc plugin reload
```

## Quick Start

The plugin provides a comprehensive skill that Claude automatically activates when you work with async Python code.

**Example conversation:**

```
User: Help me build an async web scraper that fetches 50 URLs concurrently with rate limiting

Claude: [Automatically activates async-python-patterns skill and provides guidance on:
  - Using aiohttp for concurrent requests
  - Implementing semaphores for rate limiting
  - Error handling for failed requests
  - Connection pooling for performance]
```

**Direct skill invocation:**

```
@async-python-patterns

# or in code

Skill(command: "async-python-patterns")
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | async-python-patterns | Master asyncio and concurrent programming patterns | Auto-activated or `@async-python-patterns` |

## Usage

### When Claude Uses This Skill

Claude automatically activates this skill when you:

- Build async web APIs (FastAPI, aiohttp, Sanic)
- Implement concurrent I/O operations (database, file, network)
- Create web scrapers with concurrent requests
- Develop real-time applications (WebSocket servers, chat systems)
- Process multiple independent tasks simultaneously
- Build microservices with async communication
- Optimize I/O-bound workloads
- Implement async background tasks and queues

### What You Get

The skill provides guidance on:

1. **Core Concepts**
   - Event loop mechanics
   - Coroutines and async/await syntax
   - Task creation and management
   - Futures and callbacks
   - Async context managers and iterators

2. **Fundamental Patterns**
   - Basic async/await usage
   - Concurrent execution with gather()
   - Task creation and management
   - Error handling in async code
   - Timeout handling

3. **Advanced Patterns**
   - Async context managers
   - Async iterators and generators
   - Producer-consumer queues
   - Semaphore-based rate limiting
   - Locks and synchronization primitives

4. **Real-World Applications**
   - Web scraping with aiohttp
   - Async database operations
   - WebSocket server implementation
   - Connection pooling
   - Batch processing

5. **Best Practices**
   - Avoiding blocking operations
   - Proper error handling
   - Task cancellation
   - Performance optimization
   - Testing async code

See [Skills Reference](./docs/skills.md) for complete details.

## Examples

### Example 1: Concurrent API Requests

**Scenario**: Fetch data from multiple API endpoints concurrently

```python
import asyncio
import aiohttp
from typing import List

async def fetch_url(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch single URL."""
    async with session.get(url) as response:
        return {"url": url, "status": response.status}

async def fetch_all(urls: List[str]) -> List[dict]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Usage
urls = ["https://api.example.com/1", "https://api.example.com/2"]
results = asyncio.run(fetch_all(urls))
```

### Example 2: Rate-Limited Web Scraper

**Scenario**: Scrape 100 pages with max 5 concurrent requests

```python
import asyncio
from typing import List

async def scrape_page(url: str, semaphore: asyncio.Semaphore) -> dict:
    """Scrape single page with rate limiting."""
    async with semaphore:
        # Scraping logic here
        await asyncio.sleep(0.5)  # Simulate request
        return {"url": url, "data": "..."}

async def scrape_all(urls: List[str], max_concurrent: int = 5):
    """Scrape multiple pages with rate limiting."""
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [scrape_page(url, semaphore) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### Example 3: Producer-Consumer Queue

**Scenario**: Process items from a queue with multiple workers

```python
import asyncio
from asyncio import Queue

async def producer(queue: Queue, num_items: int):
    """Produce items."""
    for i in range(num_items):
        await queue.put(f"item-{i}")
        await asyncio.sleep(0.1)
    await queue.put(None)  # Signal completion

async def consumer(queue: Queue, worker_id: int):
    """Consume items."""
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        print(f"Worker {worker_id} processing {item}")
        await asyncio.sleep(0.2)
        queue.task_done()

async def main():
    queue = Queue()
    await asyncio.gather(
        producer(queue, 10),
        consumer(queue, 1),
        consumer(queue, 2)
    )
```

See [Examples Guide](./docs/examples.md) for more usage patterns.

## Common Pitfalls

### Forgetting await

```python
# Wrong - returns coroutine object, doesn't execute
result = async_function()

# Correct - executes the coroutine
result = await async_function()
```

### Blocking the Event Loop

```python
# Wrong - blocks entire event loop
import time
async def bad():
    time.sleep(1)  # Blocks!

# Correct - yields control back to event loop
async def good():
    await asyncio.sleep(1)  # Non-blocking
```

### Not Handling Cancellation

```python
async def robust_task():
    """Task that properly handles cancellation."""
    try:
        while True:
            await asyncio.sleep(1)
            # Do work
    except asyncio.CancelledError:
        # Cleanup code here
        raise  # Re-raise to propagate cancellation
```

## Troubleshooting

### Issue: RuntimeError: This event loop is already running

**Cause**: Trying to use `asyncio.run()` within an already running event loop

**Solution**: Use `await` instead if already in async context, or use `asyncio.create_task()`

### Issue: Slow Performance with Many Concurrent Requests

**Cause**: No rate limiting or connection pooling

**Solution**:
- Use semaphores to limit concurrency
- Configure connection pools (e.g., `aiohttp.TCPConnector`)
- Process in batches

### Issue: Tasks Not Completing

**Cause**: Not properly awaiting task completion

**Solution**:
```python
# Create tasks
tasks = [asyncio.create_task(work(i)) for i in range(10)]

# Wait for all to complete
results = await asyncio.gather(*tasks)
```

## Resources

- **Python asyncio documentation**: https://docs.python.org/3/library/asyncio.html
- **aiohttp**: Async HTTP client/server framework
- **FastAPI**: Modern async web framework
- **asyncpg**: High-performance async PostgreSQL driver
- **motor**: Async MongoDB driver
- **pytest-asyncio**: Testing framework for async code

## Contributing

Contributions are welcome! To improve this plugin:

1. Fork the repository
2. Create a feature branch
3. Add or improve patterns in the skill
4. Test with real async Python projects
5. Submit a pull request

## License

See LICENSE file for details.

## Credits

Curated patterns and best practices from the Python asyncio community, official documentation, and real-world production experience.
