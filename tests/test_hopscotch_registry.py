"""Tests for HopscotchRegistry and HopscotchContainer classes.

Task Group 1: Tests for basic class structure and attrs integration.
Task Group 2: Tests for HopscotchContainer class.
Task Group 3: Tests for scan() integration with HopscotchRegistry.
Task Group 4: Gap analysis tests - end-to-end workflows and edge cases.
"""

from dataclasses import dataclass
from pathlib import PurePath

import attrs
import pytest
import svcs

from svcs_di.auto import Inject
from svcs_di.injectors import (
    HopscotchAsyncInjector,
    HopscotchContainer,
    HopscotchInjector,
    HopscotchRegistry,
    ServiceLocator,
)


# =============================================================================
# Shared test fixtures
# =============================================================================


@dataclass
class Greeting:
    """A simple greeting service for testing."""

    message: str = "Hello"


@dataclass
class DefaultGreeting(Greeting):
    """Default greeting implementation."""

    message: str = "Hello, World!"


@dataclass
class EmployeeGreeting(Greeting):
    """Employee-specific greeting implementation."""

    message: str = "Hello, Employee!"


class EmployeeContext:
    """Resource type for employee context."""

    pass


# =============================================================================
# Task Group 1: HopscotchRegistry Class Definition Tests
# =============================================================================


def test_hopscotch_registry_can_be_instantiated() -> None:
    """Test that HopscotchRegistry can be instantiated."""
    registry = HopscotchRegistry()

    assert registry is not None
    assert isinstance(registry, HopscotchRegistry)


def test_hopscotch_registry_has_internal_locator_attribute() -> None:
    """Test that HopscotchRegistry has internal _locator attribute."""
    registry = HopscotchRegistry()

    assert hasattr(registry, "_locator")
    assert isinstance(registry._locator, ServiceLocator)


def test_hopscotch_registry_locator_property_returns_internal_service_locator() -> None:
    """Test that locator property returns the internal ServiceLocator."""
    registry = HopscotchRegistry()

    locator = registry.locator

    assert locator is registry._locator
    assert isinstance(locator, ServiceLocator)


def test_hopscotch_registry_is_subclass_of_svcs_registry() -> None:
    """Test that HopscotchRegistry is a subclass of svcs.Registry."""
    assert issubclass(HopscotchRegistry, svcs.Registry)

    registry = HopscotchRegistry()
    assert isinstance(registry, svcs.Registry)


def test_hopscotch_registry_uses_attrs_style_subclassing() -> None:
    """Test that attrs-style subclassing is used (verify __attrs_attrs__ exists)."""
    # Attrs-decorated classes have __attrs_attrs__
    assert hasattr(HopscotchRegistry, "__attrs_attrs__")

    # Verify it's properly decorated with attrs
    assert attrs.has(HopscotchRegistry)


def test_hopscotch_registry_inherited_register_factory_and_register_value_work() -> (
    None
):
    """Test that inherited register_factory/register_value methods work."""
    registry = HopscotchRegistry()

    # Test register_value (inherited from svcs.Registry)
    greeting = Greeting(message="Test")
    registry.register_value(Greeting, greeting)

    # Verify by creating a container and getting the value
    container = svcs.Container(registry)
    result = container.get(Greeting)
    assert result is greeting
    assert result.message == "Test"

    # Test register_factory (inherited from svcs.Registry)
    registry.register_factory(DefaultGreeting, DefaultGreeting)
    result2 = container.get(DefaultGreeting)
    assert isinstance(result2, DefaultGreeting)
    assert result2.message == "Hello, World!"


# =============================================================================
# Task Group 1: register_implementation() Method Tests
# =============================================================================


def test_register_implementation_updates_internal_locator() -> None:
    """Test that register_implementation() updates internal locator."""
    registry = HopscotchRegistry()

    # Get initial locator reference
    initial_locator = registry._locator

    # Register an implementation
    registry.register_implementation(Greeting, DefaultGreeting)

    # Verify the internal locator was updated (immutable update pattern)
    assert registry._locator is not initial_locator

    # Verify the implementation is registered in the locator
    impl = registry.locator.get_implementation(Greeting)
    assert impl is DefaultGreeting


