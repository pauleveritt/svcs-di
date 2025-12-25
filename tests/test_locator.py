"""Tests for ServiceLocator and HopscotchInjector - single locator for all service types."""

from dataclasses import dataclass

import pytest
import svcs
from svcs.exceptions import ServiceNotFoundError

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


def test_factory_registration_matches_no_context():
    """Test matching with no context (default)."""
    reg = FactoryRegistration(service_type=Greeting, implementation=DefaultGreeting, context=None)
    assert reg.matches(None) == 0  # Default match


def test_factory_registration_matches_exact():
    """Test exact context match (highest priority)."""
    reg = FactoryRegistration(service_type=Greeting, implementation=EmployeeGreeting, context=EmployeeContext)
    assert reg.matches(EmployeeContext) == 2  # Exact match


def test_factory_registration_matches_subclass():
    """Test subclass context match (medium priority)."""
    reg = FactoryRegistration(service_type=Greeting, implementation=EmployeeGreeting, context=EmployeeContext)
    assert reg.matches(AdminContext) == 1  # Subclass match


def test_factory_registration_no_match():
    """Test when context doesn't match."""
    reg = FactoryRegistration(service_type=Greeting, implementation=EmployeeGreeting, context=EmployeeContext)
    assert reg.matches(CustomerContext) == -1  # No match


def test_service_locator_register_single_type():
    """Test registering implementation classes for a single service type."""
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, CustomerGreeting, context=CustomerContext)

    assert len(locator.registrations) == 2
    # Most recent first (LIFO)
    assert locator.registrations[0].implementation == CustomerGreeting
    assert locator.registrations[1].implementation == DefaultGreeting


def test_service_locator_register_multiple_types():
    """Test registering factories for multiple service types in ONE locator."""
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Database, PostgresDB)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
    locator.register(Database, TestDatabase, context=TestContext)

    assert len(locator.registrations) == 4
    # Verify all types are tracked
    service_types = {reg.service_type for reg in locator.registrations}
    assert service_types == {Greeting, Database}


def test_service_locator_get_implementation_default():
    """Test getting default implementation (no context) from single locator."""
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Database, PostgresDB)

    greeting_impl = locator.get_implementation(Greeting, None)
    assert greeting_impl == DefaultGreeting

    db_impl = locator.get_implementation(Database, None)
    assert db_impl == PostgresDB


def test_service_locator_get_implementation_exact_match():
    """Test getting implementation with exact context match."""
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)

    impl = locator.get_implementation(Greeting, EmployeeContext)
    assert impl == EmployeeGreeting


def test_service_locator_isolates_service_types():
    """Test that service types are properly isolated in single locator."""
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
    locator.register(Database, PostgresDB)
    locator.register(Database, TestDatabase, context=TestContext)

    # Greeting lookups don't interfere with Database
    assert locator.get_implementation(Greeting, None) == DefaultGreeting
    assert locator.get_implementation(Greeting, EmployeeContext) == EmployeeGreeting
    assert locator.get_implementation(Database, None) == PostgresDB
    assert locator.get_implementation(Database, TestContext) == TestDatabase


def test_get_from_locator_single_locator(registry):
    """Test get_from_locator with ServiceLocator registered in registry."""
    # ONE locator registered as a service
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
    locator.register(Database, PostgresDB)
    locator.register(Database, TestDatabase, context=TestContext)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)

    # Get greetings
    greeting = get_from_locator(container, Greeting)
    assert isinstance(greeting, DefaultGreeting)

    greeting = get_from_locator(container, Greeting, request_context=EmployeeContext)
    assert isinstance(greeting, EmployeeGreeting)

    # Get databases
    db = get_from_locator(container, Database)
    assert isinstance(db, PostgresDB)

    db = get_from_locator(container, Database, request_context=TestContext)
    assert isinstance(db, TestDatabase)


def test_get_from_locator_no_implementation_raises(registry):
    """Test that LookupError is raised when no implementation matches."""
    locator = ServiceLocator()
    locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)

    with pytest.raises(LookupError, match="No implementation found"):
        get_from_locator(container, Greeting, request_context=CustomerContext)


def test_system_site_override_without_context(registry):
    """Test that site registration overrides system registration via LIFO (no context needed)."""

    # Define system-level and site-level implementations
    @dataclass
    class SystemGreeting:
        salutation: str = "System Default"

    @dataclass
    class SiteGreeting:
        salutation: str = "Site Override"

    # Setup: System registers default first
    locator = ServiceLocator()
    locator.register(Greeting, SystemGreeting)  # System default

    # Then site overrides (LIFO = most recent wins)
    locator.register(Greeting, SiteGreeting)  # Site override

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
    """Test HopscotchInjector uses locator for default (no context) resolution."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    # Setup locator with default greeting
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.greeting.salutation == "Good Day"


def test_hopscotch_injector_with_locator_and_context(registry):
    """Test HopscotchInjector uses context from container to resolve implementation."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    # Setup locator with multiple implementations
    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeRequestContext)
    locator.register(Greeting, CustomerGreeting, context=CustomerRequestContext)
    registry.register_value(ServiceLocator, locator)

    # Register context in container
    registry.register_value(RequestContext, EmployeeRequestContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, context_key=RequestContext)

    service = injector(Service)
    assert isinstance(service.greeting, EmployeeGreeting)
    assert service.greeting.salutation == "Wassup"


def test_hopscotch_injector_kwargs_override(registry):
    """Test that kwargs override locator resolution (three-tier precedence)."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
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
        greeting: Injectable[Greeting] = field(default_factory=DefaultGreeting)
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
    locator.register(Greeting, EmployeeGreeting, context=EmployeeRequestContext)
    locator.register(Database, PostgresDB)
    registry.register_value(ServiceLocator, locator)
    registry.register_value(RequestContext, EmployeeRequestContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, context_key=RequestContext)

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
    locator.register(Greeting, SystemGreeting)  # System default
    locator.register(Greeting, SiteGreeting)  # Site override (LIFO)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(Service)
    assert isinstance(service.greeting, SiteGreeting)
    assert service.greeting.salutation == "Site"


def test_hopscotch_injector_no_context_key_configured(registry):
    """Test HopscotchInjector without context_key uses None for context."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeRequestContext)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)  # No context_key

    service = injector(Service)
    # Should get default since context_key is None
    assert isinstance(service.greeting, DefaultGreeting)


@pytest.mark.anyio
async def test_hopscotch_async_injector_with_locator_and_context(registry):
    """Test HopscotchAsyncInjector uses context from container to resolve implementation."""

    @dataclass
    class Service:
        greeting: Injectable[Greeting]

    locator = ServiceLocator()
    locator.register(Greeting, DefaultGreeting)
    locator.register(Greeting, EmployeeGreeting, context=EmployeeRequestContext)
    registry.register_value(ServiceLocator, locator)
    registry.register_value(RequestContext, EmployeeRequestContext())

    container = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container, context_key=RequestContext)

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
    locator.register(Greeting, DefaultGreeting)
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container)

    custom_greeting = CustomerGreeting()
    service = await injector(Service, greeting=custom_greeting)
    assert service.greeting is custom_greeting
