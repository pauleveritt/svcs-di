"""Tests for svcs.auto() factory function."""

import asyncio
import dataclasses
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import pytest
import svcs

from svcs_di import DefaultInjector, Inject, Injector, auto, auto_async
from svcs_di.auto import (
    FieldInfo,
    _create_field_info,
)


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

    db: Inject[Database]
    timeout: int = 30


@dataclass
class NestedService:
    """A service that depends on another service."""

    service: Inject[Service]
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
        greeter: Inject[GreeterProtocol]
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
        db: Inject[Database]
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
        db: Inject[Database]
        name: str = "original"

    def custom_injector_factory(container: svcs.Container) -> CustomInjector:
        return CustomInjector(container=container)

    registry = svcs.Registry()

    # Register custom injector
    registry.register_factory(Injector, custom_injector_factory)

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

    @dataclass
    class SimpleService:
        name: str = "test"

    def injector_factory(container: svcs.Container) -> DefaultInjector:
        return DefaultInjector(container=container)

    registry = svcs.Registry()

    # Register the default injector
    registry.register_factory(Injector, injector_factory)

    # Get the injector from container
    container = svcs.Container(registry)
    injector = container.get(Injector)

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
        config: Inject[Config]

    @dataclass
    class Cache:
        config: Inject[Config]

    @dataclass
    class Repository:
        db: Inject[Database]
        cache: Inject[Cache]

    @dataclass
    class Service:
        repo: Inject[Repository]
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
        service: Inject[CountedService]

    @dataclass
    class Consumer2:
        service: Inject[CountedService]

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
        db: Inject[Database]
        timeout: int = 30

    # Dataclass-based service 2 with different fields
    @dataclass
    class ServiceB:
        db: Inject[Database]
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
        db: Inject[Database]
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


# ============================================================================
# Tests for _create_field_info() helper
# ============================================================================


def test_create_field_info_non_injectable():
    """_create_field_info() handles non-injectable fields."""
    field_info = _create_field_info(
        name="timeout",
        type_hint=int,
        has_default=True,
        default_value=30,
    )

    assert field_info.name == "timeout"
    assert field_info.type_hint is int
    assert field_info.is_injectable is False
    assert field_info.inner_type is None
    assert field_info.is_protocol is False
    assert field_info.has_default is True
    assert field_info.default_value == 30


def test_create_field_info_injectable_concrete():
    """_create_field_info() handles Inject[ConcreteType] fields."""
    field_info = _create_field_info(
        name="db",
        type_hint=Inject[Database],
        has_default=False,
        default_value=None,
    )

    assert field_info.name == "db"
    assert field_info.type_hint == Inject[Database]
    assert field_info.is_injectable is True
    assert field_info.inner_type is Database
    assert field_info.is_protocol is False
    assert field_info.has_default is False
    assert field_info.default_value is None


def test_create_field_info_injectable_protocol():
    """_create_field_info() handles Inject[Protocol] fields."""
    field_info = _create_field_info(
        name="greeter",
        type_hint=Inject[GreeterProtocol],
        has_default=False,
        default_value=None,
    )

    assert field_info.name == "greeter"
    assert field_info.type_hint == Inject[GreeterProtocol]
    assert field_info.is_injectable is True
    assert field_info.inner_type is GreeterProtocol
    assert field_info.is_protocol is True
    assert field_info.has_default is False
    assert field_info.default_value is None


def test_create_field_info_with_default_factory():
    """_create_field_info() handles fields with default_factory."""

    def make_list():
        return []

    field_info = _create_field_info(
        name="items",
        type_hint=list,
        has_default=True,
        default_value=make_list,
    )

    assert field_info.name == "items"
    assert field_info.type_hint is list
    assert field_info.is_injectable is False
    assert field_info.has_default is True
    assert field_info.default_value is make_list


def test_create_field_info_none_type_hint():
    """_create_field_info() handles None type_hint gracefully."""
    field_info = _create_field_info(
        name="unknown",
        type_hint=None,
        has_default=True,
        default_value="default",
    )

    assert field_info.name == "unknown"
    assert field_info.type_hint is None
    assert field_info.is_injectable is False
    assert field_info.inner_type is None
    assert field_info.is_protocol is False
    assert field_info.has_default is True
    assert field_info.default_value == "default"


def test_create_field_info_injectable_with_default():
    """_create_field_info() handles Inject fields that also have defaults."""
    field_info = _create_field_info(
        name="optional_db",
        type_hint=Inject[Database],
        has_default=True,
        default_value=Database(),
    )

    assert field_info.name == "optional_db"
    assert field_info.is_injectable is True
    assert field_info.inner_type is Database
    assert field_info.has_default is True
    assert isinstance(field_info.default_value, Database)


def test_create_field_info_returns_field_info_instance():
    """_create_field_info() returns a FieldInfo instance."""
    result = _create_field_info(
        name="test",
        type_hint=str,
        has_default=False,
        default_value=None,
    )

    assert isinstance(result, FieldInfo)


# ============================================================================
# Tests for default_factory resolution
# ============================================================================