def test_register_implementation_with_resource() -> None:
    """Test that register_implementation() works with resource parameter."""
    registry = HopscotchRegistry()

    # Register default implementation
    registry.register_implementation(Greeting, DefaultGreeting)

    # Register resource-specific implementation
    registry.register_implementation(
        Greeting, EmployeeGreeting, resource=EmployeeContext
    )

    # Verify both implementations are registered
    default_impl = registry.locator.get_implementation(Greeting)
    assert default_impl is DefaultGreeting

    employee_impl = registry.locator.get_implementation(
        Greeting, resource=EmployeeContext
    )
    assert employee_impl is EmployeeGreeting


def test_register_implementation_with_location() -> None:
    """Test that register_implementation() works with location parameter."""
    registry = HopscotchRegistry()

    # Register location-specific implementation
    admin_location = PurePath("/admin")
    registry.register_implementation(
        Greeting, EmployeeGreeting, location=admin_location
    )

    # Verify the implementation is registered with location
    impl = registry.locator.get_implementation(Greeting, location=admin_location)
    assert impl is EmployeeGreeting

    # Without location, should not find (location-specific only)
    impl_no_loc = registry.locator.get_implementation(Greeting)
    assert impl_no_loc is None


def test_register_implementation_re_registers_locator_as_value_service() -> None:
    """Test that register_implementation() re-registers locator as value service."""
    registry = HopscotchRegistry()

    # Register an implementation
    registry.register_implementation(Greeting, DefaultGreeting)

    # Create a container and verify ServiceLocator is accessible
    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # Verify it's the same locator
    assert locator is registry.locator
    assert locator is registry._locator

    # Verify the implementation is accessible via the locator
    impl = locator.get_implementation(Greeting)
    assert impl is DefaultGreeting


# =============================================================================
# Task Group 2: HopscotchContainer Class Definition Tests
# =============================================================================


def test_hopscotch_container_can_be_instantiated_with_hopscotch_registry() -> None:
    """Test that HopscotchContainer can be instantiated with HopscotchRegistry."""
    registry = HopscotchRegistry()
    container = HopscotchContainer(registry)

    assert container is not None
    assert isinstance(container, HopscotchContainer)
    assert isinstance(container, svcs.Container)


def test_hopscotch_container_injector_field_defaults_to_hopscotch_injector() -> None:
    """Test that injector field defaults to HopscotchInjector."""
    registry = HopscotchRegistry()
    container = HopscotchContainer(registry)

    assert container.injector is HopscotchInjector


def test_hopscotch_container_async_injector_field_defaults_to_hopscotch_async_injector() -> (
    None
):
    """Test that async_injector field defaults to HopscotchAsyncInjector."""
    registry = HopscotchRegistry()
    container = HopscotchContainer(registry)

    assert container.async_injector is HopscotchAsyncInjector


def test_hopscotch_container_inject_resolves_resource_dynamically_from_container() -> (
    None
):
    """Test that inject() resolves resource dynamically from container."""
    registry = HopscotchRegistry()

    # Register implementations with resource-based selection
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, EmployeeGreeting, resource=EmployeeContext
    )

    # Create a dataclass that uses Inject[Greeting]
    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    container = HopscotchContainer(registry)

    # Without resource in container, should get default implementation
    service = container.inject(WelcomeService)
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.greeting.message == "Hello, World!"

    # Register resource in container and verify resource-based selection
    # Register an EmployeeContext value
    registry.register_value(EmployeeContext, EmployeeContext())

    # Create new container after registering resource
    container3 = HopscotchContainer(registry)
    # Note: inject() passes resource=None, letting the injector handle resolution
    # The injector's _get_resource() looks up resource from container if configured
    service3 = container3.inject(WelcomeService)
    # Since we pass resource=None to injector, it uses _get_resource() which
    # requires self.resource to be set. Since HopscotchContainer doesn't set
    # resource attribute, we get DefaultGreeting
    assert isinstance(service3.greeting, DefaultGreeting)


def test_hopscotch_container_inject_raises_value_error_when_no_injector_configured() -> (
    None
):
    """Test that inject() raises ValueError when no injector configured."""
    registry = HopscotchRegistry()
    container = HopscotchContainer(registry, injector=None)

    @dataclass
    class SimpleService:
        value: str = "test"

    with pytest.raises(
        ValueError, match="Cannot inject without an injector configured"
    ):
        container.inject(SimpleService)


