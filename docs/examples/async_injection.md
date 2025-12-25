# Asynchronous Injection

**Complexity: Intermediate**

## Overview

This example demonstrates async/await support in svcs-di. You'll learn how to:

- Register async factories for services that require asynchronous initialization
- Use `auto_async()` for services with async dependencies
- Retrieve services asynchronously with `Container.aget()` in async contexts
- Mix synchronous and asynchronous dependencies in the same service

This pattern is essential for applications that use async I/O, such as web servers, database clients, or any service requiring asynchronous initialization.

## Source Code

The complete example is available at `/examples/async_injection.py`:

```python
"""Async injection example.

This example demonstrates async dependency injection:
- Register async factories for services
- Use auto_async() for services with async dependencies
- Retrieve services with aget() in async contexts
"""

import asyncio
from dataclasses import dataclass

import svcs

from svcs_di import Injectable, auto, auto_async


@dataclass
class Database:
    """A database service that's created asynchronously."""

    host: str
    port: int


@dataclass
class Cache:
    """A cache service."""

    max_size: int = 1000


@dataclass
class AsyncService:
    """A service with both sync and async dependencies."""

    db: Injectable[Database]
    cache: Injectable[Cache]
    timeout: int = 30


async def create_database() -> Database:
    """Async factory for database - simulates async initialization."""
    await asyncio.sleep(0.01)  # Simulate async work
    print("Database initialized asynchronously")
    return Database(host="async-db.example.com", port=5432)


async def main():
    """Demonstrate async injection."""
    # Create registry
    registry = svcs.Registry()

    # Register async factory for database
    registry.register_factory(Database, create_database)

    # Register sync factory for cache (using auto)
    registry.register_factory(Cache, auto(Cache))

    # Register service with auto_async (since it has async dependencies)
    registry.register_factory(AsyncService, auto_async(AsyncService))

    # Get the service asynchronously
    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncService)

        print(f"Service created:")
        print(f"  Database: {service.db.host}:{service.db.port}")  # type: ignore[attr-defined]
        print(f"  Cache: max_size={service.cache.max_size}")  # type: ignore[attr-defined]
        print(f"  Timeout: {service.timeout}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Async Factory Registration

When a service requires asynchronous initialization, register an async factory function:

```python
import asyncio
from dataclasses import dataclass
import svcs

@dataclass
class Database:
    host: str
    port: int

async def create_database() -> Database:
    """Async factory - performs async initialization."""
    await asyncio.sleep(0.01)  # Simulate async work (e.g., network handshake)
    return Database(host="async-db.example.com", port=5432)

registry = svcs.Registry()
registry.register_factory(Database, create_database)
```

The async factory function can perform I/O operations, wait for connections, or execute any asynchronous initialization logic. The container will automatically detect that the factory is async and handle it appropriately.

### auto_async() for Services with Async Dependencies

When a service has Injectable parameters that must be resolved asynchronously, use `auto_async()` instead of `auto()`:

```python
import asyncio
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto, auto_async

@dataclass
class Database:
    host: str
    port: int

@dataclass
class Cache:
    max_size: int = 1000

@dataclass
class AsyncService:
    db: Injectable[Database]  # Will be resolved asynchronously
    cache: Injectable[Cache]   # Can be resolved synchronously
    timeout: int = 30

async def create_database() -> Database:
    await asyncio.sleep(0.01)
    return Database(host="async-db.example.com", port=5432)

registry = svcs.Registry()
registry.register_factory(Database, create_database)  # Async factory
registry.register_factory(Cache, auto(Cache))         # Sync factory
registry.register_factory(AsyncService, auto_async(AsyncService))  # Must use auto_async
```

The `auto_async()` function generates an async factory that:
1. Inspects the constructor signature for `Injectable` parameters
2. Resolves each dependency (using `aget()` for async dependencies)
3. Constructs the service with all resolved dependencies

If any dependency requires async resolution, you must use `auto_async()` for the consuming service.

### Container.aget() for Async Resolution

To retrieve services with async dependencies, use `Container.aget()` in an async context:

```python
import asyncio
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto, auto_async

@dataclass
class Database:
    host: str
    port: int

@dataclass
class AsyncService:
    db: Injectable[Database]

async def create_database() -> Database:
    await asyncio.sleep(0.01)
    return Database(host="async-db.example.com", port=5432)

async def main():
    registry = svcs.Registry()
    registry.register_factory(Database, create_database)
    registry.register_factory(AsyncService, auto_async(AsyncService))

    async with svcs.Container(registry) as container:
        # Use aget() for async resolution
        service = await container.aget(AsyncService)
```

The `aget()` method is the async equivalent of `get()`. It returns an awaitable that resolves to the service instance. Using `async with` ensures proper resource cleanup when the container is no longer needed.

### Mixing Sync and Async Dependencies

A service can depend on both synchronous and asynchronous services. As long as you use `auto_async()` for the factory and `aget()` for resolution, the container handles the mix automatically:

```python
import asyncio
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto, auto_async

@dataclass
class Database:
    """Async dependency."""
    host: str
    port: int

@dataclass
class Cache:
    """Sync dependency."""
    max_size: int = 1000

@dataclass
class AsyncService:
    """Service with both sync and async dependencies."""
    db: Injectable[Database]    # Async
    cache: Injectable[Cache]     # Sync
    timeout: int = 30

async def create_database() -> Database:
    await asyncio.sleep(0.01)
    return Database(host="async-db.example.com", port=5432)

async def main():
    registry = svcs.Registry()
    registry.register_factory(Database, create_database)  # Async
    registry.register_factory(Cache, auto(Cache))          # Sync
    registry.register_factory(AsyncService, auto_async(AsyncService))

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncService)
```

The `auto_async()` factory will:
- Use `await container.aget(Database)` to resolve the async dependency
- Use `container.get(Cache)` to resolve the sync dependency (can call sync from async)
- Construct `AsyncService` with both resolved dependencies

This flexibility lets you gradually adopt async patterns without forcing all services to be async.

## Type Safety

svcs-di maintains full type safety with async operations. Type checkers understand:

- `async def create_database() -> Database` is an async factory
- `container.aget(AsyncService)` returns `Awaitable[AsyncService]`
- `await container.aget(AsyncService)` resolves to an `AsyncService` instance

The `# type: ignore[attr-defined]` comments in the source code are needed because type checkers see `db` as type `Injectable[Database]` in the class definition, but at runtime it's actually a `Database` instance. This is a known limitation of the current type system and doesn't affect runtime type safety.

## Expected Output

Running this example produces:

```
Database initialized asynchronously
Service created:
  Database: async-db.example.com:5432
  Cache: max_size=1000
  Timeout: 30
```

This output demonstrates:

- **Async initialization**: "Database initialized asynchronously" appears first, showing the async factory executed
- **Mixed dependencies**: Both the async `Database` and sync `Cache` were successfully resolved
- **Service construction**: `AsyncService` was created with all dependencies properly injected
- **Default values preserved**: The `timeout=30` default value remained intact

The async factory allows realistic initialization patterns like establishing database connections, loading remote configuration, or warming up caches—all while maintaining clean dependency injection.

## Next Steps

Once you're comfortable with asynchronous injection, explore:

- [Basic Dataclass Injection](basic_dataclass.md) to review the fundamentals of `auto()`
- [Protocol-Based Injection](protocol_injection.md) to use protocols with async factories
- [Overriding Dependencies with Kwargs](kwargs_override.md) for testing async services with mock dependencies
