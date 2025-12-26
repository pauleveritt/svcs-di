"""Nested scanning example with string package name.

This example demonstrates scanning a nested application structure using a string
package name. The scan() function automatically discovers all @injectable decorated
classes in subdirectories recursively.

Directory structure:
    nested_app/
    ├── __init__.py
    ├── services/
    │   ├── __init__.py
    │   ├── cache.py          # CacheService
    │   └── email.py          # EmailService
    ├── models/
    │   ├── __init__.py
    │   └── database.py       # DatabaseConnection
    └── repositories/
        ├── __init__.py
        └── user_repository.py  # UserRepository (depends on DatabaseConnection, CacheService)

Key features demonstrated:
- Recursive scanning of nested package structure
- String-based package name (no imports needed!)
- Cross-module dependencies within nested structure
- Single scan call discovers everything
"""

import svcs

from svcs_di.injectors.locator import scan

# Import the classes only for type annotations - NOT required for scanning!
from nested_app.models.database import DatabaseConnection
from nested_app.repositories.user_repository import UserRepository
from nested_app.services.cache import CacheService
from nested_app.services.email import EmailService


def main():
    """Demonstrate nested package scanning with string package name."""
    print("\n" + "=" * 80)
    print("Nested Package Scanning Example (String-Based)")
    print("=" * 80)

    # ========================================================================
    # Step 1: Scan using string package name - discovers ALL subdirectories!
    # ========================================================================

    print("\nStep 1: Scanning nested package using string name...")
    print("  Package: 'nested_app'")
    print("  This will recursively scan:")
    print("    - nested_app/services/cache.py")
    print("    - nested_app/services/email.py")
    print("    - nested_app/models/database.py")
    print("    - nested_app/repositories/user_repository.py")

    registry = svcs.Registry()

    # Single scan call with string package name - NO imports required!
    # The scan() function will:
    # 1. Import 'nested_app' package
    # 2. Use pkgutil.walk_packages() to find all submodules recursively
    # 3. Import each submodule to trigger decorator execution
    # 4. Discover and register all @injectable decorated classes
    scan(registry, "nested_app")

    print("\n  ✓ Scan complete! All decorated services discovered and registered.")

    # ========================================================================
    # Step 2: Verify services were registered from different subdirectories
    # ========================================================================

    print("\nStep 2: Retrieving services from nested subdirectories...")
    container = svcs.Container(registry)

    # Get service from services/cache.py
    cache = container.get(CacheService)
    print(f"\n  From services/cache.py:")
    print(f"    Type: {type(cache).__name__}")
    print(f"    TTL: {cache.ttl}, Max Size: {cache.max_size}")
    print(f"    Cache get: {cache.get('test_key')}")

    # Get service from services/email.py
    email = container.get(EmailService)
    print(f"\n  From services/email.py:")
    print(f"    Type: {type(email).__name__}")
    print(f"    SMTP: {email.smtp_host}:{email.smtp_port}")
    print(f"    Send: {email.send('user@example.com', 'Test', 'Hello')}")

    # Get service from models/database.py
    db = container.get(DatabaseConnection)
    print(f"\n  From models/database.py:")
    print(f"    Type: {type(db).__name__}")
    print(f"    Connection: {db.host}:{db.port}/{db.database}")
    print(f"    Query: {db.query('SELECT 1')}")

    # ========================================================================
    # Step 3: Demonstrate cross-module dependencies
    # ========================================================================

    print("\nStep 3: Cross-module dependencies (repositories -> models + services)...")

    # UserRepository depends on DatabaseConnection and CacheService
    # Both from different subdirectories!
    repo = container.get(UserRepository)
    print(f"\n  From repositories/user_repository.py:")
    print(f"    Type: {type(repo).__name__}")
    print(f"    Database: {repo.db.host}:{repo.db.port}")
    print(f"    Cache: TTL={repo.cache.ttl}")
    print(f"    Get user: {repo.get_user(42)}")

    # ========================================================================
    # Step 4: Show the power of string-based scanning
    # ========================================================================

    print("\n" + "-" * 80)
    print("Key Advantage: String-Based Scanning")
    print("-" * 80)
    print("\nNotice that we used: scan(registry, 'nested_app')")
    print("\nBenefits:")
    print("  1. No need to import the package first")
    print("  2. Automatically discovers ALL subdirectories recursively")
    print("  3. Clean separation: main code doesn't import implementation details")
    print("  4. Easy to add new subdirectories - they're discovered automatically")
    print("  5. Works great for plugin architectures")

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "=" * 80)
    print("Summary:")
    print("  1. Used scan(registry, 'nested_app') with string package name")
    print("  2. Scan automatically discovered 4 services across 3 subdirectories")
    print("  3. Cross-module dependencies resolved automatically")
    print("  4. No manual imports needed for scanning!")
    print("  5. Recursive discovery makes it easy to organize large applications")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
