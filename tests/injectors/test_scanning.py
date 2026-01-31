"""Tests for scan() function - Task Group 2: Module Discovery and Import."""

import sys
from dataclasses import dataclass
from pathlib import Path

import svcs

from svcs_di import DefaultInjector, Inject, Injector
from svcs_di.injectors.locator import HopscotchInjector, ServiceLocator, scan

# Add test_fixtures to path so we can import test modules
test_fixtures_path = Path(__file__).parent.parent / "test_fixtures"
if str(test_fixtures_path) not in sys.path:
    sys.path.insert(0, str(test_fixtures_path))


# ============================================================================
# Task 2.1: Focused tests for scan() function
# ============================================================================


def test_scan_single_module_with_decorated_classes():
    """Test scanning a single module discovers decorated classes."""
    registry = svcs.Registry()

    # Import the module as a ModuleType
    from tests.test_fixtures.scanning_test_package import service_a

    # Scan the module
    result = scan(registry, service_a)

    # Verify scan returns registry for chaining
    assert result is registry

    # At this stage (Task Group 2), we're only testing that:
    # 1. scan() accepts the module and returns registry
    # 2. No exceptions are raised during scanning
    # 3. Decorated classes are imported (decorator execution happens)

    # Verify decorated classes exist and have metadata
    assert hasattr(service_a.ServiceA, "__injectable_metadata__")
    assert hasattr(service_a.AnotherServiceA, "__injectable_metadata__")


def test_scan_package_multiple_modules():
    """Test scanning a package discovers decorated classes in multiple modules."""
    registry = svcs.Registry()

    # Scan the entire package by name
    result = scan(registry, "tests.test_fixtures.scanning_test_package")

    # Verify registry is returned
    assert result is registry

    # Import modules to verify they were scanned
    from tests.test_fixtures.scanning_test_package import service_a, service_b

    # Verify decorated classes have metadata
    assert hasattr(service_a.ServiceA, "__injectable_metadata__")
    assert hasattr(service_b.ServiceB, "__injectable_metadata__")


def test_scan_returns_registry_for_chaining():
    """Test that scan() returns registry to enable method chaining."""
    registry = svcs.Registry()

    # Test chaining pattern
    result = scan(registry, "tests.test_fixtures.scanning_test_package.service_a")

    assert result is registry
    # Could chain more operations like: scan(...).register_value(...)


def test_scan_with_string_package_name():
    """Test scan() accepts string package name."""
    registry = svcs.Registry()

    # Should accept string package name
    result = scan(registry, "tests.test_fixtures.scanning_test_package.service_a")

    assert result is registry


def test_scan_with_module_type_object():
    """Test scan() accepts ModuleType objects."""
    registry = svcs.Registry()

    import tests.test_fixtures.scanning_test_package.service_a as service_module

    # Should accept ModuleType
    result = scan(registry, service_module)

    assert result is registry


def test_scan_handles_empty_package_gracefully():
    """Test scan() handles packages with no decorated classes."""
    registry = svcs.Registry()

    # Scan module with no decorated classes
    result = scan(registry, "tests.test_fixtures.scanning_test_package.no_decorators")

    # Should not raise an error
    assert result is registry


def test_scan_nested_packages():
    """Test scan() discovers modules in nested packages."""
    registry = svcs.Registry()

    # Scan package that contains nested packages
    result = scan(registry, "tests.test_fixtures.scanning_test_package")

    assert result is registry

    # Verify nested module was scanned
    from tests.test_fixtures.scanning_test_package.nested import nested_service

    assert hasattr(nested_service.NestedService, "__injectable_metadata__")


# ============================================================================
# Task 4.1: Focused tests for HopscotchInjector context integration
# ============================================================================


# Test fixtures for context integration
class CustomerContext:
    """Context for customer requests."""

    pass


class EmployeeContext:
    """Context for employee requests."""

    pass


class RequestContext:
    """Base context for requests."""

    pass


def test_scan_phase_is_context_agnostic():
    """
    Test that scan() phase only records resource metadata without resolving context.

    Task 4.2: Verify scan phase is context-agnostic
    - Scan phase only records resource metadata
    - No context detection or resolution during scanning
    - No invocation of HopscotchInjector during scan
    """
    registry = svcs.Registry()

    # Create test module with decorated classes with resources
    from tests.test_fixtures.scanning_test_package import service_b

    # Scan should NOT:
    # - Resolve any context types
    # - Invoke HopscotchInjector
    # - Construct any service instances
    # - Access any container

    # Scan only records metadata
    result = scan(registry, service_b)

    # Verify scan completed without needing any context
    assert result is registry

    # Verify metadata was stored (not resolved)
    assert hasattr(service_b.ServiceB, "__injectable_metadata__")
    metadata = service_b.ServiceB.__injectable_metadata__
    assert "resource" in metadata
    # The resource type is stored as-is, not resolved
    assert metadata["resource"] == service_b.CustomerContext


