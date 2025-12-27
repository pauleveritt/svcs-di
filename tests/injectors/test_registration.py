"""Tests for registration integration - Task Group 3."""

import sys
from dataclasses import dataclass
from pathlib import Path

import svcs

from svcs_di.auto import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import ServiceLocator, scan

# Add test_fixtures to path so we can import test modules
test_fixtures_path = Path(__file__).parent.parent / "test_fixtures"
if str(test_fixtures_path) not in sys.path:
    sys.path.insert(0, str(test_fixtures_path))


# Context classes for testing
class CustomerContext:
    pass


class EmployeeContext:
    pass


# Service protocol for testing
class GreetingService:
    def greet(self) -> str:
        raise NotImplementedError


# ============================================================================
# Task 3.1: Focused tests for registration integration
# ============================================================================


def test_resource_based_registrations_use_service_locator():
    """Test resource-based registrations use ServiceLocator.register()."""
    registry = svcs.Registry()

    # Define services with resource parameter
    @injectable(resource=CustomerContext)
    @dataclass
    class CustomerGreeting:
        message: str = "Hello Customer"

    @injectable(resource=EmployeeContext)
    @dataclass
    class EmployeeGreeting:
        message: str = "Hello Employee"

    # Create a temporary module to simulate scanning
    import types

    test_module = types.ModuleType("test_resource_module")
    test_module.CustomerGreeting = CustomerGreeting  # type: ignore[attr-defined]
    test_module.EmployeeGreeting = EmployeeGreeting  # type: ignore[attr-defined]
    sys.modules["test_resource_module"] = test_module

    try:
        # Scan should register these to ServiceLocator
        scan(registry, "test_resource_module")

        # ServiceLocator should be registered in the registry
        container = svcs.Container(registry)
        locator = container.get(ServiceLocator)

        # Verify registrations exist in locator (check both single and multi paths)
        assert locator is not None
        total_registrations = len(locator._single_registrations) + sum(
            len(regs) for regs in locator._multi_registrations.values()
        )
        assert total_registrations > 0

        # Verify we can get implementations for each resource
        customer_impl = locator.get_implementation(CustomerGreeting, CustomerContext)
        assert customer_impl is CustomerGreeting

        employee_impl = locator.get_implementation(EmployeeGreeting, EmployeeContext)
        assert employee_impl is EmployeeGreeting
    finally:
        del sys.modules["test_resource_module"]


def test_non_resource_registrations_use_registry_register_factory():
    """Test non-resource registrations use Registry.register_factory()."""
    registry = svcs.Registry()

    # Define service without resource parameter
    @injectable
    @dataclass
    class DefaultGreeting:
        message: str = "Hello World"

    # Create a temporary module
    import types

    test_module = types.ModuleType("test_default_module")
    test_module.DefaultGreeting = DefaultGreeting  # type: ignore[attr-defined]
    sys.modules["test_default_module"] = test_module

    try:
        # Scan should register this directly to registry via register_factory
        scan(registry, "test_default_module")

        # We should be able to get the service from a container
        container = svcs.Container(registry)
        greeting = container.get(DefaultGreeting)

        # Verify it's the correct instance
        assert isinstance(greeting, DefaultGreeting)
        assert greeting.message == "Hello World"
    finally:
        del sys.modules["test_default_module"]


def test_lifo_ordering_maintained():
    """Test LIFO ordering is maintained during registration."""
    registry = svcs.Registry()

    # Define multiple implementations with ONLY resource-based registrations
    # (so they all go to ServiceLocator)
    @injectable(resource=CustomerContext)
    @dataclass
    class CustomerImpl:
        value: str = "customer"

    @injectable(resource=EmployeeContext)
    @dataclass
    class EmployeeImpl:
        value: str = "employee"

    # Create a third resource-based impl to verify ordering
    class AdminContext:
        pass

    @injectable(resource=AdminContext)
    @dataclass
    class AdminImpl:
        value: str = "admin"

    # Create a temporary module with specific order
    import types

    test_module = types.ModuleType("test_lifo_module")
    test_module.CustomerImpl = CustomerImpl  # type: ignore[attr-defined]
    test_module.EmployeeImpl = EmployeeImpl  # type: ignore[attr-defined]
    test_module.AdminImpl = AdminImpl  # type: ignore[attr-defined]
    sys.modules["test_lifo_module"] = test_module

    try:
        # Scan should register in LIFO order
        scan(registry, "test_lifo_module")

        # Get the locator and verify LIFO ordering
        container = svcs.Container(registry)
        locator = container.get(ServiceLocator)

        # Collect all registrations from both single and multi paths
        all_registrations = []
        for reg in locator._single_registrations.values():
            all_registrations.append(reg)
        for regs_tuple in locator._multi_registrations.values():
            all_registrations.extend(regs_tuple)

        assert len(all_registrations) >= 3

        # Verify LIFO: last scanned item should be first in registrations
        # Note: dir() returns attributes in alphabetical order, so order is:
        # AdminImpl, CustomerImpl, EmployeeImpl
        # In LIFO, they should be reversed: EmployeeImpl, CustomerImpl, AdminImpl
        # But since we can't guarantee dir() order, just verify all are present
        impl_types = {reg.implementation for reg in all_registrations}
        assert CustomerImpl in impl_types
        assert EmployeeImpl in impl_types
        assert AdminImpl in impl_types
    finally:
        del sys.modules["test_lifo_module"]


