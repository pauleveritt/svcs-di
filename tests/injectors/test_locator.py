"""Tests for ServiceLocator and HopscotchInjector - single locator for all service types."""

from dataclasses import dataclass
from pathlib import PurePath

import pytest
import svcs

from svcs_di.auto import Inject
from svcs_di.injectors.locator import (
    FactoryRegistration,
    HopscotchAsyncInjector,
    HopscotchInjector,
    Location,
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
    # Scoring: exact resource match = 100
    assert reg.matches(EmployeeContext) == 100  # Exact match


def test_service_locator_register_with_resource_parameter():
    """Test ServiceLocator.register() with resource parameter."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    # Verify single registration uses fast path
    assert len(locator._single_registrations) == 1
    assert Greeting in locator._single_registrations
    assert locator._single_registrations[Greeting].resource == EmployeeContext


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
# Original tests - updated for resource terminology and new scoring
# ============================================================================


def test_factory_registration_matches_no_resource():
    """Test matching with no resource (default)."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=DefaultGreeting, resource=None
    )
    # Scoring: default resource = 0
    assert reg.matches(None) == 0  # Default match


def test_factory_registration_matches_exact():
    """Test exact resource match (highest priority)."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=EmployeeGreeting, resource=EmployeeContext
    )
    # Scoring: exact resource = 100
    assert reg.matches(EmployeeContext) == 100  # Exact match


def test_factory_registration_matches_subclass():
    """Test subclass resource match (medium priority)."""
    reg = FactoryRegistration(
        service_type=Greeting, implementation=EmployeeGreeting, resource=EmployeeContext
    )
    # Scoring: subclass resource = 10
    assert reg.matches(AdminContext) == 10  # Subclass match


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

    # Second registration promotes to multi-registration path
    assert len(locator._multi_registrations) == 1
    assert Greeting in locator._multi_registrations
    assert len(locator._multi_registrations[Greeting]) == 2
    # Most recent first (LIFO)
    assert locator._multi_registrations[Greeting][0].implementation == CustomerGreeting
    assert locator._multi_registrations[Greeting][1].implementation == DefaultGreeting


def test_service_locator_register_multiple_types():
    """Test registering factories for multiple service types in ONE locator."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Database, PostgresDB)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Database, TestDatabase, resource=TestContext)

    # Both Greeting and Database have 2 registrations each (multi path)
    assert len(locator._multi_registrations) == 2
    assert Greeting in locator._multi_registrations
    assert Database in locator._multi_registrations
    assert len(locator._multi_registrations[Greeting]) == 2
    assert len(locator._multi_registrations[Database]) == 2


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
# HopscotchInjector Tests - Inject[T] with locator support
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
        greeting: Inject[Greeting]

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
        greeting: Inject[Greeting]

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
    """Test HopscotchInjector uses resource type to resolve implementation."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

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

    container = svcs.Container(registry)
    # Pass resource type directly
    injector = HopscotchInjector(container=container, resource=EmployeeRequestContext)

    service = injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert service.greeting.salutation == "Wassup"


def test_hopscotch_injector_kwargs_override(registry):
    """Test that kwargs override locator resolution (three-tier precedence)."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

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
        greeting: Inject[Greeting] = field(default_factory=DefaultGreeting)  # type: ignore[assignment]
        name: str = "World"

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.name == "World"


def test_hopscotch_injector_multiple_injectable_fields(registry):
    """Test HopscotchInjector with multiple Inject fields."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]
        database: Inject[Database]

    locator = ServiceLocator()
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeRequestContext
    )
    locator = locator.register(Database, PostgresDB)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    # Pass resource type directly
    injector = HopscotchInjector(container=container, resource=EmployeeRequestContext)

    service = injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert isinstance(service.database, PostgresDB)


def test_hopscotch_injector_lifo_override(registry):
    """Test that LIFO ordering allows later registrations to override earlier ones."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

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
        greeting: Inject[Greeting]

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
    """Test HopscotchAsyncInjector uses resource type to resolve implementation."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeRequestContext
    )
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    # Pass resource type directly
    injector = HopscotchAsyncInjector(
        container=container, resource=EmployeeRequestContext
    )

    service = await injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert service.greeting.salutation == "Wassup"


@pytest.mark.anyio
async def test_hopscotch_async_injector_kwargs_override(registry):
    """Test that kwargs override locator resolution in async injector."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

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
    """Test that cache returns same r for repeated lookups with same service_type and resource."""
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