def test_hopscotch_injector_uses_resource_type_directly():
    """
    Test that HopscotchInjector uses resource type directly for ServiceLocator matching.

    Task 4.3: Verify resource type usage
    - HopscotchInjector.resource stores the resource type directly
    - The type is typically derived from HopscotchContainer's stored resource instance
    """
    from tests.test_fixtures.scanning_test_package.service_b import (
        CustomerContext,
    )

    # Setup: Scan phase registers metadata only
    registry = svcs.Registry()
    scan(registry, "tests.test_fixtures.scanning_test_package.service_b")

    # Create container and injector with resource type directly
    container = svcs.Container(registry)
    injector = HopscotchInjector(container=container, resource=CustomerContext)

    # Verify resource attribute stores the resource type directly
    assert injector.resource == CustomerContext


def test_resource_matching_three_tier_precedence():
    """
    Test resource matching follows three-tier precedence: exact > subclass > default.

    Task 4.3 & 4.4: Test three-tier precedence from FactoryRegistration.matches()
    """
    from tests.test_fixtures.scanning_test_package.service_b import (
        CustomerContext,
    )

    # Define service protocol
    class Greeting:
        name: str

    @dataclass
    class DefaultGreeting:
        name: str = "Default"

    @dataclass
    class CustomerGreeting:
        name: str = "Customer"

    @dataclass
    class EmployeeGreeting:
        name: str = "Employee"

    # Setup locator with three-tier precedence
    locator = ServiceLocator()
    locator = locator.register(
        Greeting, DefaultGreeting, resource=None
    )  # Default (score=0)
    locator = locator.register(
        Greeting, CustomerGreeting, resource=CustomerContext
    )  # Exact (score=2)
    locator = locator.register(
        Greeting, EmployeeGreeting, resource=EmployeeContext
    )  # Exact (score=2)

    registry = svcs.Registry()
    registry.register_value(ServiceLocator, locator)

    # Test exact match (highest priority)
    impl = locator.get_implementation(Greeting, resource=CustomerContext)
    assert impl == CustomerGreeting

    # Test default fallback (lowest priority)
    impl = locator.get_implementation(Greeting, resource=None)
    assert impl == DefaultGreeting


def test_decorated_services_work_with_hopscotch_injector():
    """
    Test that decorated services work with existing HopscotchInjector patterns.

    Task 4.4: Test decorated services with existing injector patterns
    - Decorated classes work with HopscotchInjector
    """
    from tests.test_fixtures.scanning_test_package.service_a import ServiceA

    # Scan to register decorated services
    registry = svcs.Registry()
    scan(registry, "tests.test_fixtures.scanning_test_package.service_a")

    # Create container
    container = svcs.Container(registry)

    # Get service via container (uses factory registered by scan)
    service = container.get(ServiceA)

    # Verify service was constructed correctly
    assert isinstance(service, ServiceA)
    assert service.name == "ServiceA"


def test_decorated_services_with_context_resolution():
    """
    Test HopscotchInjector resolves context for decorated services at request time.

    Task 4.3 & 4.4: End-to-end test of scan + HopscotchInjector + context resolution
    """
    from tests.test_fixtures.scanning_test_package.service_b import (
        CustomerContext,
        ServiceB,
    )

    # Scan to register decorated services with resource
    registry = svcs.Registry()
    scan(registry, "tests.test_fixtures.scanning_test_package.service_b")

    # Register context in container
    registry.register_value(RequestContext, CustomerContext())

    # Create container
    container = svcs.Container(registry)

    # Get locator to verify registration
    locator = container.get(ServiceLocator)

    # Verify ServiceB was registered with CustomerContext resource
    impl = locator.get_implementation(ServiceB, resource=CustomerContext)
    assert impl == ServiceB


def test_decorated_classes_with_injectable_fields():
    """
    Test decorated classes with Inject[T] fields resolve correctly via HopscotchInjector.

    Task 4.4: Inject[T] fields in decorated classes resolve via existing logic
    """
    from tests.test_fixtures.scanning_test_package.service_a import ServiceA

    # Define a service that depends on ServiceA
    @dataclass
    class CompositeService:
        dependency: Inject[ServiceA]
        name: str = "Composite"

    # Scan to register ServiceA
    registry = svcs.Registry()
    scan(registry, "tests.test_fixtures.scanning_test_package.service_a")

    # Register CompositeService manually
    def composite_factory(container: svcs.Container) -> CompositeService:
        injector = DefaultInjector(container=container)
        return injector(CompositeService)

    registry.register_factory(CompositeService, composite_factory)

    # Create container
    container = svcs.Container(registry)

    # Get CompositeService - should resolve ServiceA via Inject[T]
    service = container.get(CompositeService)

    # Verify dependency was injected
    assert isinstance(service, CompositeService)
    assert isinstance(service.dependency, ServiceA)
    assert service.dependency.name == "ServiceA"


