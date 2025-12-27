"""Tests for Injectable[Container] support across all injector types."""

import pytest
import svcs

from dataclasses import dataclass

from svcs_di.auto import (
    DefaultAsyncInjector,
    DefaultInjector,
    Injectable,
)
from svcs_di.injectors.keyword import KeywordAsyncInjector, KeywordInjector
from svcs_di.injectors.locator import (
    HopscotchAsyncInjector,
    HopscotchInjector,
)


# ============================================================================
# Shared Test Fixtures
# ============================================================================


@dataclass
class Database:
    """Simple database service."""

    host: str = "localhost"


@dataclass
class ServiceWithContainer:
    """Service that needs the container for dynamic service resolution."""

    container: Injectable[svcs.Container]
    name: str = "test"


@dataclass
class ServiceUsingContainer:
    """Service that uses injected container to get other services dynamically."""

    container: Injectable[svcs.Container]

    def get_database(self):
        """Dynamically resolve Database using the injected container."""
        return self.container.get(Database)


# ============================================================================
# Task Group 1: DefaultInjector and DefaultAsyncInjector Tests
# ============================================================================


def test_default_injector_injects_container():
    """DefaultInjector injects self.container when Injectable[Container] is detected."""
    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = DefaultInjector(container=container)

    service = injector(ServiceWithContainer)

    assert isinstance(service, ServiceWithContainer)
    assert service.container is container
    assert service.name == "test"


def test_default_injector_container_in_dataclass_field():
    """DefaultInjector injects Container in dataclass fields."""
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod"))
    container = svcs.Container(registry)
    injector = DefaultInjector(container=container)

    service = injector(ServiceUsingContainer)

    # Container should be injected
    assert service.container is container
    # Use injected container to get another service
    db = service.get_database()
    assert isinstance(db, Database)
    assert db.host == "prod"


def test_default_injector_container_with_default_fallback():
    """DefaultInjector falls back to default value when Container is not injectable."""

    @dataclass
    class ServiceWithDefault:
        container: svcs.Container | None = None
        name: str = "test"

    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = DefaultInjector(container=container)

    service = injector(ServiceWithDefault)

    # No Injectable marker, so default value should be used
    assert service.container is None
    assert service.name == "test"


@pytest.mark.anyio
async def test_default_async_injector_injects_container():
    """DefaultAsyncInjector injects self.container when Injectable[Container] is detected."""
    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = DefaultAsyncInjector(container=container)

    service = await injector(ServiceWithContainer)

    assert isinstance(service, ServiceWithContainer)
    assert service.container is container
    assert service.name == "test"


@pytest.mark.anyio
async def test_default_async_injector_container_in_dataclass_field():
    """DefaultAsyncInjector injects Container in dataclass fields."""
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="async-prod"))
    container = svcs.Container(registry)
    injector = DefaultAsyncInjector(container=container)

    service = await injector(ServiceUsingContainer)

    # Container should be injected
    assert service.container is container
    # Use injected container to get another service
    db = service.get_database()
    assert isinstance(db, Database)
    assert db.host == "async-prod"


@pytest.mark.anyio
async def test_default_async_injector_container_with_default_fallback():
    """DefaultAsyncInjector falls back to default value when Container is not injectable."""

    @dataclass
    class ServiceWithDefault:
        container: svcs.Container | None = None
        name: str = "async-test"

    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = DefaultAsyncInjector(container=container)

    service = await injector(ServiceWithDefault)

    # No Injectable marker, so default value should be used
    assert service.container is None
    assert service.name == "async-test"


# ============================================================================
# Task Group 2: KeywordInjector and KeywordAsyncInjector Tests
# ============================================================================


def test_keyword_injector_three_tier_precedence_kwargs_wins():
    """KeywordInjector: kwargs override takes highest priority (Tier 1)."""
    registry = svcs.Registry()
    container1 = svcs.Container(registry)
    container2 = svcs.Container(registry)
    injector = KeywordInjector(container=container1)

    # Pass explicit container in kwargs - should override injector's container
    service = injector(ServiceWithContainer, container=container2)

    assert service.container is container2  # kwargs wins
    assert service.container is not container1


def test_keyword_injector_three_tier_precedence_container_injection():
    """KeywordInjector: Container injection happens when not in kwargs (Tier 2)."""
    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = KeywordInjector(container=container)

    service = injector(ServiceWithContainer)

    assert service.container is container  # injected from injector