def test_single_registration_fast_path():
    """Test that single registrations use the fast O(1) path."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)

    # Single registration should be in _single_registrations (fast path)
    assert len(locator._single_registrations) == 1
    assert Greeting in locator._single_registrations
    assert len(locator._multi_registrations) == 0

    # Verify it can still be retrieved correctly
    impl = locator.get_implementation(Greeting)
    assert impl == DefaultGreeting


def test_multiple_registrations_scoring_path():
    """Test that multiple registrations use the O(m) scoring path."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    # Second registration promotes to multi-registration (scoring path)
    assert len(locator._single_registrations) == 0
    assert len(locator._multi_registrations) == 1
    assert Greeting in locator._multi_registrations
    assert len(locator._multi_registrations[Greeting]) == 2

    # Verify scoring still works correctly
    impl = locator.get_implementation(Greeting, resource=EmployeeContext)
    assert impl == EmployeeGreeting

    impl = locator.get_implementation(Greeting, resource=None)
    assert impl == DefaultGreeting


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


# ============================================================================
# Task 3.1: Hierarchical Location Resolution Tests
# ============================================================================


# Location-specific test fixtures
@dataclass
class PublicGreeting:
    salutation: str = "Welcome"


@dataclass
class AdminGreeting:
    salutation: str = "Admin Portal"


@dataclass
class AdminUsersGreeting:
    salutation: str = "User Management"


def test_exact_location_match_resolution():
    """Test that exact location matches are resolved correctly."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    # Request from /admin should get AdminGreeting
    impl = locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl == AdminGreeting

    # Request from root should get DefaultGreeting
    impl = locator.get_implementation(Greeting, location=PurePath("/"))
    assert impl == DefaultGreeting


def test_hierarchical_fallback_child_uses_parent_service():
    """Test that child location falls back to parent's service when no exact match."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    # Child location /admin/users should fall back to parent /admin
    impl = locator.get_implementation(Greeting, location=PurePath("/admin/users"))
    assert impl == AdminGreeting

    # Deep child location should also fall back
    impl = locator.get_implementation(
        Greeting, location=PurePath("/admin/users/profile")
    )
    assert impl == AdminGreeting


def test_location_resource_precedence():
    """Test precedence: location+resource > location-only > default."""
    locator = ServiceLocator()
    # Default (no location, no resource): score = 1
    locator = locator.register(Greeting, DefaultGreeting)
    # Location only: score = 100 + 1 = 101
    locator = locator.register(Greeting, PublicGreeting, location=PurePath("/public"))
    # Location + resource: score = 100 + 10 + 1 = 111
    locator = locator.register(
        Greeting, AdminGreeting, location=PurePath("/admin"), resource=EmployeeContext
    )

    # Request with location + resource should get highest score (111)
    impl = locator.get_implementation(
        Greeting, resource=EmployeeContext, location=PurePath("/admin")
    )
    assert impl == AdminGreeting

    # Request with location only should get location-only match (101)
    impl = locator.get_implementation(Greeting, location=PurePath("/public"))
    assert impl == PublicGreeting

    # Request with no location should get default (1)
    impl = locator.get_implementation(Greeting)
    assert impl == DefaultGreeting


def test_lifo_ordering_with_tied_scores():
    """Test that most recent registration wins when scores are tied."""
    locator = ServiceLocator()
    # First registration at /admin
    locator = locator.register(Greeting, DefaultGreeting, location=PurePath("/admin"))
    # Second registration at /admin (same location, tied score)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    # Most recent (AdminGreeting) should win due to LIFO
    impl = locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl == AdminGreeting


def test_service_not_available_at_location():
    """Test that services not available at a location return None (distinct from not registered)."""
    locator = ServiceLocator()
    # Only register at /admin
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    # Request from /public should return None (not available at this location)
    impl = locator.get_implementation(Greeting, location=PurePath("/public"))
    assert impl is None

    # But request from /admin should work
    impl = locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl == AdminGreeting


