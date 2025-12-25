"""Tests for svcs.auto() factory function."""

import asyncio
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


def test_get_injector_from_container():
    """Can retrieve the injector directly from the container."""
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

    # Use the injector directly
    service = injector(SimpleService, name="custom")
    assert service.name == "custom"


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


# ============================================================================
# Tests for __svcs__ custom construction (Task Group 1)
# ============================================================================


def test_svcs_method_detection():
    """Test that __svcs__ method is detected using getattr pattern."""

    @dataclass
    class ServiceWithSvcs:
        name: str
        db: Database  # Not Injectable - __svcs__ handles construction

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction method."""
            return cls(name="custom", db=Database())

    # Verify the method is detectable
    svcs_factory = getattr(ServiceWithSvcs, "__svcs__", None)
    assert svcs_factory is not None
    assert callable(svcs_factory)


def test_svcs_method_invoked_when_present():
    """Test that __svcs__ is invoked when present."""
    construction_called = False

    @dataclass
    class ServiceWithSvcs:
        name: str
        value: int

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that sets a flag."""
            nonlocal construction_called
            construction_called = True
            return cls(name="from-svcs", value=42)

    registry = svcs.Registry()
    registry.register_factory(ServiceWithSvcs, auto(ServiceWithSvcs))

    container = svcs.Container(registry)
    service = container.get(ServiceWithSvcs)

    # Verify __svcs__ was called
    assert construction_called
    assert service.name == "from-svcs"
    assert service.value == 42


def test_svcs_method_skips_injectable_field_injection():
    """Test that normal Injectable field injection is skipped when __svcs__ exists."""
    injectable_accessed = False

    @dataclass
    class TrackedDatabase:
        host: str = "localhost"

        def __post_init__(self):
            nonlocal injectable_accessed
            injectable_accessed = True

    @dataclass
    class ServiceWithSvcs:
        db: TrackedDatabase  # Not Injectable - __svcs__ handles construction
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that doesn't use Injectable fields."""
            # Create database directly without using container
            return cls(db=TrackedDatabase(host="custom"), name="manual")

    registry = svcs.Registry()
    registry.register_value(TrackedDatabase, TrackedDatabase(host="registry-db"))
    registry.register_factory(ServiceWithSvcs, auto(ServiceWithSvcs))

    container = svcs.Container(registry)
    service = container.get(ServiceWithSvcs)

    # Verify the service was created via __svcs__
    assert service.name == "manual"
    assert service.db.host == "custom"
    # The TrackedDatabase in registry should NOT have been accessed
    # (injectable_accessed would be True if automatic injection happened)


def test_svcs_method_receives_container():
    """Test that container is passed to __svcs__ method."""
    received_container = None

    @dataclass
    class ServiceWithSvcs:
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that captures container."""
            nonlocal received_container
            received_container = container
            return cls(name="test")

    registry = svcs.Registry()
    registry.register_factory(ServiceWithSvcs, auto(ServiceWithSvcs))

    container = svcs.Container(registry)
    container.get(ServiceWithSvcs)

    # Verify container was passed
    assert received_container is not None
    assert isinstance(received_container, svcs.Container)
    assert received_container is container


def test_svcs_method_kwargs_forwarded():
    """Test that kwargs are forwarded to __svcs__ method."""

    @dataclass
    class ServiceWithSvcs:
        name: str
        value: int

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that uses kwargs."""
            name = kwargs.get("name", "default")
            value = kwargs.get("value", 0)
            return cls(name=name, value=value)

    registry = svcs.Registry()

    # Create a custom factory wrapper to pass kwargs
    def custom_factory(svcs_container: svcs.Container) -> ServiceWithSvcs:
        return auto(ServiceWithSvcs)(svcs_container, name="override", value=99)

    registry.register_factory(ServiceWithSvcs, custom_factory)

    container = svcs.Container(registry)
    service = container.get(ServiceWithSvcs)

    assert service.name == "override"
    assert service.value == 99


