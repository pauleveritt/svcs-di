"""
HopscotchInjector - Injector with ServiceLocator integration for multi-implementation resolution.

This module provides HopscotchInjector and HopscotchAsyncInjector which extend the
basic injector pattern with ServiceLocator support for resource and location-based
service resolution.
"""

import inspect
from collections.abc import Awaitable
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, cast

import svcs

from svcs_di.auto import (
    AsyncInjectionTarget,
    FieldInfo,
    InjectionTarget,
    ResolutionResult,
    get_field_infos,
)
from svcs_di.injectors._helpers import (
    build_resolved_kwargs,
    resolve_default_value,
    validate_kwargs,
)


def _try_resolve_from_locator_sync(
    field_info: FieldInfo,
    container: svcs.Container,
    resource: type | None,
    location: PurePath | None,
    injector_callable,
) -> ResolutionResult:
    """
    Try to resolve a field using ServiceLocator (sync version).

    Precondition: field_info.inner_type must not be None (caller must validate).

    Args:
        field_info: Information about the field to resolve
        container: The svcs container
        resource: Optional resource type for resolution
        location: Optional location for resolution
        injector_callable: The injector to use for constructing implementations

    Returns:
        ResolutionResult: (found, value) where found indicates if locator had a match
    """
    # Import here to avoid circular dependency
    from svcs_di.injectors.locator import ServiceLocator

    # Precondition: caller must have validated inner_type is not None
    assert field_info.inner_type is not None

    try:
        locator = container.get(ServiceLocator)
        implementation = locator.get_implementation(
            field_info.inner_type,
            resource,
            location,
        )
        if implementation is not None:
            # Construct instance using the injector recursively (for nested injection)
            return (True, injector_callable(implementation))
    except svcs.exceptions.ServiceNotFoundError:
        pass  # No locator registered

    return (False, None)


async def _try_resolve_from_locator_async(
    field_info: FieldInfo,
    container: svcs.Container,
    resource: type | None,
    location: PurePath | None,
    injector_callable,
) -> ResolutionResult:
    """
    Try to resolve a field using ServiceLocator (async version).

    Precondition: field_info.inner_type must not be None (caller must validate).

    Args:
        field_info: Information about the field to resolve
        container: The svcs container
        resource: Optional resource type for resolution
        location: Optional location for resolution
        injector_callable: The async injector to use for constructing implementations

    Returns:
        ResolutionResult: (found, value) where found indicates if locator had a match
    """
    # Import here to avoid circular dependency
    from svcs_di.injectors.locator import ServiceLocator

    # Precondition: caller must have validated inner_type is not None
    assert field_info.inner_type is not None

    try:
        locator = await container.aget(ServiceLocator)
        implementation = locator.get_implementation(
            field_info.inner_type,
            resource,
            location,
        )
        if implementation is not None:
            # Construct instance using the injector recursively (for nested injection)
            return (True, await injector_callable(implementation))
    except svcs.exceptions.ServiceNotFoundError:
        pass  # No locator registered

    return (False, None)


def _resolve_from_container_with_fallback_sync(
    field_info: FieldInfo, container: svcs.Container
) -> ResolutionResult:
    """
    Try to resolve from container, returning (False, None) if not found.

    Precondition: field_info.inner_type must not be None (caller must validate).

    Args:
        field_info: Information about the field to resolve
        container: The svcs container

    Returns:
        ResolutionResult: (found, value)
    """
    # Precondition: caller must have validated inner_type is not None
    assert field_info.inner_type is not None

    try:
        if field_info.is_protocol:
            return True, container.get_abstract(field_info.inner_type)
        else:
            return True, container.get(field_info.inner_type)
    except svcs.exceptions.ServiceNotFoundError:
        return False, None


async def _resolve_from_container_with_fallback_async(
    field_info: FieldInfo, container: svcs.Container
) -> ResolutionResult:
    """
    Try to resolve from container async, returning (False, None) if not found.

    Precondition: field_info.inner_type must not be None (caller must validate).

    Args:
        field_info: Information about the field to resolve
        container: The svcs container

    Returns:
        ResolutionResult: (found, value)
    """
    # Precondition: caller must have validated inner_type is not None
    assert field_info.inner_type is not None

    try:
        if field_info.is_protocol:
            return True, await container.aget_abstract(field_info.inner_type)
        else:
            return True, await container.aget(field_info.inner_type)
    except svcs.exceptions.ServiceNotFoundError:
        return False, None


