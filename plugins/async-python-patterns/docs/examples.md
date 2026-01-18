# Usage Examples

Concrete, real-world examples of using the async-python-patterns skill to build high-performance asynchronous Python applications.

## Example 1: Building a Concurrent API Client

**Scenario**: You need to fetch data from 50 different API endpoints and aggregate the results. Sequential requests would take too long.

**Steps**:
1. Invoke the async-python-patterns skill (automatic when discussing async code)
2. Use `asyncio.gather()` for concurrent execution
3. Implement proper error handling
4. Add timeout protection

**Code**:
```python
import asyncio
import aiohttp
from typing import List, Dict, Optional

async def fetch_endpoint(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 10
) -> Optional[Dict]:
    """Fetch single API endpoint with error handling."""
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {"url": url, "status": "success", "data": data}
            else:
                return {"url": url, "status": "error", "code": response.status}
    except asyncio.TimeoutError:
        return {"url": url, "status": "timeout"}
    except Exception as e:
        return {"url": url, "status": "error", "message": str(e)}

async def fetch_all_endpoints(urls: List[str]) -> List[Dict]:
    """Fetch all endpoints concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_endpoint(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

async def main():
    """Main entry point."""
    urls = [f"https://api.example.com/items/{i}" for i in range(1, 51)]

    print(f"Fetching {len(urls)} endpoints concurrently...")
    results = await fetch_all_endpoints(urls)

    # Aggregate results
    successful = [r for r in results if r and r["status"] == "success"]
    failed = [r for r in results if r and r["status"] != "success"]

    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    return successful

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: All 50 API calls execute concurrently, completing in approximately the time of the slowest request rather than the sum of all requests. Proper error handling ensures failures don't crash the application.

---

## Example 2: Rate-Limited Web Scraper

**Scenario**: Scrape 1000 product pages from an e-commerce site while respecting rate limits (max 10 concurrent requests).

**Steps**:
1. Use semaphore for rate limiting
2. Implement connection pooling for efficiency
3. Add retry logic for transient failures
4. Parse and extract data asynchronously

**Code**:
```python
import asyncio
import aiohttp
from typing import List, Dict
from bs4 import BeautifulSoup

class RateLimitedScraper:
    """Web scraper with rate limiting and retry logic."""

    def __init__(self, max_concurrent: int = 10, max_retries: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_retries = max_retries
        self.connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)

    async def scrape_page(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Dict:
        """Scrape single page with rate limiting and retries."""
        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            return self.parse_product(url, html)
                        elif response.status == 429:  # Too many requests
                            wait_time = 2 ** attempt  # Exponential backoff
                            await asyncio.sleep(wait_time)
                        else:
                            return {"url": url, "error": f"Status {response.status}"}
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        return {"url": url, "error": str(e)}
                    await asyncio.sleep(1)

        return {"url": url, "error": "Max retries exceeded"}

    def parse_product(self, url: str, html: str) -> Dict:
        """Parse product data from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        # Simplified parsing example
        return {
            "url": url,
            "title": soup.find("h1", class_="product-title").text.strip(),
            "price": soup.find("span", class_="price").text.strip(),
            "in_stock": "In Stock" in html
        }

    async def scrape_all(self, urls: List[str]) -> List[Dict]:
        """Scrape all URLs with rate limiting."""
        async with aiohttp.ClientSession(connector=self.connector) as session:
            tasks = [self.scrape_page(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return results

async def main():
    """Scrape 1000 products."""
    urls = [f"https://store.example.com/product/{i}" for i in range(1, 1001)]

    scraper = RateLimitedScraper(max_concurrent=10, max_retries=3)
    results = await scraper.scrape_all(urls)

    # Save results
    successful = [r for r in results if "error" not in r]
    print(f"Successfully scraped {len(successful)}/{len(urls)} products")

    return successful

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: 1000 pages scraped with only 10 concurrent requests at any time, respecting server limits while maintaining efficiency. Automatic retry with exponential backoff handles transient failures.

---

## Example 3: Async Database Operations with Connection Pool

**Scenario**: Build an API endpoint that fetches user data along with their orders, profile, and preferences from a database, all in parallel.

**Steps**:
1. Set up async database connection pool
2. Execute related queries concurrently
3. Aggregate results into response object
4. Handle database errors gracefully

**Code**:
```python
import asyncio
from typing import Dict, List, Optional
import asyncpg  # Async PostgreSQL driver

class AsyncUserService:
    """Service for fetching user data with async database operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool."""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=10,
            max_size=50,
            command_timeout=5
        )

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Fetch user record."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email, created_at FROM users WHERE id = $1",
                user_id
            )
            return dict(row) if row else None

    async def get_user_orders(self, user_id: int) -> List[Dict]:
        """Fetch user's orders."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, total, status, created_at
                FROM orders
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 10
                """,
                user_id
            )
            return [dict(row) for row in rows]

    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Fetch user profile."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT bio, avatar_url, location FROM profiles WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None

    async def get_user_preferences(self, user_id: int) -> Dict:
        """Fetch user preferences."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT key, value FROM user_preferences WHERE user_id = $1",
                user_id
            )
            return {row["key"]: row["value"] for row in rows}

    async def get_complete_user_data(self, user_id: int) -> Dict:
        """
        Fetch all user-related data concurrently.

        This executes 4 database queries in parallel, significantly
        faster than sequential execution.
        """
        try:
            # Execute all queries concurrently
            user, orders, profile, preferences = await asyncio.gather(
                self.get_user_by_id(user_id),
                self.get_user_orders(user_id),
                self.get_user_profile(user_id),
                self.get_user_preferences(user_id),
                return_exceptions=True
            )

            # Handle individual query failures
            if isinstance(user, Exception):
                raise ValueError(f"Failed to fetch user: {user}")

            if not user:
                return {"error": "User not found"}

            return {
                "user": user,
                "orders": orders if not isinstance(orders, Exception) else [],
                "profile": profile if not isinstance(profile, Exception) else {},
                "preferences": preferences if not isinstance(preferences, Exception) else {}
            }

        except Exception as e:
            return {"error": str(e)}

