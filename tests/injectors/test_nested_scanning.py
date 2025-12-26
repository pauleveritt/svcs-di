"""Tests for nested package scanning with string package names."""

import sys
from pathlib import Path

import svcs

from svcs_di.injectors.locator import scan

# Add examples to path so we can import the nested_app package
examples_path = Path(__file__).parent.parent.parent / "examples" / "scanning"
if str(examples_path) not in sys.path:
    sys.path.insert(0, str(examples_path))


def test_nested_package_scanning_with_string_name():
    """Test that string-based scanning recursively discovers all subdirectories and resolves cross-module dependencies."""
    registry = svcs.Registry()

    # Remove nested_app from sys.modules to verify no prior import needed
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith("nested_app")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Scan using string package name - should discover all subdirectories recursively
    result = scan(registry, "nested_app")
    assert result is registry  # Should return registry for chaining

    container = svcs.Container(registry)

    # Import classes for verification (after scanning!)
    from nested_app.models.database import DatabaseConnection  # type: ignore[import-not-found]
    from nested_app.repositories.user_repository import UserRepository  # type: ignore[import-not-found]
    from nested_app.services.cache import CacheService  # type: ignore[import-not-found]
    from nested_app.services.email import EmailService  # type: ignore[import-not-found]

    # Verify all 4 services from different subdirectories were discovered
    cache = container.get(CacheService)
    assert cache.ttl == 300
    assert cache.max_size == 1000

    email = container.get(EmailService)
    assert email.smtp_host == "localhost"

    db = container.get(DatabaseConnection)
    assert db.host == "localhost"
    assert db.database == "myapp"

    # Verify cross-module dependencies: UserRepository depends on DatabaseConnection + CacheService
    repo = container.get(UserRepository)
    assert isinstance(repo.db, DatabaseConnection)
    assert isinstance(repo.cache, CacheService)
    assert "cached_value_for_user:123" in repo.get_user(123)


def test_nested_scanning_multiple_packages():
    """Test scanning multiple packages in one call."""
    registry = svcs.Registry()

    # Import test fixtures for additional packages
    from tests.test_fixtures.scanning_test_package import service_a

    # Scan multiple packages - one nested, one flat
    scan(registry, "nested_app", service_a)

    container = svcs.Container(registry)

    # Should find services from both packages
    from nested_app.services.cache import CacheService  # type: ignore[import-not-found]

    cache = container.get(CacheService)
    assert cache is not None

    # Should also find services from the non-nested package
    assert hasattr(service_a, "ServiceA")
