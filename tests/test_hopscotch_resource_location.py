"""Tests for resource and location attributes on HopscotchContainer.

Tests the new API:
- HopscotchContainer(registry, resource=instance, location=PurePath(...))
- Resource[T] for resource injection (type parameter is for static typing only)
- Inject[Location] for location injection
- Automatic type derivation for ServiceLocator matching
"""

from dataclasses import dataclass
from pathlib import PurePath

import pytest

from svcs_di import Inject, Resource
from svcs_di.injectors import (
    HopscotchContainer,
    HopscotchRegistry,
    Location,
    injectable,
    scan,
)


# =============================================================================
# Test fixtures
# =============================================================================


class Employee:
    """Base resource type for employee requests."""

    name: str = "Employee"


class MarketingEmployee(Employee):
    """Marketing department employee."""

    name: str = "Marketing Employee"


@dataclass
class Greeting:
    """Default greeting service."""

    salutation: str = "Hello"


@dataclass
class EmployeeGreeting(Greeting):
    """Greeting for employees."""

    salutation: str = "Hey"


@dataclass
class AdminGreeting(Greeting):
    """Greeting for admin location."""

    salutation: str = "Welcome, Admin"


# =============================================================================
# Task 1: Container with resource makes it available via Resource[T]
# =============================================================================


def test_container_with_resource_makes_it_available_via_resource_marker() -> None:
    """Test that resource instance is available via Resource[T]."""

    @dataclass
    class ResourceAwareService:
        resource: Resource[Employee]

    registry = HopscotchRegistry()
    employee = Employee()
    container = HopscotchContainer(registry, resource=employee)

    service = container.inject(ResourceAwareService)

    assert service.resource is employee


def test_container_with_resource_variation_available_via_resource_marker() -> None:
    """Test that resource variations are available via Resource[T]."""

    @dataclass
    class ResourceAwareService:
        resource: Resource[MarketingEmployee]

    registry = HopscotchRegistry()
    marketing = MarketingEmployee()
    container = HopscotchContainer(registry, resource=marketing)

    service = container.inject(ResourceAwareService)

    assert service.resource is marketing
    assert isinstance(service.resource, Employee)


# =============================================================================
# Task 2: Location injection via Inject[Location]
# =============================================================================


def test_container_with_location_makes_it_available_via_inject_location() -> None:
    """Test that location is available via Inject[Location]."""

    @dataclass
    class LocationAwareService:
        location: Inject[Location]

    registry = HopscotchRegistry()
    container = HopscotchContainer(registry, location=PurePath("/admin"))

    service = container.inject(LocationAwareService)

    assert service.location == PurePath("/admin")


def test_container_with_location_hierarchical_path() -> None:
    """Test that hierarchical location paths work."""

    @dataclass
    class LocationAwareService:
        location: Inject[Location]

    registry = HopscotchRegistry()
    container = HopscotchContainer(registry, location=PurePath("/admin/users/123"))

    service = container.inject(LocationAwareService)

    assert service.location == PurePath("/admin/users/123")
    assert service.location.is_relative_to(PurePath("/admin"))


# =============================================================================
# Task 3: Resource type is automatically derived for ServiceLocator matching
# =============================================================================


def test_resource_type_automatically_derived_for_locator_matching() -> None:
    """Test that resource type is derived from instance for ServiceLocator."""

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(Greeting, EmployeeGreeting, resource=Employee)

    # Pass instance, type should be derived automatically
    container = HopscotchContainer(registry, resource=Employee())
    service = container.inject(WelcomeService)

    # Should get EmployeeGreeting because resource type was derived
    assert isinstance(service.greeting, EmployeeGreeting)
    assert service.greeting.salutation == "Hey"


def test_resource_subclass_matching_with_derived_type() -> None:
    """Test that subclass resources match parent resource registrations."""

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(Greeting, EmployeeGreeting, resource=Employee)

    # MarketingEmployee is subclass of Employee
    container = HopscotchContainer(registry, resource=MarketingEmployee())
    service = container.inject(WelcomeService)

    # Should get EmployeeGreeting via subclass matching
    assert isinstance(service.greeting, EmployeeGreeting)