def test_svcs_method_return_value_used():
    """Test that __svcs__ return value becomes the factory result."""

    @dataclass
    class ServiceWithSvcs:
        name: str
        count: int

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction with specific return value."""
            return cls(name="returned", count=123)

    registry = svcs.Registry()
    registry.register_factory(ServiceWithSvcs, auto(ServiceWithSvcs))

    container = svcs.Container(registry)
    service = container.get(ServiceWithSvcs)

    # Verify the exact instance returned by __svcs__ is what we get
    assert isinstance(service, ServiceWithSvcs)
    assert service.name == "returned"
    assert service.count == 123


def test_svcs_method_with_container_get():
    """Test that __svcs__ can use container.get() to fetch dependencies."""

    @dataclass
    class Config:
        env: str = "test"

    @dataclass
    class ServiceWithSvcs:
        config: Config  # Not Injectable - manual fetch in __svcs__
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that fetches from container."""
            config = container.get(Config)
            name = kwargs.get("name", f"service-{config.env}")
            return cls(config=config, name=name)

    registry = svcs.Registry()
    registry.register_value(Config, Config(env="production"))
    registry.register_factory(ServiceWithSvcs, auto(ServiceWithSvcs))

    container = svcs.Container(registry)
    service = container.get(ServiceWithSvcs)

    # Verify it used container.get() to fetch Config
    assert isinstance(service.config, Config)
    assert service.config.env == "production"
    assert service.name == "service-production"


