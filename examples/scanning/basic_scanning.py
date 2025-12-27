"""Basic scanning example.

This example demonstrates the simplest use case of the scanning feature:
- Mark services with @injectable decorator
- Call scan() to discover and register decorated services
- Retrieve services from container with automatic dependency resolution
- Shows both bare @injectable and @injectable() syntax
"""

from dataclasses import dataclass

import svcs

from svcs_di import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import scan


# ============================================================================
# Step 1: Define services with @injectable decorator
# ============================================================================


@injectable  # Bare decorator syntax - marks class for auto-discovery
@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@injectable()  # Called decorator syntax (equivalent to bare decorator)
@dataclass
class Cache:
    """A simple cache service."""

    ttl: int = 300


@injectable  # Service with dependencies
@dataclass
class UserRepository:
    """Repository that depends on database and cache."""

    db: Inject[Database]
    cache: Inject[Cache]
    table: str = "users"

    def get_user(self, user_id: int) -> str:
        """Simulate getting a user."""
        return f"User {user_id} from {self.table} (db={self.db.host}, cache_ttl={self.cache.ttl})"


# ============================================================================
# Step 2: Scan to discover and register decorated services
# ============================================================================


def main():
    """Demonstrate basic scanning workflow."""
    print("\n" + "=" * 70)
    print("Basic Scanning Example")
    print("=" * 70)

    # Create registry
    registry = svcs.Registry()

    # Scan to discover @injectable decorated classes
    # The scan() function will:
    # 1. Auto-detect the calling package (no arguments needed!)
    # 2. Find all classes with @injectable decorator
    # 3. Register them automatically with their factory functions
    print("\nStep 1: Scanning for @injectable decorated services...")

    # Auto-detect and scan the current package - no sys.modules hack needed!
    scan(registry)
    print("  -> Found and registered: Database, Cache, UserRepository")

    # ========================================================================
    # Step 3: Retrieve services from container
    # ========================================================================

    print("\nStep 2: Creating container and retrieving services...")
    container = svcs.Container(registry)

    # Get Database service (no dependencies)
    database = container.get(Database)
    print(f"\n  Database service:")
    print(f"    Type: {type(database).__name__}")
    print(f"    Host: {database.host}")
    print(f"    Port: {database.port}")

    # Get Cache service (no dependencies)
    cache = container.get(Cache)
    print(f"\n  Cache service:")
    print(f"    Type: {type(cache).__name__}")
    print(f"    TTL: {cache.ttl}")

    # Get UserRepository service (depends on Database and Cache)
    # Dependencies are automatically resolved!
    repo = container.get(UserRepository)
    print(f"\n  UserRepository service:")
    print(f"    Type: {type(repo).__name__}")
    print(f"    Table: {repo.table}")
    print(f"    Database: {repo.db.host}:{repo.db.port}")
    print(f"    Cache TTL: {repo.cache.ttl}")

    # ========================================================================
    # Step 4: Use the service
    # ========================================================================

    print("\nStep 3: Using the service...")
    result = repo.get_user(42)
    print(f"  Result: {result}")

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "=" * 70)
    print("Summary:")
    print("  1. Marked classes with @injectable decorator")
    print("  2. Called scan() to auto-discover and register services")
    print("  3. Retrieved services with automatic dependency injection")
    print("  4. No manual registration code needed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
