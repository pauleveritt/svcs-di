"""Auto-discovery with @injectable and scan().

Shows how to use the @injectable decorator for automatic service
registration via scan(), removing boilerplate registration code.
"""

from dataclasses import dataclass

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry, injectable, scan


# Resource class for varying implementations
class EmployeeContext:
    """Resource type for employee requests."""


# @injectable marks a class for auto-discovery by scan()
@injectable
@dataclass
class Greeting:
    """Default greeting (discovered by scan)."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


# @injectable(resource=...) constrains when this implementation is used
@injectable(for_=Greeting, resource=EmployeeContext)
@dataclass
class EmployeeGreeting:
    """Greeting for EmployeeContext (discovered by scan)."""

    salutation: str = "Hey"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


@dataclass
class WelcomeService:
    """Service using Inject[Greeting]."""

    greeting: Inject[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)


def main() -> WelcomeService:
    """Demonstrate @injectable and scan() with HopscotchRegistry."""
    # scan() discovers @injectable classes and registers them automatically
    registry = HopscotchRegistry()
    scan(
        registry,
        locals_dict={
            "Greeting": Greeting,
            "EmployeeGreeting": EmployeeGreeting,
        },
    )

    # Test 1: No resource - gets Greeting
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)
    assert service.greeting.salutation == "Hello"

    # Test 2: EmployeeContext resource - gets EmployeeGreeting
    container = HopscotchContainer(registry)
    container.register_local_value(EmployeeContext, EmployeeContext())
    service = container.inject(WelcomeService, resource=EmployeeContext)
    assert service.greeting.salutation == "Hey"

    return service


if __name__ == "__main__":
    print(main())
