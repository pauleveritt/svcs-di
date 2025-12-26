"""Tests for ServiceLocator and HopscotchInjector - single locator for all service types."""

from dataclasses import dataclass

import pytest
import svcs

from svcs_di.auto import Injectable
from svcs_di.injectors.locator import (
    FactoryRegistration,
    HopscotchAsyncInjector,
    HopscotchInjector,
    ServiceLocator,
    get_from_locator,
)


# Test fixtures - different greetings
@dataclass
class DefaultGreeting:
    salutation: str = "Good Day"


@dataclass
class CustomerGreeting:
    salutation: str = "Hello"


@dataclass
class EmployeeGreeting:
    salutation: str = "Wassup"


# Test fixtures - different databases
@dataclass
class PostgresDB:
    name: str = "postgres"


@dataclass
class TestDatabase:
    name: str = "test"


# Context classes
class CustomerContext:
    pass


class EmployeeContext:
    pass


class AdminContext(EmployeeContext):
    """Subclass of EmployeeContext for testing inheritance."""

    pass


class TestContext:
    pass


# Protocols
class Greeting:
    salutation: str


class Database:
    name: str


# ============================================================================
# Task 1.1: New tests for resource terminology
# ============================================================================


def test_factory_registration_with_resource_parameter():
    """Test FactoryRegistration with resource parameter instead of context."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=EmployeeGreeting, resource=EmployeeContext
    )
    assert reg.resource == EmployeeContext
    assert reg.matches(EmployeeContext) == 2  # Exact match


def test_service_locator_register_with_resource_parameter():
    """Test ServiceLocator.register() with resource parameter."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    assert len(locator.registrations) == 1
    assert locator.registrations[0].resource == EmployeeContext


def test_service_locator_get_implementation_with_resource_parameter():
    """Test ServiceLocator.get_implementation() with resource parameter."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting, resource=None)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    impl = locator.get_implementation(Greeting, resource=EmployeeContext)
    assert impl == EmployeeGreeting


def test_get_from_locator_with_resource_parameter(registry):
    """Test get_from_locator() with resource parameter."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting, resource=None)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    greeting = get_from_locator(container, Greeting, resource=EmployeeContext)
    assert isinstance(greeting, EmployeeGreeting)


def test_backwards_compatibility_not_required():
    """Verify that old 'context' parameter is NOT supported (pre-1.0 breaking change)."""
    # This test verifies we intentionally removed backwards compatibility
    # If someone tries to use context=, it should raise TypeError
    locator = ServiceLocator()

    with pytest.raises(TypeError):
        locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)  # type: ignore[call-arg]


# ============================================================================
# Original tests - updated for resource terminology
# ============================================================================


def test_factory_registration_matches_no_resource():
    """Test matching with no resource (default)."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=DefaultGreeting, resource=None
    )
    assert reg.matches(None) == 0  # Default match


def test_factory_registration_matches_exact():
    """Test exact resource match (highest priority)."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=EmployeeGreeting, resource=EmployeeContext
    )
    assert reg.matches(EmployeeContext) == 2  # Exact match


def test_factory_registration_matches_subclass():
    """Test subclass resource match (medium priority)."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=EmployeeGreeting, resource=EmployeeContext
    )
    assert reg.matches(AdminContext) == 1  # Subclass match


def test_factory_registration_no_match():
    """Test when resource doesn't match."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=EmployeeGreeting, resource=EmployeeContext
    )
    assert reg.matches(CustomerContext) == -1  # No match


def test_service_locator_register_single_type():
    """Test registering implementation classes for a single service type."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, CustomerGreeting, resource=CustomerContext)

    assert len(locator.registrations) == 2
    # Most recent first (LIFO)
    assert locator.registrations[0].implementation == CustomerGreeting
    assert locator.registrations[1].implementation == DefaultGreeting


def test_service_locator_register_multiple_types():
    """Test registering factories for multiple service types in ONE locator."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Database, PostgresDB)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Database, TestDatabase, resource=TestContext)

    assert len(locator.registrations) == 4
    # Verify all types are tracked
    service_types = {reg.service_type for reg in locator.registrations}
    assert service_types == {Greeting, Database}


def test_service_locator_get_implementation_default():
    """Test getting default implementation (no resource) from single locator."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Database, PostgresDB)

    greeting_impl = locator.get_implementation(Greeting, None)
    assert greeting_impl == DefaultGreeting

    db_impl = locator.get_implementation(Database, None)
    assert db_impl == PostgresDB


def test_service_locator_get_implementation_exact_match():
    """Test getting implementation with exact resource match."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    impl = locator.get_implementation(Greeting, EmployeeContext)
    assert impl == EmployeeGreeting