async def main():
    """Example usage."""
    service = AsyncUserService("postgresql://localhost/myapp")

    try:
        await service.connect()

        # Fetch data for user 123
        user_data = await service.get_complete_user_data(123)

        if "error" not in user_data:
            print(f"User: {user_data['user']['username']}")
            print(f"Orders: {len(user_data['orders'])}")
            print(f"Profile: {user_data['profile']}")
        else:
            print(f"Error: {user_data['error']}")

    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: All related data queries execute concurrently, reducing total fetch time from ~400ms (4 queries × 100ms) to ~100ms (slowest query). Connection pooling ensures efficient resource usage.

---

## Example 4: Real-Time WebSocket Chat Server

**Scenario**: Build a WebSocket server that handles multiple concurrent chat connections, broadcasting messages to all connected clients.

**Steps**:
1. Implement WebSocket connection handler
2. Manage client registration and cleanup
3. Broadcast messages to all clients concurrently
4. Handle disconnections gracefully

**Code**:
```python
import asyncio
import json
import websockets
from typing import Set, List, Dict
from datetime import datetime

class ChatServer:
    """Real-time chat server using WebSockets."""

    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.message_history: List[Dict] = []

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register new client connection."""
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"Client {client_id} connected. Total clients: {len(self.clients)}")

        # Send message history to new client
        for msg in self.message_history[-50:]:  # Last 50 messages
            await websocket.send(json.dumps(msg))

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister client connection."""
        self.clients.discard(websocket)
        client_id = id(websocket)
        print(f"Client {client_id} disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        # Store in history
        self.message_history.append(message)

        # Broadcast concurrently to all clients
        message_json = json.dumps(message)
        tasks = [client.send(message_json) for client in self.clients]

        # Gather with return_exceptions to handle disconnected clients
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Remove clients that failed to receive message
        for client, result in zip(list(self.clients), results):
            if isinstance(result, Exception):
                await self.unregister(client)

    async def handle_client(
        self,
        websocket: websockets.WebSocketServerProtocol,
        path: str
    ):
        """Handle individual client connection."""
        await self.register(websocket)

        try:
            async for message in websocket:
                # Parse incoming message
                data = json.loads(message)

                # Create broadcast message
                broadcast_msg = {
                    "username": data.get("username", "Anonymous"),
                    "message": data.get("message", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Broadcast to all clients
                await self.broadcast(broadcast_msg)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            await self.unregister(websocket)

    async def start(self, host: str = "localhost", port: int = 8765):
        """Start WebSocket server."""
        async with websockets.serve(self.handle_client, host, port):
            print(f"Chat server started on ws://{host}:{port}")
            await asyncio.Future()  # Run forever

async def main():
    """Start chat server."""
    server = ChatServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: Multiple clients can connect and exchange messages in real-time. Messages are broadcast concurrently to all connected clients, ensuring low latency even with hundreds of concurrent connections.

---

## Example 5: Background Task Processing with Queues

**Scenario**: Process uploaded images in the background (resize, compress, generate thumbnails) while immediately returning response to user.

**Steps**:
1. Set up async queue for task distribution
2. Create worker pool to process tasks
3. Implement graceful shutdown
4. Handle task failures with retry logic

**Code**:
```python
import asyncio
from asyncio import Queue
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ImageTask:
    """Image processing task."""
    task_id: str
    image_path: str
    operations: List[str]  # ["resize", "compress", "thumbnail"]
    retries: int = 0
    max_retries: int = 3

