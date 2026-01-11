"""User repository implementation in repositories subdirectory."""

from dataclasses import dataclass

from svcs_di import Inject
from svcs_di.injectors.decorators import injectable

from ..protocols import Cache, Database, UserRepository


@injectable(for_=UserRepository)
@dataclass
class SqlUserRepository:
    """SQL implementation of UserRepository protocol."""

    db: Inject[Database]
    cache: Inject[Cache]

    def get_user(self, user_id: int) -> str:
        """Get user with database and cache."""
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached

        result = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        return f"User {user_id}: {result}"
