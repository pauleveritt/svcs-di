"""Tests for function parameter injection.

These tests verify that function factories can have their parameters
automatically injected via Inject[T] annotations.
"""

from dataclasses import dataclass
from typing import Protocol

import svcs

from svcs_di import DefaultInjector, Inject
from svcs_di.auto import get_field_infos
from svcs_di.hopscotch_registry import HopscotchRegistry
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.scanning import scan


# Test service types
@dataclass
class Database:
    """Database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Cache:
    """Cache service."""

    ttl: int = 300


class Greeting(Protocol):
    """Greeting protocol."""

    message: str


@dataclass
class DefaultGreeting:
    """Default greeting implementation."""

    message: str = "Hello"


# ============================================================================
# Task 3.1: Tests for function parameter injection
# ============================================================================


def test_function_with_inject_parameter_resolved_from_container():
    """Test function with Inject[T] parameter is resolved from container."""

    def create_service(db: Inject[Database]) -> str:
        return f"Connected to {db.host}:{db.port}"

    # Setup registry and container
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod-db", port=5433))
    container = svcs.Container(registry)

    # Use DefaultInjector to call the function
    injector = DefaultInjector(container=container)
    result = injector(create_service)

    assert result == "Connected to prod-db:5433"


def test_function_with_multiple_inject_parameters():
    """Test function with multiple Inject[T] parameters."""

    def create_service(db: Inject[Database], cache: Inject[Cache]) -> str:
        return f"DB: {db.host}, Cache TTL: {cache.ttl}"

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="multi-db"))
    registry.register_value(Cache, Cache(ttl=600))
    container = svcs.Container(registry)

    injector = DefaultInjector(container=container)
    result = injector(create_service)

    assert result == "DB: multi-db, Cache TTL: 600"


def test_function_with_mixed_injectable_and_non_injectable_parameters():
    """Test function with mixed injectable and non-injectable parameters."""

    def create_service(db: Inject[Database], prefix: str = "Server") -> str:
        return f"{prefix}: {db.host}"

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="mixed-db"))
    container = svcs.Container(registry)

    injector = DefaultInjector(container=container)
    result = injector(create_service)

    # The injector resolves Inject[T] and uses defaults for non-injectable
    assert result == "Server: mixed-db"


def test_function_with_default_values_on_non_injectable_parameters():
    """Test function with default values on non-injectable parameters."""

    def create_greeting(
        db: Inject[Database],
        salutation: str = "Hello",
        punctuation: str = "!",
    ) -> str:
        return f"{salutation} from {db.host}{punctuation}"

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="default-db"))
    container = svcs.Container(registry)

    injector = DefaultInjector(container=container)
    result = injector(create_greeting)

    assert result == "Hello from default-db!"


def test_protocol_based_injection_in_function_parameters():
    """Test protocol-based injection in function parameters."""

    def create_welcome(greeting: Inject[Greeting]) -> str:
        return f"Welcome: {greeting.message}"

    registry = svcs.Registry()
    # Register implementation for protocol
    registry.register_value(Greeting, DefaultGreeting(message="Hi there"))
    container = svcs.Container(registry)

    injector = DefaultInjector(container=container)
    result = injector(create_welcome)

    assert result == "Welcome: Hi there"


def test_get_field_infos_extracts_function_parameters():
    """Test that get_field_infos correctly extracts function parameters."""

    def my_factory(db: Inject[Database], name: str = "default") -> str:
        return f"{name}: {db.host}"

    field_infos = get_field_infos(my_factory)

    assert len(field_infos) == 2

    # First parameter: db with Inject[Database]
    db_info = field_infos[0]
    assert db_info.name == "db"
    assert db_info.is_injectable is True
    assert db_info.inner_type is Database
    assert db_info.has_default is False

    # Second parameter: name with default
    name_info = field_infos[1]
    assert name_info.name == "name"
    assert name_info.is_injectable is False
    assert name_info.has_default is True
    assert name_info.default_value == "default"


# ============================================================================
# Tests for scanning integration with functions
# ============================================================================


def test_scan_discovers_injectable_decorated_functions():
    """Test that scan() discovers @injectable decorated functions.

    Note: Functions require for_ parameter - return type inference is not supported.
    """

    @injectable(for_=Database)
    def create_database() -> Database:
        return Database(host="scanned-db")

    registry = HopscotchRegistry()
    scan(
        registry,
        locals_dict={
            "create_database": create_database,
        },
    )

    # The function should be registered to the locator
    impl = registry.locator.get_implementation(Database)
    assert impl is create_database


def test_scan_function_with_for_parameter():
    """Test scan() with function using for_ parameter for protocol."""

    @injectable(for_=Greeting)
    def create_greeting() -> DefaultGreeting:
        return DefaultGreeting(message="Factory greeting")

    registry = HopscotchRegistry()
    scan(
        registry,
        locals_dict={
            "create_greeting": create_greeting,
        },
    )

    # Should be registered under Greeting protocol
    # Use locator to resolve implementation
    impl = registry.locator.get_implementation(Greeting)
    assert impl is create_greeting


def test_scan_function_with_inject_parameters():
    """Test scan() with function that has Inject[T] parameters.

    Note: Functions require for_ parameter.
    """

    @injectable(for_=Cache)
    def create_cache_wrapper(db: Inject[Database]) -> Cache:
        # Factory that depends on Database
        return Cache(ttl=db.port)  # Use port as TTL for testing

    # First register Database
    registry = HopscotchRegistry()
    registry.register_value(Database, Database(host="inject-db", port=999))

    scan(
        registry,
        locals_dict={
            "create_cache_wrapper": create_cache_wrapper,
        },
    )

    # Verify it's registered in the locator
    impl = registry.locator.get_implementation(Cache)
    assert impl is create_cache_wrapper


# ============================================================================
# Tests for function edge cases
# ============================================================================


def test_scan_function_without_for_raises_error():
    """Test that function without for_ parameter raises clear error."""
    import pytest

    @injectable
    def create_something() -> DefaultGreeting:
        return DefaultGreeting(message="No for_")

    registry = svcs.Registry()
    with pytest.raises(ValueError, match="must specify for_ parameter"):
        scan(
            registry,
            locals_dict={
                "create_something": create_something,
            },
        )