def test_service_locator_isolates_service_types():
    """Test that service types are properly isolated in single locator."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Database, PostgresDB)
    locator = locator.register(Database, TestDatabase, resource=TestContext)

    # Greeting lookups don't interfere with Database
    assert locator.get_implementation(Greeting, None) == DefaultGreeting
    assert locator.get_implementation(Greeting, EmployeeContext) == EmployeeGreeting
    assert locator.get_implementation(Database, None) == PostgresDB
    assert locator.get_implementation(Database, TestContext) == TestDatabase


def test_get_from_locator_single_locator(registry):
    """Test get_from_locator with ServiceLocator registered in registry."""
    # ONE locator registered as a service
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Database, PostgresDB)
    locator = locator.register(Database, TestDatabase, resource=TestContext)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)

    # Get greetings
    greeting = get_from_locator(container, Greeting)
    assert isinstance(greeting, DefaultGreeting)

    greeting = get_from_locator(container, Greeting, resource=EmployeeContext)
    assert isinstance(greeting, EmployeeGreeting)

    # Get databases
    db = get_from_locator(container, Database)
    assert isinstance(db, PostgresDB)

    db = get_from_locator(container, Database, resource=TestContext)
    assert isinstance(db, TestDatabase)


def test_get_from_locator_no_implementation_raises(registry):
    """Test that LookupError is raised when no implementation matches."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)

    with pytest.raises(LookupError, match="No implementation found"):
        get_from_locator(container, Greeting, resource=CustomerContext)


def test_system_site_override_without_resource(registry):
    """Test that site registration overrides system registration via LIFO (no resource needed)."""

    # Define system-level and site-level implementations
    @dataclass
    class SystemGreeting:
        salutation: str = "System Default"

    @dataclass
    class SiteGreeting:
        salutation: str = "Site Override"

    # Setup: System registers default first
    locator = ServiceLocator()
    locator = locator.register(Greeting, SystemGreeting)  # System default

    # Then site overrides (LIFO = most recent wins)
    locator = locator.register(Greeting, SiteGreeting)  # Site override

    registry.register_value(ServiceLocator, locator)
    container = svcs.Container(registry)

    # Site override should be used (LIFO - latest registration wins)
    greeting = get_from_locator(container, Greeting)
    assert isinstance(greeting, SiteGreeting)
    assert greeting.salutation == "Site Override"


@pytest.fixture
def registry():
    """Create a fresh svcs.Registry for each test."""
    return svcs.Registry()


# ============================================================================
# HopscotchInjector Tests - Injectable[T] with locator support
# ============================================================================


class RequestContext:
    """Base context for request-scoped services."""

    pass


class EmployeeRequestContext(RequestContext):
    """Context for employee requests."""

    pass


class CustomerRequestContext(RequestContext):
    """Context for customer requests."""

    pass


def test_hopscotch_injector_with_injectable_no_locator(registry):
    """Test HopscotchInjector falls back to container.get when no locator is registered."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    # Register a single greeting implementation using register_value
    registry.register_value(Greeting, DefaultGreeting())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, DefaultGreeting)


def test_hopscotch_injector_with_locator_no_context(registry):
    """Test HopscotchInjector uses locator for default (no resource) resolution."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    # Setup locator with default greeting
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.greeting.salutation == "Good Day"


def test_hopscotch_injector_with_locator_and_context(registry):
    """Test HopscotchInjector uses resource from container to resolve implementation."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    # Setup locator with multiple implementations
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeRequestContext
    )
    locator = locator.register(
        Greeting, CustomerGreeting, resource=CustomerRequestContext
    )
    registry.register_value(ServiceLocator, locator)

    # Register context in container
    registry.register_value(RequestContext, EmployeeRequestContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=RequestContext)

    service = injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert service.greeting.salutation == "Wassup"


def test_hopscotch_injector_kwargs_override(registry):
    """Test that kwargs override locator resolution (three-tier precedence)."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    # Override with kwargs
    custom_greeting = CustomerGreeting()
    service = injector(Service, greeting=custom_greeting)
    assert service.greeting is custom_greeting


def test_hopscotch_injector_with_default_fallback(registry):
    """Test that default values work when neither locator nor container provides value."""
    from dataclasses import field

    @dataclass
    class Service:
        greeting: Injectable[Greeting] = field(default_factory=DefaultGreeting)  # type: ignore[assignment]
        name: str = "World"

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.name == "World"


