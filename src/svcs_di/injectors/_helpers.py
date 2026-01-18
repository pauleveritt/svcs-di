"""
Shared helper functions for injector implementations.

This module contains common functionality used across multiple injector
classes to reduce code duplication between sync/async variants.
"""

from collections.abc import Callable
from typing import Any

from svcs_di.auto import FieldInfo


def validate_kwargs(
    target: type | Callable[..., Any],
    field_infos: list[FieldInfo],
    kwargs: dict[str, Any],
    allow_children: bool = False,
) -> None:
    """
    Validate that all kwargs match actual field names.

    Args:
        target: The target class or callable being invoked
        field_infos: List of field information for the target
        kwargs: The keyword arguments to validate
        allow_children: If True, silently allow 'children' kwarg even if not a field
                       (for template systems that always pass children)

    Raises:
        ValueError: If unknown kwargs are provided
    """
    valid_field_names = {f.name for f in field_infos}
    for kwarg_name in kwargs:
        # Special case: 'children' is allowed if allow_children=True
        if allow_children and kwarg_name == "children":
            continue
        if kwarg_name not in valid_field_names:
            target_name = getattr(target, "__name__", repr(target))
            raise ValueError(
                f"Unknown parameter '{kwarg_name}' for {target_name}. "
                f"Valid parameters: {', '.join(sorted(valid_field_names))}"
            )


def is_dataclass_default_factory(value: Any) -> bool:
    """
    Check if value is a bound method (e.g., dataclass default_factory).

    Dataclass fields with default_factory store a bound method that needs
    to be called to get the default value.

    Args:
        value: The value to check

    Returns:
        True if value is a callable bound method
    """
    return callable(value) and hasattr(value, "__self__")


def resolve_default_value(default_value: Any) -> Any:
    """
    Resolve a default value, calling it if it's a default_factory.

    Dataclass fields with default_factory are represented as either:
    - Bound methods (when the field has a callable default_factory)
    - Regular callables (including classes)

    Args:
        default_value: The default value or default_factory

    Returns:
        The resolved default value
    """
    # If it's callable (including bound methods and classes), call it
    if callable(default_value):
        return default_value()
    return default_value


# Type alias for field resolution functions used by injectors
type FieldResolverWithKwargs = Callable[[FieldInfo, dict[str, Any]], tuple[bool, Any]]


def build_resolved_kwargs(
    field_infos: list[FieldInfo],
    resolver: FieldResolverWithKwargs,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """
    Build resolved kwargs dictionary using the provided resolver function.

    This is the common implementation for sync injectors to iterate through
    field_infos and build the resolved kwargs dictionary.

    Args:
        field_infos: List of field information to resolve
        resolver: Function to resolve each field value, taking (field_info, kwargs)
        kwargs: The original kwargs passed to the injector

    Returns:
        Dictionary of resolved kwargs ready to pass to target callable
    """
    resolved_kwargs: dict[str, Any] = {}
    for field_info in field_infos:
        has_value, value = resolver(field_info, kwargs)
        if has_value:
            resolved_kwargs[field_info.name] = value
    return resolved_kwargs
