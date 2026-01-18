# Skills Reference

This plugin provides a comprehensive skill for mastering Python asyncio and concurrent programming patterns.

## async-python-patterns

**Location**: `skills/async-python-patterns/SKILL.md`

**Description**: Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations.

**User Invocable**: Yes

**Allowed Tools**: All (inherits from session)

**Model**: Inherits from session

### When to Use

Claude automatically activates this skill when you:

- Build async web APIs (FastAPI, aiohttp, Sanic)
- Implement concurrent I/O operations (database, file, network)
- Create web scrapers with concurrent requests
- Develop real-time applications (WebSocket servers, chat systems)
- Process multiple independent tasks simultaneously
- Build microservices with async communication
- Optimize I/O-bound workloads
- Implement async background tasks and queues

### Activation

**Automatic (recommended)**:
Claude detects when you're working with async Python code and activates automatically.

**Manual invocation**:
```
@async-python-patterns
```

**Via Skill tool**:
```python
Skill(command: "async-python-patterns")
```

### Coverage Areas

#### 1. Core Concepts

**Event Loop**
- Single-threaded cooperative multitasking
- Task scheduling and execution
- Non-blocking I/O management
- Callbacks and futures handling

**Coroutines**
- Functions defined with `async def`
- Pause and resume execution with `await`
- Return values and exception handling

**Tasks**
- Scheduled coroutines on the event loop
- Concurrent execution management
- Task cancellation and result retrieval

**Futures**
- Low-level promise objects
- Represent eventual results
- Callback registration

**Async Context Managers**
- Support `async with` syntax
- Automatic resource cleanup
- Asynchronous `__aenter__` and `__aexit__`

**Async Iterators**
- Support `async for` syntax
- Asynchronous data stream iteration
- Generator-based async iteration

#### 2. Fundamental Patterns (Patterns 1-5)

**Pattern 1: Basic Async/Await**
- Simple async function definition
- Awaiting async operations
- Entry point with `asyncio.run()`

**Pattern 2: Concurrent Execution with gather()**
- Running multiple coroutines concurrently
- Collecting results in order
- Error propagation options

**Pattern 3: Task Creation and Management**
- Creating tasks with `asyncio.create_task()`
- Background task execution
- Awaiting task completion

**Pattern 4: Error Handling**
- Try/except in async functions
- Handling exceptions in gather()
- Graceful failure patterns

**Pattern 5: Timeout Handling**
- Using `asyncio.wait_for()`
- TimeoutError exception handling
- Setting appropriate timeout values

#### 3. Advanced Patterns (Patterns 6-10)

**Pattern 6: Async Context Managers**
- Implementing `__aenter__` and `__aexit__`
- Resource acquisition and cleanup
- Exception handling in context managers

**Pattern 7: Async Iterators and Generators**
- Defining async generators with `async def` + `yield`
- Using `async for` for iteration
- Paginated data fetching patterns

**Pattern 8: Producer-Consumer Pattern**
- Using `asyncio.Queue`
- Multiple producers and consumers
- Signaling completion with sentinel values
- Queue.join() for completion waiting

**Pattern 9: Semaphore for Rate Limiting**
- Creating semaphores with `asyncio.Semaphore(n)`
- Limiting concurrent operations
- Using `async with semaphore` pattern

**Pattern 10: Locks and Synchronization**
- Thread-safe async operations
- Using `asyncio.Lock()`
- Preventing race conditions

#### 4. Real-World Applications

**Web Scraping with aiohttp**
- Concurrent HTTP requests
- Session management and connection pooling
- Error handling for failed requests
- Timeout configuration

**Async Database Operations**
- Concurrent query execution
- Fetching related data in parallel
- Connection pool management
- Transaction handling patterns

**WebSocket Server Implementation**
- Client registration and management
- Broadcasting to multiple clients
- Message iteration patterns
- Connection cleanup

#### 5. Performance Best Practices

**Connection Pools**
- Configuring aiohttp TCPConnector
- Setting per-host limits
- Reusing connections efficiently

**Batch Operations**
- Processing items in batches
- Controlling memory usage
- Balancing throughput and resource consumption

**Avoiding Blocking Operations**
- Using `loop.run_in_executor()` for CPU-bound work
- ThreadPoolExecutor integration
- Identifying blocking operations

#### 6. Common Pitfalls and Solutions

**Forgetting await**
- Symptom: Coroutine object returned instead of result
- Solution: Always await coroutines

**Blocking the Event Loop**
- Symptom: All async operations freeze
- Solution: Use async equivalents or run_in_executor()

**Not Handling Cancellation**
- Symptom: Resources not cleaned up on task cancellation
- Solution: Catch CancelledError and re-raise after cleanup

**Mixing Sync and Async Code**
- Symptom: SyntaxError or runtime errors
- Solution: Use asyncio.run() to bridge sync-to-async

#### 7. Testing Async Code

**pytest-asyncio Integration**
- Using `@pytest.mark.asyncio` decorator
- Testing async functions
- Timeout testing with `pytest.raises()`
- Mocking async dependencies

### Code Examples Summary

The skill provides complete, runnable examples for:

- ✅ Basic async/await (Lines 64-93)
- ✅ Concurrent execution with gather() (Lines 96-118)
- ✅ Task creation and management (Lines 121-148)
- ✅ Error handling patterns (Lines 151-184)
- ✅ Timeout handling (Lines 187-205)
- ✅ Async context managers (Lines 209-241)
- ✅ Async iterators and generators (Lines 244-275)
- ✅ Producer-consumer pattern (Lines 278-331)
- ✅ Semaphore rate limiting (Lines 334-359)
- ✅ Locks and synchronization (Lines 362-402)
- ✅ Web scraping with aiohttp (Lines 407-445)
- ✅ Async database operations (Lines 448-487)
- ✅ WebSocket server (Lines 490-547)
- ✅ Connection pooling (Lines 554-565)
- ✅ Batch processing (Lines 568-582)
- ✅ Running blocking operations (Lines 585-609)

### Resources Provided

The skill references these key resources:

- **Python asyncio documentation**: Official asyncio module docs
- **aiohttp**: Popular async HTTP client/server framework
- **FastAPI**: Modern async web framework
- **asyncpg**: High-performance async PostgreSQL driver
- **motor**: Official async MongoDB driver

### Best Practices Enforced

1. Use `asyncio.run()` for entry point (Python 3.7+)
2. Always await coroutines to execute them
3. Use `gather()` for concurrent execution of multiple tasks
4. Implement proper error handling with try/except
5. Use timeouts to prevent hanging operations
6. Pool connections for better performance
7. Avoid blocking operations in async code
8. Use semaphores for rate limiting
9. Handle task cancellation properly
10. Test async code with pytest-asyncio

### No Hooks Configured

This skill does not define custom hooks. It relies on standard Claude Code tool permissions.

### No Reference Files

This skill includes all guidance directly in SKILL.md without separate reference files. All patterns and examples are available in the main skill content.

---

[Back to README](../README.md)
