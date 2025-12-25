"""Tests for svcs.auto() factory function."""

import asyncio
import dataclasses
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pytest
import svcs

from svcs_di.auto import Injectable, auto, auto_async


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
class Service:
    """A service with injectable dependencies."""

    db: Injectable[Database]
    timeout: int = 30


@dataclass
class NestedService:
    """A service that depends on another service."""

    service: Injectable[Service]
    name: str = "nested"


def test_auto_returns_factory():
    """auto() returns a factory function compatible with register_factory()."""
    factory = auto(Service)
    assert callable(factory)


def test_auto_factory_with_registry():
    """Factory returned by auto() works with svcs Registry and Container."""
    registry = svcs.Registry()

    # Register dependencies
    registry.register_value(Database, Database(host="prod", port=5433))

    # Register our service with auto()
    registry.register_factory(Service, auto(Service))

    # Retrieve the service
    container = svcs.Container(registry)
    service = container.get(Service)

    # Verify it was constructed correctly
    assert isinstance(service.db, Database)
    assert service.db.host == "prod"
    assert service.db.port == 5433
    assert service.timeout == 30


def test_auto_factory_end_to_end_injection():
    """End-to-end: multiple services with auto() registration."""
    registry = svcs.Registry()

    # Register base service
    registry.register_value(Database, Database(host="test", port=1234))

    # Register dependent services with auto()
    registry.register_factory(Service, auto(Service))
    registry.register_factory(NestedService, auto(NestedService))

    # Get nested service - should resolve all dependencies
    container = svcs.Container(registry)
    nested = container.get(NestedService)

    assert isinstance(nested, NestedService)
    assert nested.name == "nested"
    assert isinstance(nested.service, Service)
    assert isinstance(nested.service.db, Database)
    assert nested.service.db.host == "test"
    assert nested.service.db.port == 1234


def test_auto_factory_with_protocol():
    """auto() works with protocol-based dependencies."""

    @dataclass
    class ServiceWithProtocol:
        greeter: Injectable[GreeterProtocol]
        name: str = "test"

    registry = svcs.Registry()

    # Register protocol implementation
    registry.register_value(GreeterProtocol, ConcreteGreeter())

    # Register service with protocol dependency
    registry.register_factory(ServiceWithProtocol, auto(ServiceWithProtocol))

    # Get service
    container = svcs.Container(registry)
    service = container.get(ServiceWithProtocol)

    assert isinstance(service.greeter, GreeterProtocol)
    assert service.greeter.greet("World") == "Hello, World!"
    assert service.name == "test"


async def test_auto_factory_async():
    """auto_async() factory works in async contexts with async dependencies."""

    @dataclass
    class AsyncService:
        db: Injectable[Database]
        timeout: int = 30

    registry = svcs.Registry()

    # Register an async factory for Database
    async def db_factory() -> Database:
        await asyncio.sleep(0.001)  # Simulate async work
        return Database(host="async-db", port=9999)

    registry.register_factory(Database, db_factory)

    # Register our service with auto_async()
    registry.register_factory(AsyncService, auto_async(AsyncService))

    # Retrieve the service in async context
    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncService)

        assert isinstance(service, AsyncService)
        assert isinstance(service.db, Database)
        assert service.db.host == "async-db"
        assert service.db.port == 9999
        assert service.timeout == 30


def test_auto_factory_custom_injector():
    """auto() uses custom injector if registered in container."""
    from svcs_di import DefaultInjector

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


def test_get_injector_from_container():
    """Can retrieve the injector directly from the container and use it."""
    from svcs_di import DefaultInjector

    @dataclass
    class SimpleService:
        name: str = "test"

    def injector_factory(container: svcs.Container) -> DefaultInjector:
        return DefaultInjector(container=container)

    registry = svcs.Registry()

    # Register the default injector
    registry.register_factory(DefaultInjector, injector_factory)

    # Get the injector from container
    container = svcs.Container(registry)
    injector = container.get(DefaultInjector)

    # Use the injector directly - kwargs are ignored in DefaultInjector
    service = injector(SimpleService)
    assert service.name == "test"  # Default value is used, kwargs ignored


