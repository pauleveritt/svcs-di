"""Tests for callable (function) registration support.

These tests verify that functions can be registered as factory providers
alongside classes in HopscotchRegistry and ServiceLocator.
"""

import functools
from collections.abc import Callable
from pathlib import PurePath

from svcs_di.hopscotch_registry import HopscotchRegistry
from svcs_di.injectors.locator import ServiceLocator


# Test service types
class Greeting:
    """Service type for testing."""

    def __init__(self, message: str = "Hello"):
        self.message = message


class CustomerContext:
    """Resource context for testing."""

    pass


# ============================================================================
# Task 2.1: Tests for callable registration
# ============================================================================


def test_register_sync_function_as_factory():
    """Test registering a sync function as factory provider."""

    def create_greeting() -> Greeting:
        return Greeting("Hello from factory")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, create_greeting)

    # Verify registration in locator
    impl = registry.locator.get_implementation(Greeting)
    assert impl is create_greeting

    # Verify the factory can be called
    result = impl()
    assert isinstance(result, Greeting)
    assert result.message == "Hello from factory"


def test_register_async_function_as_factory():
    """Test registering an async function as factory provider."""

    async def create_async_greeting() -> Greeting:
        return Greeting("Hello from async factory")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, create_async_greeting)

    # Verify registration in locator
    impl = registry.locator.get_implementation(Greeting)
    assert impl is create_async_greeting


def test_register_lambda_as_factory():
    """Test registering a lambda as factory provider."""
    create_lambda_greeting: Callable[[], Greeting] = lambda: Greeting("Lambda greeting")  # noqa: E731

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, create_lambda_greeting)

    # Verify registration in locator
    impl = registry.locator.get_implementation(Greeting)
    assert impl is create_lambda_greeting

    # Verify the lambda can be called
    result = impl()
    assert isinstance(result, Greeting)
    assert result.message == "Lambda greeting"


def test_register_partial_as_factory():
    """Test registering a functools.partial wrapped function as factory."""

    def create_greeting_with_prefix(prefix: str) -> Greeting:
        return Greeting(f"{prefix} World")

    partial_factory = functools.partial(create_greeting_with_prefix, "Hello")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, partial_factory)

    # Verify registration in locator
    impl = registry.locator.get_implementation(Greeting)
    assert impl is partial_factory

    # Verify the partial can be called
    result = impl()
    assert isinstance(result, Greeting)
    assert result.message == "Hello World"


def test_class_registration_still_works():
    """Test that existing class-based registration still works."""

    class DefaultGreeting(Greeting):
        def __init__(self):
            super().__init__("Class-based greeting")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)

    # Verify registration in locator
    impl = registry.locator.get_implementation(Greeting)
    assert impl is DefaultGreeting

    # Verify the class can be instantiated
    result = impl()
    assert isinstance(result, Greeting)
    assert result.message == "Class-based greeting"


def test_function_with_resource_context():
    """Test registering a function with resource context."""

    def create_customer_greeting() -> Greeting:
        return Greeting("Welcome, customer!")

    registry = HopscotchRegistry()
    registry.register_implementation(
        Greeting, create_customer_greeting, resource=CustomerContext
    )

    # Verify registration with resource
    impl = registry.locator.get_implementation(Greeting, resource=CustomerContext)
    assert impl is create_customer_greeting


def test_function_with_location_context():
    """Test registering a function with location context."""

    def create_admin_greeting() -> Greeting:
        return Greeting("Welcome, admin!")

    registry = HopscotchRegistry()
    registry.register_implementation(
        Greeting, create_admin_greeting, location=PurePath("/admin")
    )

    # Verify registration with location
    impl = registry.locator.get_implementation(Greeting, location=PurePath("/admin"))
    assert impl is create_admin_greeting


# ============================================================================
# ServiceLocator direct tests
# ============================================================================


def test_service_locator_register_function():
    """Test ServiceLocator.register() with a function."""

    def create_greeting() -> Greeting:
        return Greeting("Direct locator registration")

    locator = ServiceLocator()
    locator = locator.register(Greeting, create_greeting)

    impl = locator.get_implementation(Greeting)
    assert impl is create_greeting


def test_mixed_class_and_function_registrations():
    """Test mixing class and function registrations for same service type."""

    class DefaultGreeting(Greeting):
        def __init__(self):
            super().__init__("Default")

    def create_customer_greeting() -> Greeting:
        return Greeting("Customer")

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, create_customer_greeting, resource=CustomerContext
    )

    # Default should return class
    default_impl = registry.locator.get_implementation(Greeting)
    assert default_impl is DefaultGreeting

    # With resource should return function
    customer_impl = registry.locator.get_implementation(Greeting, resource=CustomerContext)
    assert customer_impl is create_customer_greeting
