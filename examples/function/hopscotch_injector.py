"""Function factory with HopscotchInjector.

This example demonstrates using functions as factory providers with the
HopscotchInjector, which supports ServiceLocator-based multi-implementation
resolution using resource and location context.

Key concepts:
- Function factories are registered with resource and/or location context
- `@injectable(for_=X, resource=Y)` pattern works on functions
- ServiceLocator selects the appropriate implementation based on context
- Functions MUST specify `for_` parameter in @injectable decorator
- Locator is consulted when resolving Inject[T] fields, not when calling inject(T) directly
"""

from dataclasses import dataclass

from svcs_di import HopscotchContainer, HopscotchRegistry, Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.scanning import scan


# ============================================================================
# Resource context classes
# ============================================================================


class CustomerContext:
    """Resource type for customer-facing requests."""


class EmployeeContext:
    """Resource type for internal employee requests."""


# ============================================================================
# Service definitions
# ============================================================================


@dataclass
class Database:
    """Database service for connection info."""

    host: str = "localhost"


@dataclass
class Greeting:
    """A greeting service with customizable salutation."""

    salutation: str = "Hello"
    source: str = "default"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}! [{self.source}]"


@dataclass
class WelcomeService:
    """Service that depends on Greeting via injection.

    When using HopscotchRegistry with resource context, the Inject[Greeting]
    field triggers locator lookup with resource-based selection.
    """

    greeting: Inject[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)


# ============================================================================
# Factory functions with resource context
# ============================================================================


def create_default_greeting(db: Inject[Database]) -> Greeting:
    """Default greeting factory (no resource constraint).

    This is used when no specific resource context matches.
    """
    return Greeting(
        salutation="Hello",
        source=f"default factory on {db.host}",
    )


def create_customer_greeting(db: Inject[Database]) -> Greeting:
    """Customer greeting factory.

    Returns a formal greeting for customer-facing contexts.
    """
    return Greeting(
        salutation="Welcome, valued customer",
        source=f"customer factory on {db.host}",
    )


def create_employee_greeting(db: Inject[Database]) -> Greeting:
    """Employee greeting factory.

    Returns a casual greeting for internal employee contexts.
    """
    return Greeting(
        salutation="Hey there",
        source=f"employee factory on {db.host}",
    )


# ============================================================================
# Decorated factory functions for scanning
# ============================================================================


@injectable(for_=Greeting)
def create_scanned_default(db: Inject[Database]) -> Greeting:
    """Scanned default greeting factory."""
    return Greeting(salutation="Hi", source="scanned default")


@injectable(for_=Greeting, resource=CustomerContext)
def create_scanned_customer(db: Inject[Database]) -> Greeting:
    """Scanned customer greeting factory.

    The resource=CustomerContext constrains when this factory is selected.
    """
    return Greeting(salutation="Dear Customer", source="scanned customer")


@injectable(for_=Greeting, resource=EmployeeContext)
def create_scanned_employee(db: Inject[Database]) -> Greeting:
    """Scanned employee greeting factory.

    The resource=EmployeeContext constrains when this factory is selected.
    """
    return Greeting(salutation="Hi team member", source="scanned employee")


# ============================================================================
# Example demonstrations
# ============================================================================


def demonstrate_manual_resource_registration() -> dict[str, WelcomeService]:
    """Demonstrate manual function factory registration with resource context.

    Shows how to register multiple function factories for the same service
    type, differentiated by resource context. The locator is consulted when
    resolving Inject[Greeting] in WelcomeService.
    """
    registry = HopscotchRegistry()

    # Register Database (dependency for our factories)
    registry.register_implementation(Database, Database)

    # Register multiple Greeting factories with different resource contexts
    registry.register_implementation(Greeting, create_default_greeting)
    registry.register_implementation(
        Greeting, create_customer_greeting, resource=CustomerContext
    )
    registry.register_implementation(
        Greeting, create_employee_greeting, resource=EmployeeContext
    )

    results: dict[str, WelcomeService] = {}

    # Test 1: No resource context - gets default factory
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)
    results["default"] = service
    assert service.greeting.salutation == "Hello"
    assert "default factory" in service.greeting.source

    # Test 2: CustomerContext - gets customer factory
    # Register a CustomerContext value so the locator can find it
    registry.register_value(CustomerContext, CustomerContext())
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService, resource=CustomerContext)
    results["customer"] = service
    assert service.greeting.salutation == "Welcome, valued customer"
    assert "customer factory" in service.greeting.source

    # Test 3: EmployeeContext - gets employee factory
    registry.register_value(EmployeeContext, EmployeeContext())
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService, resource=EmployeeContext)
    results["employee"] = service
    assert service.greeting.salutation == "Hey there"
    assert "employee factory" in service.greeting.source

    return results


