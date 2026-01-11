"""Tests to fill critical gaps in function implementations coverage.

These tests supplement the existing tests in:
- tests/injectors/test_decorators.py (6 function tests)
- tests/test_callable_registration.py (9 tests)
- tests/test_function_parameter_injection.py (10 tests)
- tests/test_async_function_factories.py (6 tests)

Maximum 10 additional tests to fill identified critical gaps.

Key architecture notes:
- Function factories are registered for a service type and resolved when that
  type is requested via Inject[T] in another service
- container.inject(T) constructs T using the injector, NOT via locator lookup
- The ServiceLocator is consulted when resolving Inject[T] fields within T
"""

from dataclasses import dataclass

import pytest
import svcs

from svcs_di import DefaultInjector, Inject
from svcs_di.hopscotch_registry import HopscotchContainer, HopscotchRegistry
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.keyword import KeywordInjector
from svcs_di.injectors.scanning import scan


# Test service types
class Greeting:
    """Service type for testing."""

    def __init__(self, message: str = "Hello"):
        self.message = message


class Database:
    """Database service for testing."""

    def __init__(self, host: str = "localhost"):
        self.host = host


class CustomerContext:
    """Resource context for testing."""

    pass


# Wrapper service to test Inject[T] resolution with function factories
@dataclass
class WelcomeService:
    """Service that depends on Greeting via injection."""

    greeting: Inject[Greeting]


@dataclass
class DataService:
    """Service that depends on Database via injection."""

    database: Inject[Database]


# ============================================================================
# Gap 1: End-to-end workflow (decorator -> scan -> Inject[T] resolution)
# ============================================================================


def test_end_to_end_function_factory_via_inject():
    """Test complete workflow: @injectable -> scan -> resolve via Inject[T].

    This verifies the critical user workflow where a function factory
    is registered and then resolved when injecting a dependent service.
    """

    @injectable(for_=Greeting)
    def create_greeting() -> Greeting:
        return Greeting("End-to-end factory")

    # Step 1: Scan to register the function
    registry = HopscotchRegistry()
    scan(registry, locals_dict={"create_greeting": create_greeting})

    # Step 2: Create container and inject a service that depends on Greeting
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)

    # Verify the function factory was invoked via Inject[Greeting]
    assert isinstance(service.greeting, Greeting)
    assert service.greeting.message == "End-to-end factory"


# ============================================================================
# Gap 2: HopscotchContainer with function factory via Inject[T]
# ============================================================================


def test_hopscotch_container_inject_resolves_function_factory_via_inject():
    """Test HopscotchContainer.inject() resolves function factory via Inject[T].

    This tests the integration where a function factory is registered for
    Greeting and resolved when injecting WelcomeService.
    """

    def create_greeting() -> Greeting:
        return Greeting("Hopscotch factory")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, create_greeting)

    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)

    assert isinstance(service.greeting, Greeting)
    assert service.greeting.message == "Hopscotch factory"


@pytest.mark.anyio
async def test_hopscotch_container_ainject_with_async_function_factory():
    """Test HopscotchContainer.ainject() resolves async function factory.

    This tests the integration of async function factories via Inject[T].
    """
    import asyncio

    async def create_async_greeting() -> Greeting:
        await asyncio.sleep(0.001)
        return Greeting("Async Hopscotch factory")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, create_async_greeting)

    container = HopscotchContainer(registry)
    service = await container.ainject(WelcomeService)

    assert isinstance(service.greeting, Greeting)
    assert service.greeting.message == "Async Hopscotch factory"


# ============================================================================
# Gap 3: KeywordInjector with function factory and kwargs override
# ============================================================================


def test_keyword_injector_function_factory_with_kwargs_override():
    """Test KeywordInjector with function factory supports kwargs override.

    This verifies the three-tier precedence (kwargs > container > defaults)
    works correctly with function factories.
    """

    def create_greeting_with_deps(db: Inject[Database]) -> Greeting:
        return Greeting(f"Hello from {db.host}")

    # Register Database
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="container-db"))
    container = svcs.Container(registry)

    # Test with kwargs override
    injector = KeywordInjector(container=container)
    result = injector(create_greeting_with_deps, db=Database(host="override-db"))

    assert isinstance(result, Greeting)
    assert result.message == "Hello from override-db"


# ============================================================================
# Gap 4: Function with no injectable parameters
# ============================================================================