def test_root_location_fallback_behavior():
    """Test that root location (/) services are available as ultimate fallback."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting, location=PurePath("/"))
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    # Request from /public should fall back to root / service
    impl = locator.get_implementation(Greeting, location=PurePath("/public"))
    assert impl == DefaultGreeting

    # Request from /admin should get specific admin service
    impl = locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl == AdminGreeting

    # Request from deeply nested /public/api/v1 should fall back to root
    impl = locator.get_implementation(Greeting, location=PurePath("/public/api/v1"))
    assert impl == DefaultGreeting


def test_most_specific_location_wins():
    """Test that more specific location (deeper) takes precedence over less specific (shallower)."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting, location=PurePath("/"))
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(
        Greeting, AdminUsersGreeting, location=PurePath("/admin/users")
    )

    # Request from /admin/users should get most specific match
    impl = locator.get_implementation(Greeting, location=PurePath("/admin/users"))
    assert impl == AdminUsersGreeting

    # Request from /admin/settings should fall back to /admin (not root)
    impl = locator.get_implementation(Greeting, location=PurePath("/admin/settings"))
    assert impl == AdminGreeting

    # Request from /public should fall back to root
    impl = locator.get_implementation(Greeting, location=PurePath("/public"))
    assert impl == DefaultGreeting


def test_location_cache_includes_location_in_key():
    """Test that cache properly isolates lookups by location."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    # First lookup with /admin
    impl1 = locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl1 == AdminGreeting

    # Lookup without location should get different r (cached separately)
    impl2 = locator.get_implementation(Greeting)
    assert impl2 == DefaultGreeting

    # Second lookup with /admin should still get cached AdminGreeting
    impl3 = locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl3 == AdminGreeting


# ============================================================================
# Task 4.1: HopscotchInjector Integration with Location Tests
# ============================================================================


def test_location_registered_as_value_service_in_container(registry):
    """Test Location registered as value service in container."""
    # Register Location in container
    admin_location = PurePath("/admin")
    registry.register_value(Location, admin_location)

    container = svcs.Container(registry)

    # Retrieve Location from container
    location = container.get(Location)
    assert location == admin_location
    assert isinstance(location, PurePath)


def test_injectable_location_dependency_resolution(registry):
    """Test Inject[Location] dependency resolution."""

    @dataclass
    class Service:
        location: Inject[Location]
        name: str = "TestService"

    # Register Location in container
    admin_location = PurePath("/admin/users")
    registry.register_value(Location, admin_location)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    # Inject service with Location dependency
    service = injector(Service)
    assert service.location == admin_location
    assert service.name == "TestService"


def test_hopscotch_injector_uses_location_during_resolution(registry):
    """Test HopscotchInjector uses Location during service resolution."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

    # Setup locator with location-based registrations
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(Greeting, PublicGreeting, location=PurePath("/public"))
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    # Pass location directly to injector
    injector = HopscotchInjector(container=container, location=PurePath("/admin"))

    # Should resolve to AdminGreeting because location is /admin
    service = injector(Service)
    assert isinstance(service.greeting, AdminGreeting)
    assert service.greeting.salutation == "Admin Portal"


def test_three_tier_precedence_with_location(registry):
    """Test three-tier precedence preserved (kwargs > locator+location > defaults)."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

    # Setup locator with location-based registrations
    locator = ServiceLocator()
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    # Pass location directly to injector
    injector = HopscotchInjector(container=container, location=PurePath("/admin"))

    # Tier 1: kwargs override should win
    custom_greeting = CustomerGreeting()
    service = injector(Service, greeting=custom_greeting)
    assert service.greeting is custom_greeting

    # Tier 2: locator+location resolution should work without kwargs
    service = injector(Service)
    assert isinstance(service.greeting, AdminGreeting)


def test_services_restricted_to_location_only_mode(registry):
    """Test services restricted to location (ONLY mode)."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

    # Setup locator with ONLY admin greeting (no default)
    locator = ServiceLocator()
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    registry.register_value(ServiceLocator, locator)

    # Test 1: With location set to /admin - should work
    container = svcs.Container(registry)
    # Pass location directly to injector
    injector = HopscotchInjector(container=container, location=PurePath("/admin"))

    service = injector(Service)
    assert isinstance(service.greeting, AdminGreeting)

    # Test 2: With location set to /public - should fail (service not available)
    registry2 = svcs.Registry()
    locator2 = ServiceLocator()
    locator2 = locator2.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    registry2.register_value(ServiceLocator, locator2)

    container2 = svcs.Container(registry2)
    # Pass location directly to injector
    injector2 = HopscotchInjector(container=container2, location=PurePath("/public"))

    # Should raise because no implementation available at /public location
    with pytest.raises(TypeError):  # No value found at any tier
        injector2(Service)


