"""Using the KeywordInjector.

This example doesn't use keywords during injection. Instead, it just shows
we can create a `KeywordInjector` and manually inject, as we saw in the
basic function example.
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject
from svcs_di.injectors import KeywordInjector


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

    # Register database
    registry.register_factory(Database, Database)

    # Per-request container, let's use the injector manually.
    container = Container(registry)
    injector = KeywordInjector(container=container)

    # Normal usage - use container lookup + defaults, no usage of keywords.
    service = injector(Service)
    assert service.db.host == "localhost"
    assert service.db.port == 5432
    assert service.debug is False
    return service


if __name__ == "__main__":
    print(main())
