"""Tests for Injectable marker and type introspection."""

from dataclasses import dataclass
from typing import Protocol


from svcs_di.auto import (
    Injectable,
    extract_inner_type,
    get_field_infos,
    is_injectable,
    is_protocol_type,
)


class GreeterProtocol(Protocol):
    """A protocol for testing."""

    def greet(self, name: str) -> str: ...


class Database:
    """A concrete class for testing."""


@dataclass
class Config:
    """A dataclass for testing."""

    host: str = "localhost"


def test_injectable_wraps_type():
    """Injectable[T] can wrap any type T."""
    # Injectable is just a type alias, so we test type extraction
    assert extract_inner_type(Injectable[Database]) is Database
    assert extract_inner_type(Injectable[str]) is str
    assert extract_inner_type(Injectable[GreeterProtocol]) is GreeterProtocol


def test_is_injectable_detection():
    """Detect if a type is wrapped in Injectable."""
    assert is_injectable(Injectable[Database]) is True
    assert is_injectable(Database) is False
    assert is_injectable(str) is False


def test_protocol_detection():
    """Protocol types are correctly identified."""
    assert is_protocol_type(GreeterProtocol) is True
    assert is_protocol_type(Database) is False
    assert is_protocol_type(str) is False


def test_extract_inner_type_from_injectable():
    """Extract inner type from Injectable[T]."""
    inner = extract_inner_type(Injectable[Database])
    assert inner is Database

    inner_protocol = extract_inner_type(Injectable[GreeterProtocol])
    assert inner_protocol is GreeterProtocol


def test_get_field_infos_dataclass():
    """Extract field info from dataclass."""

    @dataclass
    class TestClass:
        db: Injectable[Database]
        config: Injectable[Config]
        timeout: int = 30

    fields = get_field_infos(TestClass)
    assert len(fields) == 3

    db_field = next(f for f in fields if f.name == "db")
    assert db_field.is_injectable is True
    assert db_field.inner_type is Database
    assert db_field.has_default is False

    timeout_field = next(f for f in fields if f.name == "timeout")
    assert timeout_field.is_injectable is False
    assert timeout_field.has_default is True
    assert timeout_field.default_value == 30


def test_get_field_infos_function():
    """Extract parameter info from function."""

    def create_service(
        db: Injectable[Database],
        greeter: Injectable[GreeterProtocol],
        timeout: int = 30,
    ):
        pass

    fields = get_field_infos(create_service)
    assert len(fields) == 3

    db_field = next(f for f in fields if f.name == "db")
    assert db_field.is_injectable is True
    assert db_field.inner_type is Database
    assert db_field.is_protocol is False

    greeter_field = next(f for f in fields if f.name == "greeter")
    assert greeter_field.is_injectable is True
    assert greeter_field.inner_type is GreeterProtocol
    assert greeter_field.is_protocol is True

    timeout_field = next(f for f in fields if f.name == "timeout")
    assert timeout_field.is_injectable is False
    assert timeout_field.has_default is True


def test_field_info_with_no_type_hint():
    """Handle parameters without type hints."""

    def func(param):
        pass

    fields = get_field_infos(func)
    assert len(fields) == 1
    param_field = fields[0]
    assert param_field.name == "param"
    assert param_field.is_injectable is False
    assert param_field.type_hint is None


def test_dataclass_with_default_factory():
    """Handle dataclass fields with default_factory."""
    from dataclasses import field

    @dataclass
    class ServiceWithFactory:
        items: list[str] = field(default_factory=list)
        db: Injectable[Database] = field(default=None)  # type: ignore[assignment]

    fields = get_field_infos(ServiceWithFactory)
    assert len(fields) == 2

    items_field = next(f for f in fields if f.name == "items")
    assert items_field.has_default is True
    assert callable(items_field.default_value)

    db_field = next(f for f in fields if f.name == "db")
    assert db_field.is_injectable is True


def test_multiple_injectable_dependencies():
    """Handle multiple Injectable dependencies in single class."""

    @dataclass
    class MultiDepService:
        db: Injectable[Database]
        config: Injectable[Config]
        greeter: Injectable[GreeterProtocol]
        timeout: int = 30

    fields = get_field_infos(MultiDepService)
    injectable_fields = [f for f in fields if f.is_injectable]

    assert len(injectable_fields) == 3
    assert all(f.inner_type is not None for f in injectable_fields)


def test_mixed_injectable_and_required_params():
    """Handle mix of injectable, required, and optional parameters."""

    @dataclass
    class MixedService:
        db: Injectable[Database]  # Injectable, no default
        required_name: str  # Required, not injectable
        optional_timeout: int = 30  # Optional, not injectable
        optional_config: Injectable[Config] = None  # type: ignore[assignment]  # Injectable with default

    fields = get_field_infos(MixedService)
    assert len(fields) == 4

    # Check injectable without default
    db_field = next(f for f in fields if f.name == "db")
    assert db_field.is_injectable is True
    assert db_field.has_default is False

    # Check required non-injectable
    name_field = next(f for f in fields if f.name == "required_name")
    assert name_field.is_injectable is False
    assert name_field.has_default is False

    # Check optional non-injectable
    timeout_field = next(f for f in fields if f.name == "optional_timeout")
    assert timeout_field.is_injectable is False
    assert timeout_field.has_default is True

    # Check optional injectable
    config_field = next(f for f in fields if f.name == "optional_config")
    assert config_field.is_injectable is True
    assert config_field.has_default is True
