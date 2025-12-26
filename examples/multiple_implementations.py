"""
Multiple Implementations Example - ServiceLocator and HopscotchInjector

This example demonstrates how to register multiple implementations for the same
service type and use resource-based resolution to select the appropriate one.

Key Features Demonstrated:
- Multiple implementations per service type
- Resource-based resolution with three-tier precedence
- LIFO ordering (later registrations override earlier ones)
- HopscotchInjector integration with Injectable[T]
- Dynamic resource resolution from container
"""

from dataclasses import dataclass

import svcs

from svcs_di.auto import Injectable
from svcs_di.injectors.locator import (
    HopscotchInjector,
    ServiceLocator,
)


# ============================================================================
# Domain Models - Service Interfaces
# ============================================================================


class Greeting:
    """Base protocol for greeting services."""

    salutation: str

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        return f"{self.salutation}, {name}!"


class Database:
    """Base protocol for database services."""

    name: str

    def connect(self) -> str:
        """Connect to the database."""
        return f"Connected to {self.name}"


# ============================================================================
# Resource Classes for Resolution
# ============================================================================


class RequestContext:
    """Base resource type for all requests."""

    pass


class EmployeeContext(RequestContext):
    """Resource type for employee requests."""

    pass


class CustomerContext(RequestContext):
    """Resource type for customer requests."""

    pass


class AdminContext(EmployeeContext):
    """Resource type for admin requests (subclass of EmployeeContext)."""

    pass


# ============================================================================
# Greeting Implementations
# ============================================================================


@dataclass
class DefaultGreeting(Greeting):
    """Default greeting for all resources (lowest precedence)."""

    salutation: str = "Good Day"


@dataclass
class EmployeeGreeting(Greeting):
    """Greeting for employee resources."""

    salutation: str = "Hey"


@dataclass
class CustomerGreeting(Greeting):
    """Greeting for customer resources."""

    salutation: str = "Hello"


@dataclass
class AdminGreeting(Greeting):
    """Special greeting for admin resources (overrides EmployeeGreeting)."""

    salutation: str = "Welcome, Admin"


# ============================================================================
# Database Implementations
# ============================================================================


@dataclass
class ProductionDB(Database):
    """Production database (default)."""

    name: str = "production-db"


@dataclass
class TestDB(Database):
    """Test database for testing resources."""

    name: str = "test-db"


# ============================================================================
# Application Services Using Injectable[T]
# ============================================================================


@dataclass
class WelcomeService:
    """Service that uses greeting and database via dependency injection."""

    greeting: Injectable[Greeting]
    database: Injectable[Database]

    def welcome_user(self, username: str) -> str:
        """Welcome a user with resource-appropriate greeting."""
        db_status = self.greeting.connect()
        greeting_msg = self.greeting.greet(username)
        return f"{db_status} | {greeting_msg}"


# ============================================================================
# Example 1: Basic Multiple Implementations
# ============================================================================


def example_basic_multiple_implementations():
    """
    Demonstrates registering multiple implementations and basic resource-based resolution.
    """
    print("\n" + "=" * 70)
    print("Example 1: Basic Multiple Implementations")
    print("=" * 70)

    # Setup: Create registry and locator
    registry = svcs.Registry()
    locator = ServiceLocator()

    # Register multiple greeting implementations
    locator = locator.register(Greeting, DefaultGreeting)  # Default (no resource)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Greeting, CustomerGreeting, resource=CustomerContext)

    # Register multiple database implementations
    locator = locator.register(Database, ProductionDB)  # Default
    locator = locator.register(Database, TestDB, resource=EmployeeContext)

    # Register the locator as a service
    registry.register_value(ServiceLocator, locator)

    # Test 1: No resource (uses defaults)
    print("\nTest 1: No resource - uses default implementations")
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(WelcomeService)
    print(f"  Greeting type: {type(service.greeting).__name__}")
    print(f"  Database type: {type(service.database).__name__}")
    print(f"  Result: {service.greeting.greet('World')}")

    # Test 2: Employee resource
    print("\nTest 2: Employee resource - uses employee implementations")
    registry.register_value(RequestContext, EmployeeContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=RequestContext)

    service = injector(WelcomeService)
    print(f"  Greeting type: {type(service.greeting).__name__}")
    print(f"  Database type: {type(service.database).__name__}")
    print(f"  Result: {service.greeting.greet('Alice')}")

    # Test 3: Customer resource
    print("\nTest 3: Customer resource - uses customer greeting, default database")
    registry.register_value(RequestContext, CustomerContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=RequestContext)

    service = injector(WelcomeService)
    print(f"  Greeting type: {type(service.greeting).__name__}")
    print(f"  Database type: {type(service.database).__name__}")
    print(f"  Result: {service.greeting.greet('Bob')}")


# ============================================================================
# Example 2: LIFO Override Behavior
# ============================================================================


def example_lifo_override():
    """
    Demonstrates LIFO (Last-In-First-Out) ordering where later registrations
    override earlier ones.
    """
    print("\n" + "=" * 70)
    print("Example 2: LIFO Override Behavior")
    print("=" * 70)

    registry = svcs.Registry()
    locator = ServiceLocator()

    # System-level default
    print("\nStep 1: System registers default greeting")
    locator = locator.register(Greeting, DefaultGreeting)

    # Site-level override (LIFO - inserted at position 0)
    print("Step 2: Site overrides with customer greeting (LIFO)")
    locator = locator.register(Greeting, CustomerGreeting)

    registry.register_value(ServiceLocator, locator)
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    # Use a service that depends on Greeting to demonstrate LIFO
    @dataclass
    class SimpleService:
        greeting: Injectable[Greeting]

    service = injector(SimpleService)
    print(f"\nResult: Got {type(service.greeting).__name__}")
    print(f"  Salutation: {service.greeting.salutation}")
    print("  (Site override won due to LIFO ordering)")


