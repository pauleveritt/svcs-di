"""Tests for InitVar[Inject[T]] pattern support."""

from dataclasses import InitVar, dataclass, field
from typing import Protocol, runtime_checkable

import pytest
import svcs

from svcs_di import Inject, auto
from svcs_di.injectors import KeywordInjector
from svcs_di.auto import (
    FieldInfo,
    _create_field_info,
    get_field_infos,
    is_init_var,
    unwrap_init_var,
)


@dataclass
class Config:
    """Simple config service for testing."""

    value: int = 42


@dataclass
class Database:
    """Simple database service for testing."""

    host: str = "localhost"


@runtime_checkable
class ValueProvider(Protocol):
    """Protocol for value providers."""

    def get_value(self) -> int: ...


@dataclass
class SimpleValueProvider:
    """Simple implementation of ValueProvider."""

    value: int = 100

    def get_value(self) -> int:
        return self.value


def test_is_init_var_detects_init_var():
    """is_init_var() returns True for InitVar types."""
    assert is_init_var(InitVar[int]) is True
    assert is_init_var(InitVar[Config]) is True
    assert is_init_var(InitVar[Inject[Config]]) is True


def test_is_init_var_rejects_non_init_var():
    """is_init_var() returns False for non-InitVar types."""
    assert is_init_var(int) is False
    assert is_init_var(Config) is False
    assert is_init_var(Inject[Config]) is False
    assert is_init_var(None) is False


def test_unwrap_init_var_extracts_inner_type():
    """unwrap_init_var() extracts the inner type from InitVar[T]."""
    assert unwrap_init_var(InitVar[int]) is int
    assert unwrap_init_var(InitVar[Config]) is Config
    # For InitVar[Inject[T]], we get Inject[T]
    result = unwrap_init_var(InitVar[Inject[Config]])
    assert result is not None


def test_unwrap_init_var_returns_none_for_non_init_var():
    """unwrap_init_var() returns None for non-InitVar types."""
    assert unwrap_init_var(int) is None
    assert unwrap_init_var(Config) is None
    assert unwrap_init_var(Inject[Config]) is None


def test_basic_init_var_inject_resolution():
    """Basic InitVar[Inject[T]] resolution works end-to-end."""

    @dataclass
    class ServiceWithInitVar:
        derived_value: int = field(init=False)
        config: InitVar[Inject[Config]]

        def __post_init__(self, config: Config) -> None:
            self.derived_value = config.value * 2

    registry = svcs.Registry()
    registry.register_value(Config, Config(value=21))
    registry.register_factory(ServiceWithInitVar, auto(ServiceWithInitVar))

    container = svcs.Container(registry)
    service = container.get(ServiceWithInitVar)

    assert service.derived_value == 42
    assert not hasattr(service, "config")  # InitVar is not stored


def test_mixed_inject_and_init_var_inject():
    """Mix of regular Inject[T] and InitVar[Inject[T]] works correctly."""

    @dataclass
    class MixedService:
        db: Inject[Database]
        computed: int = field(init=False)
        config: InitVar[Inject[Config]]

        def __post_init__(self, config: Config) -> None:
            self.computed = config.value

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="testhost"))
    registry.register_value(Config, Config(value=99))
    registry.register_factory(MixedService, auto(MixedService))

    container = svcs.Container(registry)
    service = container.get(MixedService)

    assert service.db.host == "testhost"
    assert service.computed == 99
    assert not hasattr(service, "config")


def test_multiple_init_var_inject_fields():
    """Multiple InitVar[Inject[T]] fields work correctly."""

    @dataclass
    class MultiInitVarService:
        combined: int = field(init=False)
        config: InitVar[Inject[Config]]
        db: InitVar[Inject[Database]]

        def __post_init__(self, config: Config, db: Database) -> None:
            self.combined = config.value + len(db.host)

    registry = svcs.Registry()
    registry.register_value(Config, Config(value=100))
    registry.register_value(Database, Database(host="db"))
    registry.register_factory(MultiInitVarService, auto(MultiInitVarService))

    container = svcs.Container(registry)
    service = container.get(MultiInitVarService)

    assert service.combined == 102  # 100 + len("db")


def test_init_var_inject_with_protocol():
    """InitVar[Inject[Protocol]] works with protocol-based injection."""

    @dataclass
    class ProtocolInitVarService:
        stored_value: int = field(init=False)
        provider: InitVar[Inject[ValueProvider]]

        def __post_init__(self, provider: ValueProvider) -> None:
            self.stored_value = provider.get_value()

    registry = svcs.Registry()
    registry.register_value(ValueProvider, SimpleValueProvider(value=777))
    registry.register_factory(ProtocolInitVarService, auto(ProtocolInitVarService))

    container = svcs.Container(registry)
    service = container.get(ProtocolInitVarService)

    assert service.stored_value == 777


def test_init_var_inject_with_keyword_injector_override():
    """InitVar[Inject[T]] can be overridden via KeywordInjector kwargs."""

    @dataclass
    class OverridableService:
        stored_value: int = field(init=False)
        config: InitVar[Inject[Config]]

        def __post_init__(self, config: Config) -> None:
            self.stored_value = config.value

    registry = svcs.Registry()
    registry.register_value(Config, Config(value=1))

    container = svcs.Container(registry)
    injector = KeywordInjector(container=container)

    # Override the config with a different value
    service = injector(OverridableService, config=Config(value=999))

    assert service.stored_value == 999


