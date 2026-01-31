"""Scanning with protocols.

Shows the recommended pattern for large-scale systems:
- Define Protocols as service contracts
- Mark implementations with @injectable(for_=Protocol)
- Services depend on Protocols, not implementations
"""

from dataclasses import dataclass
from typing import Protocol

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry, injectable, scan


# Step 1: Define Protocols as service contracts
class Database(Protocol):
    """Protocol for database services."""

    host: str
    port: int


class Cache(Protocol):
    """Protocol for cache services."""

    ttl: int


class UserRepository(Protocol):
    """Protocol for user repository services."""

    def get_user(self, user_id: int) -> str: ...


# Step 2: Mark implementations with @injectable(for_=Protocol)
@injectable(for_=Database)
@dataclass
class PostgresDatabase:
    """PostgreSQL implementation of Database protocol."""

    host: str = "localhost"
    port: int = 5432


@injectable(for_=Cache)
@dataclass
class RedisCache:
    """Redis implementation of Cache protocol."""

    ttl: int = 300


@injectable(for_=UserRepository)
@dataclass
class SqlUserRepository:
    """SQL implementation of UserRepository protocol."""

    db: Inject[Database]
    cache: Inject[Cache]

    def get_user(self, user_id: int) -> str:
        return f"User {user_id} from {self.db.host}"


# Step 3: Services depend on Protocols, not implementations
@dataclass
class UserService:
    """Service that depends on UserRepository protocol."""

    repo: Inject[UserRepository]

    def find_user(self, user_id: int) -> str:
        return self.repo.get_user(user_id)


def main() -> UserService:
    """Demonstrate scanning with protocols."""
    # HopscotchRegistry manages protocol-to-implementation mappings
    registry = HopscotchRegistry()

    # scan() discovers @injectable classes and registers them under their protocols
    scan(
        registry,
        locals_dict={
            "PostgresDatabase": PostgresDatabase,
            "RedisCache": RedisCache,
            "SqlUserRepository": SqlUserRepository,
        },
    )

    # HopscotchContainer resolves protocols to implementations via inject()
    container = HopscotchContainer(registry)

    # inject() resolves Inject[Protocol] fields to implementations
    service = container.inject(UserService)
    # Accessing implementation details for verification (not typical in production code)
    assert service.repo.db.host == "localhost"  # ty: ignore[unresolved-attribute]
    assert service.repo.db.port == 5432  # ty: ignore[unresolved-attribute]
    assert service.repo.cache.ttl == 300  # ty: ignore[unresolved-attribute]
    assert "User 42" in service.find_user(42)

    return service


if __name__ == "__main__":
    print(main())
