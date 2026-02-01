"""Tests for dataclass feature support in dependency injection."""

from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass, field
from typing import ClassVar, Protocol, runtime_checkable

import pytest
import svcs

from svcs_di import Inject, auto, auto_async


@dataclass
class Database:
    """A simple database service for testing."""

    host: str = "localhost"
    port: int = 5432


# ============================================================================
# Bug Fix: default vs default_factory
# ============================================================================


def some_handler(x: int) -> int:
    """A callable that should be stored as-is when used as a static default."""
    return x * 2


def test_field_default_callable_not_called():
    """field(default=callable) should NOT call the callable - it's a static default."""

    @dataclass
    class Config:
        handler: Callable[[int], int] = some_handler

    registry = svcs.Registry()
    registry.register_factory(Config, auto(Config))

    container = svcs.Container(registry)
    config = container.get(Config)

    # The handler should be the function itself, not the result of calling it
    assert config.handler is some_handler
    assert config.handler(5) == 10


def test_field_default_factory_callable_is_called():
    """field(default_factory=callable) SHOULD call the callable."""

    @dataclass
    class Config:
        items: list = field(default_factory=list)

    registry = svcs.Registry()
    registry.register_factory(Config, auto(Config))

    container = svcs.Container(registry)
    config = container.get(Config)

    # The items should be an empty list, not the list type
    assert config.items == []
    assert isinstance(config.items, list)


def test_static_callable_default_vs_factory():
    """Direct comparison: static callable default vs default_factory."""

    def make_list():
        return [1, 2, 3]

    @dataclass
    class Service:
        # Static default: store the function itself
        processor: Callable = some_handler
        # Factory default: call the function to get result
        items: list = field(default_factory=make_list)

    registry = svcs.Registry()
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    # processor should be the function, not called
    assert service.processor is some_handler
    assert callable(service.processor)

    # items should be the result of calling make_list()
    assert service.items == [1, 2, 3]


def test_class_as_static_default():
    """A class as a static default should NOT be instantiated."""

    class Handler:
        def process(self) -> str:
            return "processed"

    @dataclass
    class Config:
        handler_class: type[Handler] = Handler

    registry = svcs.Registry()
    registry.register_factory(Config, auto(Config))

    container = svcs.Container(registry)
    config = container.get(Config)

    # Should be the class itself, not an instance
    assert config.handler_class is Handler
    assert isinstance(config.handler_class, type)


# ============================================================================
# Bug Fix: init=False fields
# ============================================================================


def test_init_false_field_excluded():
    """Fields with init=False should not be included in injection."""

    @dataclass
    class Service:
        db: Inject[Database]
        # This field is not part of __init__, so it shouldn't be injected
        computed: str = field(init=False, default="computed_value")

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="test"))
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    # db should be injected
    assert service.db.host == "test"
    # computed should have its default value
    assert service.computed == "computed_value"


def test_init_false_with_post_init():
    """init=False fields work correctly with __post_init__."""

    @dataclass
    class Service:
        db: Inject[Database]
        name: str = "service"
        # Computed in __post_init__
        full_name: str = field(init=False)

        def __post_init__(self):
            self.full_name = f"{self.name}@{self.db.host}"

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod"))
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    assert service.full_name == "service@prod"


# ============================================================================
# KW_ONLY marker support
# ============================================================================


def test_kw_only_marker():
    """Fields after KW_ONLY marker should work correctly."""

    @dataclass
    class Config:
        name: str
        _: KW_ONLY
        timeout: int = 30
        retries: int = 3

    registry = svcs.Registry()
    registry.register_factory(Config, auto(Config))

    # Need to provide name since it has no default
    # This tests that the injection system handles kw_only correctly
    container = svcs.Container(registry)

    # Should fail because name is required
    with pytest.raises(TypeError):
        container.get(Config)


def test_kw_only_with_inject():
    """KW_ONLY works with Inject markers."""

    @dataclass
    class Service:
        db: Inject[Database]
        _: KW_ONLY
        timeout: int = 30

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    assert service.db is not None
    assert service.timeout == 30


# ============================================================================
# ClassVar exclusion
# ============================================================================


def test_classvar_excluded():
    """ClassVar fields should not be included in injection."""

    @dataclass
    class Service:
        db: Inject[Database]
        # ClassVar is a class attribute, not an instance attribute
        counter: ClassVar[int] = 0

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    # db should be injected
    assert service.db is not None
    # counter is a class variable
    assert Service.counter == 0


# ============================================================================
# frozen=True dataclasses
# ============================================================================