def demonstrate_scanned_resource_factories() -> dict[str, WelcomeService]:
    """Demonstrate @injectable decorated functions with resource context.

    The scan() function discovers decorated functions and registers them
    with the appropriate resource constraints.
    """
    registry = HopscotchRegistry()
    registry.register_implementation(Database, Database)

    # Scan discovers all @injectable decorated functions
    scan(
        registry,
        locals_dict={
            "create_scanned_default": create_scanned_default,
            "create_scanned_customer": create_scanned_customer,
            "create_scanned_employee": create_scanned_employee,
        },
    )

    results: dict[str, WelcomeService] = {}

    # Test 1: No resource - gets scanned default
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)
    results["default"] = service
    assert service.greeting.salutation == "Hi"
    assert service.greeting.source == "scanned default"

    # Test 2: CustomerContext - gets scanned customer
    registry.register_value(CustomerContext, CustomerContext())
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService, resource=CustomerContext)
    results["customer"] = service
    assert service.greeting.salutation == "Dear Customer"
    assert service.greeting.source == "scanned customer"

    # Test 3: EmployeeContext - gets scanned employee
    registry.register_value(EmployeeContext, EmployeeContext())
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService, resource=EmployeeContext)
    results["employee"] = service
    assert service.greeting.salutation == "Hi team member"
    assert service.greeting.source == "scanned employee"

    return results


def demonstrate_mixed_class_and_function() -> dict[str, WelcomeService]:
    """Demonstrate mixing class and function implementations.

    The ServiceLocator can hold both class and function implementations
    for the same service type.
    """

    @dataclass
    class VIPGreeting(Greeting):
        """VIP greeting class implementation."""

        salutation: str = "Distinguished Guest"
        source: str = "VIP class"

    class VIPContext:
        """Resource for VIP customers."""

    registry = HopscotchRegistry()
    registry.register_implementation(Database, Database)

    # Register function factory as default
    registry.register_implementation(Greeting, create_default_greeting)

    # Register class implementation for VIP context
    registry.register_implementation(Greeting, VIPGreeting, resource=VIPContext)

    results: dict[str, WelcomeService] = {}

    # Default: uses function factory
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)
    results["default"] = service
    assert "default factory" in service.greeting.source

    # VIP: uses class implementation
    registry.register_value(VIPContext, VIPContext())
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService, resource=VIPContext)
    results["vip"] = service
    assert service.greeting.source == "VIP class"
    assert isinstance(service.greeting, VIPGreeting)

    return results


def demonstrate_factory_with_dependencies() -> WelcomeService:
    """Demonstrate function factory that depends on other services.

    Factory functions can have multiple Inject[T] parameters,
    each resolved from the container via the injector.
    """

    @dataclass
    class Config:
        """Configuration service."""

        app_name: str = "MyApp"

    def create_configured_greeting(
        db: Inject[Database],
        config: Inject[Config],
    ) -> Greeting:
        """Factory with multiple dependencies."""
        return Greeting(
            salutation=f"Welcome to {config.app_name}",
            source=f"configured factory on {db.host}",
        )

    registry = HopscotchRegistry()
    registry.register_implementation(Database, Database)
    registry.register_implementation(Config, Config)
    registry.register_implementation(Greeting, create_configured_greeting)

    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)

    assert service.greeting.salutation == "Welcome to MyApp"
    assert "configured factory on localhost" in service.greeting.source

    return service


# ============================================================================
# Main entry point
# ============================================================================


def main() -> dict[str, dict[str, WelcomeService] | WelcomeService]:
    """Run all demonstrations and return results."""
    results: dict[str, dict[str, WelcomeService] | WelcomeService] = {
        "manual_resource": demonstrate_manual_resource_registration(),
        "scanned_resource": demonstrate_scanned_resource_factories(),
        "mixed_implementations": demonstrate_mixed_class_and_function(),
        "factory_dependencies": demonstrate_factory_with_dependencies(),
    }

    # Summary assertions
    manual = results["manual_resource"]
    assert isinstance(manual, dict)
    assert manual["default"].greeting.salutation == "Hello"
    assert manual["customer"].greeting.salutation == "Welcome, valued customer"

    scanned = results["scanned_resource"]
    assert isinstance(scanned, dict)
    assert scanned["default"].greeting.salutation == "Hi"
    assert scanned["customer"].greeting.salutation == "Dear Customer"

    return results


if __name__ == "__main__":
    print(main())
