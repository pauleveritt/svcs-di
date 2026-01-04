"""Basic dataclass injection example.

This example demonstrates the simplest use case of svcs-di:
- Define a dataclass with Inject dependencies
- Register services with auto()
- Uses the DefaultInjector
- Retrieve services with automatic dependency resolution
"""

from dataclasses import dataclass

import svcs

from svcs_di import Inject, auto


@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service that depends on a database."""

    db: Inject[Database]
    timeout: int = 30


def main():
    """Demonstrate basic dataclass injection."""
    # Create registry and register services
    registry = svcs.Registry()
    registry.register_factory(Database, Database)
    registry.register_factory(Service, auto(Service))

    # Get the service - dependencies are automatically resolved
    container = svcs.Container(registry)
    service = container.get(Service)

    print(f"Service created with timeout={service.timeout}")
    print(f"Database host={service.db.host}, port={service.db.port}")  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
