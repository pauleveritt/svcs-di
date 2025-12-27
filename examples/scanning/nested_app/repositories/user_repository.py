"""User repository in repositories subdirectory."""

from dataclasses import dataclass

from svcs_di.auto import Inject
from svcs_di.injectors.decorators import injectable

# Import from other nested modules to show cross-module dependencies
from ..models.database import DatabaseConnection
from ..services.cache import CacheService


@injectable
@dataclass
class UserRepository:
    """User repository found in repositories/user_repository.py.

    Demonstrates cross-module dependencies within nested structure.
    """

    db: Inject[DatabaseConnection]
    cache: Inject[CacheService]

    def get_user(self, user_id: int) -> str:
        """Get user with database and cache."""
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached

        result = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        return f"User {user_id}: {result}"
