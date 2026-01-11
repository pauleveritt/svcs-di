"""Function factory with KeywordInjector.

This example demonstrates using functions as factory providers with the
KeywordInjector. The KeywordInjector provides three-tier precedence for
value resolution:

1. kwargs passed to injector (highest priority)
2. container.get(T) for Inject[T] parameters
3. default values from parameter definition (lowest priority)

Key concepts:
- Function factories work with KeywordInjector's kwargs override
- Three-tier precedence applies to all parameters (injectable and non-injectable)
- `@injectable` decorator works the same as with DefaultInjector
"""

from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject, KeywordInjector
from svcs_di.injectors.decorators import injectable


# ============================================================================
# Service definitions
# ============================================================================


@dataclass
class Config:
    """Configuration service."""

    environment: str = "development"
    debug: bool = False


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service created by factory functions."""

    name: str
    config_env: str
    db_host: str
    timeout: int

    def describe(self) -> str:
        return f"{self.name} [{self.config_env}] on {self.db_host} (timeout={self.timeout})"


# ============================================================================
# Factory functions
# ============================================================================


def create_service(
    config: Inject[Config],
    db: Inject[Database],
    timeout: int = 30,
) -> Service:
    """Factory function with injectable and non-injectable parameters.

    Parameters:
    - config: Resolved from container (Inject[Config])
    - db: Resolved from container (Inject[Database])
    - timeout: Uses default value of 30, can be overridden via kwargs
    """
    return Service(
        name="MyService",
        config_env=config.environment,
        db_host=db.host,
        timeout=timeout,
    )


@injectable(for_=Service)
def create_decorated_service(
    config: Inject[Config],
    db: Inject[Database],
    timeout: int = 60,
) -> Service:
    """Decorated factory with different default timeout.

    The @injectable decorator marks this for scanning.
    Functions must specify `for_` parameter.
    """
    return Service(
        name="DecoratedService",
        config_env=config.environment,
        db_host=db.host,
        timeout=timeout,
    )


# ============================================================================
# Example demonstrations
# ============================================================================


def demonstrate_default_values() -> Service:
    """Demonstrate three-tier precedence with default values.

    When no kwargs are provided:
    - Inject[T] parameters get values from container (tier 2)
    - Non-injectable parameters use defaults (tier 3)
    """
    registry = Registry()
    registry.register_factory(Config, Config)
    registry.register_factory(Database, Database)

    container = Container(registry)
    injector = KeywordInjector(container=container)

    # Call factory - uses container values and defaults
    service = injector(create_service)

    # Verify: container values for injectable, default for timeout
    assert service.config_env == "development"  # From container
    assert service.db_host == "localhost"  # From container
    assert service.timeout == 30  # Default value

    return service


def demonstrate_kwargs_override_non_injectable() -> Service:
    """Demonstrate kwargs overriding non-injectable parameters.

    kwargs > container > defaults for non-injectable parameters.
    """
    registry = Registry()
    registry.register_factory(Config, Config)
    registry.register_factory(Database, Database)

    container = Container(registry)
    injector = KeywordInjector(container=container)

    # Override timeout via kwargs (tier 1)
    service = injector(create_service, timeout=120)

    # Verify: kwargs override the default
    assert service.timeout == 120  # From kwargs (not default 30)
    assert service.config_env == "development"  # Still from container
    assert service.db_host == "localhost"  # Still from container

    return service


def demonstrate_kwargs_override_injectable() -> Service:
    """Demonstrate kwargs overriding Inject[T] parameters.

    kwargs can even override Inject[T] parameters - useful for testing.
    """
    registry = Registry()
    registry.register_factory(Config, Config)
    registry.register_factory(Database, Database)

    container = Container(registry)
    injector = KeywordInjector(container=container)

    # Create custom instances to inject via kwargs
    test_config = Config(environment="testing", debug=True)
    test_db = Database(host="test-db", port=5433)

    # Override injectable parameters via kwargs (tier 1)
    service = injector(
        create_service,
        config=test_config,
        db=test_db,
        timeout=5,
    )

    # Verify: all values from kwargs
    assert service.config_env == "testing"  # From kwargs
    assert service.db_host == "test-db"  # From kwargs
    assert service.timeout == 5  # From kwargs

    return service


def demonstrate_partial_override() -> Service:
    """Demonstrate partial kwargs override.

    Some parameters from kwargs, others from container/defaults.
    """
    registry = Registry()
    registry.register_factory(Config, Config)
    registry.register_factory(Database, Database)

    container = Container(registry)
    injector = KeywordInjector(container=container)

    # Only override database, let config come from container
    custom_db = Database(host="staging-db", port=5434)
    service = injector(create_service, db=custom_db)

    # Verify: mixed sources
    assert service.config_env == "development"  # From container (tier 2)
    assert service.db_host == "staging-db"  # From kwargs (tier 1)
    assert service.timeout == 30  # Default (tier 3)

    return service


def demonstrate_custom_container_values() -> Service:
    """Demonstrate container values vs defaults.

    Container-registered values take precedence over parameter defaults.
    """
    registry = Registry()
    # Register custom Config
    registry.register_value(Config, Config(environment="production", debug=False))
    registry.register_value(Database, Database(host="prod-db", port=5432))

    container = Container(registry)
    injector = KeywordInjector(container=container)

    service = injector(create_service)

    # Verify: container values used (not defaults from Config/Database classes)
    assert service.config_env == "production"
    assert service.db_host == "prod-db"
    assert service.timeout == 30  # Still uses parameter default

    return service


# ============================================================================
# Main entry point
# ============================================================================


def main() -> dict[str, Service]:
    """Run all demonstrations and return results."""
    results = {
        "defaults": demonstrate_default_values(),
        "kwargs_non_injectable": demonstrate_kwargs_override_non_injectable(),
        "kwargs_injectable": demonstrate_kwargs_override_injectable(),
        "partial_override": demonstrate_partial_override(),
        "container_values": demonstrate_custom_container_values(),
    }

    # Summary: verify three-tier precedence works correctly
    assert results["defaults"].timeout == 30  # tier 3: default
    assert results["kwargs_non_injectable"].timeout == 120  # tier 1: kwargs
    assert results["kwargs_injectable"].config_env == "testing"  # tier 1: kwargs
    assert results["partial_override"].db_host == "staging-db"  # tier 1: kwargs
    assert results["container_values"].config_env == "production"  # tier 2: container

    return results


if __name__ == "__main__":
    print(main())