def test_location_with_hierarchical_fallback_in_injector(registry):
    """Test that injector respects hierarchical location fallback."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

    # Setup locator with parent location registration
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    # Pass child location /admin/users - should fall back to parent /admin
    injector = HopscotchInjector(container=container, location=PurePath("/admin/users"))

    # Should fall back to parent /admin location's service
    service = injector(Service)
    assert isinstance(service.greeting, AdminGreeting)


@pytest.mark.anyio
async def test_async_injector_uses_location_during_resolution(registry):
    """Test HopscotchAsyncInjector uses Location during service resolution."""

    @dataclass
    class Service:
        greeting: Inject[Greeting]

    # Setup locator with location-based registrations
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    # Pass location directly to async injector
    injector = HopscotchAsyncInjector(container=container, location=PurePath("/admin"))

    # Should resolve to AdminGreeting because location is /admin
    service = await injector(Service)
    assert isinstance(service.greeting, AdminGreeting)
    assert service.greeting.salutation == "Admin Portal"


# ============================================================================
# Task 5.3: Strategic Integration Tests (Maximum 8 additional tests)
# ============================================================================


def test_end_to_end_container_creation_to_resolution(registry):
    """Test complete workflow: container creation -> registration -> resolution."""

    @dataclass
    class OrderProcessor:
        greeting: Inject[Greeting]
        database: Inject[Database]

    # Setup: Create locator with location and resource-based registrations
    locator = ServiceLocator()

    # Register services at different locations with different resources
    locator = locator.register(Greeting, DefaultGreeting)  # Global default
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(
        Greeting,
        CustomerGreeting,
        location=PurePath("/public"),
        resource=CustomerContext,
    )
    locator = locator.register(Database, PostgresDB)  # Global database

    registry.register_value(ServiceLocator, locator)
    registry.register_value(CustomerContext, CustomerContext())

    # Create container and injector with resource and location
    container = svcs.Container(registry)
    injector = HopscotchInjector(
        container=container, resource=CustomerContext, location=PurePath("/public")
    )

    # Resolve service
    processor = injector(OrderProcessor)

    # Verify correct implementations selected
    assert isinstance(processor.greeting, CustomerGreeting)
    assert isinstance(processor.database, PostgresDB)


def test_combined_location_resource_precedence_scoring():
    """Test combined location + resource precedence scoring beats individual matches."""
    locator = ServiceLocator()

    # Register various combinations
    locator = locator.register(Greeting, DefaultGreeting)  # Score: 1
    locator = locator.register(
        Greeting, AdminGreeting, resource=EmployeeContext
    )  # Score with EmployeeContext: 11
    locator = locator.register(
        Greeting, PublicGreeting, location=PurePath("/public")
    )  # Score at /public: 101
    locator = locator.register(
        Greeting,
        CustomerGreeting,
        location=PurePath("/public"),
        resource=CustomerContext,
    )  # Score at /public with CustomerContext: 111

    # Test: Combined location+resource should win
    impl = locator.get_implementation(
        Greeting, resource=CustomerContext, location=PurePath("/public")
    )
    assert impl == CustomerGreeting

    # Test: Location-only should beat resource-only at that location
    impl = locator.get_implementation(Greeting, location=PurePath("/public"))
    assert impl == PublicGreeting

    # Test: Resource-only when no location specified
    impl = locator.get_implementation(Greeting, resource=EmployeeContext)
    assert impl == AdminGreeting


def test_location_hierarchy_multiple_nesting_levels():
    """Test location hierarchy with 4+ nesting levels."""
    locator = ServiceLocator()

    # Create deep hierarchy: / -> /admin -> /admin/users -> /admin/users/reports
    locator = locator.register(Greeting, DefaultGreeting, location=PurePath("/"))
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(
        Greeting, AdminUsersGreeting, location=PurePath("/admin/users")
    )

    @dataclass
    class ReportsGreeting:
        salutation: str = "User Reports"

    locator = locator.register(
        Greeting, ReportsGreeting, location=PurePath("/admin/users/reports")
    )

    # Test deep nesting resolution
    impl = locator.get_implementation(
        Greeting, location=PurePath("/admin/users/reports/monthly")
    )
    assert impl == ReportsGreeting

    # Test fallback to intermediate level
    impl = locator.get_implementation(
        Greeting, location=PurePath("/admin/users/settings")
    )
    assert impl == AdminUsersGreeting

    # Test fallback to higher level
    impl = locator.get_implementation(
        Greeting, location=PurePath("/admin/settings/security")
    )
    assert impl == AdminGreeting

    # Test fallback to root
    impl = locator.get_implementation(Greeting, location=PurePath("/other/path"))
    assert impl == DefaultGreeting


def test_error_invalid_location_type():
    """Test error handling when invalid location type is provided."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)

    # Should handle None gracefully
    impl = locator.get_implementation(Greeting, location=None)
    assert impl == DefaultGreeting

    # Invalid type should be caught by type checker, but test runtime behavior
    # PurePath accepts strings, so "invalid" string becomes valid PurePath
    impl = locator.get_implementation(Greeting, location=PurePath("invalid"))
    # Should return default or None depending on registrations
    assert impl == DefaultGreeting


