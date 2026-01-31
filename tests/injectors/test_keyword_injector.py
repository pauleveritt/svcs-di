"""Tests for KeywordInjector and KeywordAsyncInjector."""

import asyncio
from dataclasses import dataclass
from typing import Protocol

import pytest
from svcs import Container, Registry

from svcs_di import Inject, Injector
from svcs_di.injectors import KeywordAsyncInjector, KeywordInjector


# Test fixtures
class Greeter(Protocol):
    """A protocol for testing protocol-based injection."""

    def greet(self, name: str) -> str: ...


class DefaultGreeter:
    """A concrete implementation of Greeter."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class DBService:
    """A service with injectable dependencies."""

    db: Inject[Database]
    timeout: int = 30


@pytest.fixture
def registry() -> Registry:
    """Create a registry with a database."""
    registry = Registry()
    registry.register_factory(Injector, KeywordInjector)
    registry.register_factory(Database, Database)
    return registry


@pytest.fixture
def container(registry: Registry) -> Container:
    """Create a container from the registry."""
    return Container(registry)


@pytest.fixture
def injector(container: Container) -> KeywordInjector:
    """Get the KeywordInjector from the container."""
    _injector = container.get(Injector)
    assert isinstance(_injector, KeywordInjector)
    return _injector


# Tests for KeywordInjector
def test_keyword_injector_kwarg_precedence(injector: KeywordInjector):
    """Kwargs override everything, including injectable parameters."""

    # Create DBService with injection but with kwargs
    custom_db = Database(host="test", port=1234)
    instance = injector(DBService, db=custom_db)

    # The kwarg should override the container value
    assert isinstance(instance.db, Database)
    assert instance.db.host == "test"
    assert instance.db.port == 1234


def test_keyword_injector_kwargs_override_defaults(injector: KeywordInjector):
    """Kwargs override default values for non-injectable parameters."""

    # Override the default timeout
    instance = injector(DBService, timeout=60)

    assert instance.timeout == 60


def test_keyword_injector_validates_kwargs(injector: KeywordInjector):
    """Unknown kwargs raise ValueError."""

    # Try to pass an unknown kwarg
    with pytest.raises(ValueError, match="unknown_param"):
        injector(DBService, unknown_param="bad")


def test_keyword_injector_container_resolution(
    registry: Registry, injector: KeywordInjector
):
    """Inject parameters are resolved from container when no kwargs provided."""

    # Register a custom database to override the default registration
    db = Database(host="prod", port=5433)
    registry.register_value(Database, db)

    # Inject without kwargs
    instance = injector(DBService)

    # Should get the database from container
    assert instance.db is db
    assert instance.db.host == "prod"
    assert instance.db.port == 5433


def test_keyword_injector_protocol_injection(
    registry: Registry, injector: KeywordInjector
):
    """Protocol types are resolved using get_abstract()."""

    @dataclass
    class ServiceWithProtocol:
        greeter: Inject[Greeter]

    # Register the protocol implementation
    greeter = DefaultGreeter()
    registry.register_value(Greeter, greeter)

    # Inject
    instance = injector(ServiceWithProtocol)

    # Should get the greeter via get_abstract
    assert instance.greeter is greeter
    assert instance.greeter.greet("World") == "Hello, World!"


def test_keyword_injector_default_fallback(injector: KeywordInjector):
    """Non-injectable parameters use default values when not overridden."""

    # Create instance - timeout should use default
    instance = injector(DBService)

    assert instance.timeout == 30


async def test_keyword_async_injector_with_mixed_dependencies():
    """Test async injector can handle both sync and async dependencies."""

    @dataclass
    class SyncDep:
        value: str = "sync"

    @dataclass
    class AsyncDep:
        value: str = "async"

    @dataclass
    class MixedService:
        sync_dep: Inject[SyncDep]
        async_dep: Inject[AsyncDep]

    registry = Registry()

    # Register sync dependency as value
    registry.register_value(SyncDep, SyncDep())

    # Register async dependency with async factory
    async def async_factory():
        await asyncio.sleep(0.001)
        return AsyncDep()

    registry.register_factory(AsyncDep, async_factory)

    async with Container(registry) as container:
        # Get async injector
        injector = KeywordAsyncInjector(container=container)

        # Create service with mixed dependencies
        service = await injector(MixedService)

        assert isinstance(service.sync_dep, SyncDep)
        assert isinstance(service.async_dep, AsyncDep)
        assert service.sync_dep.value == "sync"
        assert service.async_dep.value == "async"


async def test_keyword_async_injector_kwargs_override():
    """Test async injector respects kwargs override."""

    @dataclass
    class SimpleService:
        value: Inject[Database]
        timeout: int = 10

    registry = Registry()
    registry.register_value(Database, Database(host="prod", port=5432))

    async with Container(registry) as container:
        injector = KeywordAsyncInjector(container=container)

        # Override both injectable and default
        custom_db = Database(host="test", port=1234)
        service = await injector(SimpleService, value=custom_db, timeout=99)

        assert isinstance(service.value, Database)  # Type guard
        assert service.value.host == "test"
        assert service.value.port == 1234
        assert service.timeout == 99


# Use pytest-anyio for async tests
test_keyword_async_injector_with_mixed_dependencies = pytest.mark.anyio(
    test_keyword_async_injector_with_mixed_dependencies
)
test_keyword_async_injector_kwargs_override = pytest.mark.anyio(
    test_keyword_async_injector_kwargs_override
)