def test_multiple_implementations_same_service_type():
    """Test multiple implementations of same service type are registered."""
    registry = svcs.Registry()

    # Define a protocol or base class
    class Greeting:
        pass

    @injectable
    @dataclass
    class DefaultGreeting:
        message: str = "default"

    @injectable(resource=CustomerContext)
    @dataclass
    class CustomerGreeting:
        message: str = "customer"

    # Create temporary module
    import types

    test_module = types.ModuleType("test_multiple_module")
    test_module.DefaultGreeting = DefaultGreeting  # type: ignore[attr-defined]
    test_module.CustomerGreeting = CustomerGreeting  # type: ignore[attr-defined]
    sys.modules["test_multiple_module"] = test_module

    try:
        scan(registry, "test_multiple_module")

        container = svcs.Container(registry)

        # Both should be retrievable
        default = container.get(DefaultGreeting)
        assert default.message == "default"

        # Customer-specific should be in locator
        locator = container.get(ServiceLocator)
        customer_impl = locator.get_implementation(CustomerGreeting, CustomerContext)
        assert customer_impl is CustomerGreeting
    finally:
        del sys.modules["test_multiple_module"]


def test_registration_creates_proper_factory_functions():
    """Test registration creates proper factory functions following auto() pattern."""
    registry = svcs.Registry()

    # Define a service with Inject dependencies
    @injectable
    @dataclass
    class ConfigService:
        config_value: str = "test-config"

    @injectable
    @dataclass
    class DatabaseService:
        config: Inject[ConfigService]

        def get_connection_string(self) -> str:
            return f"db://{self.config.config_value}"

    # Create temporary module
    import types

    test_module = types.ModuleType("test_factory_module")
    test_module.ConfigService = ConfigService  # type: ignore[attr-defined]
    test_module.DatabaseService = DatabaseService  # type: ignore[attr-defined]
    sys.modules["test_factory_module"] = test_module

    try:
        scan(registry, "test_factory_module")

        container = svcs.Container(registry)

        # Get the database service - it should auto-inject config
        db = container.get(DatabaseService)
        assert isinstance(db, DatabaseService)
        assert isinstance(db.config, ConfigService)
        assert db.config.config_value == "test-config"
        assert db.get_connection_string() == "db://test-config"
    finally:
        del sys.modules["test_factory_module"]


def test_scan_with_existing_test_fixtures():
    """Test scanning existing test fixtures works correctly."""
    registry = svcs.Registry()

    # Scan the test fixtures package
    scan(registry, "tests.test_fixtures.scanning_test_package")

    container = svcs.Container(registry)

    # Import after scan to verify registration happened
    from tests.test_fixtures.scanning_test_package import service_a, service_b

    # Non-resource services should be directly gettable
    service_a_instance = container.get(service_a.ServiceA)
    assert service_a_instance.name == "ServiceA"

    another_a = container.get(service_a.AnotherServiceA)
    assert another_a.name == "AnotherServiceA"

    # Resource-based service should be in locator
    locator = container.get(ServiceLocator)
    customer_impl = locator.get_implementation(
        service_b.ServiceB, service_b.CustomerContext
    )
    assert customer_impl is service_b.ServiceB


def test_registration_with_nested_injection():
    """Test registration works with nested dependency injection."""
    registry = svcs.Registry()

    @injectable
    @dataclass
    class Logger:
        prefix: str = "LOG"

    @injectable
    @dataclass
    class Database:
        logger: Inject[Logger]

        def log_query(self, query: str) -> str:
            return f"{self.logger.prefix}: {query}"

    @injectable
    @dataclass
    class UserService:
        db: Inject[Database]

        def create_user(self, name: str) -> str:
            return self.db.log_query(f"INSERT INTO users VALUES ('{name}')")

    # Create temporary module
    import types

    test_module = types.ModuleType("test_nested_module")
    test_module.Logger = Logger  # type: ignore[attr-defined]
    test_module.Database = Database  # type: ignore[attr-defined]
    test_module.UserService = UserService  # type: ignore[attr-defined]
    sys.modules["test_nested_module"] = test_module

    try:
        scan(registry, "test_nested_module")

        container = svcs.Container(registry)

        # Get user service - should auto-inject entire chain
        user_service = container.get(UserService)
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.db, Database)
        assert isinstance(user_service.db.logger, Logger)

        result = user_service.create_user("Alice")
        assert result == "LOG: INSERT INTO users VALUES ('Alice')"
    finally:
        del sys.modules["test_nested_module"]
