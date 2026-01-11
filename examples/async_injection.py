"""Async injection example.

This example demonstrates async dependency injection:
- Register async factories for services
- Use auto_async() for services with async dependencies
- Retrieve services with aget() in async contexts
"""

import asyncio
from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject, auto, auto_async


@dataclass
class Database:
    """A database service that's created asynchronously."""

    host: str
    port: int


@dataclass
class Cache:
    """A cache service."""

    max_size: int = 1000


# A service with an injected parameter that is async
@dataclass
class AsyncService:
    """A service with both sync and async dependencies."""

    db: Inject[Database]
    cache: Inject[Cache]
    timeout: int = 30


async def create_database() -> Database:
    """Async factory for database - simulates async initialization."""
    await asyncio.sleep(0.01)  # Simulate async work
    return Database(host="async-db.example.com", port=5432)


async def main() -> AsyncService:
    # Create registry
    registry = Registry()

    # Register async factory for database
    registry.register_factory(Database, create_database)

    # Register sync factory for cache (using auto)
    registry.register_factory(Cache, auto(Cache))

    # Register service with auto_async (since it has async dependencies)
    registry.register_factory(AsyncService, auto_async(AsyncService))

    # Get the service asynchronously
    async with Container(registry) as container:
        service = await container.aget(AsyncService)

        assert service.db.host == "async-db.example.com"
        assert service.db.port == 5432
        assert service.cache.max_size == 1000
        assert service.timeout == 30

        return service


if __name__ == "__main__":
    asyncio.run(main())
