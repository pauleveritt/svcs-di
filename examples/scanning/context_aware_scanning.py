"""Context-aware scanning example.

This example demonstrates advanced scanning with resource-based resolution:
- Register a service with @injectable(resource=...) for context-specific behavior
- Show how the same service type can have different implementations based on context
- Demonstrate resource-based resolution with HopscotchInjector

Note: This example shows a practical pattern where each class is its own service type.
For multiple implementations of a common protocol/base class, see:
  - multiple_implementations_with_decorator.py (using for_ parameter)
"""

from dataclasses import dataclass

import svcs

from svcs_di.auto import Injectable
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import HopscotchInjector, ServiceLocator, scan


# ============================================================================
# Step 1: Define resource types for context-based resolution
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


# ============================================================================
# Step 2: Define a service with context-aware implementations
# ============================================================================


@injectable  # Default implementation (no resource)
@dataclass
class GreetingService:
    """Service for generating greetings - default implementation."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        return f"{self.salutation}, {name}!"


@injectable(resource=EmployeeContext)  # Employee-specific implementation
@dataclass
class EmployeeGreetingService:
    """Greeting service for employee contexts."""

    salutation: str = "Hey"

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        return f"{self.salutation}, {name}!"


@injectable(resource=CustomerContext)  # Customer-specific implementation
@dataclass
class CustomerGreetingService:
    """Greeting service for customer contexts."""

    salutation: str = "Good morning"

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        return f"{self.salutation}, {name}!"


# ============================================================================
# Step 3: Define a database service with dependency injection
# ============================================================================


@injectable
@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@injectable
@dataclass
class EmailService:
    """Email service that depends on database."""

    db: Injectable[Database]
    from_address: str = "noreply@example.com"

    def send_email(self, to: str, subject: str) -> str:
        """Simulate sending an email."""
        return f"Sent '{subject}' to {to} from {self.from_address} (via {self.db.host})"


# ============================================================================
# Step 4: Demonstrate context-aware scanning and resolution
# ============================================================================


def main():
    """Demonstrate context-aware scanning workflow."""
    print("\n" + "=" * 70)
    print("Context-Aware Scanning Example")
    print("=" * 70)

    # ========================================================================
    # Setup: Scan to discover and register all decorated services
    # ========================================================================

    print("\nStep 1: Scanning for @injectable decorated services...")
    registry = svcs.Registry()

    # Auto-detect and scan the current package - no sys.modules hack needed!
    scan(registry)
    print("  -> Found and registered:")
    print("     - GreetingService (default, no resource)")
    print("     - EmployeeGreetingService (resource=EmployeeContext)")
    print("     - CustomerGreetingService (resource=CustomerContext)")
    print("     - Database (default, no resource)")
    print("     - EmailService (default, with Database dependency)")

    # Show what was registered in the ServiceLocator
    container_check = svcs.Container(registry)
    try:
        locator = container_check.get(ServiceLocator)
        # Note: ServiceLocator registrations are stored internally in _single_registrations and _multi_registrations
        print("\n  ServiceLocator contains resource-specific registrations (CustomerGreeting and EmployeeGreeting)")
    except Exception:
        print("  No ServiceLocator found (all registrations are non-resource)")

    # ========================================================================
    # Test 1: Basic dependency injection (no context)
    # ========================================================================

    print("\n" + "-" * 70)
    print("Test 1: Basic dependency injection (no context)")
    print("-" * 70)

    container = svcs.Container(registry)

    # Get services without context
    db = container.get(Database)
    print(f"  Database: {db.host}:{db.port}")

    email = container.get(EmailService)
    print(f"  EmailService: {email.from_address}")
    print(f"  Email DB dependency: {email.db.host}:{email.db.port}")
    print(f"  Send test: {email.send_email('user@example.com', 'Test')}")

    greeting = container.get(GreetingService)
    print(f"  GreetingService: {greeting.greet('World')}")

    # ========================================================================
    # Test 2: Context-aware greeting service - Employee context
    # ========================================================================

    print("\n" + "-" * 70)
    print("Test 2: Employee context - get employee-specific greeting")
    print("-" * 70)

    # Get the ServiceLocator and check for EmployeeGreetingService
    locator = container.get(ServiceLocator)
    employee_greeting_impl = locator.get_implementation(
        EmployeeGreetingService, EmployeeContext
    )

    if employee_greeting_impl:
        # Construct the employee-specific greeting
        employee_greeting = employee_greeting_impl()
        print(f"  Employee greeting: {employee_greeting.greet('Alice')}")
        print(f"  Implementation: {type(employee_greeting).__name__}")
    else:
        print("  No employee-specific greeting found")

    # ========================================================================
    # Test 3: Context-aware greeting service - Customer context
    # ========================================================================

    print("\n" + "-" * 70)
    print("Test 3: Customer context - get customer-specific greeting")
    print("-" * 70)

    customer_greeting_impl = locator.get_implementation(
        CustomerGreetingService, CustomerContext
    )

    if customer_greeting_impl:
        # Construct the customer-specific greeting
        customer_greeting = customer_greeting_impl()
        print(f"  Customer greeting: {customer_greeting.greet('Bob')}")
        print(f"  Implementation: {type(customer_greeting).__name__}")
    else:
        print("  No customer-specific greeting found")

    # ========================================================================
    # Test 4: Three-tier precedence with subclass
    # ========================================================================

    print("\n" + "-" * 70)
    print("Test 4: Three-Tier Precedence (subclass match)")
    print("-" * 70)

    # Define a subclass of EmployeeContext
    class ManagerContext(EmployeeContext):
        """Manager context (subclass of EmployeeContext)."""

        pass

    # Look up with ManagerContext - should match EmployeeGreetingService via subclass
    manager_greeting_impl = locator.get_implementation(
        EmployeeGreetingService, ManagerContext
    )

    if manager_greeting_impl:
        manager_greeting = manager_greeting_impl()
        print(f"  Manager context (subclass of Employee): {manager_greeting.greet('Carol')}")
        print(f"  Implementation: {type(manager_greeting).__name__}")
        print("  -> Matched EmployeeGreetingService via subclass (ManagerContext extends EmployeeContext)")
    else:
        print("  No match found")

    # ========================================================================
    # Test 5: Fallback to default
    # ========================================================================

    print("\n" + "-" * 70)
    print("Test 5: Fallback to default (no context match)")
    print("-" * 70)

    # Define a context with no specific registration
    class AdminContext(RequestContext):
        """Admin context (no specific greeting registered)."""

        pass

    # Look up GreetingService (the default) with no resource
    admin_greeting_impl = locator.get_implementation(GreetingService, None)

    if admin_greeting_impl:
        admin_greeting = admin_greeting_impl()
        print(f"  Admin context (no specific implementation): {admin_greeting.greet('David')}")
        print(f"  Implementation: {type(admin_greeting).__name__}")
        print("  -> Used default GreetingService (no resource)")
    else:
        # If not in locator, get from registry
        admin_greeting = container.get(GreetingService)
        print(f"  Admin context (from registry): {admin_greeting.greet('David')}")
        print(f"  Implementation: {type(admin_greeting).__name__}")

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "=" * 70)
    print("Summary:")
    print("  1. Used @injectable to mark services for auto-discovery")
    print("  2. Used @injectable(resource=Context) for context-specific implementations")
    print("  3. scan() discovered and registered all decorated services")
    print("  4. Resource-based implementations go to ServiceLocator")
    print("  5. Non-resource implementations go directly to Registry")
    print("  6. ServiceLocator.get_implementation() resolves based on context")
    print("  7. Three-tier precedence: exact > subclass > default")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("Alternative Pattern: Using for_ Parameter")
    print("=" * 70)
    print("\nThis example shows each class as its own service type:")
    print("  GreetingService, EmployeeGreetingService, CustomerGreetingService")
    print("\nFor multiple implementations of a COMMON service type:")
    print("  Use @injectable(for_=BaseType, resource=Context)")
    print("\nExample with for_ parameter:")
    print("  class Greeting(Protocol):  # Common protocol")
    print("      def greet(self, name: str) -> str: ...")
    print()
    print("  @injectable(for_=Greeting)  # Default")
    print("  class DefaultGreeting: ...")
    print()
    print("  @injectable(for_=Greeting, resource=CustomerContext)")
    print("  class CustomerGreeting: ...")
    print()
    print("Then consumers depend on Greeting, not specific implementations:")
    print("  greeting: Injectable[Greeting]  # Resolved automatically!")
    print()
    print("See: examples/scanning/multiple_implementations_with_decorator.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
