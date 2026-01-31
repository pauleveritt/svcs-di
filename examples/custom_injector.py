"""Custom injector example.

This example demonstrates implementing a custom injector:
- Define a custom injector dataclass that adds logging or validation
- Register the custom injector as DefaultInjector replacement
- All auto() factories will use the custom injector
"""

import dataclasses
from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject, Injector, auto
from svcs_di.auto import DefaultInjector


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service that depends on a database."""

    db: Inject[Database]
    timeout: int = 30


@dataclasses.dataclass
class LoggingInjector:
    """Custom injector that logs all dependency injections."""

    container: Container

    def __call__(self, target):
        """Injector that logs before and after injection."""
        print(f"[INJECTOR] Creating instance of {target.__name__}")

        # Use default injector to do the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target)

        print(f"[INJECTOR] Created {target.__name__} successfully")
        return instance


@dataclasses.dataclass
class ValidatingInjector:
    """Custom injector that validates field values after construction."""

    container: Container

    def __call__(self, target):
        """Injector that validates timeout is positive."""
        # Use default injector to do the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target)

        # Post-construction validation
        if hasattr(instance, "timeout") and instance.timeout <= 0:
            raise ValueError(f"Invalid timeout: {instance.timeout}")

        return instance


def main():
    """Demonstrate custom injector."""
    # Example 1: Logging injector
    print("Example 1: Logging Injector")
    print("=" * 50)

    def logging_injector_factory(container: Container) -> LoggingInjector:
        return LoggingInjector(container=container)

    registry = Registry()

    # Register custom logging injector
    registry.register_factory(Injector, logging_injector_factory)

    # Register services
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Service, auto(Service))

    # Get service - custom injector will log
    container = Container(registry)
    service = container.get(Service)
    print(f"Service timeout: {service.timeout}")
    print()

    # Example 2: Validating injector
    print("Example 2: Validating Injector")
    print("=" * 50)

    def validating_injector_factory(
        container: Container,
    ) -> ValidatingInjector:
        return ValidatingInjector(container=container)

    registry2 = Registry()

    # Register custom validating injector
    registry2.register_factory(Injector, validating_injector_factory)

    # Register services
    registry2.register_value(Database, Database())

    # This will work (valid timeout with default)
    registry2.register_factory(Service, auto(Service))

    container2 = Container(registry2)
    service2 = container2.get(Service)
    print(f"Valid service created with timeout: {service2.timeout}")

    # This will fail (invalid timeout set as default)
    print("\nTrying to create service with invalid timeout...")

    @dataclass
    class InvalidService:
        """A service with an invalid default timeout."""

        db: Inject[Database]
        timeout: int = -10  # Invalid!

    registry3 = Registry()
    registry3.register_factory(Injector, validating_injector_factory)
    registry3.register_value(Database, Database())
    registry3.register_factory(InvalidService, auto(InvalidService))

    container3 = Container(registry3)
    try:
        _ = container3.get(InvalidService)
    except ValueError as e:
        print(f"Validation failed as expected: {e}")


if __name__ == "__main__":
    main()