def test_init_var_without_inject_not_resolved():
    """InitVar without Inject marker is not auto-resolved."""

    @dataclass
    class PlainInitVarService:
        stored: int = field(init=False)
        value: InitVar[int]

        def __post_init__(self, value: int) -> None:
            self.stored = value

    field_infos = get_field_infos(PlainInitVarService)
    init_var_field = next(f for f in field_infos if f.is_init_var)

    # Plain InitVar[int] should not be injectable
    assert init_var_field.is_injectable is False
    assert init_var_field.name == "value"


def test_get_field_infos_includes_init_var_fields():
    """get_field_infos() includes InitVar fields."""

    @dataclass
    class ServiceWithBoth:
        regular: Inject[Database]
        derived: int = field(init=False)
        init_only: InitVar[Inject[Config]]

    field_infos = get_field_infos(ServiceWithBoth)

    names = {f.name for f in field_infos}
    assert "regular" in names
    assert "init_only" in names
    # Note: field(init=False) fields are still in dataclasses.fields(), just not passed to __init__
    assert "derived" in names

    init_var_field = next(f for f in field_infos if f.name == "init_only")
    assert init_var_field.is_init_var is True
    assert init_var_field.is_injectable is True
    assert init_var_field.inner_type is Config

    # Regular fields should NOT be marked as init_var
    regular_field = next(f for f in field_infos if f.name == "regular")
    assert regular_field.is_init_var is False
    assert regular_field.is_injectable is True


def test_create_field_info_with_init_var_flag():
    """_create_field_info respects is_init_var_field parameter."""
    field_info = _create_field_info(
        name="test",
        type_hint=Inject[Config],
        has_default=False,
        default_value=None,
        is_init_var_field=True,
    )

    assert field_info.is_init_var is True
    assert field_info.is_injectable is True
    assert field_info.inner_type is Config


def test_create_field_info_defaults_init_var_false():
    """_create_field_info defaults is_init_var to False for backward compat."""
    field_info = _create_field_info(
        name="test",
        type_hint=Inject[Config],
        has_default=False,
        default_value=None,
    )

    assert field_info.is_init_var is False


def test_field_info_is_init_var_has_default():
    """FieldInfo.is_init_var has default value of False."""
    # Create FieldInfo with required fields
    info = FieldInfo(
        name="test",
        type_hint=int,
        is_injectable=False,
        is_resource=False,
        inner_type=None,
        is_protocol=False,
        has_default=False,
        default_value=None,
    )
    assert info.is_init_var is False


def test_init_var_inject_error_on_missing_registration():
    """InitVar[Inject[T]] raises error when T is not registered."""

    @dataclass
    class UnregisteredService:
        value: int = field(init=False)
        config: InitVar[Inject[Config]]

        def __post_init__(self, config: Config) -> None:
            self.value = config.value

    registry = svcs.Registry()
    # Config is NOT registered
    registry.register_factory(UnregisteredService, auto(UnregisteredService))

    container = svcs.Container(registry)

    with pytest.raises(svcs.exceptions.ServiceNotFoundError):
        container.get(UnregisteredService)


def test_init_var_field_has_no_default():
    """InitVar fields are detected as having no default."""

    @dataclass
    class ServiceWithInitVar:
        value: int = field(init=False)
        config: InitVar[Inject[Config]]

        def __post_init__(self, config: Config) -> None:
            self.value = config.value

    field_infos = get_field_infos(ServiceWithInitVar)
    init_var_field = next(f for f in field_infos if f.is_init_var)

    assert init_var_field.has_default is False
    assert init_var_field.default_value is None


def test_optional_with_fallback_pattern():
    """Test the recommended 'optional with fallback' pattern.

    This pattern uses `T | None = None` for derived fields, allowing:
    - Auto-resolution when None (computed from InitVar dependency)
    - Manual override via kwargs
    """

    @dataclass
    class Greeting:
        users: InitVar[Inject[Database]]  # Using Database as a stand-in
        current_name: str | None = None

        def __post_init__(self, users: Database) -> None:
            if self.current_name is None:
                self.current_name = f"User from {users.host}"

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="example.com"))
    registry.register_factory(Greeting, auto(Greeting))

    container = svcs.Container(registry)

    # Auto-resolution: current_name computed from Database
    greeting1 = container.get(Greeting)
    assert greeting1.current_name == "User from example.com"

    # Manual override via KeywordInjector
    injector = KeywordInjector(container=container)
    greeting2 = injector(Greeting, current_name="Custom Name")
    assert greeting2.current_name == "Custom Name"


def test_optional_with_fallback_partial_override():
    """Test partial override - some fields auto-resolved, some overridden."""

    @dataclass
    class UserProfile:
        context: InitVar[Inject[Database]]
        username: str | None = None
        host: str | None = None

        def __post_init__(self, context: Database) -> None:
            if self.username is None:
                self.username = "default_user"
            if self.host is None:
                self.host = context.host

    registry = svcs.Registry()
    registry.register_value(Database, Database(host="prod.example.com"))

    container = svcs.Container(registry)
    injector = KeywordInjector(container=container)

    # Override username only, let host be computed
    profile = injector(UserProfile, username="alice")
    assert profile.username == "alice"  # Overridden
    assert profile.host == "prod.example.com"  # Computed from context
