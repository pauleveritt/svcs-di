"""Comprehensive tests for @injectable decorator's for_ parameter.

Tests cover:
- Multiple implementations of same service type
- Service type resolution via ServiceLocator
- Resource precedence with for_ parameter
- Mixed usage patterns
- Integration with dependency injection
"""

from dataclasses import dataclass
from typing import Protocol

import svcs

from svcs_di.auto import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import HopscotchInjector, ServiceLocator, scan


# Test contexts
class RequestContext:
    pass


class CustomerContext(RequestContext):
    pass


class EmployeeContext(RequestContext):
    pass


class AdminContext(RequestContext):
    pass


# ============================================================================
# Basic for_ Parameter Tests
# ============================================================================


def test_for_parameter_registers_to_service_locator():
    """Test that for_ parameter causes registration to ServiceLocator."""

    class BaseService:
        pass

    @injectable(for_=BaseService)
    @dataclass
    class ConcreteService:
        value: int = 42

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Should be registered to ServiceLocator
    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)
    impl = locator.get_implementation(BaseService, resource=None)
    assert impl is ConcreteService


def test_for_without_resource_uses_default():
    """Test that for_ without resource creates default implementation."""

    class Greeting:
        pass

    @injectable(for_=Greeting)
    @dataclass
    class DefaultGreeting:
        message: str = "Hello"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # Should match as default (no resource)
    impl = locator.get_implementation(Greeting, resource=None)
    assert impl is DefaultGreeting


def test_multiple_implementations_same_service_type():
    """Test multiple implementations registered for same service type."""

    class Greeting:
        pass

    @injectable(for_=Greeting)
    @dataclass
    class DefaultGreeting:
        salutation: str = "Hello"

    @injectable(for_=Greeting, resource=CustomerContext)
    @dataclass
    class CustomerGreeting:
        salutation: str = "Good morning"

    @injectable(for_=Greeting, resource=EmployeeContext)
    @dataclass
    class EmployeeGreeting:
        salutation: str = "Hey"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # All three should be registered
    default_impl = locator.get_implementation(Greeting, resource=None)
    assert default_impl is DefaultGreeting

    customer_impl = locator.get_implementation(Greeting, resource=CustomerContext)
    assert customer_impl is CustomerGreeting

    employee_impl = locator.get_implementation(Greeting, resource=EmployeeContext)
    assert employee_impl is EmployeeGreeting


# ============================================================================
# Protocol-Based Tests
# ============================================================================


def test_for_with_protocol():
    """Test for_ parameter with Protocol as service type."""

    class GreetingProtocol(Protocol):
        def greet(self, name: str) -> str: ...

    @injectable(for_=GreetingProtocol)
    @dataclass
    class DefaultGreeting:
        salutation: str = "Hello"

        def greet(self, name: str) -> str:
            return f"{self.salutation}, {name}!"

    @injectable(for_=GreetingProtocol, resource=CustomerContext)
    @dataclass
    class CustomerGreeting:
        salutation: str = "Good morning"

        def greet(self, name: str) -> str:
            return f"{self.salutation}, {name}!"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # Both should implement protocol
    default_impl = locator.get_implementation(GreetingProtocol, resource=None)
    assert default_impl is DefaultGreeting

    customer_impl = locator.get_implementation(
        GreetingProtocol, resource=CustomerContext
    )
    assert customer_impl is CustomerGreeting


# ============================================================================
# Resource Precedence Tests
# ============================================================================


def test_resource_precedence_exact_match():
    """Test exact resource match has highest precedence."""

    class Service:
        pass

    @injectable(for_=Service)
    @dataclass
    class DefaultService:
        name: str = "default"

    @injectable(for_=Service, resource=CustomerContext)
    @dataclass
    class CustomerService:
        name: str = "customer"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # Exact match wins
    impl = locator.get_implementation(Service, resource=CustomerContext)
    assert impl is CustomerService


def test_resource_precedence_subclass_match():
    """Test subclass resource match has medium precedence."""

    class Service:
        pass

    @injectable(for_=Service)
    @dataclass
    class DefaultService:
        name: str = "default"

    @injectable(for_=Service, resource=RequestContext)
    @dataclass
    class RequestService:
        name: str = "request"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # CustomerContext is subclass of RequestContext
    # Should match RequestService via subclass match
    impl = locator.get_implementation(Service, resource=CustomerContext)
    assert impl is RequestService


def test_resource_precedence_default_fallback():
    """Test default (no resource) has lowest precedence."""

    class Service:
        pass

    @injectable(for_=Service)
    @dataclass
    class DefaultService:
        name: str = "default"

    @injectable(for_=Service, resource=AdminContext)
    @dataclass
    class AdminService:
        name: str = "admin"

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # CustomerContext doesn't match AdminContext
    # Should fall back to default
    impl = locator.get_implementation(Service, resource=CustomerContext)
    assert impl is DefaultService


# ============================================================================
# Integration with HopscotchInjector
# ============================================================================


def test_for_with_hopscotch_injector():
    """Test for_ parameter works with HopscotchInjector."""

    class Greeting:
        pass

    @injectable(for_=Greeting)
    @dataclass
    class DefaultGreeting:
        salutation: str = "Hello"

        def greet(self, name: str) -> str:
            return f"{self.salutation}, {name}!"

    @injectable(for_=Greeting, resource=CustomerContext)
    @dataclass
    class CustomerGreeting:
        salutation: str = "Good morning"

        def greet(self, name: str) -> str:
            return f"{self.salutation}, {name}!"

    @injectable
    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

        def welcome(self, name: str) -> str:
            return self.greeting.greet(name)  # type: ignore[attr-defined]

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Test with CustomerContext
    registry.register_value(RequestContext, CustomerContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container, resource=RequestContext)

    service = injector(WelcomeService)
    result = service.welcome("Alice")
    assert "Good morning" in result
    assert "Alice" in result