# =============================================================================
# Task 4: inject(resource=X) overrides stored resource
# =============================================================================


def test_inject_resource_parameter_overrides_stored_resource() -> None:
    """Test that explicit resource parameter overrides container's stored resource."""

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    class VIP:
        pass

    @dataclass
    class VIPGreeting(Greeting):
        salutation: str = "Welcome, VIP"

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(Greeting, EmployeeGreeting, resource=Employee)
    registry.register_implementation(Greeting, VIPGreeting, resource=VIP)

    # Container has Employee
    container = HopscotchContainer(registry, resource=Employee())

    # But we override with VIP
    service = container.inject(WelcomeService, resource=VIP)

    # Should get VIPGreeting from override, not EmployeeGreeting
    assert isinstance(service.greeting, VIPGreeting)
    assert service.greeting.salutation == "Welcome, VIP"


# =============================================================================
# Task 5: Container without resource/location works (None values)
# =============================================================================


def test_container_without_resource_works() -> None:
    """Test that container without resource still works normally."""

    @dataclass
    class SimpleService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)

    container = HopscotchContainer(registry)  # No resource

    service = container.inject(SimpleService)

    assert isinstance(service.greeting, Greeting)
    assert service.greeting.salutation == "Hello"


def test_container_without_location_works() -> None:
    """Test that container without location still works normally."""

    @dataclass
    class SimpleService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)

    container = HopscotchContainer(registry)  # No location

    service = container.inject(SimpleService)

    assert isinstance(service.greeting, Greeting)


# =============================================================================
# Combined resource and location
# =============================================================================


def test_container_with_both_resource_and_location() -> None:
    """Test container with both resource and location."""

    @dataclass
    class FullContextService:
        resource: Resource[Employee]
        location: Inject[Location]

    registry = HopscotchRegistry()
    employee = Employee()
    container = HopscotchContainer(
        registry, resource=employee, location=PurePath("/admin")
    )

    service = container.inject(FullContextService)

    assert service.resource is employee
    assert service.location == PurePath("/admin")


def test_location_based_resolution_with_container_location() -> None:
    """Test that container location is used for ServiceLocator resolution."""

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)  # Default
    registry.register_implementation(
        Greeting, AdminGreeting, location=PurePath("/admin")
    )

    container = HopscotchContainer(registry, location=PurePath("/admin"))
    service = container.inject(WelcomeService)

    assert isinstance(service.greeting, AdminGreeting)
    assert service.greeting.salutation == "Welcome, Admin"


# =============================================================================
# Async tests
# =============================================================================


@pytest.mark.anyio
async def test_async_inject_with_container_resource() -> None:
    """Test that ainject() works with container resource."""

    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, Greeting)
    registry.register_implementation(Greeting, EmployeeGreeting, resource=Employee)

    container = HopscotchContainer(registry, resource=Employee())
    service = await container.ainject(WelcomeService)

    assert isinstance(service.greeting, EmployeeGreeting)


@pytest.mark.anyio
async def test_async_inject_with_container_location() -> None:
    """Test that ainject() works with container location."""

    @dataclass
    class LocationAwareService:
        location: Inject[Location]

    registry = HopscotchRegistry()
    container = HopscotchContainer(registry, location=PurePath("/async"))

    service = await container.ainject(LocationAwareService)

    assert service.location == PurePath("/async")


@pytest.mark.anyio
async def test_async_inject_with_resource_marker() -> None:
    """Test that ainject() works with Resource[T] marker."""

    @dataclass
    class ResourceAwareService:
        resource: Resource[Employee]

    registry = HopscotchRegistry()
    employee = Employee()
    container = HopscotchContainer(registry, resource=employee)

    service = await container.ainject(ResourceAwareService)

    assert service.resource is employee


