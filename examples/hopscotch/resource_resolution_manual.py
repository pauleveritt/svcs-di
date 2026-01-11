"""Resource-based resolution - manual approach.

Shows multiple implementations selected by resource context using
ServiceLocator and HopscotchInjector directly. This demonstrates the
two-tier precedence system: exact match > default.
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject
from svcs_di.injectors.hopscotch import HopscotchInjector
from svcs_di.injectors.locator import ServiceLocator


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
    """Demonstrate resource-based resolution with manual setup."""
    # Create ServiceLocator with multiple implementations
    locator = ServiceLocator()
    locator = locator.register(Greeting, Greeting)  # Default (score: 0)
    locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)

    # Setup registry
    registry = Registry()
    registry.register_value(ServiceLocator, locator)

    # Request 1: No resource - gets default Greeting
    container = Container(registry)
    injector = HopscotchInjector(container=container)
    service = injector(WelcomeService)
    assert service.greeting.salutation == "Hello"

    # Request 2: EmployeeContext - gets EmployeeGreeting (exact match)
    registry.register_value(EmployeeContext, EmployeeContext())
    container = Container(registry)
    injector = HopscotchInjector(container=container, resource=EmployeeContext)
    service = injector(WelcomeService)
    assert service.greeting.salutation == "Hey"

    return service


if __name__ == "__main__":
    print(main())
