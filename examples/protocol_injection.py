"""Protocol-based injection example.

This example demonstrates using protocols for abstract dependencies:
- Define a Protocol for a service interface
- Provide a concrete implementation
- Use Inject[ProtocolType] for loose coupling
"""

from dataclasses import dataclass
from typing import Protocol

import svcs

from svcs_di import Inject, auto


class GreeterProtocol(Protocol):
    """Protocol defining the interface for a greeter service."""

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        ...


class EnglishGreeter:
    """Concrete implementation of GreeterProtocol."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class SpanishGreeter:
    """Alternative concrete implementation of GreeterProtocol."""

    def greet(self, name: str) -> str:
        return f"¡Hola, {name}!"


@dataclass
class Application:
    """Application that depends on a greeter (via protocol)."""

    greeter: Inject[GreeterProtocol]
    app_name: str = "MyApp"


def main():
    """Demonstrate protocol-based injection."""
    # Create registry
    registry = svcs.Registry()

    # Register protocol with concrete implementation (English)
    registry.register_value(GreeterProtocol, EnglishGreeter())

    # Register application with auto()
    registry.register_factory(Application, auto(Application))

    # Get application - greeter is resolved via protocol
    container = svcs.Container(registry)
    app = container.get(Application)

    print(f"{app.app_name}: {app.greeter.greet('World')}")  # type: ignore[attr-defined]

    # Demonstrate swapping implementations
    registry2 = svcs.Registry()
    registry2.register_value(GreeterProtocol, SpanishGreeter())
    registry2.register_factory(Application, auto(Application))

    container2 = svcs.Container(registry2)
    app2 = container2.get(Application)

    print(f"{app2.app_name}: {app2.greeter.greet('Mundo')}")  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
