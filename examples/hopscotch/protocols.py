"""Using Protocols for replaceable service contracts.

Shows how to define Protocols as service interfaces, then register
multiple implementations. Protocols are extra work, but they provide
explicit contracts that make large-scale replaceable systems reliable.
"""

from dataclasses import dataclass
from typing import Protocol

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry


# Protocol for the Greeting service
class Greeting(Protocol):
    """Protocol defining the greeting service interface."""

    salutation: str

    def greet(self, name: str) -> str:
        """Return a greeting for the given name."""
        ...


# Protocol for the Resource (request context)
class Resource(Protocol):
    """Protocol defining the resource interface."""

    first_name: str


# Default resource implementation
@dataclass
class DefaultResource:
    """Default resource for anonymous requests."""

    first_name: str = "Guest"


# Employee resource implementation
@dataclass
class EmployeeResource:
    """Resource for employee requests."""

    first_name: str = "Team Member"


# Default implementation of the Greeting protocol
@dataclass
class DefaultGreeting:
    """Default greeting implementation."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


# Alternative implementation for employees
@dataclass
class EmployeeGreeting:
    """Greeting implementation for employees."""

    salutation: str = "Hey"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


@dataclass
class WelcomeService:
    """Service that depends on the Greeting protocol."""

    greeting: Inject[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)


def main() -> WelcomeService:
    """Demonstrate protocol-based service registration."""
    registry = HopscotchRegistry()

    # Register implementations under the Greeting protocol
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, EmployeeGreeting, resource=EmployeeResource
    )

    # Request 1: DefaultResource - gets DefaultGreeting
    container = HopscotchContainer(registry)
    container.register_local_value(Resource, DefaultResource())
    service = container.inject(WelcomeService, resource=Resource)
    assert service.greeting.salutation == "Hello"

    # Request 2: EmployeeResource - gets EmployeeGreeting
    container = HopscotchContainer(registry)
    container.register_local_value(Resource, EmployeeResource(first_name="Alice"))
    service = container.inject(WelcomeService, resource=Resource)
    assert service.greeting.salutation == "Hey"

    return service


if __name__ == "__main__":
    print(main())
