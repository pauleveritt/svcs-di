"""Resource-based resolution with HopscotchRegistry.

Shows the same multi-implementation pattern as resource_resolution_manual.py
but using HopscotchRegistry and HopscotchContainer to simplify setup.

Resource[T] is a type marker for resource injection:
- Inject[T] = "resolve service of type T from registry"
- Resource[T] = "give me the current resource, typed as T"
"""

from dataclasses import dataclass

from svcs_di import Inject, Resource
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry


# Resource class
class Employee:
    """Resource type for employee requests."""

    name: str = "Employee"


# Service implementations
@dataclass
class Greeting:
    """Default greeting (no resource constraint)."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


@dataclass
class EmployeeGreeting(Greeting):
    """Greeting for Employee."""

    salutation: str = "Hey"


@dataclass
class WelcomeService:
    """Service using Inject[Greeting]."""

    greeting: Inject[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)


@dataclass
class ResourceAwareService:
    """Service that accesses the current resource via Resource[T]."""

    greeting: Inject[Greeting]
    resource: Resource[Employee]  # Gets container.resource, typed as Employee

    def welcome(self, name: str) -> str:
        return f"[{type(self.resource).__name__}] {self.greeting.greet(name)}"


def main() -> WelcomeService:
    """Demonstrate resource-based resolution with HopscotchRegistry."""
    # HopscotchRegistry manages ServiceLocator internally
    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(
        Greeting, EmployeeGreeting, resource=Employee
    )  # A variation when talking to an Employee

    # Request 1: No resource - gets default Greeting
    container = HopscotchContainer(registry)
    service = container.inject(WelcomeService)
    assert service.greeting.salutation == "Hello"

    # Request 2: With resource instance - gets EmployeeGreeting
    # The container derives type(resource) for ServiceLocator matching
    container = HopscotchContainer(registry, resource=Employee())
    service = container.inject(WelcomeService)
    assert service.greeting.salutation == "Hey"

    # Request 3: ResourceAwareService can access the resource via Resource[Employee]
    container = HopscotchContainer(registry, resource=Employee())
    aware_service = container.inject(ResourceAwareService)
    assert isinstance(aware_service.resource, Employee)
    assert "[Employee]" in aware_service.welcome("Alice")

    # Request 4: Override resource type explicitly
    container = HopscotchContainer(registry, resource=Employee())
    service = container.inject(WelcomeService, resource=type(None))  # Override to None
    assert service.greeting.salutation == "Hello"  # Falls back to default

    return service


if __name__ == "__main__":
    print(main())
