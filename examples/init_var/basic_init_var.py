"""
Basic InitVar injection example.

This example demonstrates the InitVar[Inject[T]] pattern for computing
derived values from injected dependencies during initialization.

The pattern is useful when you need to:
- Extract specific data from a service during initialization
- Compute derived values from injected dependencies
- Allow overrides via kwargs while still auto-resolving when not provided
"""

from dataclasses import InitVar, dataclass

import svcs

from svcs_di import Inject, auto
from svcs_di.injectors import KeywordInjector


@dataclass
class AppConfig:
    """Application configuration."""

    cache_ttl: int = 300
    debug_mode: bool = False
    max_connections: int = 10


@dataclass
class CacheService:
    """A service that extracts cache TTL from config during initialization.

    The config is NOT stored on the instance - only the extracted values are kept.
    Values default to None and are computed from config if not provided,
    allowing manual override via kwargs.
    """

    # InitVar field - passed to __post_init__ but NOT stored
    config: InitVar[Inject[AppConfig]]

    # Optional fields - computed from config if None, but can be overridden
    ttl: int | None = None
    debug: bool | None = None

    def __post_init__(self, config: AppConfig) -> None:
        """Extract configuration values during initialization if not provided."""
        if self.ttl is None:
            self.ttl = config.cache_ttl
        if self.debug is None:
            self.debug = config.debug_mode


def main() -> None:
    """Demonstrate basic InitVar injection."""
    # Set up registry and register dependencies
    registry = svcs.Registry()
    registry.register_value(AppConfig, AppConfig(cache_ttl=600, debug_mode=True))
    registry.register_factory(CacheService, auto(CacheService))

    # Get the service - values computed from config
    container = svcs.Container(registry)
    cache_service = container.get(CacheService)

    print(f"Cache TTL: {cache_service.ttl}")  # 600
    print(f"Debug mode: {cache_service.debug}")  # True

    # The config is NOT stored on the instance
    assert not hasattr(cache_service, "config"), "config should not be stored"
    print("Config is NOT stored on the instance (as expected)")

    # Now demonstrate override via KeywordInjector
    injector = KeywordInjector(container=container)
    overridden_service = injector(CacheService, ttl=999)

    print(f"\nWith override - Cache TTL: {overridden_service.ttl}")  # 999 (overridden)
    print(
        f"With override - Debug mode: {overridden_service.debug}"
    )  # True (from config)


if __name__ == "__main__":
    main()
