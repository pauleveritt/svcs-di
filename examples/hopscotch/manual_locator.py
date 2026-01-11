"""Manual ServiceLocator and HopscotchInjector usage.

Same use case as getting_started.py, but using manual ServiceLocator and
HopscotchInjector instead of HopscotchRegistry and HopscotchContainer.
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject
from svcs_di.injectors.hopscotch import HopscotchInjector
from svcs_di.injectors.locator import ServiceLocator


@dataclass
class Greeting:
    """A greeting service."""

    message: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.message}, {name}!"


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"

    def connect(self) -> str:
        return f"Connected to {self.host}"


@dataclass
class WelcomeService:
    """Service that uses greeting and database via dependency injection."""

    greeting: Inject[Greeting]
    database: Inject[Database]

    def welcome(self, name: str) -> str:
        return f"{self.database.connect()} | {self.greeting.greet(name)}"


def main() -> WelcomeService:
    """Demonstrate manual ServiceLocator and HopscotchInjector setup."""
    # Create ServiceLocator and register implementations
    locator = ServiceLocator()
    locator = locator.register(Greeting, Greeting)
    locator = locator.register(Database, Database)

    # Create registry and register the locator
    registry = Registry()
    registry.register_value(ServiceLocator, locator)

    # Create container and injector manually
    container = Container(registry)
    injector = HopscotchInjector(container=container)

    # Use injector to create service
    service = injector(WelcomeService)

    # Verify injection worked
    assert service.greeting.message == "Hello"
    assert service.database.host == "localhost"
    assert "Hello, Alice!" in service.welcome("Alice")

    return service


if __name__ == "__main__":
    print(main())
