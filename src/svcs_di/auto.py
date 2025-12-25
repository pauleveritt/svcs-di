"""
Minimal svcs.auto() helper for automatic dependency injection.

This module provides a thin layer on top of svcs for automatic dependency resolution
based on type hints, with explicit opt-in via the Injectable[T] marker.

For complex initialization scenarios, classes can define a __svcs__ classmethod as
an escape hatch to take full control of construction. This is useful when automatic
field injection is insufficient for validation, conditional dependencies, or complex
initialization logic.
"""

import dataclasses
import inspect
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import (
    Any,
    NamedTuple,
    Protocol,
    Self,
    TypeGuard,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import svcs

# ============================================================================
# Type Guards and Aliases
# ============================================================================


def is_concrete_type(obj: type | None) -> TypeGuard[type]:
    """Type guard to narrow type | None to type."""
    return obj is not None


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


@dataclasses.dataclass
class _BaseInjector:
    """Shared logic for sync and async injectors."""

    container: svcs.Container

    def _validate_kwargs(
        self, target: type, field_infos: list["FieldInfo"], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )


@dataclasses.dataclass
class DefaultInjector(_BaseInjector):
    """Default dependency injector. Resolves Injectable[T] fields from container."""

    def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """Inject dependencies and construct target instance."""
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = _resolve_field_value(field_info, self.container, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


@dataclasses.dataclass
class DefaultAsyncInjector(_BaseInjector):
    """Default async dependency injector. Like DefaultInjector but for async dependencies."""

    async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """Inject async dependencies and construct target instance."""
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await _resolve_field_value_async(
                field_info, self.container, kwargs
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

    Three-tier precedence for value resolution:
    1. kwargs passed to factory (highest) - override everything
    2. container.get(T) or container.get_abstract(T) for protocols
    3. default values from parameter/field definition
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
        injectable = is_injectable(type_hint)
        inner = extract_inner_type(type_hint) if injectable else None
        protocol = is_protocol_type(inner) if inner else False

        has_default = field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING  # type: ignore[misc]
        default_value = (
            field.default
            if field.default is not dataclasses.MISSING
            else (field.default_factory if field.default_factory is not dataclasses.MISSING else None)  # type: ignore[misc]
        )

        field_infos.append(
            FieldInfo(
                name=field.name,
                type_hint=type_hint,
                is_injectable=injectable,
                inner_type=inner,
                is_protocol=protocol,
                has_default=has_default,
                default_value=default_value,
            )
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
        injectable = is_injectable(type_hint)
        inner = extract_inner_type(type_hint) if injectable else None
        protocol = is_protocol_type(inner) if inner else False

        has_default = param.default is not inspect.Parameter.empty
        default_value = param.default if has_default else None

        field_infos.append(
            FieldInfo(
                name=param_name,
                type_hint=type_hint,
                is_injectable=injectable,
                inner_type=inner,
                is_protocol=protocol,
                has_default=has_default,
                default_value=default_value,
            )
        )

    return field_infos


def _resolve_field_value(
    field_info: FieldInfo, container: svcs.Container, kwargs: dict[str, Any]
) -> tuple[bool, Any]:
    """Resolve a single field's value using three-tier precedence."""
    field_name = field_info.name

    # Tier 1: kwargs
    if field_name in kwargs:
        return (True, kwargs[field_name])

    # Tier 2: Injectable from container
    if field_info.is_injectable:
        inner_type = field_info.inner_type
        if inner_type is None:
            raise TypeError(f"Injectable field '{field_name}' has no inner type")
        else:
            if field_info.is_protocol:
                value = container.get_abstract(inner_type)
            else:
                value = container.get(inner_type)

            return True, value

    # Tier 3: default value
    if field_info.has_default:
        default_val = field_info.default_value
        if callable(default_val) and hasattr(default_val, "__self__"):
            return True, default_val()
        else:
            return True, default_val

    return (False, None)


async def _resolve_field_value_async(
    field_info: FieldInfo, container: svcs.Container, kwargs: dict[str, Any]
) -> tuple[bool, Any]:
    """Async version of _resolve_field_value."""
    field_name = field_info.name

    # Tier 1: kwargs
    if field_name in kwargs:
        return (True, kwargs[field_name])

    # Tier 2: Injectable from container (async)
    if field_info.is_injectable:
        inner_type = field_info.inner_type
        if inner_type is None:
            raise TypeError(f"Injectable field '{field_name}' has no inner type")
        else:
            if field_info.is_protocol:
                value = await container.aget_abstract(inner_type)
            else:
                value = await container.aget(inner_type)

            return True, value

    # Tier 3: default value
    if field_info.has_default:
        default_val = field_info.default_value
        if callable(default_val) and hasattr(default_val, "__self__"):
            return True, default_val()
        else:
            return True, default_val

    return (False, None)


def _validate_svcs_method(target: type, svcs_method: Any) -> None:
    """
    Validate that __svcs__ is a classmethod with the correct signature.

    Args:
        target: The class being validated
        svcs_method: The __svcs__ method to validate

    Raises:
        TypeError: If __svcs__ is not a classmethod
    """
    # Check if it's a classmethod by inspecting the descriptor
    # When we getattr on a class, a classmethod returns a bound method
    # An instance method would return a function object
    # A staticmethod would return a function object

    # Get the raw descriptor from the class dict to check its type
    if hasattr(target, "__dict__") and "__svcs__" in target.__dict__:
        raw_method = target.__dict__["__svcs__"]

        # Check if it's a classmethod descriptor
        if not isinstance(raw_method, classmethod):
            raise TypeError(
                f"__svcs__ must be a classmethod in {target.__name__}. "
                f"Expected: @classmethod def __svcs__(cls, container: svcs.Container, **kwargs) -> Self"
            )


# ============================================================================
# Public API
# ============================================================================


def auto[T](target: type[T]) -> SvcsFactory[T]:
    """
    Create a factory function for automatic dependency injection.

    Returns a factory function compatible with svcs.Registry.register_factory()
    that automatically resolves Injectable[T] dependencies from the container.

    Custom Construction with __svcs__
    ----------------------------------
    For complex initialization logic that cannot be expressed through simple field
    injection, classes can define a __svcs__ classmethod to take full control of
    construction:

        @dataclass
        class MyService:
            name: str
            db: Database  # NOT Injectable - __svcs__ handles construction

            @classmethod
            def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
                # Custom logic: validation, conditional deps, complex initialization
                db = container.get(Database)
                name = kwargs.get("name", "default")
                if not name:
                    raise ValueError("name cannot be empty")
                return cls(name=name, db=db)

    When __svcs__ is present:
    - It COMPLETELY REPLACES automatic Injectable field injection
    - Fields should NOT be annotated with Injectable[T]
    - The method receives the container and any kwargs passed to the factory
    - The method must return a fully constructed instance (Self type)
    - Must be a @classmethod with signature: (cls, container, **kwargs) -> Self

    When to use __svcs__ vs Injectable fields:
    - Use Injectable fields for simple, straightforward dependency injection
    - Use __svcs__ when you need:
      * Custom validation or post-construction setup
      * Conditional service resolution based on container contents
      * Complex initialization requiring multiple container.get() calls
      * Full control over the construction process

    To use a custom injector, register your own implementation:
        registry.register_factory(DefaultInjector, lambda c: MyCustomInjector(container=c))
    """

    def factory(svcs_container: svcs.Container, **kwargs: Any) -> T:
        """Factory function that resolves dependencies and constructs target."""
        # Check if target has a __svcs__ method for custom construction
        svcs_factory = getattr(target, "__svcs__", None)

        if svcs_factory is not None:
            # Validate that __svcs__ is a classmethod
            _validate_svcs_method(target, svcs_factory)

            # Validate that Injectable is not used with __svcs__
            field_infos = get_field_infos(target)
            injectable_fields = [fi.name for fi in field_infos if fi.is_injectable]
            if injectable_fields:
                msg = (
                    f"Class {target.__name__} defines __svcs__() but also has "
                    f"Injectable fields: {', '.join(injectable_fields)}. "
                    f"When using __svcs__() for custom construction, fields should not be "
                    f"annotated with Injectable[T]. The __svcs__() method is responsible "
                    f"for all construction logic."
                )
                raise TypeError(msg)

            # Invoke __svcs__ and return immediately, bypassing normal injection
            result: T = svcs_factory(svcs_container, **kwargs)
            return result

        # Normal Injectable field injection path
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

    Custom Construction with __svcs__ in Async Context
    ---------------------------------------------------
    The __svcs__ protocol is supported in async factories, but only synchronous
    __svcs__ methods are supported in v1. The __svcs__ method will be called
    synchronously even in an async factory context:

        @dataclass
        class MyAsyncService:
            name: str
            db: Database

            @classmethod
            def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
                # Synchronous container.get() works fine
                db = container.get(Database)
                name = kwargs.get("name", "default")
                return cls(name=name, db=db)

    Important notes for async context:
    - Only SYNCHRONOUS __svcs__ methods are supported (not async def __svcs__)
    - The __svcs__ method can use synchronous container.get() calls
    - For async dependencies, use normal Injectable[T] fields instead
    - Asynchronous __svcs__ (async def __svcs__) is planned for a future enhancement

    For detailed documentation on the __svcs__ protocol, see the auto() function
    docstring. All the same rules apply: __svcs__ completely replaces field
    injection, fields should not be annotated with Injectable[T], and the method
    must be a @classmethod.
    """

    async def async_factory(svcs_container: svcs.Container, **kwargs: Any) -> T:
        """Async factory function that resolves dependencies and constructs target."""
        # Check if target has a __svcs__ method for custom construction
        svcs_factory = getattr(target, "__svcs__", None)

        if svcs_factory is not None:
            # Validate that __svcs__ is a classmethod
            _validate_svcs_method(target, svcs_factory)

            # Validate that Injectable is not used with __svcs__
            field_infos = get_field_infos(target)
            injectable_fields = [fi.name for fi in field_infos if fi.is_injectable]
            if injectable_fields:
                msg = (
                    f"Class {target.__name__} defines __svcs__() but also has "
                    f"Injectable fields: {', '.join(injectable_fields)}. "
                    f"When using __svcs__() for custom construction, fields should not be "
                    f"annotated with Injectable[T]. The __svcs__() method is responsible "
                    f"for all construction logic."
                )
                raise TypeError(msg)

            # Invoke __svcs__ synchronously (v1 limitation: only sync __svcs__ supported)
            # No await needed - __svcs__ is synchronous only
            result: T = svcs_factory(svcs_container, **kwargs)
            return result

        # Normal async Injectable field injection path
        try:
            injector = await svcs_container.aget(DefaultAsyncInjector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultAsyncInjector(container=svcs_container)

        return await injector(target, **kwargs)

    return async_factory
