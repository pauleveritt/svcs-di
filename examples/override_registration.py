"""Override registration.

Customize a site by replacing a service registered in the underlying
app, without forking.
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

    # ---- Start a "site" configuration -----
    # Now in the "site", we want a different "Database". Normally the
    # above would be in a package and the
    @dataclass
    class CustomDatabase:
        """A simple database service."""

        host: str = "prod"
        port: int = 9876

    registry.register_factory(Database, CustomDatabase)
    # ---- Finish a "site" configuration -----

    # Get the service - dependencies are automatically resolved
    container = Container(registry)
    service = container.get(Service)

    assert service.db.host == "prod"
    assert service.db.port == 9876

    return service


if __name__ == "__main__":
    print(main())