def test_function_factory_with_no_injectable_parameters():
    """Test function factory with no Inject[T] parameters.

    This verifies simple factory functions without dependencies work correctly.
    """

    def create_simple_greeting() -> Greeting:
        return Greeting("Simple factory")

    registry = svcs.Registry()
    container = svcs.Container(registry)

    injector = DefaultInjector(container=container)
    result = injector(create_simple_greeting)

    assert isinstance(result, Greeting)
    assert result.message == "Simple factory"


# ============================================================================
# Gap 5: Function with resource context via Inject[T]
# ============================================================================


def test_function_factory_with_resource_context_via_inject():
    """Test function factory registered with resource context.

    This verifies resource-based multi-implementation resolution works
    correctly with function factories when resolving via Inject[T].

    Note: The resource must be registered in the registry for the injector
    to find it during resolution.
    """

    def create_default_greeting() -> Greeting:
        return Greeting("Default greeting")

    def create_customer_greeting() -> Greeting:
        return Greeting("Welcome, valued customer!")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, create_default_greeting)
    registry.register_implementation(
        Greeting, create_customer_greeting, resource=CustomerContext
    )

    # Register the resource in the registry so injector can find it
    registry.register_value(CustomerContext, CustomerContext())

    container = HopscotchContainer(registry)

    # Default resolution via Inject[Greeting]
    default_service = container.inject(WelcomeService)
    assert default_service.greeting.message == "Default greeting"

    # Resource-based resolution via Inject[Greeting] with resource parameter
    customer_service = container.inject(WelcomeService, resource=CustomerContext)
    assert customer_service.greeting.message == "Welcome, valued customer!"


# ============================================================================
# Gap 6: Function factory called directly via injector
# ============================================================================


def test_function_factory_called_directly_via_injector():
    """Test function factory can be called directly via injector.

    This verifies the injector can call the function factory directly
    without going through Inject[T] resolution.
    """

    def create_greeting() -> Greeting:
        return Greeting("Direct call")

    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = DefaultInjector(container=container)

    # Call the function directly (not via type resolution)
    result = injector(create_greeting)

    assert isinstance(result, Greeting)
    assert result.message == "Direct call"


# ============================================================================
# Gap 7: Function with mixed Inject and default parameters ordering
# ============================================================================


def test_function_factory_with_complex_parameter_ordering():
    """Test function factory with complex parameter ordering.

    This verifies that mixed injectable and non-injectable parameters
    in various positions work correctly.
    """

    def create_complex_greeting(
        prefix: str = "Hello",
        db: Inject[Database] = None,  # type: ignore[assignment]
        suffix: str = "!",
    ) -> Greeting:
        return Greeting(f"{prefix} from {db.host}{suffix}")

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="complex-db"))
    container = svcs.Container(registry)

    injector = DefaultInjector(container=container)
    result = injector(create_complex_greeting)

    assert isinstance(result, Greeting)
    assert result.message == "Hello from complex-db!"


# ============================================================================
# Gap 8: Scan with multiple function factories in same locals
# ============================================================================


def test_scan_multiple_function_factories():
    """Test scanning multiple function factories from same locals dict.

    This verifies that scan() correctly handles multiple decorated
    function factories.
    """

    @injectable(for_=Greeting)
    def create_greeting() -> Greeting:
        return Greeting("First factory")

    @injectable(for_=Database)
    def create_database() -> Database:
        return Database(host="scanned-db")

    registry = HopscotchRegistry()
    scan(
        registry,
        locals_dict={
            "create_greeting": create_greeting,
            "create_database": create_database,
        },
    )

    # Verify both were registered
    greeting_impl = registry.locator.get_implementation(Greeting)
    db_impl = registry.locator.get_implementation(Database)

    assert greeting_impl is create_greeting
    assert db_impl is create_database


# ============================================================================
# Gap 9: Function factory with chained dependencies via Inject[T]
# ============================================================================


def test_function_factory_with_chained_dependencies_via_inject():
    """Test function factory that depends on another function factory.

    This verifies dependency chains work correctly with function factories
    when resolving via Inject[T] in a dependent service.
    """

    @injectable(for_=Database)
    def create_database() -> Database:
        return Database(host="chained-db")

    @injectable(for_=Greeting)
    def create_greeting(db: Inject[Database]) -> Greeting:
        return Greeting(f"Connected to {db.host}")

    registry = HopscotchRegistry()
    scan(
        registry,
        locals_dict={
            "create_database": create_database,
            "create_greeting": create_greeting,
        },
    )

    container = HopscotchContainer(registry)

    # Inject WelcomeService which triggers Inject[Greeting] resolution
    # The Greeting factory depends on Database, so both factories are invoked
    service = container.inject(WelcomeService)

    assert isinstance(service.greeting, Greeting)
    assert service.greeting.message == "Connected to chained-db"
