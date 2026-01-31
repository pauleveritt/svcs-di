"""Function factory with DefaultInjector.

This example demonstrates using functions as factory providers with the
DefaultInjector. Functions can be registered via `register_implementation()`
and can have their parameters automatically injected via `Inject[T]`.

Key concepts:
- Function factories return service instances (not the function itself)
- `Inject[T]` parameters are resolved from the container
- Direct function calls via injector resolve function parameters
- HopscotchRegistry function factories are invoked when resolving Inject[T] fields
- Functions MUST specify `for_` in @injectable (return type inference not supported)
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import DefaultInjector, Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry, injectable, scan


# ============================================================================
# Service definitions
# ============================================================================


@dataclass
class Database:
    """A database service that will be injected into factories."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Greeting:
    """A greeting service created by factory functions."""

    message: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.message}, {name}!"


@dataclass
class WelcomeService:
    """Service that depends on Greeting via injection.

    When using HopscotchRegistry, the Inject[Greeting] field triggers
    a locator lookup, which finds the registered function factory.
    """

    greeting: Inject[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)


# ============================================================================
# Factory functions
# ============================================================================


def create_greeting(db: Inject[Database]) -> Greeting:
    """Factory function that creates Greeting with injected Database.

    The `db` parameter is automatically resolved from the container
    because it uses the `Inject[Database]` type annotation.
    """
    return Greeting(message=f"Hello from {db.host}:{db.port}")


@injectable(for_=Greeting)
def create_decorated_greeting(db: Inject[Database]) -> Greeting:
    """Factory function decorated with @injectable.

    The `for_=Greeting` parameter tells the scanner which service type
    this factory produces. Functions must specify `for_` explicitly.
    """
    return Greeting(message=f"Decorated factory on {db.host}")


# ============================================================================
# Example demonstrations
# ============================================================================


def demonstrate_direct_function_call() -> Greeting:
    """Demonstrate direct function call with DefaultInjector.

    This shows the basic pattern for calling a function directly:
    1. Register dependencies (Database)
    2. Create an injector
    3. Call the factory function through the injector
    """
    # Setup registry and register the Database service
    registry = Registry()
    registry.register_factory(Database, Database)

    # Create container and injector
    container = Container(registry)
    injector = DefaultInjector(container=container)

    # Call the factory function directly - Inject[Database] is resolved
    greeting = injector(create_greeting)

    # Verify the factory received the injected database
    assert greeting.message == "Hello from localhost:5432"
    assert greeting.greet("World") == "Hello from localhost:5432, World!"

    return greeting


def demonstrate_hopscotch_registration() -> WelcomeService:
    """Demonstrate function factory with HopscotchRegistry.

    Function factories are registered in the ServiceLocator and invoked
    when resolving Inject[T] fields. When WelcomeService is injected,
    its Inject[Greeting] field triggers the locator lookup, which finds
    and calls the create_greeting function factory.
    """
    # Setup HopscotchRegistry and register services
    registry = HopscotchRegistry()
    registry.register_implementation(Database, Database)
    registry.register_implementation(Greeting, create_greeting)

    # Inject WelcomeService - Inject[Greeting] triggers locator lookup
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)

    # Verify the function factory was called for the Greeting dependency
    assert service.greeting.message == "Hello from localhost:5432"
    assert service.welcome("World") == "Hello from localhost:5432, World!"

    return service


def demonstrate_injectable_decorator() -> WelcomeService:
    """Demonstrate @injectable decorator on factory functions.

    Functions can be decorated with @injectable for automatic discovery
    via scan(). The `for_` parameter is required for functions.
    """
    # Setup registry and register Database
    registry = HopscotchRegistry()
    registry.register_implementation(Database, Database)

    # Scan discovers @injectable decorated functions
    scan(
        registry,
        locals_dict={
            "create_decorated_greeting": create_decorated_greeting,
        },
    )

    # Inject WelcomeService - locator finds the decorated function
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)

    # Verify the decorated factory was used
    assert service.greeting.message == "Decorated factory on localhost"

    return service


def demonstrate_custom_database() -> Greeting:
    """Demonstrate factory with custom dependency values.

    Shows that injected values come from the container, so customizing
    the registered Database changes what the factory receives.
    """
    registry = Registry()
    # Register a custom Database configuration
    registry.register_value(Database, Database(host="production-db", port=5433))

    container = Container(registry)
    injector = DefaultInjector(container=container)

    # The factory receives the custom Database
    greeting = injector(create_greeting)

    assert greeting.message == "Hello from production-db:5433"

    return greeting


# ============================================================================
# Main entry point
# ============================================================================


def main() -> dict[str, Greeting | WelcomeService]:
    """Run all demonstrations and return results."""
    results: dict[str, Greeting | WelcomeService] = {
        "direct": demonstrate_direct_function_call(),
        "hopscotch": demonstrate_hopscotch_registration(),
        "decorator": demonstrate_injectable_decorator(),
        "custom_db": demonstrate_custom_database(),
    }

    # Summary assertions
    direct_result = results["direct"]
    assert isinstance(direct_result, Greeting)
    assert direct_result.message == "Hello from localhost:5432"

    hopscotch_result = results["hopscotch"]
    assert isinstance(hopscotch_result, WelcomeService)
    assert hopscotch_result.greeting.message == "Hello from localhost:5432"

    decorator_result = results["decorator"]
    assert isinstance(decorator_result, WelcomeService)
    assert decorator_result.greeting.message == "Decorated factory on localhost"

    custom_result = results["custom_db"]
    assert isinstance(custom_result, Greeting)
    assert custom_result.message == "Hello from production-db:5433"

    return results


if __name__ == "__main__":
    print(main())