@dataclass(frozen=True)
class HopscotchInjector:
    """
    Injector that extends KeywordInjector with locator-based multi-implementation resolution.

    Implements three-tier precedence for value resolution:
    1. kwargs passed to injector (highest priority - overrides everything)
    2. ServiceLocator for Inject[T] types with multiple implementations, falling back to container.get(T)
    3. default values from field definitions (lowest priority)

    When resolving Inject[T] fields, it first tries ServiceLocator.get_implementation()
    with resource and location obtained from container. If no locator or no matching implementation is found,
    falls back to standard container.get(T) or container.get_abstract(T) behavior.

    Special handling: The 'children' kwarg is silently ignored if not a valid field, to support
    template rendering systems (like tdom) that always pass children even when not needed.
    """

    container: svcs.Container
    resource: type | None = None  # Optional: type to get from container for resource

    def _get_resource(self) -> type | None:
        """Get the resource type from container if resource is configured."""
        if self.resource is None:
            return None

        try:
            resource_instance = self.container.get(self.resource)
            return type(resource_instance)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    def _get_location(self) -> PurePath | None:
        """Get the Location from container if registered."""
        # Import here to avoid circular dependency
        from svcs_di.injectors.locator import Location

        try:
            return self.container.get(Location)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    def _resolve_field_value_sync(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> ResolutionResult:
        """
        Resolve a single field's value using three-tier precedence with locator support.

        Returns:
            ResolutionResult: (has_value, value) where has_value indicates if a value was resolved
        """
        # Tier 1: kwargs (highest priority)
        if field_info.name in kwargs:
            return (True, kwargs[field_info.name])

        # Tier 2: Inject from container (with locator support)
        if field_info.is_injectable:
            if field_info.inner_type is None:
                raise TypeError(f"Inject field '{field_info.name}' has no inner type")

            # Check for Container injection first (bypasses locator)
            if field_info.inner_type is svcs.Container:
                return (True, self.container)

            # Try locator first for types with multiple implementations
            resource_type = self._get_resource()
            location = self._get_location()
            found, value = _try_resolve_from_locator_sync(
                field_info, self.container, resource_type, location, self
            )
            if found:
                return (True, value)

            # Fall back to standard container resolution
            found, value = _resolve_from_container_with_fallback_sync(
                field_info, self.container
            )
            if found:
                return (True, value)

        # Tier 3: default value
        if field_info.has_default:
            return True, resolve_default_value(field_info.default_value)

        # No value found at any tier
        return (False, None)

    def __call__[T](self, target: InjectionTarget[T], **kwargs: Any) -> T:
        """
        Inject dependencies and construct target instance or call function.

        Args:
            target: A class or callable to invoke with resolved dependencies
            **kwargs: Keyword arguments that override any resolved dependencies.
                     The 'children' kwarg is ignored if not a valid field.

        Returns:
            Result of calling target with dependencies injected

        Raises:
            ValueError: If unknown kwargs (other than 'children') are provided
            TypeError: If an Inject field has no inner type
        """
        field_infos = get_field_infos(target)
        validate_kwargs(target, field_infos, kwargs, allow_children=True)
        resolved_kwargs = build_resolved_kwargs(
            field_infos, self._resolve_field_value_sync, kwargs
        )
        return target(**resolved_kwargs)


@dataclass(frozen=True)
class HopscotchAsyncInjector:
    """
    Async version of HopscotchInjector.

    Like HopscotchInjector but uses async container methods (aget, aget_abstract)
    for resolving Inject[T] dependencies.

    Implements the same three-tier precedence as HopscotchInjector:
    1. kwargs passed to injector (highest priority)
    2. ServiceLocator for Inject[T] types, falling back to container.aget(T)
    3. default values from field definitions (lowest priority)

    Special handling: The 'children' kwarg is silently ignored if not a valid field, to support
    template rendering systems (like tdom) that always pass children even when not needed.
    """

    container: svcs.Container
    resource: type | None = None

    async def _get_resource(self) -> type | None:
        """Get the resource type from container if resource is configured."""
        if self.resource is None:
            return None

        try:
            resource_instance = await self.container.aget(self.resource)
            return type(resource_instance)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    async def _get_location(self) -> PurePath | None:
        """Get the Location from container if registered."""
        # Import here to avoid circular dependency
        from svcs_di.injectors.locator import Location

        try:
            return await self.container.aget(Location)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    async def _resolve_field_value_async(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> ResolutionResult:
        """
        Async version of field value resolution with three-tier precedence and locator support.

        Returns:
            ResolutionResult: (has_value, value) where has_value indicates if a value was resolved
        """
        # Tier 1: kwargs (highest priority)
        if field_info.name in kwargs:
            return (True, kwargs[field_info.name])

        # Tier 2: Inject from container (async, with locator support)
        if field_info.is_injectable:
            if field_info.inner_type is None:
                raise TypeError(f"Inject field '{field_info.name}' has no inner type")

            # Check for Container injection first (bypasses locator)
            if field_info.inner_type is svcs.Container:
                return (True, self.container)

            # Try locator first for types with multiple implementations
            resource_type = await self._get_resource()
            location = await self._get_location()
            found, value = await _try_resolve_from_locator_async(
                field_info, self.container, resource_type, location, self
            )
            if found:
                return (True, value)

            # Fall back to standard async container resolution
            found, value = await _resolve_from_container_with_fallback_async(
                field_info, self.container
            )
            if found:
                return (True, value)

        # Tier 3: default value
        if field_info.has_default:
            return True, resolve_default_value(field_info.default_value)

        # No value found at any tier
        return (False, None)

    async def __call__[T](self, target: AsyncInjectionTarget[T], **kwargs: Any) -> T:
        """
        Async inject dependencies and construct target instance or call async function.

        Args:
            target: A class or async callable to invoke with resolved dependencies
            **kwargs: Keyword arguments that override any resolved dependencies.
                     The 'children' kwarg is ignored if not a valid field.

        Returns:
            Result of calling target with dependencies injected

        Raises:
            ValueError: If unknown kwargs (other than 'children') are provided
            TypeError: If an Inject field has no inner type
        """
        field_infos = get_field_infos(target)
        validate_kwargs(target, field_infos, kwargs, allow_children=True)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await self._resolve_field_value_async(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        result = target(**resolved_kwargs)
        # If target is an async callable, await the result
        if inspect.iscoroutinefunction(target):
            return await cast(Awaitable[T], result)
        return cast(T, result)
