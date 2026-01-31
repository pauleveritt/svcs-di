"""
Mixed injection example - combining regular Inject[T] with InitVar[Inject[T]].

This example demonstrates using both:
- Regular Inject[T] fields that are stored on the instance
- InitVar[Inject[T]] fields that are only used during initialization

This pattern is useful when you need to:
- Keep some dependencies for later use (regular Inject)
- Use other dependencies only during init (InitVar)
- Compute derived values with fallback (auto-resolve if None, allow override)
"""

from dataclasses import InitVar, dataclass, field
from typing import Protocol, runtime_checkable

import svcs

from svcs_di import Inject, auto
from svcs_di.injectors import KeywordInjector


@runtime_checkable
class Cache(Protocol):
    """Protocol for cache implementations."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...


@dataclass
class InMemoryCache:
    """Simple in-memory cache implementation."""

    _store: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value


@dataclass
class UserContext:
    """Request context with user information."""

    user_id: str
    permissions: list[str]
    session_id: str


@dataclass
class UserService:
    """A service that combines regular injection with InitVar injection.

    - cache: Stored as a regular field (used throughout the service's lifetime)
    - user_id, permissions: Optional with fallback - computed from context if None
    - context: NOT stored (only used during initialization)
    """

    # Regular Inject field - stored on instance for later use
    cache: Inject[Cache]

    # InitVar field - used during init, then discarded
    context: InitVar[Inject[UserContext]]

    # Optional fields with fallback - computed from context if None, but can be overridden
    user_id: str | None = None
    permissions: set[str] | None = None

    def __post_init__(self, context: UserContext) -> None:
        """Extract user info from context if not provided via kwargs."""
        if self.user_id is None:
            self.user_id = context.user_id
        if self.permissions is None:
            self.permissions = set(context.permissions)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return self.permissions is not None and permission in self.permissions

    def get_cached_preference(self, key: str) -> str | None:
        """Get a cached user preference."""
        cache_key = f"pref:{self.user_id}:{key}"
        return self.cache.get(cache_key)

    def set_cached_preference(self, key: str, value: str) -> None:
        """Set a cached user preference."""
        cache_key = f"pref:{self.user_id}:{key}"
        self.cache.set(cache_key, value)


def main() -> None:
    """Demonstrate mixed injection patterns."""
    # Set up registry
    registry = svcs.Registry()

    # Register the cache (protocol-based)
    registry.register_value(Cache, InMemoryCache())

    # Register the user context (would typically come from request)
    registry.register_value(
        UserContext,
        UserContext(
            user_id="user-123",
            permissions=["read", "write", "admin"],
            session_id="session-abc",
        ),
    )

    # Register our service
    registry.register_factory(UserService, auto(UserService))

    # Get the service - values computed from context
    container = svcs.Container(registry)
    user_service = container.get(UserService)

    # Verify regular Inject field is stored
    print(f"Cache is stored: {user_service.cache is not None}")

    # Verify InitVar field extracted values correctly
    print(f"User ID: {user_service.user_id}")  # user-123
    print(f"Has admin permission: {user_service.has_permission('admin')}")  # True

    # Verify InitVar field is NOT stored
    assert not hasattr(user_service, "context"), "context should not be stored"
    print("Context is NOT stored on the instance (as expected)")

    # Use the cache functionality
    user_service.set_cached_preference("theme", "dark")
    print(f"Theme preference: {user_service.get_cached_preference('theme')}")

    # Demonstrate override via KeywordInjector
    print("\n--- With kwargs override ---")
    injector = KeywordInjector(container=container)
    overridden_service = injector(
        UserService, user_id="test-user", permissions={"read"}
    )
    print(f"Overridden User ID: {overridden_service.user_id}")  # test-user
    print(
        f"Has admin permission: {overridden_service.has_permission('admin')}"
    )  # False
    print(f"Has read permission: {overridden_service.has_permission('read')}")  # True


if __name__ == "__main__":
    main()