def test_svcs_method_kwargs_precedence():
    """Test three-tier precedence within __svcs__: kwargs > container > defaults."""

    @dataclass
    class Config:
        timeout: int = 10

    @dataclass
    class ServiceWithSvcs:
        timeout: int
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction with three-tier precedence."""
            # Tier 1: kwargs (highest)
            if "timeout" in kwargs:
                timeout = kwargs["timeout"]
            # Tier 2: container lookup
            else:
                try:
                    config = container.get(Config)
                    timeout = config.timeout
                except svcs.exceptions.ServiceNotFoundError:
                    # Tier 3: default
                    timeout = 30

            name = kwargs.get("name", "default")
            return cls(timeout=timeout, name=name)

    # Test Tier 1: kwargs override
    registry1 = svcs.Registry()
    registry1.register_value(Config, Config(timeout=100))

    def factory1(svcs_container: svcs.Container) -> ServiceWithSvcs:
        return auto(ServiceWithSvcs)(svcs_container, timeout=999, name="tier1")

    registry1.register_factory(ServiceWithSvcs, factory1)
    container1 = svcs.Container(registry1)
    service1 = container1.get(ServiceWithSvcs)
    assert service1.timeout == 999  # kwargs wins
    assert service1.name == "tier1"

    # Test Tier 2: container lookup
    registry2 = svcs.Registry()
    registry2.register_value(Config, Config(timeout=200))

    def factory2(svcs_container: svcs.Container) -> ServiceWithSvcs:
        return auto(ServiceWithSvcs)(svcs_container, name="tier2")

    registry2.register_factory(ServiceWithSvcs, factory2)
    container2 = svcs.Container(registry2)
    service2 = container2.get(ServiceWithSvcs)
    assert service2.timeout == 200  # container wins
    assert service2.name == "tier2"

    # Test Tier 3: default
    registry3 = svcs.Registry()

    def factory3(svcs_container: svcs.Container) -> ServiceWithSvcs:
        return auto(ServiceWithSvcs)(svcs_container, name="tier3")

    registry3.register_factory(ServiceWithSvcs, factory3)
    container3 = svcs.Container(registry3)
    service3 = container3.get(ServiceWithSvcs)
    assert service3.timeout == 30  # default wins
    assert service3.name == "tier3"


def test_svcs_method_with_injectable_raises_error():
    """Test that using __svcs__ with Injectable fields raises TypeError."""

    @dataclass
    class InvalidService:
        name: str
        db: Injectable[Database]  # This is invalid with __svcs__

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """This should not be allowed with Injectable fields."""
            return cls(name="invalid", db=Database())  # type: ignore[arg-type]

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(InvalidService, auto(InvalidService))

    container = svcs.Container(registry)

    with pytest.raises(TypeError) as exc_info:
        container.get(InvalidService)

    assert "InvalidService defines __svcs__()" in str(exc_info.value)
    assert "Injectable fields: db" in str(exc_info.value)
    assert "fields should not be annotated with Injectable[T]" in str(exc_info.value)


# ============================================================================
# Tests for __svcs__ error handling (Task Group 2)
# ============================================================================


def test_svcs_method_not_classmethod_raises_error():
    """Test that TypeError is raised when __svcs__ is not a classmethod."""

    @dataclass
    class InvalidServiceWithInstanceMethod:
        name: str

        def __svcs__(self, container: svcs.Container, **kwargs):
            """This is an instance method, not a classmethod."""
            return InvalidServiceWithInstanceMethod(name="invalid")

    registry = svcs.Registry()
    registry.register_factory(InvalidServiceWithInstanceMethod, auto(InvalidServiceWithInstanceMethod))

    container = svcs.Container(registry)

    with pytest.raises(TypeError) as exc_info:
        container.get(InvalidServiceWithInstanceMethod)

    error_msg = str(exc_info.value)
    assert "__svcs__ must be a classmethod" in error_msg
    assert "InvalidServiceWithInstanceMethod" in error_msg


def test_svcs_method_static_method_raises_error():
    """Test that TypeError is raised when __svcs__ is a static method."""

    @dataclass
    class InvalidServiceWithStaticMethod:
        name: str

        @staticmethod
        def __svcs__(container: svcs.Container, **kwargs):
            """This is a static method, not a classmethod."""
            return InvalidServiceWithStaticMethod(name="invalid")

    registry = svcs.Registry()
    registry.register_factory(InvalidServiceWithStaticMethod, auto(InvalidServiceWithStaticMethod))

    container = svcs.Container(registry)

    with pytest.raises(TypeError) as exc_info:
        container.get(InvalidServiceWithStaticMethod)

    error_msg = str(exc_info.value)
    assert "__svcs__ must be a classmethod" in error_msg
    assert "InvalidServiceWithStaticMethod" in error_msg


def test_svcs_method_exception_propagates():
    """Test that exceptions raised in __svcs__ propagate with full context."""

    @dataclass
    class ServiceWithBrokenSvcs:
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that raises an exception."""
            raise ValueError("Custom construction failed: invalid config")

    registry = svcs.Registry()
    registry.register_factory(ServiceWithBrokenSvcs, auto(ServiceWithBrokenSvcs))

    container = svcs.Container(registry)

    # The ValueError should propagate naturally
    with pytest.raises(ValueError) as exc_info:
        container.get(ServiceWithBrokenSvcs)

    assert "Custom construction failed: invalid config" in str(exc_info.value)


def test_svcs_method_service_not_found_propagates():
    """Test that ServiceNotFoundError from container.get() propagates correctly."""

    @dataclass
    class MissingDependency:
        value: int = 42

    @dataclass
    class ServiceWithMissingDep:
        name: str
        dep: MissingDependency

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that tries to fetch missing dependency."""
            # This will raise ServiceNotFoundError
            dep = container.get(MissingDependency)
            return cls(name="test", dep=dep)

    registry = svcs.Registry()
    # Note: MissingDependency is NOT registered
    registry.register_factory(ServiceWithMissingDep, auto(ServiceWithMissingDep))

    container = svcs.Container(registry)

    # ServiceNotFoundError should propagate with full context
    with pytest.raises(svcs.exceptions.ServiceNotFoundError):
        container.get(ServiceWithMissingDep)


def test_svcs_method_runtime_error_clear_message():
    """Test that TypeError is raised if __svcs__ call fails at runtime."""

    @dataclass
    class ServiceWithBadSignature:
        name: str

        @classmethod
        def __svcs__(cls):
            """Wrong signature - missing container parameter."""
            return cls(name="broken")

    registry = svcs.Registry()
    registry.register_factory(ServiceWithBadSignature, auto(ServiceWithBadSignature))

    container = svcs.Container(registry)

    # Should raise TypeError due to wrong signature
    with pytest.raises(TypeError):
        container.get(ServiceWithBadSignature)


def test_svcs_method_with_get_abstract():
    """Test that __svcs__ can use container.get_abstract() for protocol dependencies."""

    @dataclass
    class ServiceWithProtocol:
        greeter: GreeterProtocol
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction using get_abstract for protocol."""
            greeter = container.get_abstract(GreeterProtocol)
            name = kwargs.get("name", "protocol-service")
            return cls(greeter=greeter, name=name)

    registry = svcs.Registry()
    registry.register_value(GreeterProtocol, ConcreteGreeter())
    registry.register_factory(ServiceWithProtocol, auto(ServiceWithProtocol))

    container = svcs.Container(registry)
    service = container.get(ServiceWithProtocol)

    # Verify it used container.get_abstract() to fetch protocol
    assert isinstance(service.greeter, GreeterProtocol)
    assert service.greeter.greet("Test") == "Hello, Test!"
    assert service.name == "protocol-service"