def test_for_with_hopscotch_injector_fallback():
    """Test HopscotchInjector falls back to default when no resource match."""

    class Greeting:
        pass

    @injectable(for_=Greeting)
    @dataclass
    class DefaultGreeting:
        salutation: str = "Hello"

        def greet(self, name: str) -> str:
            return f"{self.salutation}, {name}!"

    @injectable(for_=Greeting, resource=AdminContext)
    @dataclass
    class AdminGreeting:
        salutation: str = "Greetings"

        def greet(self, name: str) -> str:
            return f"{self.salutation}, {name}!"

    @injectable
    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]

        def welcome(self, name: str) -> str:
            return self.greeting.greet(name)  # type: ignore[attr-defined]

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Test with CustomerContext (no match, should use default)
    registry.register_value(RequestContext, CustomerContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container, resource=RequestContext)

    service = injector(WelcomeService)
    result = service.welcome("Bob")
    assert "Hello" in result
    assert "Bob" in result


# ============================================================================
# Mixed Usage Tests
# ============================================================================


def test_mixed_for_and_non_for_services():
    """Test mixing services with and without for_ parameter."""

    class Greeting:
        pass

    @injectable(for_=Greeting)
    @dataclass
    class DefaultGreeting:
        message: str = "Hello"

    @injectable  # No for_, registered directly to registry
    @dataclass
    class Database:
        host: str = "localhost"

    @injectable
    @dataclass
    class Service:
        greeting: Inject[Greeting]
        db: Inject[Database]

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)

    # Database should be in registry directly
    db = container.get(Database)
    assert db.host == "localhost"

    # Greeting should be in ServiceLocator
    locator = container.get(ServiceLocator)
    greeting_impl = locator.get_implementation(Greeting, resource=None)
    assert greeting_impl is DefaultGreeting


def test_same_class_different_service_types():
    """Test one class can be registered for multiple service types."""

    class ServiceA:
        pass

    class ServiceB:
        pass

    @injectable(for_=ServiceA)
    @dataclass
    class ImplA:
        value: int = 1

    @injectable(for_=ServiceB)
    @dataclass
    class ImplB:
        value: int = 2

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    impl_a = locator.get_implementation(ServiceA, resource=None)
    assert impl_a is ImplA

    impl_b = locator.get_implementation(ServiceB, resource=None)
    assert impl_b is ImplB


# ============================================================================
# Dependency Injection Tests
# ============================================================================


def test_for_with_nested_dependencies():
    """Test for_ parameter with nested dependency injection."""

    class Repository:
        pass

    @injectable
    @dataclass
    class Database:
        host: str = "localhost"

    @injectable(for_=Repository)
    @dataclass
    class DefaultRepository:
        db: Inject[Database]

        def query(self) -> str:
            return f"Query on {self.db.host}"

    @injectable(for_=Repository, resource=CustomerContext)
    @dataclass
    class CustomerRepository:
        db: Inject[Database]

        def query(self) -> str:
            return f"Customer query on {self.db.host}"

    @injectable
    @dataclass
    class Service:
        repo: Inject[Repository]

        def fetch(self) -> str:
            return self.repo.query()  # type: ignore[attr-defined]

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Test with CustomerContext
    registry.register_value(RequestContext, CustomerContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container, resource=RequestContext)

    service = injector(Service)
    result = service.fetch()
    assert "Customer query" in result
    assert "localhost" in result


def test_for_with_multiple_injectable_fields():
    """Test service with multiple Inject fields using for_."""

    class Greeter:
        pass

    class Formatter:
        pass

    @injectable(for_=Greeter)
    @dataclass
    class DefaultGreeter:
        salutation: str = "Hello"

    @injectable(for_=Greeter, resource=CustomerContext)
    @dataclass
    class CustomerGreeter:
        salutation: str = "Good morning"

    @injectable(for_=Formatter)
    @dataclass
    class UpperFormatter:
        def format(self, text: str) -> str:
            return text.upper()

    @injectable
    @dataclass
    class MessageService:
        greeter: Inject[Greeter]
        formatter: Inject[Formatter]

        def create_message(self, name: str) -> str:
            greeting = f"{self.greeter.salutation}, {name}!"  # type: ignore[attr-defined]
            return self.formatter.format(greeting)  # type: ignore[attr-defined]

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Test with CustomerContext
    registry.register_value(RequestContext, CustomerContext())
    container = svcs.Container(registry)
    injector = HopscotchInjector(container, resource=RequestContext)

    service = injector(MessageService)
    result = service.create_message("Alice")
    assert result == "GOOD MORNING, ALICE!"


# ============================================================================
# Error Cases
# ============================================================================


def test_no_implementation_found_returns_none():
    """Test that requesting unregistered service type returns None."""

    class Service:
        pass

    class UnregisteredService:
        pass

    # Register at least one service so ServiceLocator is created
    @injectable(for_=Service)
    @dataclass
    class ServiceImpl:
        value: int = 1

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)
    locator = container.get(ServiceLocator)

    # Should return None (no implementation found for UnregisteredService)
    impl = locator.get_implementation(UnregisteredService, resource=None)
    assert impl is None


def test_for_none_behaves_like_no_for():
    """Test that for_=None behaves same as not specifying for_."""

    @injectable(for_=None)
    @dataclass
    class ServiceA:
        value: int = 1

    @injectable
    @dataclass
    class ServiceB:
        value: int = 2

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    container = svcs.Container(registry)

    # Both should be registered directly to registry
    service_a = container.get(ServiceA)
    assert service_a.value == 1

    service_b = container.get(ServiceB)
    assert service_b.value == 2