def test_keyword_injector_three_tier_precedence_defaults():
    """KeywordInjector: defaults are lowest priority (Tier 3)."""

    @dataclass
    class ServiceWithContainerDefault:
        container: Injectable[svcs.Container]
        name: str = "default-name"

    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = KeywordInjector(container=container)

    service = injector(ServiceWithContainerDefault)

    assert service.container is container  # Tier 2 injection
    assert service.name == "default-name"  # Tier 3 default


@pytest.mark.anyio
async def test_keyword_async_injector_three_tier_precedence_kwargs_wins():
    """KeywordAsyncInjector: kwargs override takes highest priority (Tier 1)."""
    registry = svcs.Registry()
    container1 = svcs.Container(registry)
    container2 = svcs.Container(registry)
    injector = KeywordAsyncInjector(container=container1)

    # Pass explicit container in kwargs - should override injector's container
    service = await injector(ServiceWithContainer, container=container2)

    assert service.container is container2  # kwargs wins
    assert service.container is not container1


@pytest.mark.anyio
async def test_keyword_async_injector_three_tier_precedence_container_injection():
    """KeywordAsyncInjector: Container injection happens when not in kwargs (Tier 2)."""
    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = KeywordAsyncInjector(container=container)

    service = await injector(ServiceWithContainer)

    assert service.container is container  # injected from injector


@pytest.mark.anyio
async def test_keyword_async_injector_three_tier_precedence_defaults():
    """KeywordAsyncInjector: defaults are lowest priority (Tier 3)."""

    @dataclass
    class ServiceWithContainerDefault:
        container: Injectable[svcs.Container]
        name: str = "async-default-name"

    registry = svcs.Registry()
    container = svcs.Container(registry)
    injector = KeywordAsyncInjector(container=container)

    service = await injector(ServiceWithContainerDefault)

    assert service.container is container  # Tier 2 injection
    assert service.name == "async-default-name"  # Tier 3 default


# ============================================================================
# Task Group 3: HopscotchInjector and HopscotchAsyncInjector Tests
# ============================================================================


def test_hopscotch_injector_bypasses_locator():
    """HopscotchInjector: Container injection bypasses ServiceLocator lookup."""
    from svcs_di.injectors.locator import ServiceLocator

    registry = svcs.Registry()

    # Create a locator with some registrations (should be ignored for Container)
    locator = ServiceLocator()
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(ServiceWithContainer)

    # Container should be injected directly, not resolved via locator
    assert service.container is container


def test_hopscotch_injector_kwargs_override():
    """HopscotchInjector: kwargs can override Container injection."""
    registry = svcs.Registry()
    container1 = svcs.Container(registry)
    container2 = svcs.Container(registry)
    injector = HopscotchInjector(container=container1)

    service = injector(ServiceWithContainer, container=container2)

    assert service.container is container2  # kwargs wins


def test_hopscotch_injector_context_agnostic():
    """HopscotchInjector: Container is not affected by context-aware resolution."""
    from pathlib import PurePath
    from svcs_di.injectors.locator import Location, ServiceLocator

    registry = svcs.Registry()

    # Setup location-based resolution
    locator = ServiceLocator()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/admin"))

    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container)

    service = injector(ServiceWithContainer)

    # Container should be injected regardless of location context
    assert service.container is container


@pytest.mark.anyio
async def test_hopscotch_async_injector_bypasses_locator():
    """HopscotchAsyncInjector: Container injection bypasses ServiceLocator lookup."""
    from svcs_di.injectors.locator import ServiceLocator

    registry = svcs.Registry()

    # Create a locator with some registrations (should be ignored for Container)
    locator = ServiceLocator()
    registry.register_value(ServiceLocator, locator)

    container = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container)

    service = await injector(ServiceWithContainer)

    # Container should be injected directly, not resolved via locator
    assert service.container is container


@pytest.mark.anyio
async def test_hopscotch_async_injector_kwargs_override():
    """HopscotchAsyncInjector: kwargs can override Container injection."""
    registry = svcs.Registry()
    container1 = svcs.Container(registry)
    container2 = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container1)

    service = await injector(ServiceWithContainer, container=container2)

    assert service.container is container2  # kwargs wins


@pytest.mark.anyio
async def test_hopscotch_async_injector_context_agnostic():
    """HopscotchAsyncInjector: Container is not affected by context-aware resolution."""
    from pathlib import PurePath
    from svcs_di.injectors.locator import Location, ServiceLocator

    registry = svcs.Registry()

    # Setup location-based resolution
    locator = ServiceLocator()
    registry.register_value(ServiceLocator, locator)
    registry.register_value(Location, PurePath("/admin"))

    container = svcs.Container(registry)
    injector = HopscotchAsyncInjector(container=container)

    service = await injector(ServiceWithContainer)

    # Container should be injected regardless of location context
    assert service.container is container
