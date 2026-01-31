"""InjectionContainer example.

- Create a container from InjectionContainer
- Don't need to register services with `auto()`
- Don't need to make and use your own injector instance
- Use `container.inject()` to provide keywords
"""

from dataclasses import dataclass

from svcs import Registry

from svcs_di import Inject
from svcs_di.injector_container import InjectorContainer


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

    # Let's get a service but use kwargs to override the defaults
    # in the dataclass.
    service = container.inject(Service, debug=True, timeout=99)
    assert service.debug is not False
    assert service.debug is True
    assert service.timeout != 30
    assert service.timeout == 99
    return service


if __name__ == "__main__":
    print(main())
