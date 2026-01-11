"""Registered injector.

Instead of making a `DefaultInjector` instance, get it from the container:
- Faster (might already have been called and is in the cache)
- Pluggable (you can register an alternate injector)
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import DefaultInjector, Inject, Injector


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
    # Register the DefaultInjector as the injector
    registry.register_factory(Injector, DefaultInjector)

    # Create container, get an injector, then call-with-injection the function
    container = Container(registry)
    injector = container.get(Injector)
    result = injector(create_result)

    # Test the result
    assert result["database_host"] == "localhost"
    assert result["database_port"] == 5432

    return result


if __name__ == "__main__":
    print(main())