# ============================================================================
# Example 3: Three-Tier Precedence (Exact > Subclass > Default)
# ============================================================================


def example_three_tier_precedence():
    """
    Demonstrates three-tier precedence:
    - Exact resource match (highest)
    - Subclass resource match (medium)
    - No resource/default (lowest)
    """
    print("\n" + "=" * 70)
    print("Example 3: Three-Tier Precedence")
    print("=" * 70)

    registry = svcs.Registry()
    locator = ServiceLocator()

    # Register with different precedence levels
    locator = locator.register(Greeting, DefaultGreeting)  # Low: no resource
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)  # Medium/High
    locator = locator.register(Greeting, AdminGreeting, resource=AdminContext)  # High for AdminContext

    registry.register_value(ServiceLocator, locator)

    # Test 1: Exact match (AdminContext)
    print("\nTest 1: AdminContext - exact match (highest precedence)")
    registry.register_value(RequestContext, AdminContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=RequestContext)

    @dataclass
    class TestService:
        greeting: Injectable[Greeting]

    service = injector(TestService)
    print(f"  Got: {type(service.greeting).__name__}")
    print(f"  Salutation: {service.greeting.salutation}")

    # Test 2: Subclass match (AdminContext inherits from EmployeeContext)
    print("\nTest 2: AdminContext with no exact match - subclass match (medium precedence)")
    locator2 = ServiceLocator()
    locator2 = locator2.register(Greeting, DefaultGreeting)
    locator2 = locator2.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    # No AdminGreeting registered this time

    registry2 = svcs.Registry()
    registry2.register_value(ServiceLocator, locator2)
    registry2.register_value(RequestContext, AdminContext())
    container2 = svcs.Container(registry2)
    injector2 = HopscotchInjector(container=container2, resource=RequestContext)

    service2 = injector2(TestService)
    print(f"  Got: {type(service2.greeting).__name__}")
    print(f"  Salutation: {service2.greeting.salutation}")
    print("  (Matched EmployeeContext via subclass relationship)")

    # Test 3: Default match (no resource)
    print("\nTest 3: No resource - default match (lowest precedence)")
    container3 = svcs.Container(registry2)
    injector3 = HopscotchInjector(container=container3)  # No resource

    service3 = injector3(TestService)
    print(f"  Got: {type(service3.greeting).__name__}")
    print(f"  Salutation: {service3.greeting.salutation}")


# ============================================================================
# Example 4: Kwargs Override (Highest Precedence)
# ============================================================================


def example_kwargs_override():
    """
    Demonstrates that kwargs have the highest precedence, overriding both
    locator and container resolution.
    """
    print("\n" + "=" * 70)
    print("Example 4: Kwargs Override (Highest Precedence)")
    print("=" * 70)

    registry = svcs.Registry()
    locator = ServiceLocator()

    # Register default implementations
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    locator = locator.register(Database, ProductionDB)

    registry.register_value(ServiceLocator, locator)
    registry.register_value(RequestContext, EmployeeContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=RequestContext)

    # Without kwargs - uses locator/container
    print("\nWithout kwargs override:")
    service1 = injector(WelcomeService)
    print(f"  Greeting: {type(service1.greeting).__name__}")
    print(f"  Database: {type(service1.database).__name__}")

    # With kwargs - overrides everything
    print("\nWith kwargs override:")
    custom_greeting = CustomerGreeting(salutation="Overridden!")
    custom_db = TestDB(name="override-db")
    service2 = injector(WelcomeService, greeting=custom_greeting, database=custom_db)
    print(f"  Greeting: {type(service2.greeting).__name__}")
    print(f"  Database: {type(service2.database).__name__}")
    print(f"  Salutation: {service2.greeting.salutation}")
    print("  (Kwargs override both locator and container)")


# ============================================================================
# Example 5: Fallback Behavior
# ============================================================================


def example_fallback_behavior():
    """
    Demonstrates fallback behavior when locator is not registered.
    """
    print("\n" + "=" * 70)
    print("Example 5: Fallback Behavior Without Locator")
    print("=" * 70)

    registry = svcs.Registry()

    # Register single implementations via standard svcs
    registry.register_value(Greeting, DefaultGreeting())
    registry.register_value(Database, ProductionDB())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    print("\nNo ServiceLocator registered - falls back to container.get()")
    service = injector(WelcomeService)
    print(f"  Greeting: {type(service.greeting).__name__}")
    print(f"  Database: {type(service.database).__name__}")
    print("  (Works seamlessly with or without ServiceLocator)")


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ServiceLocator and HopscotchInjector Examples")
    print("=" * 70)

    example_basic_multiple_implementations()
    example_lifo_override()
    example_three_tier_precedence()
    example_kwargs_override()
    example_fallback_behavior()

    print("\n" + "=" * 70)
    print("All Examples Complete!")
    print("=" * 70 + "\n")