def test_scan_with_hopscotch_injector_type():
    """
    Test scan() can use HopscotchInjector as the injector type.

    Task 4.4: Decorated classes work with HopscotchInjector
    """
    from tests.test_fixtures.scanning_test_package.service_a import ServiceA

    # Scan with HopscotchInjector
    registry = svcs.Registry()
    registry.register_factory(Injector, HopscotchInjector)
    scan(
        registry,
        "tests.test_fixtures.scanning_test_package.service_a",
    )

    # Create container
    container = svcs.Container(registry)

    # Register HopscotchInjector
    registry.register_value(HopscotchInjector, HopscotchInjector(container=container))

    # Get service
    service = container.get(ServiceA)

    # Verify service was constructed
    assert isinstance(service, ServiceA)


def test_context_resolution_timing():
    """
    Test that context is used at request time via HopscotchInjector, NOT during scan.

    Task 4.2 & 4.3: Verify timing of context usage
    """
    from tests.test_fixtures.scanning_test_package.service_b import (
        CustomerContext,
        ServiceB,
    )

    # Phase 1: Scan (NO context resolution)
    registry = svcs.Registry()
    scan(registry, "tests.test_fixtures.scanning_test_package.service_b")

    # At this point, NO context has been used
    # Only metadata has been stored

    # Phase 2: Request time (context is used NOW)
    container = svcs.Container(registry)

    # Create HopscotchInjector with resource type directly
    injector = HopscotchInjector(container=container, resource=CustomerContext)

    # resource attribute stores the resource type directly
    assert injector.resource == CustomerContext

    # Verify locator can find ServiceB with CustomerContext
    locator = container.get(ServiceLocator)
    impl = locator.get_implementation(ServiceB, resource=CustomerContext)
    assert impl == ServiceB


# ============================================================================
# New Feature Tests: locals_dict scanning and auto-detection
# ============================================================================


def test_scan_with_locals_dict():
    """Test scan() with locals_dict parameter for local scope scanning."""
    from svcs_di.injectors.decorators import injectable

    # Define decorated classes in local scope
    @injectable
    @dataclass
    class LocalDatabase:
        host: str = "localhost"

    @injectable
    @dataclass
    class LocalCache:
        ttl: int = 300

    registry = svcs.Registry()

    # Scan local scope
    scan(registry, locals_dict=locals())

    # Verify services were registered
    container = svcs.Container(registry)
    db = container.get(LocalDatabase)
    cache = container.get(LocalCache)

    assert db.host == "localhost"
    assert cache.ttl == 300


def test_scan_with_locals_dict_and_resources():
    """Test scan() with locals_dict handles resource-based decorators."""
    from svcs_di.injectors.decorators import injectable

    class TestContext:
        pass

    @injectable(resource=TestContext)
    @dataclass
    class ResourceService:
        value: str = "test"

    @injectable
    @dataclass
    class DefaultService:
        value: str = "default"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Verify default service works
    container = svcs.Container(registry)
    default = container.get(DefaultService)
    assert default.value == "default"

    # Verify resource service was registered to ServiceLocator
    locator = container.get(ServiceLocator)
    impl = locator.get_implementation(ResourceService, TestContext)
    assert impl == ResourceService


def test_scan_with_locals_dict_skips_module_scanning():
    """Test that providing locals_dict skips module scanning."""
    from svcs_di.injectors.decorators import injectable

    @injectable
    @dataclass
    class OnlyLocal:
        value: str = "local"

    registry = svcs.Registry()

    # Scan only locals - should not scan any modules
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    service = container.get(OnlyLocal)
    assert service.value == "local"


def test_scan_namespace_package():
    """Test scan() works with namespace packages (PEP 420, no __init__.py)."""
    registry = svcs.Registry()

    # Scan a namespace package (no __init__.py)
    result = scan(registry, "tests.test_fixtures.namespace_package")

    assert result is registry

    # Verify decorated class was discovered
    from tests.test_fixtures.namespace_package.services import NamespaceService

    assert hasattr(NamespaceService, "__injectable_metadata__")

    # Verify service was registered and can be resolved
    container = svcs.Container(registry)
    service = container.get(NamespaceService)
    assert isinstance(service, NamespaceService)
    assert service.name == "NamespaceService"
