"""Manual injection with the KeywordInjector.

- Still use the injector manually
- But this time, provide kwargs

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

    # Let's pass in values for Service.debug and Service.timeout
    service = injector(Service, debug=True, timeout=99)
    assert service.debug is True
    assert service.timeout == 99
    return service


if __name__ == "__main__":
    print(main())
