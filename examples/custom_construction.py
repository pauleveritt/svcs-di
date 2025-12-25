"""Custom construction with __svcs__ method example.

This example demonstrates the __svcs__ protocol for custom service construction:
- When to use __svcs__ instead of Injectable fields
- How to manually fetch dependencies from the container
- Complex initialization patterns like validation and conditional construction
- The kwargs override pattern for flexible service configuration

The __svcs__ method signature:
    @classmethod
    def __svcs__(cls, container: svcs.Container, **kwargs) -> Self
"""

from dataclasses import dataclass
from typing import Self

import svcs

from svcs_di import auto


# ============================================================================
# Example 1: Custom Validation Logic
# ============================================================================


@dataclass
class ValidationConfig:
    """Configuration service with validation rules."""

    min_value: int = 0
    max_value: int = 100


@dataclass
class ValidatedService:
    """A service that validates its configuration during construction.

    This demonstrates using __svcs__ for post-construction validation logic
    that cannot be expressed through simple Injectable field resolution.
    """

    config: ValidationConfig
    value: int

    @classmethod
    def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
        """Custom construction with validation logic."""
        # Fetch the config from the container
        config = container.get(ValidationConfig)

        # Get the value from kwargs or use a default
        value = kwargs.get("value", 50)

        # Perform validation that can't be done with normal injection
        if not (config.min_value <= value <= config.max_value):
            raise ValueError(
                f"Value {value} is outside valid range "
                f"[{config.min_value}, {config.max_value}]"
            )

        return cls(config=config, value=value)


# ============================================================================
# Example 2: Conditional Construction Based on Container Contents
# ============================================================================


@dataclass
class FeatureFlags:
    """Feature flags service."""

    use_cache: bool = True
    use_logging: bool = True


@dataclass
class CacheService:
    """A simple cache service."""

    enabled: bool = True


@dataclass
class LoggingService:
    """A simple logging service."""

    enabled: bool = True


@dataclass
class ConditionalService:
    """A service that conditionally fetches dependencies based on feature flags.

    This demonstrates using __svcs__ to dynamically decide which services
    to fetch based on runtime conditions (feature flags).
    """

    cache: CacheService | None
    logger: LoggingService | None
    name: str

    @classmethod
    def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
        """Custom construction that conditionally fetches services."""
        # Always fetch feature flags
        flags = container.get(FeatureFlags)

        # Conditionally fetch cache if enabled
        cache = None
        if flags.use_cache:
            try:
                cache = container.get(CacheService)
            except svcs.exceptions.ServiceNotFoundError:
                pass

        # Conditionally fetch logger if enabled
        logger = None
        if flags.use_logging:
            try:
                logger = container.get(LoggingService)
            except svcs.exceptions.ServiceNotFoundError:
                pass

        name = kwargs.get("name", "conditional-service")

        return cls(cache=cache, logger=logger, name=name)


# ============================================================================
# Example 3: Complex Initialization with Multiple Container Lookups
# ============================================================================


@dataclass
class DatabaseConfig:
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class ConnectionPool:
    """Connection pool service."""

    max_connections: int = 10


@dataclass
class QueryLogger:
    """Query logging service."""

    enabled: bool = True


@dataclass
class ComplexDatabaseService:
    """A service with complex initialization requiring multiple container lookups.

    This demonstrates using __svcs__ when construction logic is too complex
    to express through simple field injection - it needs configuration from
    multiple services and applies custom logic during initialization.
    """

    connection_string: str
    pool_size: int
    logging_enabled: bool

    @classmethod
    def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
        """Custom construction that combines data from multiple container services."""
        # Fetch multiple services from the container
        db_config = container.get(DatabaseConfig)
        pool = container.get(ConnectionPool)
        logger = container.get(QueryLogger)

        # Build connection string with custom logic
        connection_string = kwargs.get(
            "connection_string",
            f"postgresql://{db_config.host}:{db_config.port}/mydb",
        )

        # Use pool size from kwargs, fallback to container service, then default
        if "pool_size" in kwargs:
            pool_size = kwargs["pool_size"]
        else:
            pool_size = pool.max_connections

        # Logging can be overridden or taken from logger service
        logging_enabled = kwargs.get("logging_enabled", logger.enabled)

        return cls(
            connection_string=connection_string,
            pool_size=pool_size,
            logging_enabled=logging_enabled,
        )


# ============================================================================
# Example 4: Comparison - Injectable vs __svcs__
# ============================================================================


