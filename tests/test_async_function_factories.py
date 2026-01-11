"""Tests for async function factory support.

These tests verify that async functions can be used as factory providers
and are correctly awaited by the async injectors.
"""

import asyncio
from dataclasses import dataclass

import pytest
import svcs

from svcs_di import Inject
from svcs_di.auto import DefaultAsyncInjector
from svcs_di.injectors.hopscotch import HopscotchAsyncInjector
from svcs_di.injectors.keyword import KeywordAsyncInjector
from svcs_di.injectors.locator import ServiceLocator


# Test service types
@dataclass
class Database:
    """Database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Cache:
    """Cache service."""

    ttl: int = 300


@dataclass
class Config:
    """Configuration service."""

    env: str = "production"


# ============================================================================
# Task 4.1: Tests for async factory functions
# ============================================================================


@pytest.mark.anyio
async def test_async_function_factory_with_await_during_creation():
    """Test async function factory with await during creation.

    Verifies that an async factory function that performs async operations
    during creation is properly awaited by DefaultAsyncInjector.
    """

    async def create_database() -> Database:
        """Async factory that simulates async initialization."""
        await asyncio.sleep(0.001)  # Simulate async work
        return Database(host="async-created-db", port=5433)

    # Setup registry and container
    registry = svcs.Registry()
    registry.register_factory(Database, create_database)
    container = svcs.Container(registry)

    # Use DefaultAsyncInjector to call the async factory function
    injector = DefaultAsyncInjector(container=container)
    result = await injector(create_database)

    assert isinstance(result, Database)
    assert result.host == "async-created-db"
    assert result.port == 5433


@pytest.mark.anyio
async def test_async_function_with_async_dependency_resolution():
    """Test async function with async dependency resolution.

    Verifies that an async factory function with Inject[T] parameters
    can resolve those dependencies asynchronously.
    """

    async def create_async_database() -> Database:
        """Async factory for Database."""
        await asyncio.sleep(0.001)
        return Database(host="async-db", port=5433)

    async def create_cache_with_db(db: Inject[Database]) -> Cache:
        """Async factory that depends on Database."""
        await asyncio.sleep(0.001)
        # Use db.port as TTL for testing the dependency was resolved
        return Cache(ttl=db.port)

    # Setup registry
    registry = svcs.Registry()
    registry.register_factory(Database, create_async_database)
    container = svcs.Container(registry)

    # Use DefaultAsyncInjector
    injector = DefaultAsyncInjector(container=container)
    result = await injector(create_cache_with_db)

    assert isinstance(result, Cache)
    assert result.ttl == 5433  # Should match db.port from async dependency


@pytest.mark.anyio
async def test_mixed_sync_async_dependency_chain():
    """Test mixed sync/async dependency chain.

    Verifies that a chain with both sync and async factories
    works correctly with async injection.
    """

    # Sync factory for Config
    def create_config() -> Config:
        return Config(env="test")

    # Async factory for Database that depends on Config
    async def create_database(config: Inject[Config]) -> Database:
        await asyncio.sleep(0.001)
        return Database(host=f"db-{config.env}", port=5432)

    # Setup registry
    registry = svcs.Registry()
    registry.register_factory(Config, create_config)
    container = svcs.Container(registry)

    # Use DefaultAsyncInjector to call the async factory
    injector = DefaultAsyncInjector(container=container)
    result = await injector(create_database)

    assert isinstance(result, Database)
    assert result.host == "db-test"


@pytest.mark.anyio
async def test_async_function_in_hopscotch_injector_context():
    """Test async function in HopscotchInjector context.

    Verifies that async factory functions work correctly with
    HopscotchAsyncInjector and its locator-based resolution.
    """

    async def create_database() -> Database:
        """Async factory for Database."""
        await asyncio.sleep(0.001)
        return Database(host="hopscotch-async-db", port=5434)

    # Setup registry with locator
    registry = svcs.Registry()
    locator = ServiceLocator()
    locator = locator.register(Database, create_database)
    registry.register_value(ServiceLocator, locator)
    registry.register_factory(Database, create_database)
    container = svcs.Container(registry)

    # Use HopscotchAsyncInjector
    injector = HopscotchAsyncInjector(container=container)
    result = await injector(create_database)

    assert isinstance(result, Database)
    assert result.host == "hopscotch-async-db"
    assert result.port == 5434


@pytest.mark.anyio
async def test_keyword_async_injector_with_async_function_factory():
    """Test KeywordAsyncInjector with async function factory.

    Verifies that KeywordAsyncInjector correctly awaits async
    factory functions.
    """

    async def create_database() -> Database:
        """Async factory for Database."""
        await asyncio.sleep(0.001)
        return Database(host="keyword-async-db", port=5435)

    # Setup registry
    registry = svcs.Registry()
    registry.register_factory(Database, create_database)
    container = svcs.Container(registry)

    # Use KeywordAsyncInjector
    injector = KeywordAsyncInjector(container=container)
    result = await injector(create_database)

    assert isinstance(result, Database)
    assert result.host == "keyword-async-db"
    assert result.port == 5435


@pytest.mark.anyio
async def test_async_factory_function_with_multiple_inject_parameters():
    """Test async factory function with multiple Inject[T] parameters.

    Verifies that async factories can resolve multiple dependencies
    asynchronously.
    """

    async def create_async_cache() -> Cache:
        """Async factory for Cache."""
        await asyncio.sleep(0.001)
        return Cache(ttl=600)

    async def create_service_with_deps(
        db: Inject[Database], cache: Inject[Cache]
    ) -> str:
        """Async factory with multiple injected dependencies."""
        await asyncio.sleep(0.001)
        return f"DB: {db.host}, Cache TTL: {cache.ttl}"

    # Setup registry
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="multi-dep-db"))
    registry.register_factory(Cache, create_async_cache)
    container = svcs.Container(registry)

    # Use DefaultAsyncInjector
    injector = DefaultAsyncInjector(container=container)
    result = await injector(create_service_with_deps)

    assert result == "DB: multi-dep-db, Cache TTL: 600"