class ImageProcessor:
    """Background image processor with worker pool."""

    def __init__(self, num_workers: int = 5):
        self.queue: Queue = Queue()
        self.num_workers = num_workers
        self.tasks_status: Dict[str, TaskStatus] = {}
        self.workers: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()

    async def process_image(self, task: ImageTask) -> bool:
        """Process single image (simulated)."""
        try:
            for operation in task.operations:
                print(f"Task {task.task_id}: {operation} {task.image_path}")
                await asyncio.sleep(1)  # Simulate processing time

            return True

        except Exception as e:
            print(f"Task {task.task_id} failed: {e}")
            return False

    async def worker(self, worker_id: int):
        """Worker that processes tasks from queue."""
        print(f"Worker {worker_id} started")

        while not self.shutdown_event.is_set():
            try:
                # Wait for task with timeout to check shutdown event
                task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            # Update status
            self.tasks_status[task.task_id] = TaskStatus.PROCESSING

            # Process task
            success = await self.process_image(task)

            if success:
                self.tasks_status[task.task_id] = TaskStatus.COMPLETED
            elif task.retries < task.max_retries:
                # Retry failed task
                task.retries += 1
                await self.queue.put(task)
                print(f"Task {task.task_id} requeued (retry {task.retries})")
            else:
                self.tasks_status[task.task_id] = TaskStatus.FAILED
                print(f"Task {task.task_id} failed permanently")

            self.queue.task_done()

        print(f"Worker {worker_id} stopped")

    async def start(self):
        """Start worker pool."""
        self.workers = [
            asyncio.create_task(self.worker(i))
            for i in range(self.num_workers)
        ]
        print(f"Started {self.num_workers} workers")

    async def submit_task(self, task: ImageTask):
        """Submit task for processing."""
        self.tasks_status[task.task_id] = TaskStatus.PENDING
        await self.queue.put(task)
        print(f"Task {task.task_id} submitted")

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of task."""
        return self.tasks_status.get(task_id)

    async def shutdown(self):
        """Gracefully shutdown processor."""
        print("Shutting down...")

        # Wait for queue to be empty
        await self.queue.join()

        # Signal workers to stop
        self.shutdown_event.set()

        # Wait for workers to finish
        await asyncio.gather(*self.workers)

        print("Shutdown complete")

async def main():
    """Example usage."""
    processor = ImageProcessor(num_workers=3)
    await processor.start()

    # Submit tasks
    tasks = [
        ImageTask(f"img-{i}", f"/uploads/image-{i}.jpg", ["resize", "compress", "thumbnail"])
        for i in range(10)
    ]

    for task in tasks:
        await processor.submit_task(task)

    # Simulate API returning immediately
    print("API response: All tasks submitted")

    # Wait a bit for processing
    await asyncio.sleep(5)

    # Check status
    for task in tasks:
        status = await processor.get_task_status(task.task_id)
        print(f"{task.task_id}: {status.value}")

    # Shutdown
    await processor.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: Images are processed in the background by a worker pool while the API responds immediately. Failed tasks are automatically retried, and graceful shutdown ensures no tasks are lost.

---

## Common Patterns Summary

| Pattern | Use Case | Key Technique |
|---------|----------|---------------|
| Concurrent API calls | Fetch multiple resources | `asyncio.gather()` |
| Rate limiting | Respect API limits | `asyncio.Semaphore()` |
| Database operations | Parallel queries | Connection pooling + gather() |
| WebSocket server | Real-time communication | Async iteration + broadcast |
| Background processing | Async task queue | Worker pool + Queue |

---

[Back to README](../README.md) | [Skills Reference](./skills.md)