def test_frozen_dataclass():
    """frozen=True dataclasses should work with injection."""

    @dataclass(frozen=True)
    class ImmutableConfig:
        db: Inject[Database]
        name: str = "config"

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="frozen-host"))
    registry.register_factory(ImmutableConfig, auto(ImmutableConfig))

    container = svcs.Container(registry)
    config = container.get(ImmutableConfig)

    assert config.db.host == "frozen-host"
    assert config.name == "config"

    # Verify it's actually frozen
    with pytest.raises(AttributeError):
        config.name = "modified"  # type: ignore[misc]


# ============================================================================
# slots=True dataclasses
# ============================================================================


def test_slots_dataclass():
    """slots=True dataclasses should work with injection."""

    @dataclass(slots=True)
    class SlottedService:
        db: Inject[Database]
        value: int = 42

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="slotted"))
    registry.register_factory(SlottedService, auto(SlottedService))

    container = svcs.Container(registry)
    service = container.get(SlottedService)

    assert service.db.host == "slotted"
    assert service.value == 42

    # Verify it has __slots__
    assert hasattr(SlottedService, "__slots__")


# ============================================================================
# Inheritance with mixed defaults
# ============================================================================


def test_inheritance_basic():
    """Basic inheritance should work."""

    @dataclass
    class BaseService:
        db: Inject[Database]
        name: str = "base"

    @dataclass
    class ChildService(BaseService):
        timeout: int = 30

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="inherited"))
    registry.register_factory(ChildService, auto(ChildService))

    container = svcs.Container(registry)
    service = container.get(ChildService)

    assert service.db.host == "inherited"
    assert service.name == "base"
    assert service.timeout == 30


def test_inheritance_with_default_factory():
    """Inheritance with default_factory in parent and child."""

    @dataclass
    class BaseService:
        db: Inject[Database]
        items: list = field(default_factory=list)

    @dataclass
    class ChildService(BaseService):
        extra: dict = field(default_factory=dict)

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(ChildService, auto(ChildService))

    container = svcs.Container(registry)
    service = container.get(ChildService)

    assert service.items == []
    assert service.extra == {}
    assert isinstance(service.items, list)
    assert isinstance(service.extra, dict)


def test_inheritance_override_default():
    """Child can override parent's default values."""

    @dataclass
    class BaseConfig:
        db: Inject[Database]
        timeout: int = 30

    @dataclass
    class ChildConfig(BaseConfig):
        timeout: int = 60  # Override parent's default

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(ChildConfig, auto(ChildConfig))

    container = svcs.Container(registry)
    config = container.get(ChildConfig)

    assert config.timeout == 60


# ============================================================================
# Async tests
# ============================================================================


async def test_callable_default_async():
    """Callable defaults work correctly in async context."""

    @dataclass
    class AsyncConfig:
        handler: Callable[[int], int] = some_handler
        items: list = field(default_factory=list)

    registry = svcs.Registry()
    registry.register_factory(AsyncConfig, auto_async(AsyncConfig))

    async with svcs.Container(registry) as container:
        config = await container.aget(AsyncConfig)

        # handler should be the function, not called
        assert config.handler is some_handler

        # items should be an empty list
        assert config.items == []


test_callable_default_async = pytest.mark.anyio(test_callable_default_async)


async def test_init_false_async():
    """init=False fields work correctly in async context."""

    @dataclass
    class AsyncService:
        name: str = "async"
        computed: str = field(init=False, default="computed")

    registry = svcs.Registry()
    registry.register_factory(AsyncService, auto_async(AsyncService))

    async with svcs.Container(registry) as container:
        service = await container.aget(AsyncService)

        assert service.name == "async"
        assert service.computed == "computed"


test_init_false_async = pytest.mark.anyio(test_init_false_async)


# ============================================================================
# Protocol with callable default
# ============================================================================


@runtime_checkable
class Handler(Protocol):
    def handle(self, data: str) -> str: ...


class DefaultHandler:
    def handle(self, data: str) -> str:
        return f"handled: {data}"


def test_protocol_implementation_as_default():
    """A protocol implementation instance as default should not be called."""

    default_handler = DefaultHandler()

    @dataclass
    class Service:
        db: Inject[Database]
        handler: Handler = default_handler

    registry = svcs.Registry()
    registry.register_value(Database, Database())
    registry.register_factory(Service, auto(Service))

    container = svcs.Container(registry)
    service = container.get(Service)

    # handler should be the instance itself
    assert service.handler is default_handler
    assert service.handler.handle("test") == "handled: test"