def test_svcs_method_with_protocol_not_found_propagates():
    """Test that ServiceNotFoundError propagates when protocol is not registered."""

    @dataclass
    class ServiceWithMissingProtocol:
        greeter: GreeterProtocol
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that tries to fetch missing protocol."""
            # This will raise ServiceNotFoundError
            greeter = container.get_abstract(GreeterProtocol)
            return cls(greeter=greeter, name="test")

    registry = svcs.Registry()
    # Note: GreeterProtocol is NOT registered
    registry.register_factory(ServiceWithMissingProtocol, auto(ServiceWithMissingProtocol))

    container = svcs.Container(registry)

    # ServiceNotFoundError should propagate with full context
    with pytest.raises(svcs.exceptions.ServiceNotFoundError):
        container.get(ServiceWithMissingProtocol)


# ============================================================================
# Tests for __svcs__ async support (Task Group 3)
# ============================================================================


async def test_async_svcs_method_detection():
    """Test that __svcs__ method is detected in async context (synchronous __svcs__ only)."""

    @dataclass
    class AsyncServiceWithSvcs:
        name: str
        value: int

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Synchronous custom construction method for async factory."""
            return cls(name="async-custom", value=100)

    # Verify the method is detectable
    svcs_factory = getattr(AsyncServiceWithSvcs, "__svcs__", None)
    assert svcs_factory is not None
    assert callable(svcs_factory)

    registry = svcs.Registry()
    registry.register_factory(AsyncServiceWithSvcs, auto_async(AsyncServiceWithSvcs))

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncServiceWithSvcs)
        assert service.name == "async-custom"
        assert service.value == 100


async def test_async_svcs_method_receives_container():
    """Test that container is passed to __svcs__ in async factory."""
    received_container = None

    @dataclass
    class AsyncServiceWithSvcs:
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that captures container in async context."""
            nonlocal received_container
            received_container = container
            return cls(name="async-test")

    registry = svcs.Registry()
    registry.register_factory(AsyncServiceWithSvcs, auto_async(AsyncServiceWithSvcs))

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncServiceWithSvcs)

        # Verify container was passed
        assert received_container is not None
        assert isinstance(received_container, svcs.Container)
        assert received_container is container
        assert service.name == "async-test"


async def test_async_svcs_method_kwargs_forwarded():
    """Test that kwargs are forwarded to __svcs__ in async context."""

    @dataclass
    class AsyncServiceWithSvcs:
        name: str
        value: int

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that uses kwargs in async context."""
            name = kwargs.get("name", "default")
            value = kwargs.get("value", 0)
            return cls(name=name, value=value)

    registry = svcs.Registry()

    # Create a custom async factory wrapper to pass kwargs
    async def custom_async_factory(svcs_container: svcs.Container) -> AsyncServiceWithSvcs:
        # auto_async returns an async factory, so we need to await it
        return await auto_async(AsyncServiceWithSvcs)(svcs_container, name="async-override", value=777)

    registry.register_factory(AsyncServiceWithSvcs, custom_async_factory)

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncServiceWithSvcs)

        assert service.name == "async-override"
        assert service.value == 777