def test_default_factory_list():
    """field(default_factory=list) creates [] not <class 'list'>."""

    @dataclass
    class ServiceWithList:
        db: Inject[Database]
        items: list = field(default_factory=list)

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(ServiceWithList, auto(ServiceWithList))

    container = svcs.Container(registry)
    service = container.get(ServiceWithList)

    assert service.items == []
    assert isinstance(service.items, list)
    assert service.items is not list  # Should be an instance, not the type


def test_default_factory_dict():
    """field(default_factory=dict) creates {} not <class 'dict'>."""

    @dataclass
    class ServiceWithDict:
        db: Inject[Database]
        config: dict = field(default_factory=dict)

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(ServiceWithDict, auto(ServiceWithDict))

    container = svcs.Container(registry)
    service = container.get(ServiceWithDict)

    assert service.config == {}
    assert isinstance(service.config, dict)
    assert service.config is not dict  # Should be an instance, not the type


def test_default_factory_lambda():
    """field(default_factory=lambda: [1, 2, 3]) creates [1, 2, 3]."""

    @dataclass
    class ServiceWithLambda:
        db: Inject[Database]
        values: list = field(default_factory=lambda: [1, 2, 3])

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(ServiceWithLambda, auto(ServiceWithLambda))

    container = svcs.Container(registry)
    service = container.get(ServiceWithLambda)

    assert service.values == [1, 2, 3]
    assert isinstance(service.values, list)


def test_default_factory_creates_new_instances():
    """Each resolution creates a new instance from default_factory (not shared)."""

    @dataclass
    class ServiceWithMutableDefault:
        items: list = field(default_factory=list)

    registry = svcs.Registry()
    registry.register_factory(
        ServiceWithMutableDefault, auto(ServiceWithMutableDefault)
    )

    # Get two instances using separate containers to avoid svcs caching
    container1 = svcs.Container(registry)
    service1 = container1.get(ServiceWithMutableDefault)

    container2 = svcs.Container(registry)
    service2 = container2.get(ServiceWithMutableDefault)

    # Modify one instance's list
    service1.items.append("modified")

    # Other instance should not be affected
    assert service1.items == ["modified"]
    assert service2.items == []
    assert service1.items is not service2.items


def test_default_factory_function():
    """field(default_factory=some_function) calls the function."""

    def make_config():
        return {"env": "test", "debug": True}

    @dataclass
    class ServiceWithFunctionFactory:
        db: Inject[Database]
        config: dict = field(default_factory=make_config)

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(
        ServiceWithFunctionFactory, auto(ServiceWithFunctionFactory)
    )

    container = svcs.Container(registry)
    service = container.get(ServiceWithFunctionFactory)

    assert service.config == {"env": "test", "debug": True}
    assert isinstance(service.config, dict)


# ============================================================================
# Integration tests for default_factory with full DI resolution
# ============================================================================


def test_default_factory_integration_nested_services():
    """Integration test: default_factory works through full DI container resolution."""

    @dataclass
    class Config:
        settings: dict = field(default_factory=dict)

    @dataclass
    class Cache:
        config: Inject[Config]
        entries: list = field(default_factory=list)

    @dataclass
    class Repository:
        cache: Inject[Cache]
        queries: list = field(default_factory=list)

    @dataclass
    class Service:
        repo: Inject[Repository]
        handlers: list = field(default_factory=lambda: ["default_handler"])

    registry = svcs.Registry()
    registry.register_factory(Config, auto(Config))
    registry.register_factory(Cache, auto(Cache))
    registry.register_factory(Repository, auto(Repository))
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    # Verify all default_factory fields were properly resolved
    assert isinstance(service.handlers, list)
    assert service.handlers == ["default_handler"]

    assert isinstance(service.repo.queries, list)
    assert service.repo.queries == []

    assert isinstance(service.repo.cache.entries, list)
    assert service.repo.cache.entries == []

    assert isinstance(service.repo.cache.config.settings, dict)
    assert service.repo.cache.config.settings == {}

    # Verify we can mutate the lists without issues
    service.handlers.append("another_handler")
    service.repo.queries.append("SELECT *")
    service.repo.cache.entries.append({"key": "value"})
    service.repo.cache.config.settings["debug"] = True

    assert service.handlers == ["default_handler", "another_handler"]
    assert service.repo.queries == ["SELECT *"]
    assert service.repo.cache.entries == [{"key": "value"}]
    assert service.repo.cache.config.settings == {"debug": True}


async def test_default_factory_async():
    """default_factory works with async resolution."""

    @dataclass
    class AsyncServiceWithFactory:
        items: list = field(default_factory=list)
        config: dict = field(default_factory=lambda: {"async": True})

    registry = svcs.Registry()

    # Register with async factory
    registry.register_factory(
        AsyncServiceWithFactory, auto_async(AsyncServiceWithFactory)
    )

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncServiceWithFactory)

        assert isinstance(service.items, list)
        assert service.items == []

        assert isinstance(service.config, dict)
        assert service.config == {"async": True}


test_default_factory_async = pytest.mark.anyio(test_default_factory_async)