@dataclass
class SimpleConfig:
    """Simple configuration service."""

    timeout: int = 30


# BEFORE: Using Injectable fields (simple case)
@dataclass
class ServiceWithInjectable:
    """Service using normal Injectable field injection.

    Use this pattern when:
    - Dependencies can be directly injected into fields
    - No custom logic needed during construction
    - No validation or conditional construction required
    """

    # config: Injectable[SimpleConfig]  # Automatic injection
    # name: str = "default"


# AFTER: Using __svcs__ (when you need custom control)
@dataclass
class ServiceWithSvcs:
    """Service using __svcs__ for custom construction.

    Use this pattern when:
    - You need validation logic during construction
    - Construction depends on runtime conditions
    - You need to fetch services conditionally
    - Initialization is too complex for simple field injection
    """

    config: SimpleConfig
    name: str

    @classmethod
    def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
        """Custom construction with full control."""
        config = container.get(SimpleConfig)

        # Add custom logic here that can't be done with Injectable
        name = kwargs.get("name", "custom")

        # Could add validation, logging, conditional logic, etc.
        return cls(config=config, name=name)


# ============================================================================
# Demo Functions
# ============================================================================


def demo_validation():
    """Demonstrate custom validation logic."""
    print("\n=== Example 1: Custom Validation ===")

    registry = svcs.Registry()
    registry.register_value(ValidationConfig, ValidationConfig(min_value=10, max_value=90))
    registry.register_factory(ValidatedService, auto(ValidatedService))

    container = svcs.Container(registry)

    # Valid value
    service1 = container.get(ValidatedService)
    print(f"Service created with default value: {service1.value}")

    # Override with valid value
    def factory_valid(svcs_container: svcs.Container) -> ValidatedService:
        return auto(ValidatedService)(svcs_container, value=75)

    registry.register_factory(ValidatedService, factory_valid)
    container = svcs.Container(registry)
    service2 = container.get(ValidatedService)
    print(f"Service created with custom valid value: {service2.value}")

    # Try invalid value (this will raise ValueError)
    try:
        def factory_invalid(svcs_container: svcs.Container) -> ValidatedService:
            return auto(ValidatedService)(svcs_container, value=999)

        registry.register_factory(ValidatedService, factory_invalid)
        container = svcs.Container(registry)
        container.get(ValidatedService)
    except ValueError as e:
        print(f"Validation failed as expected: {e}")


def demo_conditional():
    """Demonstrate conditional construction."""
    print("\n=== Example 2: Conditional Construction ===")

    # Setup with cache and logging enabled
    registry = svcs.Registry()
    registry.register_value(FeatureFlags, FeatureFlags(use_cache=True, use_logging=True))
    registry.register_value(CacheService, CacheService(enabled=True))
    registry.register_value(LoggingService, LoggingService(enabled=True))
    registry.register_factory(ConditionalService, auto(ConditionalService))

    container = svcs.Container(registry)
    service1 = container.get(ConditionalService)
    print(f"Service with cache: {service1.cache is not None}")
    print(f"Service with logger: {service1.logger is not None}")

    # Setup with only cache enabled
    registry2 = svcs.Registry()
    registry2.register_value(FeatureFlags, FeatureFlags(use_cache=True, use_logging=False))
    registry2.register_value(CacheService, CacheService(enabled=True))
    registry2.register_factory(ConditionalService, auto(ConditionalService))

    container2 = svcs.Container(registry2)
    service2 = container2.get(ConditionalService)
    print(f"Service with cache only: {service2.cache is not None}")
    print(f"Service without logger: {service2.logger is None}")


def demo_complex():
    """Demonstrate complex initialization."""
    print("\n=== Example 3: Complex Initialization ===")

    registry = svcs.Registry()
    registry.register_value(DatabaseConfig, DatabaseConfig(host="prod.db.com", port=5433))
    registry.register_value(ConnectionPool, ConnectionPool(max_connections=50))
    registry.register_value(QueryLogger, QueryLogger(enabled=True))
    registry.register_factory(ComplexDatabaseService, auto(ComplexDatabaseService))

    container = svcs.Container(registry)
    service = container.get(ComplexDatabaseService)
    print(f"Connection string: {service.connection_string}")
    print(f"Pool size: {service.pool_size}")
    print(f"Logging enabled: {service.logging_enabled}")


def main():
    """Run all demonstrations."""
    print("Custom Construction with __svcs__ Examples")
    print("=" * 60)

    demo_validation()
    demo_conditional()
    demo_complex()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
