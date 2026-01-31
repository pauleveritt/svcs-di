"""Location-based resolution.

Shows URL-path-like service selection using PurePath locations with
hierarchical fallback. Locations let you register different implementations
for different parts of your application.

New in this version: HopscotchContainer accepts location directly,
automatically registering it for injection and ServiceLocator matching.
"""

from dataclasses import dataclass
from pathlib import PurePath

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry, Location


@dataclass
class Greeting:
    """Default greeting."""

    salutation: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"


@dataclass
class PublicGreeting(Greeting):
    """Greeting for public pages."""

    salutation: str = "Welcome"

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}! Thanks for visiting."


@dataclass
class PageRenderer:
    """Service that renders pages using injected greeting."""

    greeting: Inject[Greeting]
    location: Inject[Location]

    def render(self, name: str) -> str:
        return f"[{self.location}] {self.greeting.greet(name)}"


def main() -> PageRenderer:
    """Demonstrate location-based resolution."""
    # Setup registry with location-specific implementations
    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(
        Greeting, PublicGreeting, location=PurePath("/public")
    )

    # Test 1: /public location - gets PublicGreeting (new API)
    # The container automatically registers location for:
    # - Inject[Location] dependency injection
    # - ServiceLocator location-based matching
    container = HopscotchContainer(registry, location=PurePath("/public"))
    service = container.inject(PageRenderer)
    assert "Thanks for visiting" in service.render("Alice")
    assert service.location == PurePath("/public")

    # Test 2: Hierarchical fallback - /public/gallery falls back to /public
    container = HopscotchContainer(registry, location=PurePath("/public/gallery"))
    service = container.inject(PageRenderer)
    # No /public/gallery registration, falls back to /public
    assert "Thanks for visiting" in service.render("Bob")
    assert service.location == PurePath("/public/gallery")

    # Test 3: Unknown location - falls back to default
    container = HopscotchContainer(registry, location=PurePath("/unknown"))
    service = container.inject(PageRenderer)
    assert service.greeting.salutation == "Hello"

    # Test 4: Backward compatible API - register_local_value still works
    container = HopscotchContainer(registry)
    container.register_local_value(Location, PurePath("/legacy"))
    service = container.inject(PageRenderer)
    assert service.location == PurePath("/legacy")

    return service


if __name__ == "__main__":
    print(main())
