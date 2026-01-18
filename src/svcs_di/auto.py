"""
Minimal svcs.auto() helper for automatic dependency injection.

This module provides a thin layer on top of svcs for automatic dependency resolution
based on type hints, with explicit opt-in via the Inject[T] marker.

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
    cast,
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
type InjectionTarget[T] = type[T] | Callable[..., T]
type AsyncInjectionTarget[T] = type[T] | Callable[..., Awaitable[T]]

# Resolution result: (found, value) where found indicates if resolution succeeded
type ResolutionResult = tuple[bool, Any]


# ============================================================================
# Injector Protocols and Implementations
# ============================================================================


type FieldResolver = Callable[[FieldInfo, svcs.Container], ResolutionResult]


def _build_injected_kwargs(
    field_infos: list[FieldInfo],
    container: svcs.Container,
    resolver: FieldResolver,
) -> dict[str, Any]:
    """
    Build resolved kwargs dictionary for dependency injection.

    Args:
        field_infos: List of field information to resolve
        container: The svcs container to resolve dependencies from
        resolver: Function to resolve each field value

    Returns:
        Dictionary of resolved kwargs ready to pass to target callable
    """
    resolved_kwargs: dict[str, Any] = {}
    for field_info in field_infos:
        has_value, value = resolver(field_info, container)
        if has_value:
            resolved_kwargs[field_info.name] = value
    return resolved_kwargs


async def _build_injected_kwargs_async(
    field_infos: list[FieldInfo], container: svcs.Container
) -> dict[str, Any]:
    """Build resolved kwargs dictionary for async dependency injection."""
    resolved_kwargs: dict[str, Any] = {}
    for field_info in field_infos:
        has_value, value = await _resolve_field_value_async(field_info, container)
        if has_value:
            resolved_kwargs[field_info.name] = value
    return resolved_kwargs


class Injector(Protocol):
    """Protocol for dependency injector that constructs instances with resolved dependencies."""

    def __call__[T](self, target: InjectionTarget[T], **kwargs: Any) -> T:
        """Construct an instance of target with dependencies resolved.

        Args:
            target: A class or callable to invoke with resolved dependencies
            **kwargs: Additional keyword arguments to pass through

        Returns:
            Result of calling target with resolved dependencies
        """
        ...


class AsyncInjector(Protocol):
    """Protocol for async dependency injector."""

    async def __call__[T](self, target: AsyncInjectionTarget[T], **kwargs: Any) -> T:
        """Construct an instance of target with async dependencies resolved.

        Args:
            target: A class or async callable to invoke with resolved dependencies
            **kwargs: Additional keyword arguments to pass through

        Returns:
            Result of calling target with resolved dependencies
        """
        ...


@dataclasses.dataclass(frozen=True)
class DefaultInjector:
    """
    Default dependency injector. Resolves Inject[T] fields from container.

    Uses two-tier precedence for value resolution:
    1. container.get(T) or container.get_abstract(T) for Inject[T] fields
    2. Default values from parameter/field definition

    For kwargs override support, use KeywordInjector from svcs_di.injectors.
    """

    container: svcs.Container

    def __call__[T](self, target: InjectionTarget[T], **kwargs: Any) -> T:
        """Inject dependencies and construct target instance or call function.

        Args:
            target: A class or callable to invoke with resolved dependencies
            **kwargs: Additional keyword arguments (not used in DefaultInjector)

        Returns:
            Result of calling target with resolved dependencies
        """
        field_infos = get_field_infos(target)
        resolved_kwargs = _build_injected_kwargs(
            field_infos, self.container, _resolve_field_value
        )
        return target(**resolved_kwargs)


@dataclasses.dataclass(frozen=True)
class DefaultAsyncInjector:
    """
    Default async dependency injector. Like DefaultInjector but for async dependencies.

    Uses two-tier precedence for value resolution:
    1. container.aget(T) or container.aget_abstract(T) for Inject[T] fields
    2. default values from parameter/field definition

    For kwargs override support, use KeywordAsyncInjector from svcs_di.injectors.
    """

    container: svcs.Container

    async def __call__[T](self, target: AsyncInjectionTarget[T], **kwargs: Any) -> T:
        """Async inject dependencies and construct target instance or call async function.

        Args:
            target: A class or async callable to invoke with resolved dependencies
            **kwargs: Additional keyword arguments (not used in DefaultAsyncInjector)

        Returns:
            Result of calling target with resolved dependencies
        """
        field_infos = get_field_infos(target)
        resolved_kwargs = await _build_injected_kwargs_async(
            field_infos, self.container
        )

        result = target(**resolved_kwargs)
        # If target is an async callable, await the result
        if inspect.iscoroutinefunction(target):
            return await cast(Awaitable[T], result)
        return cast(T, result)


# ============================================================================
# Inject Marker
# ============================================================================


type Inject[T] = T
"""
Marker type for dependency injection.

Use Inject[T] to mark a parameter/field that should be automatically
resolved from the svcs container. Only parameters marked with Inject
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
Using Python 3.14's PEP 695 type alias syntax (`type Inject[T] = T`), this
creates a TypeAliasType that is both:
- Detectable at runtime via get_origin(Inject[T])
- Transparent to type checkers (they see T directly)

This eliminates the need for a separate .pyi stub file while providing
full type safety and runtime introspection capabilities.

