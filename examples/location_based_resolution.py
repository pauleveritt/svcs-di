"""
Location-Based Service Resolution Example.

Demonstrates URL-path-like service selection using hierarchical locations
with PurePath. Shows how services can be registered at specific locations
and how hierarchical fallback works.

This example shows:
1. Registering services at different locations (/admin, /public, /api)
2. Hierarchical fallback (child locations inherit parent services)
3. Combined resource + location matching for fine-grained control
4. Location as a special service that can be injected

Run:
    uv run python examples/location_based_resolution.py
"""

from dataclasses import dataclass
from pathlib import PurePath
from typing import Protocol

import svcs

from svcs_di.auto import Injectable
from svcs_di.injectors.locator import (
    HopscotchInjector,
    Location,
    ServiceLocator,
)


# ============================================================================
# Define Service Protocols and Implementations
# ============================================================================


class Greeting(Protocol):
    """Protocol for greeting services."""

    def greet(self, name: str) -> str: ...


@dataclass
class PublicGreeting:
    """Greeting for public-facing pages."""

    salutation: str = "Welcome"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}! Thanks for visiting our site."


@dataclass
class AdminGreeting:
    """Greeting for admin portal."""

    salutation: str = "Hello Admin"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}. You have full system access."


@dataclass
class APIGreeting:
    """Greeting for API endpoints."""

    salutation: str = "API"

    def greet(self, name: str) -> str:
        return f'{{"message": "{self.salutation} access", "user": "{name}"}}'


@dataclass
class DefaultGreeting:
    """Default greeting for all other locations."""

    salutation: str = "Hi"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


# ============================================================================
# Context types for combined resource + location matching
# ============================================================================


class GuestContext:
    """Context for guest/unauthenticated users."""

    pass


class AuthenticatedContext:
    """Context for authenticated users."""

    pass


@dataclass
class EnhancedAdminGreeting:
    """Enhanced greeting for authenticated admin users."""

    salutation: str = "Welcome back, Administrator"

    def greet(self, name: str) -> str:
        return f"{self.salutation} {name}! All systems operational."


# ============================================================================
# Service that uses location
# ============================================================================


@dataclass
class PageRenderer:
    """Service that depends on both Greeting and Location."""

    greeting: Injectable[Greeting]
    location: Injectable[Location]

    def render(self, username: str) -> str:
        """Render a page with greeting and location info."""
        greeting_text = self.greeting.greet(username)
        return f"[Page at {self.location}]\n{greeting_text}"


# ============================================================================
# Example 1: Basic Location-Based Resolution
# ============================================================================