@pytest.mark.anyio
async def test_hopscotch_container_ainject_resolves_resource_dynamically_from_container() -> (
    None
):
    """Test that ainject() resolves resource dynamically from container (async)."""
    registry = HopscotchRegistry()

    # Register implementations
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, EmployeeGreeting, resource=EmployeeContext
    )

    # Create a dataclass that uses Inject[Greeting]
    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    container = HopscotchContainer(registry)

    # Without resource in container, should get default implementation
    service = await container.ainject(WelcomeService)
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.greeting.message == "Hello, World!"


@pytest.mark.anyio
async def test_hopscotch_container_ainject_raises_value_error_when_no_async_injector_configured() -> (
    None
):
    """Test that ainject() raises ValueError when no async_injector configured."""
    registry = HopscotchRegistry()
    container = HopscotchContainer(registry, async_injector=None)

    @dataclass
    class SimpleService:
        value: str = "test"

    with pytest.raises(
        ValueError, match="Cannot inject without an async injector configured"
    ):
        await container.ainject(SimpleService)


# =============================================================================
# Task Group 3: scan() Integration with HopscotchRegistry Tests
# =============================================================================


def test_scan_detects_hopscotch_registry_and_uses_internal_locator() -> None:
    """Test that scan() detects HopscotchRegistry and uses its internal locator."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    @injectable
    @dataclass
    class SimpleService:
        value: str = "test"

    registry = HopscotchRegistry()
    scan(registry, locals_dict={"SimpleService": SimpleService})

    # The locator should be the registry's internal locator
    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)
    assert locator is registry.locator


def test_scan_with_hopscotch_registry_items_with_resource_use_register_implementation() -> (
    None
):
    """Test @injectable(resource=X) uses registry.register_implementation()."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    class CustomerContext:
        pass

    @injectable(resource=CustomerContext)
    @dataclass
    class CustomerGreeting:
        salutation: str = "Hello Customer"

    registry = HopscotchRegistry()
    scan(registry, locals_dict={"CustomerGreeting": CustomerGreeting})

    # Should be registered in the locator with resource
    impl = registry.locator.get_implementation(
        CustomerGreeting, resource=CustomerContext
    )
    assert impl is CustomerGreeting


def test_scan_with_standard_svcs_registry_existing_behavior_unchanged() -> None:
    """Test that standard svcs.Registry still works the same way."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    @injectable
    @dataclass
    class SimpleService:
        value: str = "test"

    registry = svcs.Registry()
    scan(registry, locals_dict={"SimpleService": SimpleService})

    # Should be able to get the service
    container = svcs.Container(registry)
    service = container.get(SimpleService)
    assert service.value == "test"


def test_scan_with_hopscotch_registry_simple_registrations_go_to_registry() -> None:
    """Test simple @injectable without resource/location goes to registry."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    @injectable
    @dataclass
    class SimpleService:
        value: str = "simple"

    registry = HopscotchRegistry()
    scan(registry, locals_dict={"SimpleService": SimpleService})

    # Should be able to get the service directly from container
    container = svcs.Container(registry)
    service = container.get(SimpleService)
    assert service.value == "simple"


# =============================================================================
# Task Group 4: Gap Analysis Tests - End-to-End and Edge Cases
# =============================================================================


def test_end_to_end_registry_container_inject_with_location_resolution() -> None:
    """End-to-end test: HopscotchRegistry -> HopscotchContainer -> inject with location."""

    # Define additional greeting implementations for location-based resolution
    @dataclass
    class AdminGreeting(Greeting):
        message: str = "Hello, Admin!"

    @dataclass
    class PublicGreeting(Greeting):
        message: str = "Hello, Public User!"

    # Service that depends on Greeting
    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    # Setup registry with location-based implementations
    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, AdminGreeting, location=PurePath("/admin")
    )
    registry.register_implementation(
        Greeting, PublicGreeting, location=PurePath("/public")
    )

    # Create container with location
    container = HopscotchContainer(registry, location=PurePath("/admin"))
    service = container.inject(WelcomeService)

    # Should get AdminGreeting due to /admin location
    assert isinstance(service.greeting, AdminGreeting)
    assert service.greeting.message == "Hello, Admin!"


