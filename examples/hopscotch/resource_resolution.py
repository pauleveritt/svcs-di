"""Resource-based resolution with HopscotchRegistry.

Shows the same multi-implementation pattern as resource_resolution_manual.py
but using HopscotchRegistry and HopscotchContainer to simplify setup.
"""

from dataclasses import dataclass

from svcs_di import HopscotchContainer, HopscotchRegistry, Inject


# Resource class
class EmployeeContext:
    """Resource type for employee requests."""


# Service implementations
@dataclass
class Greeting:
    """Default greeting (no resource constraint)."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


@dataclass
class EmployeeGreeting(Greeting):
    """Greeting for EmployeeContext."""

    salutation: str = "Hey"


@dataclass
class WelcomeService:
    """Service using Inject[Greeting]."""

    greeting: Inject[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)


def main() -> WelcomeService:
    """Demonstrate resource-based resolution with HopscotchRegistry."""
    # HopscotchRegistry manages ServiceLocator internally
    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(
        Greeting, EmployeeGreeting, resource=EmployeeContext
    ) # A variation when talking to an Employee

    # Request 1: No resource - gets default Greeting
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)
    assert service.greeting.salutation == "Hello"

    # Request 2: EmployeeContext - gets EmployeeGreeting (exact match)
    registry.register_value(EmployeeContext, EmployeeContext())
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService, resource=EmployeeContext)
    assert service.greeting.salutation == "Hey"

    return service


if __name__ == "__main__":
    print(main())