def test_hopscotch_injector_multiple_injectable_fields(registry):
    """Test HopscotchInjector with multiple Injectable fields."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]
        database: Injectable[Database]

    locator = ServiceLocator()
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeRequestContext
    )
    locator = locator.register(Database, PostgresDB)
    registry.register_value(ServiceLocator, locator)
    registry.register_value(RequestContext, EmployeeRequestContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=RequestContext)

    service = injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert isinstance(service.database, PostgresDB)


def test_hopscotch_injector_lifo_override(registry):
    """Test that LIFO ordering allows later registrations to override earlier ones."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    @dataclass
    class SystemGreeting:
        salutation: str = "System"

    @dataclass
    class SiteGreeting:
        salutation: str = "Site"

    locator = ServiceLocator()
    locator = locator.register(Greeting, SystemGreeting)  # System default
    locator = locator.register(Greeting, SiteGreeting)  # Site override (LIFO)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, SiteGreeting)
    assert service.greeting.salutation == "Site"


def test_hopscotch_injector_no_resource_configured(registry):
    """Test HopscotchInjector without resource uses None for resource lookup."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeRequestContext
    )
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)  # No resource

    service = injector(Service)
    # Should get default since resource is None
    assert isinstance(service.greeting, DefaultGreeting)


@pytest.mark.anyio
async def test_hopscotch_async_injector_with_locator_and_context(registry):
    """Test HopscotchAsyncInjector uses resource from container to resolve implementation."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeRequestContext
    )
    registry.register_value(ServiceLocator, locator)
    registry.register_value(RequestContext, EmployeeRequestContext())

    container = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container, resource=RequestContext)

    service = await injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert service.greeting.salutation == "Wassup"


@pytest.mark.anyio
async def test_hopscotch_async_injector_kwargs_override(registry):
    """Test that kwargs override locator resolution in async injector."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container)

    custom_greeting = CustomerGreeting()
    service = await injector(Service, greeting=custom_greeting)
    assert service.greeting is custom_greeting


# ============================================================================
# Task 3.1: Caching Tests
# ============================================================================


def test_cache_hit_after_first_lookup():
    """Test that cache returns same result for repeated lookups with same service_type and resource."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    # First lookup - cache miss
    impl1 = locator.get_implementation(Greeting, EmployeeContext)
    assert impl1 == EmployeeGreeting

    # Second lookup - should be cache hit
    impl2 = locator.get_implementation(Greeting, EmployeeContext)
    assert impl2 == EmployeeGreeting
    assert impl1 is impl2  # Same class object


def test_cache_invalidation_on_new_registration():
    """Test that cache is cleared when new registration is added."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)

    # First lookup - cache miss, stores DefaultGreeting
    impl1 = locator.get_implementation(Greeting, None)
    assert impl1 == DefaultGreeting

    # Add new registration - returns NEW locator with empty cache
    locator = locator.register(Greeting, EmployeeGreeting)

    # Lookup on new locator should get latest (LIFO)
    impl2 = locator.get_implementation(Greeting, None)
    assert impl2 == EmployeeGreeting


def test_cache_isolation_between_service_types():
    """Test that cache properly isolates different service types."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Database, PostgresDB)

    # Lookup Greeting - caches (Greeting, None) -> DefaultGreeting
    greeting_impl = locator.get_implementation(Greeting, None)
    assert greeting_impl == DefaultGreeting

    # Lookup Database - should not interfere with Greeting cache
    db_impl = locator.get_implementation(Database, None)
    assert db_impl == PostgresDB

    # Verify Greeting still cached correctly
    greeting_impl2 = locator.get_implementation(Greeting, None)
    assert greeting_impl2 == DefaultGreeting


def test_cache_with_none_resource():
    """Test caching works correctly with None resource (default case)."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    # Cache None resource
    impl1 = locator.get_implementation(Greeting, None)
    assert impl1 == DefaultGreeting

    # Cache specific resource
    impl2 = locator.get_implementation(Greeting, EmployeeContext)
    assert impl2 == EmployeeGreeting

    # Verify both cached independently
    impl1_again = locator.get_implementation(Greeting, None)
    impl2_again = locator.get_implementation(Greeting, EmployeeContext)
    assert impl1_again == DefaultGreeting
    assert impl2_again == EmployeeGreeting


def test_cache_with_no_match():
    """Test that None results (no match) are also cached."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    # Lookup with non-matching resource - should return None and cache it
    impl1 = locator.get_implementation(Greeting, CustomerContext)
    assert impl1 is None

    # Second lookup - should return cached None
    impl2 = locator.get_implementation(Greeting, CustomerContext)
    assert impl2 is None