def test_complex_nested_dependencies():
    """Test complex dependency graph with multiple levels of nesting."""

    @dataclass
    class Config:
        env: str = "production"

    @dataclass
    class Database:
        config: Injectable[Config]

    @dataclass
    class Cache:
        config: Injectable[Config]

    @dataclass
    class Repository:
        db: Injectable[Database]
        cache: Injectable[Cache]

    @dataclass
    class Service:
        repo: Injectable[Repository]
        timeout: int = 30

    registry = svcs.Registry()

    # Register base config
    registry.register_factory(Config, auto(Config))

    # Register intermediate services
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Cache, auto(Cache))

    # Register repository
    registry.register_factory(Repository, auto(Repository))

    # Register top-level service
    registry.register_factory(Service, auto(Service))

    # Get service - should resolve entire dependency tree
    container = svcs.Container(registry)
    service = container.get(Service)

    assert isinstance(service, Service)
    assert service.timeout == 30
    assert isinstance(service.repo, Repository)
    assert isinstance(service.repo.db, Database)
    assert isinstance(service.repo.cache, Cache)
    assert isinstance(service.repo.db.config, Config)
    assert isinstance(service.repo.cache.config, Config)
    assert service.repo.db.config.env == "production"
    assert service.repo.cache.config.env == "production"


def test_service_caching_behavior():
    """Verify that services are properly cached by svcs container."""
    call_count = 0

    @dataclass
    class CountedService:
        value: int = 42

        def __post_init__(self):
            nonlocal call_count
            call_count += 1

    @dataclass
    class Consumer1:
        service: Injectable[CountedService]

    @dataclass
    class Consumer2:
        service: Injectable[CountedService]

    registry = svcs.Registry()
    registry.register_factory(CountedService, auto(CountedService))
    registry.register_factory(Consumer1, auto(Consumer1))
    registry.register_factory(Consumer2, auto(Consumer2))

    container = svcs.Container(registry)

    # Get both consumers
    consumer1 = container.get(Consumer1)
    consumer2 = container.get(Consumer2)

    # CountedService should only be created once (cached)
    assert call_count == 1
    assert consumer1.service is consumer2.service
    assert consumer1.service.value == 42


def test_function_vs_dataclass_injection():
    """Test that both regular functions and dataclasses can be injected."""

    @dataclass
    class Database:
        host: str = "localhost"

    # Dataclass-based service 1
    @dataclass
    class ServiceA:
        db: Injectable[Database]
        timeout: int = 30

    # Dataclass-based service 2 with different fields
    @dataclass
    class ServiceB:
        db: Injectable[Database]
        port: int = 5432

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod"))

    # Test both dataclass patterns
    registry.register_factory(ServiceA, auto(ServiceA))
    registry.register_factory(ServiceB, auto(ServiceB))
    container = svcs.Container(registry)

    service_a = container.get(ServiceA)
    service_b = container.get(ServiceB)

    assert isinstance(service_a.db, Database)
    assert isinstance(service_b.db, Database)
    assert service_a.db.host == "prod"
    assert service_a.timeout == 30
    assert service_b.db.host == "prod"
    assert service_b.port == 5432


def test_missing_required_non_injectable_parameter():
    """Test error when required non-injectable parameter is missing."""

    @dataclass
    class ServiceNeedsValue:
        db: Injectable[Database]
        required_value: str  # No default, not injectable

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(ServiceNeedsValue, auto(ServiceNeedsValue))

    container = svcs.Container(registry)

    # Should raise TypeError because required_value is missing
    with pytest.raises(TypeError):
        container.get(ServiceNeedsValue)


# Use pytest-anyio instead of pytest-asyncio
test_auto_factory_async = pytest.mark.anyio(test_auto_factory_async)
