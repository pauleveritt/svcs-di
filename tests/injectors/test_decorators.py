"""Tests for @injectable decorator."""

from dataclasses import dataclass
from typing import Any, get_type_hints

from svcs_di.injectors.decorators import injectable


# Context classes for testing
class CustomerContext:
    pass


class EmployeeContext:
    pass


class TestContext:
    pass


# ============================================================================
# @injectable Decorator Tests - Classes
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
# @injectable Decorator Tests - Plain Classes
# ============================================================================


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


# ============================================================================
# @injectable Decorator Tests - Functions (Task Group 1)
# ============================================================================


class Greeting:
    """Service type for function factory tests."""

    def __init__(self, message: str = "Hello"):
        self.message = message


def test_injectable_bare_decorator_on_function():
    """Test @injectable bare decorator on a function factory."""

    @injectable
    def create_greeting() -> Greeting:
        return Greeting("Hello from factory")

    # Check metadata is stored on function
    assert hasattr(create_greeting, "__injectable_metadata__")
    metadata: dict[str, Any] = create_greeting.__injectable_metadata__  # type: ignore[attr-defined]
    assert metadata["for_"] is None
    assert metadata["resource"] is None

    # Function should still work normally
    result = create_greeting()
    assert isinstance(result, Greeting)
    assert result.message == "Hello from factory"


def test_injectable_with_explicit_for_on_function():
    """Test @injectable(for_=X) with explicit service type on a function."""

    @injectable(for_=Greeting)
    def create_custom_greeting() -> Greeting:
        return Greeting("Custom greeting")

    # Check metadata stores for_
    assert hasattr(create_custom_greeting, "__injectable_metadata__")
    metadata: dict[str, Any] = create_custom_greeting.__injectable_metadata__  # type: ignore[attr-defined]
    assert metadata["for_"] is Greeting
    assert metadata["resource"] is None


def test_injectable_with_for_and_resource_on_function():
    """Test @injectable(for_=X, resource=Y) with resource context on a function."""

    @injectable(for_=Greeting, resource=CustomerContext)
    def create_customer_greeting() -> Greeting:
        return Greeting("Welcome, valued customer!")

    # Check metadata stores both for_ and resource
    assert hasattr(create_customer_greeting, "__injectable_metadata__")
    metadata: dict[str, Any] = create_customer_greeting.__injectable_metadata__  # type: ignore[attr-defined]
    assert metadata["for_"] is Greeting
    assert metadata["resource"] is CustomerContext


def test_injectable_return_type_inference_for_function():
    """Test return type inference when for_ is not specified on a function."""

    @injectable
    def create_inferred_greeting() -> Greeting:
        return Greeting("Inferred type")

    # Check metadata is stored
    assert hasattr(create_inferred_greeting, "__injectable_metadata__")
    metadata: dict[str, Any] = create_inferred_greeting.__injectable_metadata__  # type: ignore[attr-defined]

    # for_ should be None (inference happens at registration time, not decoration time)
    assert metadata["for_"] is None
    assert metadata["resource"] is None

    # The return type should be extractable via get_type_hints
    hints = get_type_hints(create_inferred_greeting)
    assert hints.get("return") is Greeting


def test_injectable_class_behavior_unchanged():
    """Test that existing class decorator behavior remains unchanged after function support."""

    class ServiceBase:
        pass

    @injectable(for_=ServiceBase, resource=EmployeeContext)
    @dataclass
    class ServiceImpl:
        name: str = "default"

    # Check metadata is stored correctly for class
    assert hasattr(ServiceImpl, "__injectable_metadata__")
    metadata = ServiceImpl.__injectable_metadata__
    assert metadata["for_"] is ServiceBase
    assert metadata["resource"] is EmployeeContext

    # Class should work normally
    instance = ServiceImpl(name="test")
    assert instance.name == "test"


def test_injectable_async_function():
    """Test @injectable on async function factory."""
    import inspect

    @injectable(for_=Greeting)
    async def create_async_greeting() -> Greeting:
        return Greeting("Async greeting")

    # Check metadata is stored
    assert hasattr(create_async_greeting, "__injectable_metadata__")
    metadata: dict[str, Any] = create_async_greeting.__injectable_metadata__  # type: ignore[attr-defined]
    assert metadata["for_"] is Greeting
    assert metadata["resource"] is None

    # Function should be detectable as async
    assert inspect.iscoroutinefunction(create_async_greeting)
