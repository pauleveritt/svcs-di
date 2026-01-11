"""Basic function injection example.

This example demonstrates using svcs-di with regular functions. These require manual injection since `svcs` can't
register factories for non-types:
- Uses the DefaultInjector
- Register a service in the container
- Define a function with Inject dependencies
- Use an injector to manually call the function with dependencies resolved
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import DefaultInjector, Inject


# A service that will be registered then injected with Inject[Database]
@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


def create_result(db: Inject[Database], timeout: int = 30) -> dict:
    """A function that depends on a database via injection."""
    return {
        "database_host": db.host,
        "database_port": db.port,
        "timeout": timeout,
    }


def main() -> dict[str, str | int]:
    """Demonstrate basic function injection."""
    # Create registry and register the service
    registry = Registry()
    registry.register_factory(Database, Database)

    # Create container and injector, then call-with-injection the function
    container = Container(registry)
    injector = DefaultInjector(container=container)
    result = injector(create_result)

    # Test the result
    assert result["database_host"] == "localhost"
    assert result["database_port"] == 5432

    return result


if __name__ == "__main__":
    print(main())
