"""Protocol-based injection example.

This example demonstrates using protocols for abstract dependencies:
- Define a Protocol for a service interface
- Provide a concrete implementation
- Use Inject[ProtocolType] for loose coupling
"""

from dataclasses import dataclass
from typing import Protocol

from svcs import Container, Registry

from svcs_di import Inject, auto


class Greeter(Protocol):
    """Protocol defining the interface for a greeter service."""

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        ...


class DefaultGreeter:
    """Concrete implementation of GreeterProtocol."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


# A service that depends on an implementation of the protocol
@dataclass
class Application:
    """Application that depends on a greeter (via protocol)."""

    greeter: Inject[Greeter]
    app_name: str = "MyApp"


def main() -> Application:
    # Create registry
    registry = Registry()

    # Register protocol with concrete implementation
    registry.register_factory(Greeter, DefaultGreeter)

    # Register application with auto(), which lets us resolve `Inject`
    registry.register_factory(Application, auto(Application))

    # Later, during a request...
    # Get application - greeter is resolved via protocol
    container = Container(registry)
    app = container.get(Application)

    assert app.greeter.greet("World") == "Hello, World!"

    return app


if __name__ == "__main__":
    print(main())