def example_basic_location_routing():
    """Show basic location-based service routing."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Location-Based Routing")
    print("=" * 70)

    # Setup: Register greetings at different locations
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting)  # Global default
    locator = locator.register(Greeting, PublicGreeting, location=PurePath("/public"))
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(Greeting, APIGreeting, location=PurePath("/api"))

    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)

    # Scenario 1: Request from /public
    print("\n1. Request from /public:")
    registry.register_value(Location, PurePath("/public"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Alice"))

    # Scenario 2: Request from /admin
    print("\n2. Request from /admin:")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/admin"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Bob"))

    # Scenario 3: Request from /api
    print("\n3. Request from /api:")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/api"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Charlie"))

    # Scenario 4: Request from unknown location (falls back to default)
    print("\n4. Request from /unknown (fallback to default):")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/unknown"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Diana"))


# ============================================================================
# Example 2: Hierarchical Fallback
# ============================================================================


def example_hierarchical_fallback():
    """Show hierarchical fallback behavior."""
    print("\n" + "=" * 70)
    print("Example 2: Hierarchical Location Fallback")
    print("=" * 70)

    # Setup: Register greetings at different hierarchy levels
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting, location=PurePath("/"))
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))

    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)

    # No specific greeting at /admin/users - should fall back to /admin
    print("\n1. Request from /admin/users (falls back to /admin):")
    registry.register_value(Location, PurePath("/admin/users"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Eve"))

    # Even deeper nesting still falls back to /admin
    print("\n2. Request from /admin/users/profile (falls back to /admin):")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/admin/users/profile"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Frank"))

    # /public paths fall back to root
    print("\n3. Request from /public/blog (falls back to root):")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/public/blog"))
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Grace"))


# ============================================================================
# Example 3: Combined Resource + Location Matching
# ============================================================================


def example_combined_resource_location():
    """Show combined resource + location matching for fine-grained control."""
    print("\n" + "=" * 70)
    print("Example 3: Combined Resource + Location Matching")
    print("=" * 70)

    # Setup: Register with both location and resource
    locator = ServiceLocator()
    # Default for guests everywhere
    locator = locator.register(Greeting, PublicGreeting)
    # Regular admin greeting
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    # Enhanced admin greeting for authenticated users
    locator = locator.register(
        Greeting,
        EnhancedAdminGreeting,
        location=PurePath("/admin"),
        resource=AuthenticatedContext,
    )

    # Scenario 1: Guest at /admin (gets regular admin greeting)
    print("\n1. Guest user at /admin:")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/admin"))
    # No resource context registered = guest

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    renderer = injector(PageRenderer)
    print(renderer.render("Henry"))

    # Scenario 2: Authenticated user at /admin (gets enhanced greeting)
    print("\n2. Authenticated user at /admin:")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/admin"))
    registry.register_value(AuthenticatedContext, AuthenticatedContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=AuthenticatedContext)

    renderer = injector(PageRenderer)
    print(renderer.render("Isabel"))

    # Scenario 3: Authenticated user at /public (gets default public greeting)
    print("\n3. Authenticated user at /public (no special handling):")
    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/public"))
    registry.register_value(AuthenticatedContext, AuthenticatedContext())

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=AuthenticatedContext)

    renderer = injector(PageRenderer)
    print(renderer.render("Jack"))


# ============================================================================
# Example 4: Most Specific Location Wins
# ============================================================================


def example_most_specific_wins():
    """Show that more specific locations take precedence."""
    print("\n" + "=" * 70)
    print("Example 4: Most Specific Location Wins")
    print("=" * 70)

    @dataclass
    class AdminUsersGreeting:
        """Specific greeting for user management."""

        salutation: str = "User Management"

        def greet(self, name: str) -> str:
            return f"{self.salutation}: {name}, you're managing user accounts."

    @dataclass
    class AdminSettingsGreeting:
        """Specific greeting for settings."""

        salutation: str = "System Settings"

        def greet(self, name: str) -> str:
            return f"{self.salutation}: {name}, configure system options here."

    # Setup: Register at multiple hierarchy levels
    locator = ServiceLocator()
    locator = locator.register(Greeting, DefaultGreeting, location=PurePath("/"))
    locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
    locator = locator.register(
        Greeting, AdminUsersGreeting, location=PurePath("/admin/users")
    )
    locator = locator.register(
        Greeting, AdminSettingsGreeting, location=PurePath("/admin/settings")
    )

    # Test different paths
    test_cases = [
        ("/admin", "General admin area"),
        ("/admin/users", "User management (most specific)"),
        ("/admin/users/create", "User creation (falls back to /admin/users)"),
        ("/admin/settings", "Settings area (most specific)"),
        ("/admin/other", "Other admin page (falls back to /admin)"),
    ]

    for path, description in test_cases:
        print(f"\n{description}:")
        print(f"Path: {path}")
        registry = svcs.Registry()
        registry.register_value(ServiceLocator, locator)
        registry.register_value(Location, PurePath(path))

        container = svcs.Container(registry)
        injector = HopscotchInjector(container=container)

        renderer = injector(PageRenderer)
        print(renderer.render("Kevin"))


# ============================================================================
# Main: Run all examples
# ============================================================================


if __name__ == "__main__":
    print("\n")
    print("#" * 70)
    print("# Location-Based Service Resolution Examples")
    print("#" * 70)

    example_basic_location_routing()
    example_hierarchical_fallback()
    example_combined_resource_location()
    example_most_specific_wins()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70 + "\n")
