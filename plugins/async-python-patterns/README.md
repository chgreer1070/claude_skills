# Async Python Patterns

Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install async-python-patterns@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/async-python-patterns
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [async-python-patterns](./skills/async-python-patterns/SKILL.md) | Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations. |

## Quick Start

Ask Claude to help build an async application:

```text
@async-python-patterns
Help me build an async web scraper that fetches data from 100 URLs concurrently
```

Claude will activate the skill automatically and provide guidance on:

- Implementing async/await patterns with proper error handling
- Using asyncio.gather() for concurrent operations
- Managing connection pools and rate limiting
- Handling timeouts and retries
- Structuring async code following best practices

Example code structure Claude might suggest:

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url, timeout=10) as response:
        return await response.text()

async def main():
    urls = [...]  # 100 URLs
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

if __name__ == "__main__":
    asyncio.run(main())
```

## Use Cases

- Async web APIs (FastAPI, aiohttp, Sanic)
- Concurrent I/O operations (database, file, network)
- Web scrapers with concurrent requests
- Real-time applications (WebSocket servers, chat systems)
- Microservices with async communication
- Async background tasks and queues

## License

See repository root for license information.
