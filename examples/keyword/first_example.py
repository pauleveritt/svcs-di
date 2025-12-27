"""Keyword Injector example with three-tier precedence.

This example demonstrates KeywordInjector's three-tier precedence for dependency resolution:
1. kwargs (highest) - override everything, including Inject params
2. container lookup - for Inject[T] parameters only
3. default values - from parameter/field definitions

KeywordInjector is extracted from DefaultInjector to provide kwargs override support.
Use this when you need runtime parameter overrides, especially useful for testing.
"""

from dataclasses import dataclass

import svcs

from svcs_di import Inject
from svcs_di.injectors import KeywordInjector


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service with injectable and non-injectable parameters."""

    db: Inject[Database]
    timeout: int = 30
    debug: bool = False


def main():
    """Demonstrate KeywordInjector's three-tier precedence."""
    registry = svcs.Registry()

    # Register production database
    prod_db = Database(host="prod.example.com", port=5433)
    registry.register_value(Database, prod_db)

    container = svcs.Container(registry)
    injector = KeywordInjector(container=container)

    # Case 1: Normal usage - use container lookup + defaults (Tier 2 & 3)
    print("Case 1: Normal usage (Tier 2: container, Tier 3: defaults)")
    service1 = injector(Service)
    assert isinstance(service1.db, Database)  # Type guard
    print(f"  Database: {service1.db.host}:{service1.db.port}")  # From container
    print(f"  Timeout: {service1.timeout}")  # Default value
    print(f"  Debug: {service1.debug}")  # Default value
    print()

    # Case 2: Override non-injectable parameter via kwargs (Tier 1)
    print("Case 2: Override timeout via kwargs (Tier 1 > Tier 3)")
    service2 = injector(Service, timeout=60)
    assert isinstance(service2.db, Database)  # Type guard
    print(f"  Database: {service2.db.host}:{service2.db.port}")  # From container
    print(f"  Timeout: {service2.timeout}")  # Overridden by kwargs
    print(f"  Debug: {service2.debug}")  # Default value
    print()

    # Case 3: Override Inject parameter for testing (Tier 1 > Tier 2)
    print("Case 3: Override Inject db for testing (Tier 1 > Tier 2)")
    test_db = Database(host="localhost", port=5432)
    service3 = injector(Service, db=test_db, debug=True)
    assert isinstance(service3.db, Database)  # Type guard
    print(f"  Database: {service3.db.host}:{service3.db.port}")  # Overridden by kwargs
    print(f"  Timeout: {service3.timeout}")  # Default value
    print(f"  Debug: {service3.debug}")  # Overridden by kwargs
    print()

    # Case 4: Use KeywordInjector as custom injector in auto() pattern
    print("Case 4: Register KeywordInjector as custom injector")
    from svcs_di import DefaultInjector, auto

    registry2 = svcs.Registry()

    # Register KeywordInjector as the default injector
    # Use proper factory function signature that svcs recognizes
    def keyword_injector_factory(svcs_container: svcs.Container) -> KeywordInjector:
        return KeywordInjector(container=svcs_container)

    registry2.register_factory(DefaultInjector, keyword_injector_factory)

    # Register dependencies
    registry2.register_value(Database, prod_db)
    registry2.register_factory(Service, auto(Service))

    # Now auto() will use KeywordInjector for kwargs support
    container2 = svcs.Container(registry2)

    # Get service through auto() factory (which uses our KeywordInjector)
    service4 = container2.get(Service)
    assert isinstance(service4.db, Database)  # Type guard
    print(f"  Database: {service4.db.host}:{service4.db.port}")  # From container
    print(f"  Timeout: {service4.timeout}")  # Default value
    print(f"  Debug: {service4.debug}")  # Default value
    print()

    # Case 5: Demonstrate kwargs validation
    print("Case 5: Kwargs validation (catches typos)")
    try:
        injector(Service, timout=60)  # Typo: 'timout' instead of 'timeout'
    except ValueError as e:
        print(f"  Error caught: {e}")


if __name__ == "__main__":
    main()
