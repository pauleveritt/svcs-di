"""Tests for InjectorContainer class.

Task Group 1: Tests for basic class structure and attrs integration.
Task Group 2: Tests for synchronous inject() method with kwargs support.
Task Group 3: Tests for asynchronous ainject() method with kwargs support.
Task Group 4: Tests for error handling and edge cases.
Task Group 5: Tests for module exports and integration.
Task Group 6: Strategic gap-filling tests for real-world usage scenarios.
"""

from dataclasses import dataclass
from typing import Any

import attrs
import pytest
import svcs
import svcs.exceptions

from svcs_di import Inject, InjectorContainer, KeywordAsyncInjector, KeywordInjector


# =============================================================================
# Shared test fixtures for Task Groups 2+
# =============================================================================


@dataclass
class Database:
    """A simple database service for testing."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class DBService:
    """A service with injectable dependencies for testing."""

    db: Inject[Database]
    timeout: int = 30


# =============================================================================
# Task Group 1: InjectorContainer Class Definition Tests
# =============================================================================


def test_injector_container_can_be_instantiated_with_registry() -> None:
    """Test that InjectorContainer can be instantiated with a Registry."""
    registry = svcs.Registry()
    container = InjectorContainer(registry)

    assert container.registry is registry


def test_injector_container_has_injector_attribute() -> None:
    """Test that InjectorContainer has an injector attribute."""
    registry = svcs.Registry()
    container = InjectorContainer(registry)

    assert hasattr(container, "injector")


def test_injector_container_default_injector_is_keyword_injector() -> None:
    """Test that default injector is KeywordInjector when not specified."""
    registry = svcs.Registry()
    container = InjectorContainer(registry)

    assert container.injector is KeywordInjector


def test_injector_container_custom_injector_can_be_passed() -> None:
    """Test that a custom injector class can be passed via constructor."""

    @dataclass(frozen=True)
    class CustomInjector:
        container: svcs.Container

        def __call__[T](self, target: type[T], **kwargs: Any) -> T:
            return target()

    registry = svcs.Registry()
    container = InjectorContainer(registry, injector=CustomInjector)

    assert container.injector is CustomInjector


def test_injector_container_is_subclass_of_svcs_container() -> None:
    """Test that InjectorContainer is a subclass of svcs.Container."""
    assert issubclass(InjectorContainer, svcs.Container)

    registry = svcs.Registry()
    container = InjectorContainer(registry)
    assert isinstance(container, svcs.Container)


def test_injector_container_uses_attrs_style_subclassing() -> None:
    """Test that attrs-style subclassing is used (verify __attrs_attrs__ exists)."""
    # Attrs-decorated classes have __attrs_attrs__
    assert hasattr(InjectorContainer, "__attrs_attrs__")

    # Verify it's properly decorated with attrs
    assert attrs.has(InjectorContainer)


def test_injector_container_has_async_injector_attribute() -> None:
    """Test that InjectorContainer has an async_injector attribute."""
    registry = svcs.Registry()
    container = InjectorContainer(registry)

    assert hasattr(container, "async_injector")
    assert container.async_injector is KeywordAsyncInjector


# =============================================================================
# Task Group 2: Synchronous inject() Method Tests
# =============================================================================


def test_get_without_kwargs_uses_standard_svcs_behavior() -> None:
    """Test get() without kwargs uses standard svcs.Container behavior."""
    registry = svcs.Registry()
    db = Database(host="prod", port=5433)
    registry.register_value(Database, db)

    container = InjectorContainer(registry)

    # Call get() - should use standard svcs behavior
    result = container.get(Database)

    assert result is db
    assert result.host == "prod"
    assert result.port == 5433


def test_inject_with_kwargs_uses_injector() -> None:
    """Test inject() with kwargs uses injector."""
    registry = svcs.Registry()
    container_db = Database(host="container", port=1111)
    registry.register_value(Database, container_db)

    container = InjectorContainer(registry)

    # Call inject() with kwargs - should use injector for dependency resolution
    override_db = Database(host="override", port=9999)
    result = container.inject(DBService, db=override_db)

    # kwargs should override container value (three-tier precedence)
    assert isinstance(result, DBService)
    assert result.db is override_db
    assert result.db.host == "override"
    assert result.db.port == 9999
    # Default timeout should still be used
    assert result.timeout == 30


def test_inject_without_kwargs_uses_container_and_defaults() -> None:
    """Test inject() without kwargs uses container values and defaults."""
    registry = svcs.Registry()
    container_db = Database(host="container", port=1111)
    registry.register_value(Database, container_db)

    container = InjectorContainer(registry)

    # Call inject() without kwargs
    result = container.inject(DBService)

    assert isinstance(result, DBService)
    assert result.db is container_db  # from container
    assert result.timeout == 30  # default


def test_inject_with_no_injector_raises_value_error() -> None:
    """Test inject() with no injector configured raises ValueError."""
    registry = svcs.Registry()
    registry.register_value(Database, Database())

    # Create container with injector set to None
    container = InjectorContainer(registry, injector=None)

    with pytest.raises(
        ValueError, match="Cannot inject without an injector configured"
    ):
        container.inject(DBService, db=Database())


def test_inject_three_tier_precedence_kwargs_over_container_over_defaults() -> None:
    """Test three-tier precedence: kwargs > container > defaults.

    Three-tier precedence within the injector:
    1. kwargs (highest priority) - overrides everything
    2. container values - for Inject[T] fields
    3. defaults (lowest priority) - from field definitions
    """
    registry = svcs.Registry()
    container_db = Database(host="container-host", port=2222)
    registry.register_value(Database, container_db)

    container = InjectorContainer(registry)

    # Test 1: No kwargs - container value for injectable, default for timeout
    result1 = container.inject(DBService)
    assert result1.db is container_db  # from container (tier 2)
    assert result1.timeout == 30  # default (tier 3)

    # Test 2: Override timeout via kwargs
    result2 = container.inject(DBService, timeout=99)
    assert result2.db is container_db  # from container (tier 2)
    assert result2.timeout == 99  # kwargs override (tier 1)

    # Test 3: Override db via kwargs
    override_db = Database(host="kwargs-host", port=8888)
    result3 = container.inject(DBService, db=override_db)
    assert result3.db is override_db  # kwargs override (tier 1)
    assert result3.timeout == 30  # default (tier 3)

    # Test 4: Override both via kwargs
    result4 = container.inject(DBService, db=override_db, timeout=77)
    assert result4.db is override_db  # kwargs override (tier 1)
    assert result4.timeout == 77  # kwargs override (tier 1)


def test_inject_returns_resolved_service_correctly() -> None:
    """Test that inject() returns resolved service correctly."""
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="test", port=1234))

    container = InjectorContainer(registry)

    # inject service with kwargs
    result = container.inject(DBService, timeout=42)

    # Verify the result is correctly constructed
    assert isinstance(result, DBService)
    assert isinstance(result.db, Database)
    assert result.db.host == "test"
    assert result.db.port == 1234
    assert result.timeout == 42


# =============================================================================
# Task Group 3: Asynchronous ainject() Method Tests
# =============================================================================


@pytest.mark.anyio
async def test_aget_without_kwargs_uses_standard_svcs_behavior() -> None:
    """Test aget() without kwargs uses standard svcs.Container async behavior."""
    registry = svcs.Registry()
    db = Database(host="async-prod", port=5434)
    registry.register_value(Database, db)

    container = InjectorContainer(registry)

    # Call aget() - should use standard svcs async behavior
    result = await container.aget(Database)

    assert result is db
    assert result.host == "async-prod"
    assert result.port == 5434


@pytest.mark.anyio
async def test_ainject_with_kwargs_uses_async_injector() -> None:
    """Test ainject() with kwargs uses async injector."""
    registry = svcs.Registry()
    container_db = Database(host="async-container", port=2222)
    registry.register_value(Database, container_db)

    container = InjectorContainer(registry)

    # Call ainject() with kwargs - should use async injector for dependency resolution
    override_db = Database(host="async-override", port=8888)
    result = await container.ainject(DBService, db=override_db)

    # kwargs should override container value (three-tier precedence)
    assert isinstance(result, DBService)
    assert result.db is override_db
    assert result.db.host == "async-override"
    assert result.db.port == 8888
    # Default timeout should still be used
    assert result.timeout == 30


@pytest.mark.anyio
async def test_ainject_without_kwargs_uses_container_and_defaults() -> None:
    """Test ainject() without kwargs uses container values and defaults."""
    registry = svcs.Registry()
    container_db = Database(host="async-container", port=2222)
    registry.register_value(Database, container_db)

    container = InjectorContainer(registry)

    # Call ainject() without kwargs
    result = await container.ainject(DBService)

    assert isinstance(result, DBService)
    assert result.db is container_db  # from container
    assert result.timeout == 30  # default


@pytest.mark.anyio
async def test_ainject_with_no_async_injector_raises_value_error() -> None:
    """Test ainject() with no async_injector configured raises ValueError."""
    registry = svcs.Registry()
    registry.register_value(Database, Database())

    # Create container with async_injector set to None
    container = InjectorContainer(registry, async_injector=None)

    with pytest.raises(
        ValueError, match="Cannot inject without an async injector configured"
    ):
        await container.ainject(DBService, db=Database())


@pytest.mark.anyio
async def test_ainject_three_tier_precedence_kwargs_over_container_over_defaults() -> (
    None
):
    """Test three-tier precedence: kwargs > container > defaults (async).

    Three-tier precedence within the async injector:
    1. kwargs (highest priority) - overrides everything
    2. container values - for Inject[T] fields (resolved via aget)
    3. defaults (lowest priority) - from field definitions
    """
    registry = svcs.Registry()
    container_db = Database(host="async-container-host", port=3333)
    registry.register_value(Database, container_db)

    container = InjectorContainer(registry)

    # Test 1: No kwargs - container value for injectable, default for timeout
    result1 = await container.ainject(DBService)
    assert result1.db is container_db  # from container (tier 2)
    assert result1.timeout == 30  # default (tier 3)

    # Test 2: Override timeout via kwargs
    result2 = await container.ainject(DBService, timeout=88)
    assert result2.db is container_db  # from container (tier 2)
    assert result2.timeout == 88  # kwargs override (tier 1)

    # Test 3: Override db via kwargs
    override_db = Database(host="async-kwargs-host", port=7777)
    result3 = await container.ainject(DBService, db=override_db)
    assert result3.db is override_db  # kwargs override (tier 1)
    assert result3.timeout == 30  # default (tier 3)

    # Test 4: Override both via kwargs
    result4 = await container.ainject(DBService, db=override_db, timeout=66)
    assert result4.db is override_db  # kwargs override (tier 1)
    assert result4.timeout == 66  # kwargs override (tier 1)


@pytest.mark.anyio
async def test_ainject_returns_resolved_service_correctly() -> None:
    """Test that ainject() returns resolved service correctly (await properly)."""
    registry = svcs.Registry()
    registry.register_value(Database, Database(host="async-test", port=4321))

    container = InjectorContainer(registry)

    # ainject service with kwargs via async path
    result = await container.ainject(DBService, timeout=55)

    # Verify the result is correctly constructed
    assert isinstance(result, DBService)
    assert isinstance(result.db, Database)
    assert result.db.host == "async-test"
    assert result.db.port == 4321
    assert result.timeout == 55


# =============================================================================
# Task Group 4: Error Handling and Edge Cases Tests
# =============================================================================


def test_error_message_no_injector_exact_message() -> None:
    """Test ValueError message content for no injector configured.

    Verifies the exact error message:
    "Cannot inject without an injector configured"
    """
    registry = svcs.Registry()
    registry.register_value(Database, Database())

    container = InjectorContainer(registry, injector=None)

    with pytest.raises(ValueError) as exc_info:
        container.inject(DBService, db=Database())

    # Verify exact error message
    assert str(exc_info.value) == "Cannot inject without an injector configured"


def test_injector_validation_errors_propagate_naturally() -> None:
    """Test that injector's own validation errors (unknown kwargs) propagate naturally.

    When unknown kwargs are provided, the KeywordInjector's validate_kwargs()
    raises ValueError which should bubble up unchanged.
    """
    registry = svcs.Registry()
    registry.register_value(Database, Database())

    container = InjectorContainer(registry)

    # Provide an unknown kwarg that is not a valid parameter for DBService
    with pytest.raises(ValueError) as exc_info:
        container.inject(DBService, unknown_param="invalid")

    # The error should come from the injector's validation and include helpful info
    error_message = str(exc_info.value)
    assert "Unknown parameter 'unknown_param'" in error_message
    assert "DBService" in error_message


def test_duck_typing_invalid_kwargs_types_surface_during_construction() -> None:
    """Test duck typing: invalid kwargs types surface during target construction.

    Per spec requirements, kwargs type validation uses duck typing approach -
    let Python's natural type errors surface during construction rather than
    doing explicit type checking in the container.
    """

    @dataclass
    class StrictService:
        """A service that requires specific types during construction."""

        value: int  # Requires an int, will fail if wrong type is used

        def __post_init__(self) -> None:
            # Simulate strict type validation in __post_init__
            if not isinstance(self.value, int):
                raise TypeError(f"value must be int, got {type(self.value).__name__}")

    registry = svcs.Registry()
    container = InjectorContainer(registry)

    # Pass a wrong type - duck typing lets this through the container/injector
    # The error surfaces during target construction
    with pytest.raises(TypeError) as exc_info:
        container.inject(StrictService, value="not_an_int")

    # The error comes from the target's own validation, not from container/injector
    assert "must be int" in str(exc_info.value)


def test_svcs_service_not_found_error_propagates_correctly() -> None:
    """Test that standard svcs errors (ServiceNotFoundError) propagate correctly.

    When the container cannot resolve an Inject[T] dependency because it's not
    registered, the svcs.exceptions.ServiceNotFoundError should propagate up
    unchanged.
    """
    registry = svcs.Registry()
    # Intentionally NOT registering Database service

    container = InjectorContainer(registry)

    # Try to inject DBService which requires Database via Inject[Database]
    # Since Database is not registered, svcs should raise ServiceNotFoundError
    with pytest.raises(svcs.exceptions.ServiceNotFoundError) as exc_info:
        container.inject(DBService, timeout=99)

    # Verify the error is about the missing Database service
    assert "Database" in str(exc_info.value)


@pytest.mark.anyio
async def test_ainject_svcs_service_not_found_error_propagates_correctly() -> None:
    """Test that svcs errors propagate correctly in async path.

    Same as sync version but verifies the async ainject() path properly
    propagates ServiceNotFoundError.
    """
    registry = svcs.Registry()
    # Intentionally NOT registering Database service

    container = InjectorContainer(registry)

    # Try to ainject DBService which requires Database via Inject[Database]
    with pytest.raises(svcs.exceptions.ServiceNotFoundError) as exc_info:
        await container.ainject(DBService, timeout=99)

    # Verify the error is about the missing Database service
    assert "Database" in str(exc_info.value)


# =============================================================================
# Task Group 5: Module Exports and Integration Tests
# =============================================================================


def test_injector_container_importable_from_svcs_di() -> None:
    """Test that InjectorContainer can be imported from svcs_di package.

    This verifies that the public API export is correctly configured
    in __init__.py and the import works as expected.
    """
    # Import from the top-level package (already imported at module level)
    from svcs_di import InjectorContainer as ImportedContainer

    # Verify it's the same class
    assert ImportedContainer is InjectorContainer

    # Also verify it's in __all__
    import svcs_di

    assert "InjectorContainer" in svcs_di.__all__


def test_injector_container_works_with_keyword_injector() -> None:
    """Test that InjectorContainer works with existing KeywordInjector.

    This verifies seamless integration between InjectorContainer and the
    KeywordInjector, which is the default injector.
    """
    registry = svcs.Registry()
    db = Database(host="integration-test", port=5555)
    registry.register_value(Database, db)

    # Create container with explicit KeywordInjector (should be same as default)
    container = InjectorContainer(registry, injector=KeywordInjector)

    # Verify the injector is set correctly
    assert container.injector is KeywordInjector

    # Test that injection works
    result = container.inject(DBService, timeout=100)

    assert isinstance(result, DBService)
    assert result.db is db
    assert result.timeout == 100


@pytest.mark.anyio
async def test_injector_container_works_with_keyword_async_injector() -> None:
    """Test that InjectorContainer works with existing KeywordAsyncInjector.

    This verifies seamless integration between InjectorContainer and the
    KeywordAsyncInjector for async dependency resolution.
    """
    registry = svcs.Registry()
    db = Database(host="async-integration-test", port=6666)
    registry.register_value(Database, db)

    # Create container with explicit KeywordAsyncInjector (should be same as default)
    container = InjectorContainer(registry, async_injector=KeywordAsyncInjector)

    # Verify the async injector is set correctly
    assert container.async_injector is KeywordAsyncInjector

    # Test that async injection works
    result = await container.ainject(DBService, timeout=200)

    assert isinstance(result, DBService)
    assert result.db is db
    assert result.timeout == 200


def test_end_to_end_workflow_create_register_inject_with_kwargs() -> None:
    """Test basic end-to-end workflow (create container, register service, inject with kwargs).

    This integration test verifies the complete workflow:
    1. Create a registry
    2. Register a service
    3. Create an InjectorContainer
    4. Use inject() with kwargs to resolve a dependent service
    """
    # Step 1: Create a registry
    registry = svcs.Registry()

    # Step 2: Register the Database service
    db = Database(host="production", port=5432)
    registry.register_value(Database, db)

    # Step 3: Create an InjectorContainer
    container = InjectorContainer(registry)

    # Step 4a: Get a service without kwargs (standard svcs behavior)
    retrieved_db = container.get(Database)
    assert retrieved_db is db

    # Step 4b: inject a dependent service with kwargs override
    custom_timeout = 120
    service = container.inject(DBService, timeout=custom_timeout)

    # Verify the complete workflow worked
    assert isinstance(service, DBService)
    assert service.db is db  # Injected from container
    assert service.timeout == custom_timeout  # Overridden via kwargs

    # Step 4c: inject with full kwargs override
    override_db = Database(host="test", port=9999)
    service2 = container.inject(DBService, db=override_db, timeout=60)

    assert isinstance(service2, DBService)
    assert service2.db is override_db  # Overridden via kwargs
    assert service2.db.host == "test"
    assert service2.timeout == 60


# =============================================================================
# Task Group 6: Strategic Gap-Filling Tests
# =============================================================================


def test_custom_injector_implementation_works_with_inject() -> None:
    """Test InjectorContainer with custom injector implementation (not just KeywordInjector).

    This test verifies that InjectorContainer can work with any custom injector
    that follows the Injector protocol, not just the default KeywordInjector.
    The custom injector transforms kwargs in a specific way to prove it's being used.
    """

    @dataclass
    class SimpleService:
        """A simple service for custom injector testing."""

        value: str = "default"
        multiplier: int = 1

    @dataclass(frozen=True)
    class TransformingInjector:
        """A custom injector that transforms kwargs before passing to target.

        This injector uppercases string values to prove it's being used.
        """

        container: svcs.Container

        def __call__[T](self, target: type[T], **kwargs: Any) -> T:
            # Transform: uppercase all string kwargs
            transformed_kwargs = {
                k: v.upper() if isinstance(v, str) else v for k, v in kwargs.items()
            }
            return target(**transformed_kwargs)

    registry = svcs.Registry()
    container = InjectorContainer(registry, injector=TransformingInjector)

    # Use the container with our custom injector
    result = container.inject(SimpleService, value="hello", multiplier=5)

    # Verify the custom injector was used (string was uppercased)
    assert isinstance(result, SimpleService)
    assert result.value == "HELLO"  # Transformed by custom injector
    assert result.multiplier == 5  # Non-string left unchanged


def test_drop_in_replacement_multiple_service_types() -> None:
    """Test InjectorContainer as drop-in replacement for svcs.Container.

    Verifies that InjectorContainer supports all standard svcs.Container
    behaviors, specifically requesting multiple service types at once.
    """

    @dataclass
    class ServiceA:
        name: str = "A"

    @dataclass
    class ServiceB:
        name: str = "B"

    @dataclass
    class ServiceC:
        name: str = "C"

    registry = svcs.Registry()
    svc_a = ServiceA(name="service-a")
    svc_b = ServiceB(name="service-b")
    svc_c = ServiceC(name="service-c")
    registry.register_value(ServiceA, svc_a)
    registry.register_value(ServiceB, svc_b)
    registry.register_value(ServiceC, svc_c)

    container = InjectorContainer(registry)

    # Request multiple service types at once - standard svcs behavior
    result_a, result_b = container.get(ServiceA, ServiceB)
    assert result_a is svc_a
    assert result_b is svc_b

    # Request three services at once
    result_a2, result_b2, result_c = container.get(ServiceA, ServiceB, ServiceC)
    assert result_a2 is svc_a
    assert result_b2 is svc_b
    assert result_c is svc_c


@pytest.mark.anyio
async def test_mixed_sync_async_usage_same_container() -> None:
    """Test InjectorContainer with mixed sync/async usage patterns.

    Verifies that the same InjectorContainer instance can be used for both
    synchronous get()/inject() and asynchronous aget()/ainject() operations.
    """
    registry = svcs.Registry()
    db = Database(host="mixed-usage", port=5555)
    registry.register_value(Database, db)

    container = InjectorContainer(registry)

    # First: sync get()
    sync_db = container.get(Database)
    assert sync_db is db

    # Second: async aget()
    async_db = await container.aget(Database)
    assert async_db is db

    # Third: sync inject() with kwargs
    sync_service = container.inject(DBService, timeout=111)
    assert isinstance(sync_service, DBService)
    assert sync_service.db is db
    assert sync_service.timeout == 111

    # Fourth: async ainject() with kwargs
    async_service = await container.ainject(DBService, timeout=222)
    assert isinstance(async_service, DBService)
    assert async_service.db is db
    assert async_service.timeout == 222


def test_context_manager_close_inherited_from_svcs_container() -> None:
    """Test InjectorContainer context manager support (inherited from svcs.Container).

    Verifies that InjectorContainer properly inherits context manager behavior
    from svcs.Container, including the close() method for cleanup.
    """
    registry = svcs.Registry()
    db = Database(host="context-test", port=7777)
    registry.register_value(Database, db)

    # Use InjectorContainer as context manager
    with InjectorContainer(registry) as container:
        # Container should work normally inside context
        result = container.get(Database)
        assert result is db
        assert result.host == "context-test"

        # Also test inject() with kwargs
        service = container.inject(DBService, timeout=50)
        assert service.db is db


@pytest.mark.anyio
async def test_async_context_manager_aclose_inherited_from_svcs_container() -> None:
    """Test InjectorContainer async context manager support (inherited from svcs.Container).

    Verifies that InjectorContainer properly inherits async context manager
    behavior from svcs.Container, including the aclose() method for async cleanup.
    """
    registry = svcs.Registry()
    db = Database(host="async-context-test", port=8888)
    registry.register_value(Database, db)

    # Use InjectorContainer as async context manager
    async with InjectorContainer(registry) as container:
        # Container should work normally inside async context
        result = await container.aget(Database)
        assert result is db
        assert result.host == "async-context-test"

        # Also test ainject() with kwargs via async path
        service = await container.ainject(DBService, timeout=60)
        assert service.db is db
        assert service.timeout == 60


@pytest.mark.anyio
async def test_custom_async_injector_implementation_works_with_ainject() -> None:
    """Test InjectorContainer with custom async injector implementation.

    This test verifies that InjectorContainer can work with any custom async
    injector that follows the AsyncInjector protocol, not just KeywordAsyncInjector.
    """

    @dataclass
    class AsyncService:
        """A service for custom async injector testing."""

        prefix: str = "sync"
        value: int = 0

    @dataclass(frozen=True)
    class AsyncTransformingInjector:
        """A custom async injector that transforms kwargs.

        This injector adds 'async-' prefix to string values to prove it's being used.
        """

        container: svcs.Container

        async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
            # Transform: add async prefix to string kwargs
            transformed_kwargs = {
                k: f"async-{v}" if isinstance(v, str) else v for k, v in kwargs.items()
            }
            return target(**transformed_kwargs)

    registry = svcs.Registry()
    container = InjectorContainer(registry, async_injector=AsyncTransformingInjector)

    # Use the container with our custom async injector
    result = await container.ainject(AsyncService, prefix="test", value=42)

    # Verify the custom async injector was used (string was prefixed)
    assert isinstance(result, AsyncService)
    assert result.prefix == "async-test"  # Transformed by custom async injector
    assert result.value == 42  # Non-string left unchanged
