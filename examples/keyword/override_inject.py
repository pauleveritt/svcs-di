"""Injection that overrides an Inject.

- The keyword args can also take precedence over ``Inject`` values.
"""

from dataclasses import dataclass

from svcs import Registry

from svcs_di import Inject, InjectorContainer


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service with injectable and non-injectable parameters."""

    db: Inject[Database]
    debug: bool = False
    timeout: int = 30


def main() -> Service:
    """Demonstrate KeywordInjector's three-tier precedence."""
    registry = Registry()

    # Register services and the KeywordInjector as the default injector
    registry.register_factory(Database, Database)
    registry.register_factory(Service, Service)

    # Per-request container
    container = InjectorContainer(registry)

    # Make a custom Database instance
    this_database = Database(host="prod", port=1234)

    # Override the `Inject[Database]` field
    service = container.inject(Service, db=this_database, debug=True)
    assert service.db is this_database
    assert service.debug is True
    return service


if __name__ == "__main__":
    print(main())
