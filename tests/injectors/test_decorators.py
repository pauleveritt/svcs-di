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
    """Test bare @injectable decorator marks dataclass for registration."""

    @injectable
    @dataclass
    class SimpleService:
        pass

    # Check metadata is stored
    assert hasattr(SimpleService, "__injectable_metadata__")
    metadata = SimpleService.__injectable_metadata__
    assert metadata["for_"] is None
    assert metadata["resource"] is None

    # Verify class is unchanged (transparent decorator)
    instance = SimpleService()
    assert isinstance(instance, SimpleService)


def test_injectable_with_resource_parameter():
    """Test @injectable(resource=CustomerContext) decorator."""

    @injectable(resource=CustomerContext)
    @dataclass
    class CustomerService:
        pass

    # Check metadata stores resource
    assert hasattr(CustomerService, "__injectable_metadata__")
    metadata = CustomerService.__injectable_metadata__
    assert metadata["for_"] is None
    assert metadata["resource"] is CustomerContext


def test_injectable_without_resource():
    """Test @injectable() decorator (called without resource)."""

    @injectable()
    @dataclass
    class DefaultService:
        pass

    # Check metadata shows no resource
    assert hasattr(DefaultService, "__injectable_metadata__")
    metadata = DefaultService.__injectable_metadata__
    assert metadata["for_"] is None
    assert metadata["resource"] is None


def test_injectable_metadata_storage_no_registration():
    """Test that @injectable stores metadata without performing registration."""

    @injectable(resource=EmployeeContext)
    @dataclass
    class EmployeeService:
        pass

    # Metadata should be stored
    assert hasattr(EmployeeService, "__injectable_metadata__")

    # No registration should have occurred (no side effects)
    # We verify this by ensuring the decorator didn't interact with any registry
    # The class should just have metadata attached, nothing more
    metadata = EmployeeService.__injectable_metadata__
    assert metadata["for_"] is None
    assert metadata["resource"] == EmployeeContext


def test_injectable_multiple_decorators_same_type():
    """Test multiple @injectable decorators on different implementations of same service type."""

    @injectable
    @dataclass
    class ServiceImplA:
        pass

    @injectable(resource=CustomerContext)
    @dataclass
    class ServiceImplB:
        pass

    @injectable(resource=EmployeeContext)
    @dataclass
    class ServiceImplC:
        pass

    # All three should have metadata
    assert hasattr(ServiceImplA, "__injectable_metadata__")
    assert hasattr(ServiceImplB, "__injectable_metadata__")
    assert hasattr(ServiceImplC, "__injectable_metadata__")

    # Each with correct resource and for_
    assert ServiceImplA.__injectable_metadata__["for_"] is None
    assert ServiceImplA.__injectable_metadata__["resource"] is None
    assert ServiceImplB.__injectable_metadata__["for_"] is None
    assert ServiceImplB.__injectable_metadata__["resource"] is CustomerContext
    assert ServiceImplC.__injectable_metadata__["for_"] is None
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
    assert ComplexService.__injectable_metadata__["for_"] is None
    assert ComplexService.__injectable_metadata__["resource"] == TestContext


# ============================================================================
# @injectable Decorator Tests - for_ Parameter
# ============================================================================


def test_injectable_with_for_parameter():
    """Test @injectable(for_=BaseType) decorator."""

    class BaseService:
        pass

    @injectable(for_=BaseService)
    class ConcreteService:
        pass

    # Check metadata stores for_
    assert hasattr(ConcreteService, "__injectable_metadata__")
    metadata = ConcreteService.__injectable_metadata__
    assert metadata["for_"] is BaseService
    assert metadata["resource"] is None


def test_injectable_with_for_and_resource():
    """Test @injectable(for_=BaseType, resource=Context) decorator."""

    class BaseService:
        pass

    @injectable(for_=BaseService, resource=CustomerContext)
    class CustomerServiceImpl:
        pass

    # Check metadata stores both
    assert hasattr(CustomerServiceImpl, "__injectable_metadata__")
    metadata = CustomerServiceImpl.__injectable_metadata__
    assert metadata["for_"] is BaseService
    assert metadata["resource"] is CustomerContext


def test_injectable_for_defaults_to_none():
    """Test that for_ defaults to None when not specified."""

    @injectable
    class SomeService:
        pass

    metadata = SomeService.__injectable_metadata__  # type: ignore[attr-defined]
    assert metadata["for_"] is None


def test_injectable_multiple_implementations_same_for():
    """Test multiple @injectable decorators implementing same service type."""

    class Greeting:
        pass

    @injectable(for_=Greeting)
    class DefaultGreeting:
        pass

    @injectable(for_=Greeting, resource=CustomerContext)
    class CustomerGreeting:
        pass

    @injectable(for_=Greeting, resource=EmployeeContext)
    class EmployeeGreeting:
        pass

    # All three should have metadata pointing to Greeting
    assert DefaultGreeting.__injectable_metadata__["for_"] is Greeting  # type: ignore[attr-defined]
    assert DefaultGreeting.__injectable_metadata__["resource"] is None  # type: ignore[attr-defined]

    assert CustomerGreeting.__injectable_metadata__["for_"] is Greeting  # type: ignore[attr-defined]
    assert CustomerGreeting.__injectable_metadata__["resource"] is CustomerContext  # type: ignore[attr-defined]

    assert EmployeeGreeting.__injectable_metadata__["for_"] is Greeting  # type: ignore[attr-defined]
    assert EmployeeGreeting.__injectable_metadata__["resource"] is EmployeeContext  # type: ignore[attr-defined]


# ============================================================================
# @injectable Decorator Error Tests
# ============================================================================


def test_injectable_rejects_function():
    """Test that @injectable raises TypeError when applied to a function."""
    import pytest

    with pytest.raises(TypeError, match="can only be applied to classes"):

        @injectable
        def some_function():
            pass


def test_injectable_accepts_plain_class():
    """Test that @injectable works with plain (non-dataclass) classes."""

    @injectable
    class PlainService:
        def __init__(self, name: str):
            self.name = name

    # Check metadata is stored
    assert hasattr(PlainService, "__injectable_metadata__")
    metadata = PlainService.__injectable_metadata__
    assert metadata["for_"] is None
    assert metadata["resource"] is None

    # Verify class works normally
    instance = PlainService("test")
    assert instance.name == "test"