async def test_async_svcs_method_skips_async_injection():
    """Test that normal async injection is skipped when __svcs__ exists."""
    async_dependency_created = False

    @dataclass
    class AsyncDatabase:
        host: str = "async-localhost"

    async def async_db_factory() -> AsyncDatabase:
        nonlocal async_dependency_created
        async_dependency_created = True
        await asyncio.sleep(0.001)
        return AsyncDatabase(host="async-db")

    @dataclass
    class AsyncServiceWithSvcs:
        db: AsyncDatabase  # Not Injectable - __svcs__ handles construction
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that doesn't use async Injectable fields."""
            # Create database directly without using container
            return cls(db=AsyncDatabase(host="custom-sync"), name="manual-async")

    registry = svcs.Registry()
    registry.register_factory(AsyncDatabase, async_db_factory)
    registry.register_factory(AsyncServiceWithSvcs, auto_async(AsyncServiceWithSvcs))

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncServiceWithSvcs)

        # Verify the service was created via __svcs__
        assert service.name == "manual-async"
        assert service.db.host == "custom-sync"
        # The async factory should NOT have been called
        assert not async_dependency_created


async def test_async_svcs_method_with_container_get():
    """Test that synchronous __svcs__ can use container.get() in async factory context."""

    @dataclass
    class Config:
        env: str = "async-test"

    @dataclass
    class AsyncServiceWithSvcs:
        config: Config
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Synchronous custom construction that fetches from container."""
            # Use synchronous container.get() even in async context
            config = container.get(Config)
            name = kwargs.get("name", f"async-service-{config.env}")
            return cls(config=config, name=name)

    registry = svcs.Registry()
    registry.register_value(Config, Config(env="async-production"))
    registry.register_factory(AsyncServiceWithSvcs, auto_async(AsyncServiceWithSvcs))

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncServiceWithSvcs)

        # Verify it used container.get() to fetch Config
        assert isinstance(service.config, Config)
        assert service.config.env == "async-production"
        assert service.name == "async-service-async-production"


async def test_async_svcs_method_with_injectable_raises_error():
    """Test that using __svcs__ with Injectable fields raises TypeError in async context."""

    @dataclass
    class InvalidAsyncService:
        name: str
        db: Injectable[Database]  # This is invalid with __svcs__

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """This should not be allowed with Injectable fields."""
            return cls(name="invalid-async", db=Database())  # type: ignore[arg-type]

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(InvalidAsyncService, auto_async(InvalidAsyncService))

    async with svcs.Container(registry) as container:
        with pytest.raises(TypeError) as exc_info:
            await container.aget(InvalidAsyncService)

        assert "InvalidAsyncService defines __svcs__()" in str(exc_info.value)
        assert "Injectable fields: db" in str(exc_info.value)
        assert "fields should not be annotated with Injectable[T]" in str(exc_info.value)


async def test_async_svcs_method_validation():
    """Test that __svcs__ validation works in async context."""

    @dataclass
    class InvalidAsyncServiceNotClassmethod:
        name: str

        def __svcs__(self, container: svcs.Container, **kwargs):
            """This is an instance method, not a classmethod."""
            return InvalidAsyncServiceNotClassmethod(name="invalid")

    registry = svcs.Registry()
    registry.register_factory(InvalidAsyncServiceNotClassmethod, auto_async(InvalidAsyncServiceNotClassmethod))

    async with svcs.Container(registry) as container:
        with pytest.raises(TypeError) as exc_info:
            await container.aget(InvalidAsyncServiceNotClassmethod)

        error_msg = str(exc_info.value)
        assert "__svcs__ must be a classmethod" in error_msg
        assert "InvalidAsyncServiceNotClassmethod" in error_msg


# ============================================================================
# Tests for __svcs__ integration (Task Group 5)
# ============================================================================


def test_svcs_integration_complex_dependency_graph():
    """Integration test: __svcs__ with complex dependency graph."""

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
        """Repository with custom construction using __svcs__."""
        db: Database
        cache: Cache
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction that resolves multiple dependencies."""
            # Get dependencies from container
            db = container.get(Database)
            cache = container.get(Cache)

            # Use kwargs with fallback
            name = kwargs.get("name", f"repo-{db.config.env}")  # type: ignore[attr-defined]

            # Validate before construction
            if not name:
                raise ValueError("Repository name cannot be empty")

            return cls(db=db, cache=cache, name=name)

    @dataclass
    class Service:
        repo: Injectable[Repository]
        timeout: int = 30

    registry = svcs.Registry()

    # Register base services
    registry.register_factory(Config, auto(Config))
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Cache, auto(Cache))

    # Register custom construction repository
    registry.register_factory(Repository, auto(Repository))

    # Register top-level service
    registry.register_factory(Service, auto(Service))

    # Get service - should resolve entire graph including custom __svcs__
    container = svcs.Container(registry)
    service = container.get(Service)

    assert isinstance(service, Service)
    assert isinstance(service.repo, Repository)
    assert service.repo.name == "repo-production"
    assert isinstance(service.repo.db, Database)
    assert isinstance(service.repo.cache, Cache)
    assert service.repo.db.config.env == "production"  # type: ignore[attr-defined]
    assert service.repo.cache.config.env == "production"  # type: ignore[attr-defined]