Example:
    @dataclass
    class WelcomeService:
        greeting: Inject[Greeting]  # Type checkers see: Greeting
        database: Inject[Database]  # Type checkers see: Database

    service = injector(WelcomeService)
    service.greeting.greet("World")  # ✓ Type checker knows about greet()
    service.database.connect()       # ✓ Type checker knows about connect()
"""


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
    """Check if a type hint is Inject[T]."""
    return get_origin(type_hint) is Inject


def extract_inner_type(type_hint: Any) -> type | None:
    """Extract the inner type from Inject[T]."""
    if not is_injectable(type_hint):
        return None
    return args[0] if (args := get_args(type_hint)) else None


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
    and determining Inject, protocol, and default value information.
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


def _safe_get_type_hints(target: Any, context_name: str) -> dict[str, Any]:
    """
    Get type hints with unified error handling.

    Args:
        target: The target to get type hints from (class or callable)
        context_name: Name to use in error messages (e.g., "dataclass Foo" or "callable bar")

    Returns:
        Dictionary of type hints

    Raises:
        TypeHintResolutionError: If type hints cannot be resolved
    """
    try:
        return get_type_hints(target)
    except NameError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for {context_name}: "
            f"undefined name in annotation. This typically means a forward reference "
            f"is not quoted or the imported type is missing. Original error: {e}"
        ) from e
    except AttributeError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for {context_name}: "
            f"missing attribute. This typically means an annotation references an "
            f"attribute that doesn't exist. Original error: {e}"
        ) from e
    except TypeError as e:
        raise TypeHintResolutionError(
            f"Cannot resolve type hints for {context_name}: "
            f"type error in annotation. Original error: {e}"
        ) from e


def _get_dataclass_field_infos(target: type) -> list[FieldInfo]:
    """Extract field information from a dataclass."""
    type_hints = _safe_get_type_hints(target, f"dataclass {target.__name__!r}")

    # dataclasses.fields() expects DataclassInstance. We've validated target is a
    # dataclass via is_dataclass() check in get_field_infos(), but type checkers
    # can't narrow based on that runtime check.
    fields = dataclasses.fields(cast(Any, target))

    field_infos = []
    for field in fields:
        type_hint = type_hints.get(field.name)

        has_default = (
            field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING
        )
        match (field.default, field.default_factory):
            case (d, _) if d is not dataclasses.MISSING:
                default_value = d
            case (_, f) if f is not dataclasses.MISSING:
                default_value = f
            case _:
                default_value = None

        field_infos.append(
            _create_field_info(field.name, type_hint, has_default, default_value)
        )

    return field_infos


def _get_safe_signature(
    target: Callable, callable_name: str
) -> inspect.Signature | None:
    """
    Get signature for a callable with unified error handling.

    Tries with eval_str=True first (to resolve string annotations), then falls back
    to eval_str=False if forward references fail to resolve.

    Args:
        target: The callable to get signature from
        callable_name: Name to use in error messages

    Returns:
        The signature object, or None if signature cannot be obtained

    Raises:
        TypeHintResolutionError: If signature cannot be obtained due to introspection issues
    """
    try:
        return inspect.signature(target, eval_str=True)
    except NameError:
        # Try without eval_str as forward references might not resolve
        try:
            return inspect.signature(target)
        except (ValueError, TypeError) as e:
            raise TypeHintResolutionError(
                f"Cannot get signature for callable {callable_name!r}: {e}. "
                f"This typically means the callable is a built-in or C extension "
                f"without proper introspection support."
            ) from e
    except (ValueError, TypeError) as e:
        raise TypeHintResolutionError(
            f"Cannot get signature for callable {callable_name!r}: {e}. "
            f"This typically means the callable is a built-in or C extension "
            f"without proper introspection support."
        ) from e


def _get_callable_field_infos(target: Callable) -> list[FieldInfo]:
    """Extract parameter information from a callable."""
    callable_name = getattr(target, "__name__", repr(target))
    sig = _get_safe_signature(target, callable_name)

    if sig is None:
        return []

    type_hints = _safe_get_type_hints(target, f"callable {callable_name!r}")

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
) -> ResolutionResult:
    """
    Resolve a single field's value using two-tier precedence.

    Two-tier precedence:
    1. container.get(T) or container.get_abstract(T) for Inject[T] fields
    2. default values from field definition
    """
    # Tier 1: Inject from container
    if field_info.is_injectable:
        inner_type = field_info.inner_type
        if inner_type is None:
            raise TypeError(f"Inject field '{field_info.name}' has no inner type")

        # Check for Container injection first
        if inner_type is svcs.Container:
            return True, container

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
) -> ResolutionResult:
    """
    Async version of _resolve_field_value using two-tier precedence.

    Two-tier precedence:
    1. container.aget(T) or container.aget_abstract(T) for Inject[T] fields
    2. default values from field definition
    """
    # Tier 1: Inject from container (async)
    if field_info.is_injectable:
        inner_type = field_info.inner_type
        if inner_type is None:
            raise TypeError(f"Inject field '{field_info.name}' has no inner type")

        # Check for Container injection first
        if inner_type is svcs.Container:
            return True, container

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
    that automatically resolves Inject[T] dependencies from the container.

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
            injector = svcs_container.get(Injector)
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
