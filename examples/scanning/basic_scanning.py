"""Basic scanning example.

Shows the simplest use case of scanning:
- Mark services with @injectable decorator
- Call scan() to discover and register
- Retrieve services from container
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.scanning import scan


@injectable
@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@injectable
@dataclass
class Cache:
    """A simple cache service."""

    ttl: int = 300


@injectable
@dataclass
class UserRepository:
    """Repository that depends on database and cache."""

    db: Inject[Database]
    cache: Inject[Cache]

    def get_user(self, user_id: int) -> str:
        return f"User {user_id} from {self.db.host}"


def main() -> UserRepository:
    """Demonstrate basic scanning workflow."""
    registry = Registry()

    # scan() discovers @injectable classes and registers them
    scan(
        registry,
        locals_dict={
            "Database": Database,
            "Cache": Cache,
            "UserRepository": UserRepository,
        },
    )

    container = Container(registry)

    # Get services - dependencies are automatically resolved
    repo = container.get(UserRepository)
    assert repo.db.host == "localhost"
    assert repo.db.port == 5432
    assert repo.cache.ttl == 300
    assert "User 42" in repo.get_user(42)

    return repo


if __name__ == "__main__":
    print(main())