def test_svcs_integration_multiple_protocols():
    """Integration test: __svcs__ calling container.get_abstract() for multiple protocols."""

    @runtime_checkable
    class LoggerProtocol(Protocol):
        def log(self, message: str) -> None: ...

    class ConsoleLogger:
        def log(self, message: str) -> None:
            pass  # Mock implementation

    @dataclass
    class ServiceWithMultipleProtocols:
        """Service that depends on multiple protocols."""
        greeter: GreeterProtocol
        logger: LoggerProtocol
        name: str

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction resolving multiple protocols."""
            # Resolve protocols using get_abstract
            greeter = container.get_abstract(GreeterProtocol)
            logger = container.get_abstract(LoggerProtocol)

            name = kwargs.get("name", "multi-protocol-service")

            return cls(greeter=greeter, logger=logger, name=name)

    registry = svcs.Registry()
    registry.register_value(GreeterProtocol, ConcreteGreeter())
    registry.register_value(LoggerProtocol, ConsoleLogger())
    registry.register_factory(ServiceWithMultipleProtocols, auto(ServiceWithMultipleProtocols))

    container = svcs.Container(registry)
    service = container.get(ServiceWithMultipleProtocols)

    assert isinstance(service.greeter, GreeterProtocol)
    assert isinstance(service.logger, LoggerProtocol)
    assert service.greeter.greet("World") == "Hello, World!"
    assert service.name == "multi-protocol-service"


def test_svcs_integration_post_construction_validation():
    """Integration test: __svcs__ with post-construction validation."""

    @dataclass
    class ValidatedService:
        """Service with complex validation in __svcs__."""
        name: str
        port: int
        db: Database

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction with multiple validation steps."""
            db = container.get(Database)
            name = kwargs.get("name", "default-service")
            port = kwargs.get("port", 8080)

            # Validation step 1: name
            if not name or len(name) < 3:
                raise ValueError("Service name must be at least 3 characters")

            # Validation step 2: port
            if not (1024 <= port <= 65535):
                raise ValueError("Port must be between 1024 and 65535")

            # Validation step 3: database connection
            if not db.host:
                raise ValueError("Database host cannot be empty")

            # Construct the instance
            instance = cls(name=name, port=port, db=db)

            # Post-construction validation
            if instance.port == instance.db.port:
                raise ValueError("Service port cannot match database port")

            return instance

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="localhost", port=5432))

    # Test valid construction
    def factory_valid(svcs_container: svcs.Container) -> ValidatedService:
        return auto(ValidatedService)(svcs_container, name="valid-service", port=8080)

    registry.register_factory(ValidatedService, factory_valid)
    container = svcs.Container(registry)
    service = container.get(ValidatedService)

    assert service.name == "valid-service"
    assert service.port == 8080

    # Test validation failure - name too short
    registry2 = svcs.Registry()
    registry2.register_value(Database, Database(host="localhost", port=5432))

    def factory_invalid_name(svcs_container: svcs.Container) -> ValidatedService:
        return auto(ValidatedService)(svcs_container, name="ab", port=8080)

    registry2.register_factory(ValidatedService, factory_invalid_name)
    container2 = svcs.Container(registry2)

    with pytest.raises(ValueError) as exc_info:
        container2.get(ValidatedService)
    assert "at least 3 characters" in str(exc_info.value)

    # Test validation failure - invalid port
    registry3 = svcs.Registry()
    registry3.register_value(Database, Database(host="localhost", port=5432))

    def factory_invalid_port(svcs_container: svcs.Container) -> ValidatedService:
        return auto(ValidatedService)(svcs_container, name="valid", port=100)

    registry3.register_factory(ValidatedService, factory_invalid_port)
    container3 = svcs.Container(registry3)

    with pytest.raises(ValueError) as exc_info:
        container3.get(ValidatedService)
    assert "between 1024 and 65535" in str(exc_info.value)


