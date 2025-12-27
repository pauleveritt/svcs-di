"""Multiple implementations example using @injectable(for_=...).

This example demonstrates how to use the for_ parameter to create
multiple implementations of the same service type (protocol or base class).

Key concepts demonstrated:
- Using for_ to specify the service type being implemented
- Multiple implementations selected based on resource context
- Resource-based precedence (exact > subclass > default)
- Integration with HopscotchInjector for automatic resolution
- Comparison with manual ServiceLocator.register() approach

The for_ parameter enables a Hopscotch-style pattern where:
1. You define a common service type (protocol/base class)
2. Multiple implementations registered with @injectable(for_=ServiceType)
3. ServiceLocator automatically resolves based on resource context
4. Consumers depend on the abstract type, not concrete implementations
"""

from dataclasses import dataclass
from typing import Protocol

import svcs

from svcs_di.auto import Injectable
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import HopscotchInjector, scan


# ============================================================================
# Step 1: Define resource types for context-based resolution
# ============================================================================


class RequestContext:
    """Base resource type for all requests."""

    pass


class CustomerContext(RequestContext):
    """Resource type for customer-facing requests."""

    pass


class EmployeeContext(RequestContext):
    """Resource type for internal employee requests."""

    pass


class AdminContext(RequestContext):
    """Resource type for admin/privileged requests."""

    pass


# ============================================================================
# Step 2: Define service protocol (the abstract type)
# ============================================================================


class Greeting(Protocol):
    """Protocol defining the greeting service interface.

    This is the service type that consumers will depend on.
    Multiple implementations will be registered for this type.
    """

    def greet(self, name: str) -> str:
        """Return a personalized greeting message."""
        ...


# ============================================================================
# Step 3: Define multiple implementations using for_ parameter
# ============================================================================