def test_thread_safety_purepath_immutability():
    """Test that PurePath immutability ensures thread-safe location handling."""
    locator = ServiceLocator()
    admin_location = PurePath("/admin")

    locator = locator.register(Greeting, AdminGreeting, location=admin_location)

    # PurePath is immutable - operations return new instances
    child_location = admin_location / "users"
    assert admin_location == PurePath("/admin")  # Original unchanged
    assert child_location == PurePath("/admin/users")

    # Verify both locations work independently
    impl1 = locator.get_implementation(Greeting, location=admin_location)
    impl2 = locator.get_implementation(Greeting, location=child_location)

    assert impl1 == AdminGreeting
    assert impl2 == AdminGreeting  # Falls back to parent


def test_cache_behavior_with_location_lookups():
    """Test that cache correctly handles location parameter in key."""
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(Greeting, PublicGreeting, location=PurePath("/public"))

    # Warm up cache with different locations
    impl1 = locator.get_implementation(Greeting, location=PurePath("/admin"))
    impl2 = locator.get_implementation(Greeting, location=PurePath("/public"))
    impl3 = locator.get_implementation(Greeting)  # No location

    # Verify cached results are returned
    assert impl1 == AdminGreeting
    assert impl2 == PublicGreeting
    assert impl3 == DefaultGreeting

    # Verify cache hits return same results
    assert (
        locator.get_implementation(Greeting, location=PurePath("/admin"))
        == AdminGreeting
    )
    assert (
        locator.get_implementation(Greeting, location=PurePath("/public"))
        == PublicGreeting
    )
    assert locator.get_implementation(Greeting) == DefaultGreeting


def test_decorator_integration_with_location_scanning(registry):
    """Test that @injectable decorator with location works with scanning."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.locator import scan

    # Define services with location decorator
    @injectable(location=PurePath("/admin"))
    @dataclass
    class AdminService:
        name: str = "Admin"

    @injectable(location=PurePath("/public"))
    @dataclass
    class PublicService:
        name: str = "Public"

    @injectable
    @dataclass
    class GlobalService:
        name: str = "Global"

    # Scan locals
    scan(registry, locals_dict=locals())

    # Verify locator was created and services registered
    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # Check location-based registrations go to locator
    admin_impl = locator.get_implementation(AdminService, location=PurePath("/admin"))
    public_impl = locator.get_implementation(
        PublicService, location=PurePath("/public")
    )

    assert admin_impl == AdminService
    assert public_impl == PublicService

    # GlobalService should be registered directly to registry (no location/resource)
    # It gets registered via factory pattern, so we get it through container
    global_service = container.get(GlobalService)
    assert isinstance(global_service, GlobalService)
    assert global_service.name == "Global"
    # It gets registered via factory pattern, so we get it through container
    global_service = container.get(GlobalService)
    assert isinstance(global_service, GlobalService)
    assert global_service.name == "Global"
