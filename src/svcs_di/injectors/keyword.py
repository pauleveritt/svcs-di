"""
KeywordInjector implementation with three-tier precedence for kwargs support.

This module provides KeywordInjector and KeywordAsyncInjector which support
kwargs override functionality that was extracted from DefaultInjector.

Helper functions are imported from svcs_di.auto to maintain a standalone DefaultInjector.
"""

import inspect
from dataclasses import dataclass
from typing import Any

import svcs

# Import helper functions from auto.py
from svcs_di.auto import (
    AsyncInjectionTarget,
    FieldInfo,
    InjectionTarget,
    get_field_infos,
)
from svcs_di.injectors._helpers import resolve_default_value, validate_kwargs


def _resolve_from_container_sync(
    field_info: FieldInfo, container: svcs.Container
) -> tuple[bool, Any]:
    """
    Resolve an injectable field from the container (sync version).

    Args:
        field_info: Information about the field to resolve
        container: The svcs container to resolve from

    Returns:
        tuple[bool, Any]: (has_value, value) where has_value indicates if resolved

    Raises:
        TypeError: If inner_type is None
    """
    inner_type = field_info.inner_type
    if inner_type is None:
        raise TypeError(f"Inject field '{field_info.name}' has no inner type")

    # Container injection - return the container itself
    if inner_type is svcs.Container:
        return True, container

    # Protocol vs concrete type
    if field_info.is_protocol:
        return True, container.get_abstract(inner_type)
    return True, container.get(inner_type)


async def _resolve_from_container_async(
    field_info: FieldInfo, container: svcs.Container
) -> tuple[bool, Any]:
    """
    Resolve an injectable field from the container (async version).

    Args:
        field_info: Information about the field to resolve
        container: The svcs container to resolve from

    Returns:
        tuple[bool, Any]: (has_value, value) where has_value indicates if resolved

    Raises:
        TypeError: If inner_type is None
    """
    inner_type = field_info.inner_type
    if inner_type is None:
        raise TypeError(f"Inject field '{field_info.name}' has no inner type")

    # Container injection - return the container itself
    if inner_type is svcs.Container:
        return True, container

    # Protocol vs concrete type (async)
    if field_info.is_protocol:
        return True, await container.aget_abstract(inner_type)
    return True, await container.aget(inner_type)


@dataclass(frozen=True)
class KeywordInjector:
    """
    Dependency injector with kwargs override support.

    Implements three-tier precedence for value resolution:
    1. kwargs passed to injector (highest priority - overrides everything)
    2. container.get(T) or container.get_abstract(T) for Inject[T] fields
    3. default values from field definitions (lowest priority)

    This is the extracted kwargs functionality from the original DefaultInjector,
    designed to be used when kwargs override support is needed.
    """

    container: svcs.Container

    def _resolve_field_value_sync(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Resolve a single field's value using three-tier precedence.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        # Tier 1: kwargs (highest priority)
        if field_info.name in kwargs:
            return (True, kwargs[field_info.name])

        # Tier 2: Inject from container
        if field_info.is_injectable:
            return _resolve_from_container_sync(field_info, self.container)

        # Tier 3: default value
        if field_info.has_default:
            return True, resolve_default_value(field_info.default_value)

        return False, None

    def __call__[T](self, target: InjectionTarget[T], **kwargs: Any) -> T:
        """
        Inject dependencies and construct target instance or call function.

        Args:
            target: A class or callable to invoke with resolved dependencies
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            Result of calling target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Inject field has no inner type
        """
        field_infos = get_field_infos(target)
        validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = self._resolve_field_value_sync(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)  # type: ignore[return-value]


@dataclass(frozen=True)
class KeywordAsyncInjector:
    """
    Async dependency injector with kwargs override support.

    Like KeywordInjector but uses async container methods (aget, aget_abstract)
    for resolving Inject[T] dependencies.

    Implements the same three-tier precedence as KeywordInjector:
    1. kwargs passed to injector (highest priority)
    2. container.aget(T) or container.aget_abstract(T) for Inject[T] fields
    3. default values from field definitions (lowest priority)
    """

    container: svcs.Container

    async def _resolve_field_value_async(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Async version of field value resolution with three-tier precedence.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        # Tier 1: kwargs (highest priority)
        if field_info.name in kwargs:
            return (True, kwargs[field_info.name])

        # Tier 2: Inject from container (async)
        if field_info.is_injectable:
            return await _resolve_from_container_async(field_info, self.container)

        # Tier 3: default value
        if field_info.has_default:
            return True, resolve_default_value(field_info.default_value)

        return (False, None)

    async def __call__[T](self, target: AsyncInjectionTarget[T], **kwargs: Any) -> T:
        """
        Async inject dependencies and construct target instance or call async function.

        Args:
            target: A class or async callable to invoke with resolved dependencies
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            Result of calling target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Inject field has no inner type
        """
        field_infos = get_field_infos(target)
        validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await self._resolve_field_value_async(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        result = target(**resolved_kwargs)
        # If target is an async callable, await the result
        if inspect.iscoroutinefunction(target):
            return await result  # type: ignore[return-value]
        return result  # type: ignore[return-value]
