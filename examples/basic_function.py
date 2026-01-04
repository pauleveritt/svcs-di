"""Basic function injection example.

This example demonstrates using svcs-di with regular functions:
- Define a function with Inject dependencies
- Register services in the container
- Use an injector to manually call the function with dependencies resolved
"""

from dataclasses import dataclass

import svcs

from svcs_di import DefaultInjector, Inject


@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


def create_service(db: Inject[Database], timeout: int = 30) -> dict:
    """A function that depends on a database.

    Args:
        db: Database instance (injected from container)
        timeout: Connection timeout in seconds (has default)

    Returns:
        Dictionary with service configuration
    """
    return {
        "database_host": db.host,
        "database_port": db.port,
        "timeout": timeout,
    }


def main():
    """Demonstrate basic function injection."""
    # Create registry and register services
    registry = svcs.Registry()
    registry.register_factory(Database, Database)

    # Create container and injector
    container = svcs.Container(registry)
    injector = DefaultInjector(container=container)

    # Call the function with automatic dependency resolution
    result = injector(create_service)

    print(f"Service configuration: {result}")
    print(f"Database host={result['database_host']}, port={result['database_port']}")
    print(f"Timeout={result['timeout']}")


if __name__ == "__main__":
    main()
