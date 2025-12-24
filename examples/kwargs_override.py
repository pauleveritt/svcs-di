"""Kwargs override example.

This example demonstrates the precedence order for dependency resolution:
1. kwargs (highest) - override everything, including Injectable params
2. container lookup - for Injectable[T] parameters only
3. default values - from parameter/field definitions

This pattern is especially useful for testing.
"""

from dataclasses import dataclass

import svcs

from svcs_di import Injectable, auto


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service with injectable and non-injectable parameters."""

    db: Injectable[Database]
    timeout: int = 30
    debug: bool = False


def main():
    """Demonstrate kwargs override precedence."""
    registry = svcs.Registry()

    # Register production database
    prod_db = Database(host="prod.example.com", port=5433)
    registry.register_value(Database, prod_db)

    # Register service with auto()
    registry.register_factory(Service, auto(Service))

    # Case 1: Normal usage - use container + defaults
    print("Case 1: Normal usage")
    container = svcs.Container(registry)
    service = container.get(Service)
    print(f"  Database: {service.db.host}")  # type: ignore[attr-defined]
    print(f"  Timeout: {service.timeout}")
    print(f"  Debug: {service.debug}")
    print()

    # Case 2: Override non-injectable parameter via factory kwargs
    print("Case 2: Override timeout via factory")
    # Note: We can't pass kwargs through container.get() directly
    # But factories can accept kwargs
    def custom_factory(svcs_container):
        return auto(Service)(svcs_container, timeout=60)

    registry2 = svcs.Registry()
    registry2.register_value(Database, prod_db)
    registry2.register_factory(Service, custom_factory)

    container2 = svcs.Container(registry2)
    service2 = container2.get(Service)
    print(f"  Database: {service2.db.host}")  # type: ignore[attr-defined]
    print(f"  Timeout: {service2.timeout}")  # Overridden
    print(f"  Debug: {service2.debug}")
    print()

    # Case 3: Override Injectable parameter for testing
    print("Case 3: Override db for testing")
    test_db = Database(host="localhost", port=5432)

    def test_factory(svcs_container):
        return auto(Service)(svcs_container, db=test_db, debug=True)
    registry3 = svcs.Registry()
    registry3.register_value(Database, prod_db)  # This will be ignored
    registry3.register_factory(Service, test_factory)

    container3 = svcs.Container(registry3)
    service3 = container3.get(Service)
    print(f"  Database: {service3.db.host}")  # type: ignore[attr-defined]  # Test DB, not prod
    print(f"  Timeout: {service3.timeout}")
    print(f"  Debug: {service3.debug}")  # Overridden


if __name__ == "__main__":
    main()
