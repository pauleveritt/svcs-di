"""
Minimal svcs.auto() helper for automatic dependency injection.

This module provides a thin layer on top of svcs for automatic dependency resolution
based on type hints, with explicit opt-in via the Injectable[T] marker.
"""

import dataclasses
import inspect
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import (
    Any,
    NamedTuple,
    Protocol,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import svcs

# ============================================================================
# Type Aliases
# ============================================================================


type SvcsFactory[T] = Callable[..., T]
type AsyncSvcsFactory[T] = Callable[..., Awaitable[T]]


# ============================================================================
# Injector Protocols and Implementations
# ============================================================================


class Injector(Protocol):
    """Protocol for dependency injector that constructs instances with resolved dependencies."""

    def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """Construct an instance of target with dependencies resolved."""
        ...


class AsyncInjector(Protocol):
    """Protocol for async dependency injector."""

    async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """Construct an instance of target with async dependencies resolved."""
        ...


@dataclasses.dataclass(frozen=True)
class DefaultInjector:
    """
    Default dependency injector. Resolves Injectable[T] fields from container.

    Uses two-tier precedence for value resolution:
    1. container.get(T) or container.get_abstract(T) for Injectable[T] fields
    2. default values from parameter/field definition

    Note: **kwargs is accepted for protocol compliance but is ignored.
    For kwargs override support, use KeywordInjector from svcs_di.injectors.
    """

    container: svcs.Container

    def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Inject dependencies and construct target instance.

        Note: kwargs are ignored in DefaultInjector. For kwargs override support,
        use KeywordInjector from svcs_di.injectors.
        """
        field_infos = get_field_infos(target)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = _resolve_field_value(field_info, self.container)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


@dataclasses.dataclass(frozen=True)
class DefaultAsyncInjector:
    """
    Default async dependency injector. Like DefaultInjector but for async dependencies.

    Uses two-tier precedence for value resolution:
    1. container.aget(T) or container.aget_abstract(T) for Injectable[T] fields
    2. default values from parameter/field definition

    Note: **kwargs is accepted for protocol compliance but is ignored.
    For kwargs override support, use KeywordAsyncInjector from svcs_di.injectors.
    """

    container: svcs.Container

    async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Async inject dependencies and construct target instance.

        Note: kwargs are ignored in DefaultAsyncInjector. For kwargs override support,
        use KeywordAsyncInjector from svcs_di.injectors.
        """
        field_infos = get_field_infos(target)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await _resolve_field_value_async(
                field_info, self.container
            )
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


# ============================================================================
# Injectable Marker
# ============================================================================


class Injectable[T]:
    """
    Marker type for dependency injection.

    Use Injectable[T] to mark a parameter/field that should be automatically
    resolved from the svcs container. Only parameters marked with Injectable
    will be injected.

    Two-tier precedence for value resolution (DefaultInjector):
    1. container.get(T) or container.get_abstract(T) for protocols
    2. default values from parameter/field definition

    For kwargs override support (three-tier precedence), use KeywordInjector:
    1. kwargs passed to injector (highest priority)
    2. container.get(T) or container.get_abstract(T) for protocols
    3. default values from parameter/field definition (lowest priority)
    """

    __slots__ = ()


class FieldInfo(NamedTuple):
    """Field metadata for both dataclass fields and function parameters."""

    name: str
    type_hint: Any
    is_injectable: bool
    inner_type: type | None
    is_protocol: bool
    has_default: bool
    default_value: Any


# ============================================================================
# Helper Functions
# ============================================================================


def is_injectable(type_hint: Any) -> bool:
    """Check if a type hint is Injectable[T]."""
    return get_origin(type_hint) is Injectable


def extract_inner_type(type_hint: Any) -> type | None:
    """Extract the inner type from Injectable[T]."""
    if not is_injectable(type_hint):
        return None
    args = get_args(type_hint)
    return args[0] if args else None


def is_protocol_type(cls: type | Any) -> bool:
    """Check if a type is a Protocol."""
    return isinstance(cls, type) and getattr(cls, "_is_protocol", False)


def _create_field_info(
    name: str,
    type_hint: Any,
    has_default: bool,
    default_value: Any,
) -> FieldInfo:
    """
    Create a FieldInfo instance from field/parameter metadata.

    This helper encapsulates the common logic for processing type hints
    and determining Injectable, protocol, and default value information.
    """
    injectable = is_injectable(type_hint)
    inner = extract_inner_type(type_hint) if injectable else None
    protocol = is_protocol_type(inner) if inner else False

    return FieldInfo(
        name=name,
        type_hint=type_hint,
        is_injectable=injectable,
        inner_type=inner,
        is_protocol=protocol,
        has_default=has_default,
        default_value=default_value,
    )


def get_field_infos(target: type | Callable) -> list[FieldInfo]:
    """Extract field information from a dataclass or callable."""
    if dataclasses.is_dataclass(target):
        return _get_dataclass_field_infos(cast(type, target))
    else:
        return _get_callable_field_infos(target)


def _get_dataclass_field_infos(target: type) -> list[FieldInfo]:
    """Extract field information from a dataclass."""
    type_hints: dict[str, Any] = {}
    with suppress(Exception):
        type_hints = get_type_hints(target)

    fields = dataclasses.fields(cast(Any, target))

    field_infos = []
    for field in fields:
        type_hint = type_hints.get(field.name)

        has_default = (
            field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING
        )  # type: ignore[misc]
        default_value = (
            field.default
            if field.default is not dataclasses.MISSING
            else (
                field.default_factory
                if field.default_factory is not dataclasses.MISSING
                else None
            )  # type: ignore[misc]
        )

        field_infos.append(
            _create_field_info(field.name, type_hint, has_default, default_value)
        )

    return field_infos


def _get_callable_field_infos(target: Callable) -> list[FieldInfo]:
    """Extract parameter information from a callable."""
    sig = None
    with suppress(Exception):
        sig = inspect.signature(target, eval_str=True)
    if sig is None:
        with suppress(Exception):
            sig = inspect.signature(target)
    if sig is None:
        return []

    type_hints: dict[str, Any] = {}
    with suppress(Exception):
        type_hints = get_type_hints(target)

    field_infos = []
    for param_name, param in sig.parameters.items():
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        type_hint = type_hints.get(param_name)
        has_default = param.default is not inspect.Parameter.empty
        default_value = param.default if has_default else None

        field_infos.append(
            _create_field_info(param_name, type_hint, has_default, default_value)
        )

    return field_infos


def _resolve_field_value(
    field_info: FieldInfo, container: svcs.Container
) -> tuple[bool, Any]:
    """
    Resolve a single field's value using two-tier precedence.

    Two-tier precedence:
    1. container.get(T) or container.get_abstract(T) for Injectable[T] fields
    2. default values from field definition
    """
    # Tier 1: Injectable from container
    if field_info.is_injectable:
        inner_type = field_info.inner_type
        if inner_type is None:
            raise TypeError(f"Injectable field '{field_info.name}' has no inner type")

        if field_info.is_protocol:
            value = container.get_abstract(inner_type)
        else:
            value = container.get(inner_type)

        return True, value

    # Tier 2: default value
    if field_info.has_default:
        default_val = field_info.default_value
        # Call default_factory if it's a callable (bound method from dataclass field)
        if callable(default_val) and hasattr(default_val, "__self__"):
            return True, default_val()
        return True, default_val

    return False, None


async def _resolve_field_value_async(
    field_info: FieldInfo, container: svcs.Container
) -> tuple[bool, Any]:
    """
    Async version of _resolve_field_value using two-tier precedence.

    Two-tier precedence:
    1. container.aget(T) or container.aget_abstract(T) for Injectable[T] fields
    2. default values from field definition
    """
    # Tier 1: Injectable from container (async)
    if field_info.is_injectable:
        inner_type = field_info.inner_type
        if inner_type is None:
            raise TypeError(f"Injectable field '{field_info.name}' has no inner type")

        if field_info.is_protocol:
            value = await container.aget_abstract(inner_type)
        else:
            value = await container.aget(inner_type)

        return True, value

    # Tier 2: default value
    if field_info.has_default:
        default_val = field_info.default_value
        # Call default_factory if it's a callable (bound method from dataclass field)
        if callable(default_val) and hasattr(default_val, "__self__"):
            return True, default_val()
        return True, default_val

    return False, None


# ============================================================================
# Public API
# ============================================================================


def auto[T](target: type[T]) -> SvcsFactory[T]:
    """
    Create a factory function for automatic dependency injection.

    Returns a factory function compatible with svcs.Registry.register_factory()
    that automatically resolves Injectable[T] dependencies from the container.

    DefaultInjector uses two-tier precedence (container.get, then defaults).
    For kwargs override support, register KeywordInjector as a custom injector:
        from svcs_di.injectors import KeywordInjector
        registry.register_factory(DefaultInjector, lambda c: KeywordInjector(container=c))

    To use a custom injector:
        registry.register_factory(DefaultInjector, lambda c: MyCustomInjector(container=c))
    """

    def factory(svcs_container: svcs.Container, **kwargs: Any) -> T:
        """Factory function that resolves dependencies and constructs target."""
        try:
            injector = svcs_container.get(DefaultInjector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultInjector(container=svcs_container)

        return injector(target, **kwargs)

    return factory


def auto_async[T](target: type[T]) -> AsyncSvcsFactory[T]:
    """
    Create an async factory function for automatic dependency injection.

    Like auto() but returns an async factory for use with async dependencies.

    DefaultAsyncInjector uses two-tier precedence (container.aget, then defaults).
    For kwargs override support, register KeywordAsyncInjector as a custom injector:
        from svcs_di.injectors import KeywordAsyncInjector
        registry.register_factory(DefaultAsyncInjector, lambda c: KeywordAsyncInjector(container=c))
    """

    async def async_factory(svcs_container: svcs.Container, **kwargs: Any) -> T:
        """Async factory function that resolves dependencies and constructs target."""
        try:
            injector = await svcs_container.aget(DefaultAsyncInjector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultAsyncInjector(container=svcs_container)

        return await injector(target, **kwargs)

    return async_factory