@injectable(for_=Greeting)  # Default implementation (no resource)
@dataclass
class DefaultGreeting:
    """Default greeting implementation - used when no resource matches."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        """Return a standard greeting."""
        return f"{self.salutation}, {name}!"


@injectable(for_=Greeting, resource=CustomerContext)
@dataclass
class CustomerGreeting:
    """Customer-specific greeting implementation."""

    salutation: str = "Good morning"

    def greet(self, name: str) -> str:
        """Return a customer-friendly greeting."""
        return f"{self.salutation}, valued customer {name}!"


@injectable(for_=Greeting, resource=EmployeeContext)
@dataclass
class EmployeeGreeting:
    """Employee-specific greeting implementation."""

    salutation: str = "Hey"

    def greet(self, name: str) -> str:
        """Return a casual employee greeting."""
        return f"{self.salutation}, {name}! How's it going?"


@injectable(for_=Greeting, resource=AdminContext)
@dataclass
class AdminGreeting:
    """Admin-specific greeting implementation."""

    salutation: str = "Greetings"

    def greet(self, name: str) -> str:
        """Return a formal admin greeting."""
        return f"{self.salutation}, Administrator {name}."


# ============================================================================
# Step 4: Define a service that uses the greeting protocol
# ============================================================================


@injectable
@dataclass
class Database:
    """Database service (no for_ - registered directly)."""

    host: str = "localhost"
    port: int = 5432


@injectable
@dataclass
class WelcomeService:
    """Service that depends on Greeting protocol.

    Note: We depend on Greeting (the protocol), not a specific implementation.
    The HopscotchInjector will resolve the appropriate implementation based on
    the resource context at request time.
    """

    greeting: Injectable[Greeting]  # Depends on protocol, not implementation!
    db: Injectable[Database]

    def welcome_user(self, user_id: int, name: str) -> str:
        """Welcome a user with context-appropriate greeting."""
        greeting_msg = self.greeting.greet(name)
        return f"{greeting_msg} [User {user_id} from {self.db.host}]"


# ============================================================================
# Step 5: Demonstration
# ============================================================================


def main():
    """Demonstrate multiple implementations with for_ parameter."""
    print("\n" + "=" * 70)
    print("Multiple Implementations Example - Using @injectable(for_=...)")
    print("=" * 70)

    # ========================================================================
    # Setup: Scan to discover and register all decorated services
    # ========================================================================

    print("\nStep 1: Scanning for @injectable decorated services...")
    registry = svcs.Registry()
    scan(registry)  # Auto-detects current package

    print("✓ Scan complete!")
    print("  - Registered 4 Greeting implementations to ServiceLocator")
    print("    (DefaultGreeting, CustomerGreeting, EmployeeGreeting, AdminGreeting)")
    print("  - Registered Database and WelcomeService to Registry")

    # ========================================================================
    # Usage: Customer Context
    # ========================================================================

    print("\n" + "-" * 70)
    print("Customer Context Request")
    print("-" * 70)

    # Register the context for this request
    registry.register_value(RequestContext, CustomerContext())
    customer_container = svcs.Container(registry)
    customer_injector = HopscotchInjector(
        customer_container, resource=RequestContext
    )

    # Get service - it will resolve CustomerGreeting automatically
    customer_service = customer_injector(WelcomeService)
    result = customer_service.welcome_user(123, "Alice")

    print(f"Result: {result}")
    print(f"  Greeting type used: {type(customer_service.greeting).__name__}")
    assert "Good morning" in result
    assert "valued customer" in result

    # ========================================================================
    # Usage: Employee Context
    # ========================================================================

    print("\n" + "-" * 70)
    print("Employee Context Request")
    print("-" * 70)

    # New request with employee context
    registry.register_value(RequestContext, EmployeeContext())
    employee_container = svcs.Container(registry)
    employee_injector = HopscotchInjector(
        employee_container, resource=RequestContext
    )

    # Get service - it will resolve EmployeeGreeting automatically
    employee_service = employee_injector(WelcomeService)
    result = employee_service.welcome_user(456, "Bob")

    print(f"Result: {result}")
    print(f"  Greeting type used: {type(employee_service.greeting).__name__}")
    assert "Hey" in result
    assert "How's it going" in result

    # ========================================================================
    # Usage: Admin Context
    # ========================================================================

    print("\n" + "-" * 70)
    print("Admin Context Request")
    print("-" * 70)

    registry.register_value(RequestContext, AdminContext())
    admin_container = svcs.Container(registry)
    admin_injector = HopscotchInjector(admin_container, resource=RequestContext)

    admin_service = admin_injector(WelcomeService)
    result = admin_service.welcome_user(789, "Carol")

    print(f"Result: {result}")
    print(f"  Greeting type used: {type(admin_service.greeting).__name__}")
    assert "Greetings" in result
    assert "Administrator" in result

    # ========================================================================
    # Usage: No Context (Uses Default)
    # ========================================================================

    print("\n" + "-" * 70)
    print("No Context (Default Fallback)")
    print("-" * 70)

    # Don't register any context - should use default
    default_container = svcs.Container(svcs.Registry())
    scan(default_container.registry)  # Re-scan in clean registry

    default_injector = HopscotchInjector(default_container, resource=None)
    default_service = default_injector(WelcomeService)
    result = default_service.welcome_user(999, "Dave")

    print(f"Result: {result}")
    print(f"  Greeting type used: {type(default_service.greeting).__name__}")
    assert "Hello" in result

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("1. Use @injectable(for_=ServiceType) to register implementations")
    print("2. Multiple implementations of same type are stored in ServiceLocator")
    print("3. Resource-based precedence: exact > subclass > default")
    print("4. Consumers depend on protocol/base class, not concrete implementations")
    print("5. HopscotchInjector resolves appropriate implementation at request time")
    print("\n✓ All assertions passed!")

    print("\n" + "=" * 70)
    print("Comparison: for_ vs Manual Registration")
    print("=" * 70)
    print("\nWith for_ parameter:")
    print("  @injectable(for_=Greeting, resource=CustomerContext)")
    print("  class CustomerGreeting: ...")
    print("\nManual equivalent:")
    print("  locator = locator.register(")
    print("      Greeting, CustomerGreeting, resource=CustomerContext")
    print("  )")
    print("\nThe for_ parameter provides:")
    print("  ✓ Declarative style (mark at definition, not registration)")
    print("  ✓ Auto-discovery via scan()")
    print("  ✓ No manual ServiceLocator setup code")
    print("  ✓ Clear intent: 'this implements that'")


if __name__ == "__main__":
    main()
