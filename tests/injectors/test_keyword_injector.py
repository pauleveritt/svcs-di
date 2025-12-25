"""Tests for KeywordInjector and KeywordAsyncInjector."""

from dataclasses import dataclass
from typing import Protocol

import pytest
import svcs

from svcs_di import Injectable


# Test fixtures
class GreeterProtocol(Protocol):
    """A protocol for testing protocol-based injection."""

    def greet(self, name: str) -> str: ...


class ConcreteGreeter:
    """A concrete implementation of GreeterProtocol."""

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

    db: Injectable[Database]
    timeout: int = 30


# Tests for KeywordInjector
def test_keyword_injector_kwarg_precedence():
    """Kwargs override everything, including injectable parameters."""
    from svcs_di.injectors import KeywordInjector

    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register a database
    registry.register_value(Database, Database(host="prod", port=5433))

    # Get the injector
    injector = KeywordInjector(container=container)

    # But override it with kwargs
    custom_db = Database(host="test", port=1234)
    instance = injector(DBService, db=custom_db)

    # The kwarg should override the container value
    assert isinstance(instance.db, Database)
    assert instance.db.host == "test"
    assert instance.db.port == 1234


def test_keyword_injector_kwargs_override_defaults():
    """Kwargs override default values for non-injectable parameters."""
    from svcs_di.injectors import KeywordInjector

    registry = svcs.Registry()
    container = svcs.Container(registry)

    registry.register_value(Database, Database())

    # Get the injector
    injector = KeywordInjector(container=container)

    # Override the default timeout
    instance = injector(DBService, timeout=60)

    assert instance.timeout == 60


def test_keyword_injector_validates_kwargs():
    """Unknown kwargs raise ValueError."""
    from svcs_di.injectors import KeywordInjector

    registry = svcs.Registry()
    container = svcs.Container(registry)

    registry.register_value(Database, Database())

    # Get the injector
    injector = KeywordInjector(container=container)

    # Try to pass an unknown kwarg
    with pytest.raises(ValueError, match="unknown_param"):
        injector(DBService, unknown_param="bad")


def test_keyword_injector_container_resolution():
    """Injectable parameters are resolved from container when no kwargs provided."""
    from svcs_di.injectors import KeywordInjector

    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register a database
    db = Database(host="prod", port=5433)
    registry.register_value(Database, db)

    # Get the injector
    injector = KeywordInjector(container=container)

    # Inject without kwargs
    instance = injector(DBService)

    # Should get the database from container
    assert instance.db is db
    assert instance.db.host == "prod"
    assert instance.db.port == 5433


def test_keyword_injector_protocol_injection():
    """Protocol types are resolved using get_abstract()."""
    from svcs_di.injectors import KeywordInjector

    @dataclass
    class ServiceWithProtocol:
        greeter: Injectable[GreeterProtocol]

    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register the protocol implementation
    greeter = ConcreteGreeter()
    registry.register_value(GreeterProtocol, greeter)

    # Get the injector
    injector = KeywordInjector(container=container)

    # Inject
    instance = injector(ServiceWithProtocol)

    # Should get the greeter via get_abstract
    assert instance.greeter is greeter
    assert instance.greeter.greet("World") == "Hello, World!"


def test_keyword_injector_default_fallback():
    """Non-injectable parameters use default values when not overridden."""
    from svcs_di.injectors import KeywordInjector

    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register a database
    registry.register_value(Database, Database())

    # Get the injector
    injector = KeywordInjector(container=container)

    # Create instance - timeout should use default
    instance = injector(DBService)

    assert instance.timeout == 30


async def test_keyword_async_injector_with_mixed_dependencies():
    """Test async injector can handle both sync and async dependencies."""
    import asyncio
    from svcs_di.injectors import KeywordAsyncInjector

    @dataclass
    class SyncDep:
        value: str = "sync"

    @dataclass
    class AsyncDep:
        value: str = "async"

    @dataclass
    class MixedService:
        sync_dep: Injectable[SyncDep]
        async_dep: Injectable[AsyncDep]

    registry = svcs.Registry()

    # Register sync dependency as value
    registry.register_value(SyncDep, SyncDep())

    # Register async dependency with async factory
    async def async_factory():
        await asyncio.sleep(0.001)
        return AsyncDep()

    registry.register_factory(AsyncDep, async_factory)

    async with svcs.Container(registry) as container:
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
    from svcs_di.injectors import KeywordAsyncInjector

    @dataclass
    class SimpleService:
        value: Injectable[Database]
        timeout: int = 10

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod", port=5432))

    async with svcs.Container(registry) as container:
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
