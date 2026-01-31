"""Getting Started with HopscotchInjector.

The simplest example using HopscotchRegistry and HopscotchContainer for
service resolution with dependency injection.
"""

from dataclasses import dataclass

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry


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
    """Demonstrate basic HopscotchRegistry and HopscotchContainer usage."""
    # Setup registry with implementations
    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)
    registry.register_implementation(Database, Database)

    # Create container and inject
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)

    # Verify injection worked
    assert service.greeting.message == "Hello"
    assert service.database.host == "localhost"
    assert "Hello, Alice!" in service.welcome("Alice")

    return service


if __name__ == "__main__":
    print(main())
