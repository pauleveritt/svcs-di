"""Tests for Injector protocol and default implementation."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pytest
import svcs

from svcs_di import DefaultInjector, Injectable
from svcs_di.auto import auto


@runtime_checkable
class GreeterProtocol(Protocol):
    """A protocol for testing."""

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


def test_injector_kwarg_precedence():
    """Kwargs override everything, including injectable parameters."""
    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register a database
    registry.register_value(Database, Database(host="prod", port=5433))

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # But override it with kwargs
    custom_db = Database(host="test", port=1234)
    instance = injector(DBService, db=custom_db)

    # The kwarg should override the container value
    assert isinstance(instance.db, Database)
    assert instance.db.host == "test"
    assert instance.db.port == 1234


def test_injector_container_resolution():
    """Injectable parameters are resolved from container."""
    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register a database
    db = Database(host="prod", port=5433)
    registry.register_value(Database, db)

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # Inject without kwargs
    instance = injector(DBService)

    # Should get the database from container
    assert instance.db is db
    assert instance.db.host == "prod"
    assert instance.db.port == 5433


def test_injector_default_fallback():
    """Non-injectable parameters use default values."""
    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register a database
    registry.register_value(Database, Database())

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # Create instance - timeout should use default
    instance = injector(DBService)

    assert instance.timeout == 30


def test_injector_protocol_uses_get_abstract():
    """Protocol types use get_abstract() method."""

    @dataclass
    class ServiceWithProtocol:
        greeter: Injectable[GreeterProtocol]

    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Register the protocol implementation
    greeter = ConcreteGreeter()
    registry.register_value(GreeterProtocol, greeter)

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # Inject
    instance = injector(ServiceWithProtocol)

    # Should get the greeter via get_abstract
    assert instance.greeter is greeter
    assert instance.greeter.greet("World") == "Hello, World!"


def test_injector_validates_kwargs():
    """Unknown kwargs raise ValueError."""
    registry = svcs.Registry()
    container = svcs.Container(registry)

    registry.register_value(Database, Database())

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # Try to pass an unknown kwarg
    with pytest.raises(ValueError, match="unknown_param"):
        injector(DBService, unknown_param="bad")


def test_injector_propagates_service_not_found():
    """ServiceNotFoundError from container propagates as-is."""
    registry = svcs.Registry()
    container = svcs.Container(registry)

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # Don't register Database - should raise ServiceNotFoundError
    with pytest.raises(svcs.exceptions.ServiceNotFoundError):
        injector(DBService)


def test_injector_kwargs_override_defaults():
    """Kwargs override default values for non-injectable parameters."""
    registry = svcs.Registry()
    container = svcs.Container(registry)

    registry.register_value(Database, Database())

    # Get the injector from factory
    injector = DefaultInjector(container=container)

    # Override the default timeout
    instance = injector(DBService, timeout=60)

    assert instance.timeout == 60


async def test_async_injector_with_mixed_dependencies():
    """Test async injector can handle both sync and async dependencies."""
    import asyncio
    from svcs_di import DefaultAsyncInjector

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
        injector = DefaultAsyncInjector(container=container)

        # Create service with mixed dependencies
        service = await injector(MixedService)

        assert isinstance(service.sync_dep, SyncDep)
        assert isinstance(service.async_dep, AsyncDep)
        assert service.sync_dep.value == "sync"
        assert service.async_dep.value == "async"


def test_custom_injector_with_auto():
    """auto() uses custom injector if registered in container."""
    import dataclasses

    # Create a custom injector that adds a prefix to string fields
    @dataclasses.dataclass
    class CustomInjector:
        container: svcs.Container

        def __call__(self, target, **kwargs):
            # Use default logic
            default_injector = DefaultInjector(container=self.container)
            instance = default_injector(target, **kwargs)
            # Custom behavior: modify the instance
            if hasattr(instance, "name"):
                instance.name = f"CUSTOM-{instance.name}"
            return instance

    @dataclass
    class ServiceWithName:
        db: Injectable[Database]
        name: str = "original"

    def custom_injector_factory(container: svcs.Container) -> CustomInjector:
        return CustomInjector(container=container)

    registry = svcs.Registry()

    # Register custom injector
    registry.register_factory(DefaultInjector, custom_injector_factory)

    # Register dependencies
    registry.register_value(Database, Database())

    # Register service with auto()
    registry.register_factory(ServiceWithName, auto(ServiceWithName))

    # Get service
    container = svcs.Container(registry)
    service = container.get(ServiceWithName)

    # Custom injector should have modified the name
    assert service.name == "CUSTOM-original"


# Use pytest-anyio for async tests
test_async_injector_with_mixed_dependencies = pytest.mark.anyio(
    test_async_injector_with_mixed_dependencies
)


# ============================================================================
# Protocol validation tests
# ============================================================================


class FakeGreeter:
    """A class that doesn't match the protocol - missing greet method."""

    pass


def test_protocol_based_injection_with_runtime_check():
    """Protocol-based injection works with runtime validation."""

    @dataclass
    class ServiceWithProtocol:
        greeter: Injectable[GreeterProtocol]

    registry = svcs.Registry()
    greeter = ConcreteGreeter()

    # Verify the greeter matches the protocol at runtime
    assert isinstance(greeter, GreeterProtocol)

    # Register and inject
    registry.register_value(GreeterProtocol, greeter)
    registry.register_factory(ServiceWithProtocol, auto(ServiceWithProtocol))

    container = svcs.Container(registry)
    service = container.get(ServiceWithProtocol)

    # The injected greeter should match the protocol
    assert isinstance(service.greeter, GreeterProtocol)
    assert service.greeter.greet("Test") == "Hello, Test!"


def test_protocol_validation_fails_for_incompatible_type():
    """Ensure incompatible objects fail protocol validation."""

    @dataclass
    class ServiceWithProtocol:
        greeter: Injectable[GreeterProtocol]

    registry = svcs.Registry()

    # Register an incompatible type
    fake = FakeGreeter()
    registry.register_value(GreeterProtocol, fake)
    registry.register_factory(ServiceWithProtocol, auto(ServiceWithProtocol))

    container = svcs.Container(registry)
    service = container.get(ServiceWithProtocol)

    # The service will have the fake, but it doesn't match the protocol
    assert not isinstance(service.greeter, GreeterProtocol)