# =============================================================================
# Decorator and scanning tests
# =============================================================================


def test_injectable_decorator_with_resource_and_container() -> None:
    """Test @injectable(resource=X) works with HopscotchContainer resource."""

    class Customer:
        pass

    class Protocol:
        pass

    @injectable(for_=Protocol)
    @dataclass
    class DefaultImpl:
        name: str = "default"

    @injectable(for_=Protocol, resource=Customer)
    @dataclass
    class CustomerImpl:
        name: str = "customer"

    @dataclass
    class Service:
        impl: Inject[Protocol]

    registry = HopscotchRegistry()
    scan(registry, locals_dict=locals())

    # Without resource - gets default
    container = HopscotchContainer(registry)
    service = container.inject(Service)
    assert service.impl.name == "default"

    # With resource - gets customer impl
    container = HopscotchContainer(registry, resource=Customer())
    service = container.inject(Service)
    assert service.impl.name == "customer"


def test_injectable_decorator_with_location_and_container() -> None:
    """Test @injectable(location=X) works with HopscotchContainer location."""

    class Protocol:
        pass

    @injectable(for_=Protocol)
    @dataclass
    class DefaultImpl:
        name: str = "default"

    @injectable(for_=Protocol, location=PurePath("/admin"))
    @dataclass
    class AdminImpl:
        name: str = "admin"

    @dataclass
    class Service:
        impl: Inject[Protocol]

    registry = HopscotchRegistry()
    scan(registry, locals_dict=locals())

    # Without location - gets default
    container = HopscotchContainer(registry)
    service = container.inject(Service)
    assert service.impl.name == "default"

    # With /admin location - gets admin impl
    container = HopscotchContainer(registry, location=PurePath("/admin"))
    service = container.inject(Service)
    assert service.impl.name == "admin"

    # With /admin/users location - hierarchical match to /admin
    container = HopscotchContainer(registry, location=PurePath("/admin/users"))
    service = container.inject(Service)
    assert service.impl.name == "admin"


def test_injectable_decorator_with_both_resource_and_location() -> None:
    """Test @injectable with both resource and location on container."""

    class VIP:
        pass

    class Protocol:
        pass

    @injectable(for_=Protocol)
    @dataclass
    class DefaultImpl:
        name: str = "default"

    @injectable(for_=Protocol, resource=VIP, location=PurePath("/premium"))
    @dataclass
    class VIPPremiumImpl:
        name: str = "vip-premium"

    @dataclass
    class Service:
        impl: Inject[Protocol]

    registry = HopscotchRegistry()
    scan(registry, locals_dict=locals())

    # Without resource or location - gets default
    container = HopscotchContainer(registry)
    service = container.inject(Service)
    assert service.impl.name == "default"

    # With VIP but wrong location - gets default
    container = HopscotchContainer(
        registry, resource=VIP(), location=PurePath("/other")
    )
    service = container.inject(Service)
    assert service.impl.name == "default"

    # With VIP and /premium location - gets VIP premium impl
    container = HopscotchContainer(
        registry, resource=VIP(), location=PurePath("/premium")
    )
    service = container.inject(Service)
    assert service.impl.name == "vip-premium"


def test_scanning_with_resource_marker() -> None:
    """Test scanned services can use Resource[T]."""

    class Customer:
        id: int = 123

    class Protocol:
        pass

    @injectable(for_=Protocol, resource=Customer)
    @dataclass
    class CustomerImpl:
        resource: Resource[Customer]  # Access the resource via marker

        @property
        def name(self) -> str:
            return f"customer-{type(self.resource).__name__}"

    @dataclass
    class Service:
        impl: Inject[Protocol]

    registry = HopscotchRegistry()
    scan(registry, locals_dict=locals())

    container = HopscotchContainer(registry, resource=Customer())
    service = container.inject(Service)
    assert service.impl.name == "customer-Customer"
    assert isinstance(service.impl.resource, Customer)
