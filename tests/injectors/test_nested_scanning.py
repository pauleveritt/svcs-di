"""Tests for nested package scanning with string package names."""

import sys
from dataclasses import dataclass
from pathlib import Path

from svcs_di import Inject
from svcs_di.hopscotch_registry import HopscotchContainer, HopscotchRegistry
from svcs_di.injectors.locator import scan

# Add examples/scanning to path so we can import the nested_app package
examples_path = Path(__file__).parent.parent.parent / "examples" / "scanning"
if str(examples_path) not in sys.path:
    sys.path.insert(0, str(examples_path))


def test_nested_package_scanning_with_string_name():
    """Test that string-based scanning recursively discovers all subdirectories and resolves cross-module dependencies."""
    registry = HopscotchRegistry()

    # Remove nested_app from sys.modules to verify no prior import needed
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith("nested_app")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Scan using string package name - should discover all subdirectories recursively
    result = scan(registry, "nested_app")
    assert result is registry  # Should return registry for chaining

    container = HopscotchContainer(registry)

    # Import protocols for service retrieval (must match scan path for type identity)
    from nested_app.protocols import (  # ty: ignore[unresolved-import]
        Cache,
        Database,
        Email,
        UserRepository,
    )

    # Import concrete classes for isinstance checks
    from nested_app.models.database import (  # ty: ignore[unresolved-import]
        DatabaseConnection,
    )
    from nested_app.repositories.user_repository import (  # ty: ignore[unresolved-import]
        SqlUserRepository,
    )
    from nested_app.services.cache import CacheService  # ty: ignore[unresolved-import]
    from nested_app.services.email import EmailService  # ty: ignore[unresolved-import]

    # Create a test service that depends on all protocols
    @dataclass
    class TestService:
        cache: Inject[Cache]
        email: Inject[Email]
        db: Inject[Database]
        repo: Inject[UserRepository]

    # inject() resolves Inject[Protocol] fields to implementations
    service = container.inject(TestService)

    # Verify all 4 services from different subdirectories were discovered
    assert isinstance(service.cache, CacheService)
    assert service.cache.ttl == 300
    assert service.cache.max_size == 1000

    assert isinstance(service.email, EmailService)
    assert service.email.smtp_host == "localhost"

    assert isinstance(service.db, DatabaseConnection)
    assert service.db.host == "localhost"
    assert service.db.database == "myapp"

    # Verify cross-module dependencies: repo depends on Database + Cache
    assert isinstance(service.repo, SqlUserRepository)
    assert isinstance(service.repo.db, DatabaseConnection)
    assert isinstance(service.repo.cache, CacheService)
    assert "cached_value_for_user:123" in service.repo.get_user(123)


def test_nested_scanning_multiple_packages():
    """Test scanning multiple packages in one call."""
    registry = HopscotchRegistry()

    # Import test fixtures for additional packages
    from tests.test_fixtures.scanning_test_package import service_a

    # Scan multiple packages - one nested, one flat
    scan(registry, "nested_app", service_a)

    container = HopscotchContainer(registry)

    # Import protocol for service retrieval
    from nested_app.protocols import Cache  # ty: ignore[unresolved-import]

    # Import concrete class for isinstance check
    from nested_app.services.cache import CacheService  # ty: ignore[unresolved-import]

    # Create a test service that depends on Cache
    @dataclass
    class TestService:
        cache: Inject[Cache]

    # inject() resolves Inject[Cache] to CacheService
    service = container.inject(TestService)
    assert isinstance(service.cache, CacheService)

    # Should also find services from the non-nested package
    assert hasattr(service_a, "ServiceA")
