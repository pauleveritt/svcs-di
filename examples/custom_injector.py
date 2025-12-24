"""Custom injector example.

This example demonstrates implementing a custom injector:
- Define a custom injector dataclass that adds logging or validation
- Register the custom injector as DefaultInjector replacement
- All auto() factories will use the custom injector
"""

import dataclasses
from dataclasses import dataclass

import svcs

from svcs_di import DefaultInjector, Injectable, auto


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service that depends on a database."""

    db: Injectable[Database]
    timeout: int = 30


@dataclasses.dataclass
class LoggingInjector:
    """Custom injector that logs all dependency injections."""

    container: svcs.Container

    def __call__(self, target, **kwargs):
        """Injector that logs before and after injection."""
        print(f"[INJECTOR] Creating instance of {target.__name__}")
        print(f"[INJECTOR] Kwargs: {kwargs}")

        # Use default injector to do the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        print(f"[INJECTOR] Created {target.__name__} successfully")
        return instance


@dataclasses.dataclass
class ValidatingInjector:
    """Custom injector that validates field values."""

    container: svcs.Container

    def __call__(self, target, **kwargs):
        """Injector that validates timeout is positive."""
        # Check if timeout is being set and validate it
        if "timeout" in kwargs and kwargs["timeout"] <= 0:
            raise ValueError(f"timeout must be positive, got {kwargs['timeout']}")

        # Use default injector to do the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        # Post-construction validation
        if hasattr(instance, "timeout") and instance.timeout <= 0:
            raise ValueError(f"Invalid timeout: {instance.timeout}")

        return instance


def main():
    """Demonstrate custom injector."""
    # Example 1: Logging injector
    print("Example 1: Logging Injector")
    print("=" * 50)

    def logging_injector_factory(container: svcs.Container) -> LoggingInjector:
        return LoggingInjector(container=container)

    registry = svcs.Registry()

    # Register custom logging injector
    registry.register_factory(DefaultInjector, logging_injector_factory)

    # Register services
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Service, auto(Service))

    # Get service - custom injector will log
    container = svcs.Container(registry)
    service = container.get(Service)
    print(f"Service timeout: {service.timeout}")
    print()

    # Example 2: Validating injector
    print("Example 2: Validating Injector")
    print("=" * 50)

    def validating_injector_factory(
        container: svcs.Container,
    ) -> ValidatingInjector:
        return ValidatingInjector(container=container)

    registry2 = svcs.Registry()

    # Register custom validating injector
    registry2.register_factory(DefaultInjector, validating_injector_factory)

    # Register services
    registry2.register_value(Database, Database())

    # This will work (valid timeout)
    def valid_factory(svcs_container):
        return auto(Service)(svcs_container, timeout=60)

    registry2.register_factory(Service, valid_factory)

    container2 = svcs.Container(registry2)
    service2 = container2.get(Service)
    print(f"Valid service created with timeout: {service2.timeout}")

    # This will fail (invalid timeout)
    print("\nTrying to create service with invalid timeout...")
    registry3 = svcs.Registry()
    registry3.register_factory(DefaultInjector, validating_injector_factory)
    registry3.register_value(Database, Database())

    def invalid_factory(svcs_container):
        return auto(Service)(svcs_container, timeout=-10)

    registry3.register_factory(Service, invalid_factory)

    container3 = svcs.Container(registry3)
    try:
        service3 = container3.get(Service)
    except ValueError as e:
        print(f"Validation failed as expected: {e}")


if __name__ == "__main__":
    main()
