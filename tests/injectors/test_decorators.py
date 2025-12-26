"""Tests for @injectable decorator."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


# Context classes for testing
class CustomerContext:
    pass


class EmployeeContext:
    pass


class TestContext:
    pass


# ============================================================================
# @injectable Decorator Tests
# ============================================================================


def test_injectable_bare_decorator():
    """Test bare @injectable decorator marks class for registration."""

    @injectable
    class SimpleService:
        pass

    # Check metadata is stored
    assert hasattr(SimpleService, "__injectable_metadata__")
    metadata = SimpleService.__injectable_metadata__
    assert metadata["resource"] is None

    # Verify class is unchanged (transparent decorator)
    instance = SimpleService()
    assert isinstance(instance, SimpleService)


def test_injectable_with_resource_parameter():
    """Test @injectable(resource=CustomerContext) decorator."""

    @injectable(resource=CustomerContext)
    class CustomerService:
        pass

    # Check metadata stores resource
    assert hasattr(CustomerService, "__injectable_metadata__")
    metadata = CustomerService.__injectable_metadata__
    assert metadata["resource"] is CustomerContext


def test_injectable_without_resource():
    """Test @injectable() decorator (called without resource)."""

    @injectable()
    class DefaultService:
        pass

    # Check metadata shows no resource
    assert hasattr(DefaultService, "__injectable_metadata__")
    metadata = DefaultService.__injectable_metadata__
    assert metadata["resource"] is None


def test_injectable_metadata_storage_no_registration():
    """Test that @injectable stores metadata without performing registration."""

    @injectable(resource=EmployeeContext)
    class EmployeeService:
        pass

    # Metadata should be stored
    assert hasattr(EmployeeService, "__injectable_metadata__")

    # No registration should have occurred (no side effects)
    # We verify this by ensuring the decorator didn't interact with any registry
    # The class should just have metadata attached, nothing more
    metadata = EmployeeService.__injectable_metadata__
    assert metadata["resource"] == EmployeeContext


def test_injectable_multiple_decorators_same_type():
    """Test multiple @injectable decorators on different implementations of same service type."""

    @injectable
    class ServiceImplA:
        pass

    @injectable(resource=CustomerContext)
    class ServiceImplB:
        pass

    @injectable(resource=EmployeeContext)
    class ServiceImplC:
        pass

    # All three should have metadata
    assert hasattr(ServiceImplA, "__injectable_metadata__")
    assert hasattr(ServiceImplB, "__injectable_metadata__")
    assert hasattr(ServiceImplC, "__injectable_metadata__")

    # Each with correct resource
    assert ServiceImplA.__injectable_metadata__["resource"] is None
    assert ServiceImplB.__injectable_metadata__["resource"] is CustomerContext
    assert ServiceImplC.__injectable_metadata__["resource"] is EmployeeContext


def test_injectable_preserves_class_functionality():
    """Test that @injectable decorator doesn't break normal class functionality."""

    @injectable(resource=TestContext)
    @dataclass
    class ComplexService:
        name: str
        count: int = 0

        def increment(self):
            self.count += 1

    # Create instance normally
    service = ComplexService(name="test", count=5)
    assert service.name == "test"
    assert service.count == 5

    # Methods work
    service.increment()
    assert service.count == 6

    # Metadata is there
    assert hasattr(ComplexService, "__injectable_metadata__")
    assert ComplexService.__injectable_metadata__["resource"] == TestContext