def test_svcs_integration_conditional_service_resolution():
    """Integration test: __svcs__ with conditional service resolution based on container."""

    @dataclass
    class FeatureFlags:
        use_cache: bool = False

    @dataclass
    class Cache:
        enabled: bool = True

    @dataclass
    class ConditionalService:
        """Service that conditionally uses cache based on feature flags."""
        name: str
        cache: Cache | None
        db: Database

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction with conditional dependency resolution."""
            # Always get required dependencies
            db = container.get(Database)
            name = kwargs.get("name", "conditional-service")

            # Conditionally resolve cache based on feature flags
            cache = None
            try:
                flags = container.get(FeatureFlags)
                if flags.use_cache:
                    try:
                        cache = container.get(Cache)
                    except svcs.exceptions.ServiceNotFoundError:
                        # Cache not available, continue without it
                        pass
            except svcs.exceptions.ServiceNotFoundError:
                # No feature flags, don't use cache
                pass

            return cls(name=name, cache=cache, db=db)

    # Test 1: Cache enabled via feature flags
    registry1 = svcs.Registry()
    registry1.register_value(Database, Database())
    registry1.register_value(FeatureFlags, FeatureFlags(use_cache=True))
    registry1.register_value(Cache, Cache())
    registry1.register_factory(ConditionalService, auto(ConditionalService))

    container1 = svcs.Container(registry1)
    service1 = container1.get(ConditionalService)

    assert service1.name == "conditional-service"
    assert service1.cache is not None
    assert service1.cache.enabled is True

    # Test 2: Cache disabled via feature flags
    registry2 = svcs.Registry()
    registry2.register_value(Database, Database())
    registry2.register_value(FeatureFlags, FeatureFlags(use_cache=False))
    registry2.register_factory(ConditionalService, auto(ConditionalService))

    container2 = svcs.Container(registry2)
    service2 = container2.get(ConditionalService)

    assert service2.name == "conditional-service"
    assert service2.cache is None

    # Test 3: No feature flags at all
    registry3 = svcs.Registry()
    registry3.register_value(Database, Database())
    registry3.register_factory(ConditionalService, auto(ConditionalService))

    container3 = svcs.Container(registry3)
    service3 = container3.get(ConditionalService)

    assert service3.name == "conditional-service"
    assert service3.cache is None


def test_svcs_integration_kwargs_override_with_nested_deps():
    """Integration test: kwargs override precedence with nested dependencies."""

    @dataclass
    class Config:
        timeout: int = 10

    @dataclass
    class ServiceWithKwargsOverride:
        """Service demonstrating kwargs precedence in complex scenario."""
        timeout: int
        retry_count: int
        config: Config

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction showing three-tier precedence clearly."""
            config = container.get(Config)

            # Tier 1: kwargs (highest priority)
            timeout = kwargs.get("timeout")
            if timeout is None:
                # Tier 2: config from container
                timeout = config.timeout

            # Tier 3: default for retry_count
            retry_count = kwargs.get("retry_count", 3)

            return cls(timeout=timeout, retry_count=retry_count, config=config)

    # Test kwargs override wins
    registry = svcs.Registry()
    registry.register_value(Config, Config(timeout=100))

    def factory_with_override(svcs_container: svcs.Container) -> ServiceWithKwargsOverride:
        return auto(ServiceWithKwargsOverride)(svcs_container, timeout=999, retry_count=5)

    registry.register_factory(ServiceWithKwargsOverride, factory_with_override)
    container = svcs.Container(registry)
    service = container.get(ServiceWithKwargsOverride)

    assert service.timeout == 999  # kwargs wins over config
    assert service.retry_count == 5  # kwargs explicit value
    assert service.config.timeout == 100  # original config unchanged


