"""Basic dataclass injection example.

This example demonstrates the simplest use case of svcs-di:
- Uses the DefaultInjector
- Define a dataclass with Inject dependencies
- Register services with auto()
- Retrieve services with automatic dependency resolution
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject, auto


@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


# The `db` is injected from the container
@dataclass
class Service:
    """A service that depends on a database."""

    db: Inject[Database]
    timeout: int = 30


def main() -> Service:
    # Create registry and register services
    registry = Registry()
    registry.register_factory(Database, Database)
    registry.register_factory(Service, auto(Service))

    # Get the service - dependencies are automatically resolved
    container = Container(registry)
    service = container.get(Service)

    assert service.db.host == "localhost"
    assert service.db.port == 5432

    return service


if __name__ == "__main__":
    print(main())
