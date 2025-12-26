"""
Minimal svcs.auto() helper for automatic dependency injection.

This module provides a thin layer on top of svcs for automatic dependency resolution
based on type hints, with explicit opt-in via the Injectable[T] marker.

Requires Python 3.14+ for PEP 695 generic syntax (class Generic[T]:) and modern
type parameter features.
"""

import dataclasses
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import (
    Any,
    NamedTuple,
    Protocol,
    get_args,
    get_origin,
    get_type_hints,
)

import svcs

log = logging.getLogger("svcs_di")


# ============================================================================
# Exceptions
# ============================================================================


class TypeHintResolutionError(Exception):
    """Failed to resolve type hints for dependency injection target."""


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

    def __call__[T](self, target: type[T]) -> T:
        """Construct an instance of target with dependencies resolved."""
        ...


class AsyncInjector(Protocol):
    """Protocol for async dependency injector."""

    async def __call__[T](self, target: type[T]) -> T:
        """Construct an instance of target with async dependencies resolved."""
        ...


@dataclasses.dataclass(frozen=True)
class DefaultInjector:
    """
    Default dependency injector. Resolves Injectable[T] fields from container.

    Uses two-tier precedence for value resolution:
    1. container.get(T) or container.get_abstract(T) for Injectable[T] fields
    2. Default values from parameter/field definition

    For kwargs override support, use KeywordInjector from svcs_di.injectors.
    """

    container: svcs.Container

    def __call__[T](self, target: type[T]) -> T:
        """Inject dependencies and construct target instance."""
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

    For kwargs override support, use KeywordAsyncInjector from svcs_di.injectors.
    """

    container: svcs.Container

    async def __call__[T](self, target: type[T]) -> T:
        """Async inject dependencies and construct target instance."""
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

    Type Checking:
    --------------
    At runtime, this is a marker class. At type-checking time, the accompanying
    auto.pyi stub file provides `type Injectable[T] = T`, making type checkers
    understand that Injectable[Greeting] has all attributes of Greeting.

    This dual-representation approach (runtime marker + type stub) enables:
    - Runtime detection via get_origin(Injectable[T])
    - Type-safe attribute access without cast()

    Example:
        @dataclass
        class WelcomeService:
            greeting: Injectable[Greeting]  # Type checkers see: Greeting
            database: Injectable[Database]  # Type checkers see: Database

        service = injector(WelcomeService)
        service.greeting.greet("World")  # ✓ Type checker knows about greet()
        service.database.connect()       # ✓ Type checker knows about connect()
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
        assert isinstance(target, type)
        return _get_dataclass_field_infos(target)
    else:
        return _get_callable_field_infos(target)


def _get_dataclass_field_infos(target: type) -> list[FieldInfo]:
    """Extract field information from a dataclass."""
    type_hints: dict[str, Any] = {}
    try:
        type_hints = get_type_hints(target)
    except NameError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for dataclass {target.__name__!r}: "
            f"undefined name in annotation. This typically means a forward reference "
            f"is not quoted or the imported type is missing. Original error: {e}"
        ) from e
    except AttributeError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for dataclass {target.__name__!r}: "
            f"missing attribute. This typically means an annotation references an "
            f"attribute that doesn't exist. Original error: {e}"
        ) from e
    except TypeError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for dataclass {target.__name__!r}: "
            f"type error in annotation. Original error: {e}"
        ) from e

    # dataclasses.fields() expects DataclassInstance, but we've already validated
    # target is a dataclass via is_dataclass() check. Type checkers can't infer this.
    fields = dataclasses.fields(target)  # type: ignore[arg-type]

    field_infos = []
    for field in fields:
        type_hint = type_hints.get(field.name)

        has_default = (
            field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING
        )
        default_value = (
            field.default
            if field.default is not dataclasses.MISSING
            else (
                field.default_factory
                if field.default_factory is not dataclasses.MISSING
                else None
            )
        )

        field_infos.append(
            _create_field_info(field.name, type_hint, has_default, default_value)
        )

    return field_infos


def _get_callable_field_infos(target: Callable) -> list[FieldInfo]:
    """Extract parameter information from a callable."""
    callable_name = getattr(target, '__name__', repr(target))
    sig = None
    try:
        sig = inspect.signature(target, eval_str=True)
    except NameError as e:
        # Try without eval_str as forward references might not resolve
        try:
            sig = inspect.signature(target)
        except (ValueError, TypeError) as e2:
            raise TypeHintResolutionError(
                f"Cannot get signature for callable {callable_name!r}: {e2}. "
                f"This typically means the callable is a built-in or C extension "
                f"without proper introspection support."
            ) from e2
    except (ValueError, TypeError) as e:
        raise TypeHintResolutionError(
            f"Cannot get signature for callable {callable_name!r}: {e}. "
            f"This typically means the callable is a built-in or C extension "
            f"without proper introspection support."
        ) from e

    if sig is None:
        return []

    type_hints: dict[str, Any] = {}
    try:
        type_hints = get_type_hints(target)
    except NameError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for callable {callable_name!r}: "
            f"undefined name in annotation. This typically means a forward reference "
            f"is not quoted or the imported type is missing. Original error: {e}"
        ) from e
    except AttributeError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for callable {callable_name!r}: "
            f"missing attribute. This typically means an annotation references an "
            f"attribute that doesn't exist. Original error: {e}"
        ) from e
    except TypeError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for callable {callable_name!r}: "
            f"type error in annotation. Original error: {e}"
        ) from e

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

    def factory(svcs_container: svcs.Container, **kwargs: object) -> T:
        """Factory function that resolves dependencies and constructs target."""
        try:
            injector = svcs_container.get(DefaultInjector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultInjector(container=svcs_container)

        return injector(target)

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

    async def async_factory(svcs_container: svcs.Container, **kwargs: object) -> T:
        """Async factory function that resolves dependencies and constructs target."""
        try:
            injector = await svcs_container.aget(DefaultAsyncInjector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultAsyncInjector(container=svcs_container)

        return await injector(target)

    return async_factory