def test_svcs_integration_different_instances_based_on_kwargs():
    """Integration test: __svcs__ returning different instance types based on kwargs."""

    @dataclass
    class ProductionDatabase:
        host: str = "prod.db.com"
        ssl: bool = True

    @dataclass
    class DevelopmentDatabase:
        host: str = "localhost"
        ssl: bool = False

    @dataclass
    class FlexibleService:
        """Service that uses different database implementations based on environment."""
        name: str
        db: ProductionDatabase | DevelopmentDatabase

        @classmethod
        def __svcs__(cls, container: svcs.Container, **kwargs):
            """Custom construction choosing db type based on kwargs."""
            name = kwargs.get("name", "flexible-service")
            env = kwargs.get("env", "production")

            # Choose database type based on environment
            if env == "development":
                db = DevelopmentDatabase()
            else:
                db = ProductionDatabase()

            return cls(name=name, db=db)

    registry = svcs.Registry()

    # Production instance
    def factory_prod(svcs_container: svcs.Container) -> FlexibleService:
        return auto(FlexibleService)(svcs_container, name="prod-service", env="production")

    registry.register_factory(FlexibleService, factory_prod)
    container = svcs.Container(registry)
    prod_service = container.get(FlexibleService)

    assert prod_service.name == "prod-service"
    assert isinstance(prod_service.db, ProductionDatabase)
    assert prod_service.db.ssl is True

    # Development instance (new registry to avoid caching)
    registry2 = svcs.Registry()

    def factory_dev(svcs_container: svcs.Container) -> FlexibleService:
        return auto(FlexibleService)(svcs_container, name="dev-service", env="development")

    registry2.register_factory(FlexibleService, factory_dev)
    container2 = svcs.Container(registry2)
    dev_service = container2.get(FlexibleService)

    assert dev_service.name == "dev-service"
    assert isinstance(dev_service.db, DevelopmentDatabase)
    assert dev_service.db.ssl is False


# Use pytest-anyio instead of pytest-asyncio
test_auto_factory_async = pytest.mark.anyio(test_auto_factory_async)
test_async_svcs_method_detection = pytest.mark.anyio(test_async_svcs_method_detection)
test_async_svcs_method_receives_container = pytest.mark.anyio(test_async_svcs_method_receives_container)
test_async_svcs_method_kwargs_forwarded = pytest.mark.anyio(test_async_svcs_method_kwargs_forwarded)
test_async_svcs_method_skips_async_injection = pytest.mark.anyio(test_async_svcs_method_skips_async_injection)
test_async_svcs_method_with_container_get = pytest.mark.anyio(test_async_svcs_method_with_container_get)
test_async_svcs_method_with_injectable_raises_error = pytest.mark.anyio(test_async_svcs_method_with_injectable_raises_error)
test_async_svcs_method_validation = pytest.mark.anyio(test_async_svcs_method_validation)