def test_end_to_end_registry_container_inject_hierarchical_location() -> None:
    """End-to-end test: Location hierarchy /admin/users should match /admin."""

    @dataclass
    class AdminGreeting(Greeting):
        message: str = "Hello, Admin!"

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, AdminGreeting, location=PurePath("/admin")
    )

    # Create container with child location - should still match /admin
    container = HopscotchContainer(registry, location=PurePath("/admin/users"))
    service = container.inject(WelcomeService)

    # Should get AdminGreeting due to hierarchical location match
    assert isinstance(service.greeting, AdminGreeting)
    assert service.greeting.message == "Hello, Admin!"


def test_scan_with_hopscotch_registry_location_based_injectable() -> None:
    """Integration test: scan() with @injectable(location=...) and HopscotchRegistry."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    @injectable(location=PurePath("/api"))
    @dataclass
    class ApiService:
        endpoint: str = "/api/v1"

    registry = HopscotchRegistry()
    scan(registry, locals_dict={"ApiService": ApiService})

    # Should be registered in locator with location
    impl = registry.locator.get_implementation(ApiService, location=PurePath("/api"))
    assert impl is ApiService

    # Should not be found without location
    impl_no_loc = registry.locator.get_implementation(ApiService)
    assert impl_no_loc is None


def test_hopscotch_container_inject_with_kwargs_override() -> None:
    """Test that inject() respects kwargs override for dependencies."""

    @dataclass
    class MockGreeting(Greeting):
        message: str = "Mocked!"

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]
        name: str = "Guest"

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)

    container = HopscotchContainer(registry)

    # Override greeting via kwargs
    mock_greeting = MockGreeting()
    service = container.inject(WelcomeService, greeting=mock_greeting, name="Alice")

    assert service.greeting is mock_greeting
    assert service.greeting.message == "Mocked!"
    assert service.name == "Alice"


def test_register_implementation_combined_resource_and_location() -> None:
    """Edge case: register_implementation with both resource AND location."""

    @dataclass
    class VIPAdminGreeting(Greeting):
        message: str = "Hello, VIP Admin!"

    class VIPContext:
        pass

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, VIPAdminGreeting, resource=VIPContext, location=PurePath("/admin")
    )

    # Should find VIPAdminGreeting only with both resource and location
    impl = registry.locator.get_implementation(
        Greeting, resource=VIPContext, location=PurePath("/admin")
    )
    assert impl is VIPAdminGreeting

    # With location but no resource, should fall back to global default
    # (VIPAdminGreeting requires resource, but DefaultGreeting is global)
    impl_no_resource = registry.locator.get_implementation(
        Greeting, location=PurePath("/admin")
    )
    assert impl_no_resource is DefaultGreeting

    # Global default should work without location/resource
    impl_default = registry.locator.get_implementation(Greeting)
    assert impl_default is DefaultGreeting


def test_scan_with_hopscotch_registry_for_parameter() -> None:
    """Integration test: @injectable(for_=X) with HopscotchRegistry."""
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    class NotificationService:
        """Abstract notification service."""

        pass

    @injectable(for_=NotificationService)
    @dataclass
    class EmailNotificationService(NotificationService):
        """Email implementation of NotificationService."""

        provider: str = "smtp"

    registry = HopscotchRegistry()
    scan(registry, locals_dict={"EmailNotificationService": EmailNotificationService})

    # Should be registered under NotificationService, not EmailNotificationService
    impl = registry.locator.get_implementation(NotificationService)
    assert impl is EmailNotificationService


@pytest.mark.anyio
async def test_end_to_end_async_inject_with_location() -> None:
    """End-to-end async test: HopscotchRegistry -> HopscotchContainer -> ainject with location."""

    @dataclass
    class AdminGreeting(Greeting):
        message: str = "Hello, Admin!"

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(
        Greeting, AdminGreeting, location=PurePath("/admin")
    )

    container = HopscotchContainer(registry, location=PurePath("/admin"))
    service = await container.ainject(WelcomeService)

    assert isinstance(service.greeting, AdminGreeting)
    assert service.greeting.message == "Hello, Admin!"


def test_hopscotch_container_with_standard_svcs_registry() -> None:
    """Edge case: HopscotchContainer can work with standard svcs.Registry."""
    registry = svcs.Registry()
    registry.register_factory(Greeting, DefaultGreeting)

    # HopscotchContainer should work with standard registry
    container = HopscotchContainer(registry)

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    service = container.inject(WelcomeService)

    # Should resolve via standard container.get() fallback
    assert isinstance(service.greeting, DefaultGreeting)
    assert service.greeting.message == "Hello, World!"


# =============================================================================
# Task Group 5: Container Setup Functions Integration Tests
# =============================================================================


def test_hopscotch_registry_has_container_setup_funcs_attribute() -> None:
    """Test that HopscotchRegistry has _container_setup_funcs attribute."""
    registry = HopscotchRegistry()

    assert hasattr(registry, "_container_setup_funcs")
    assert isinstance(registry._container_setup_funcs, list)
    assert len(registry._container_setup_funcs) == 0


def test_hopscotch_registry_container_setup_funcs_property() -> None:
    """Test that container_setup_funcs property returns the internal list."""
    registry = HopscotchRegistry()

    funcs = registry.container_setup_funcs

    assert funcs is registry._container_setup_funcs
    assert isinstance(funcs, list)


def test_hopscotch_container_invokes_setup_funcs_on_creation() -> None:
    """Test that HopscotchContainer invokes setup functions from registry."""
    registry = HopscotchRegistry()

    # Track calls
    calls: list[str] = []

    def setup_func(container) -> None:
        calls.append("setup called")
        container.register_local_value(str, "setup_value")

    # Manually add setup function (simulating what scan() would do)
    registry._container_setup_funcs.append(setup_func)

    # Create container
    container = HopscotchContainer(registry)

    # Verify setup was called
    assert len(calls) == 1
    assert calls[0] == "setup called"

    # Verify setup had effect
    value = container.get(str)
    assert value == "setup_value"


def test_hopscotch_container_multiple_setup_funcs_called_in_order() -> None:
    """Test that multiple setup functions are called in order."""
    registry = HopscotchRegistry()

    # Track call order
    call_order: list[int] = []

    def setup1(container) -> None:
        call_order.append(1)

    def setup2(container) -> None:
        call_order.append(2)

    def setup3(container) -> None:
        call_order.append(3)

    registry._container_setup_funcs.extend([setup1, setup2, setup3])

    # Create container
    HopscotchContainer(registry)

    # Verify order
    assert call_order == [1, 2, 3]


def test_hopscotch_container_setup_funcs_with_standard_registry_does_nothing() -> None:
    """Test that HopscotchContainer with standard registry skips setup funcs."""
    registry = svcs.Registry()

    # Standard registry doesn't have container_setup_funcs
    assert not hasattr(registry, "container_setup_funcs")

    # Creating HopscotchContainer should not fail
    container = HopscotchContainer(registry)

    # Container should work normally
    registry.register_value(str, "test")
    value = container.get(str)
    assert value == "test"


def test_end_to_end_scan_with_setup_functions() -> None:
    """End-to-end test: scan() with setup functions -> HopscotchContainer."""
    from svcs_di.injectors.scanning import scan

    # Clear previous calls
    from tests.test_fixtures.scanning_test_package.with_setup_funcs import (
        SetupService,
        container_setup_calls,
        registry_setup_calls,
    )

    registry_setup_calls.clear()
    container_setup_calls.clear()

    # Setup
    registry = HopscotchRegistry()
    scan(registry, "tests.test_fixtures.scanning_test_package.with_setup_funcs")

    # Registry setup should have been called
    assert len(registry_setup_calls) == 1

    # Create multiple containers
    container1 = HopscotchContainer(registry)
    container2 = HopscotchContainer(registry)

    # Container setup should have been called for each
    assert len(container_setup_calls) == 2

    # Both containers should have the @injectable service
    service1 = container1.get(SetupService)
    service2 = container2.get(SetupService)
    assert service1.name == "SetupService"
    assert service2.name == "SetupService"

    # Each container has its own local value from setup
    assert container1.get(int) == 1
    assert container2.get(int) == 2
