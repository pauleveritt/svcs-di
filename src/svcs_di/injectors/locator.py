"""
Service Locator - Multiple implementation registrations with context-based selection.

This is a radical simplification that uses svcs.Registry as the underlying storage
and provides a locator service that tracks multiple implementations.

Also includes HopscotchInjector which extends KeywordInjector to support automatic
locator-based resolution for Injectable[T] fields with multiple implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import svcs

from svcs_di.auto import FieldInfo, get_field_infos


@dataclass
class FactoryRegistration:
    """A single implementation registration with service type and optional context."""

    service_type: type
    implementation: type
    context: Optional[type] = None

    def matches(self, request_context: Optional[type]) -> int:
        """
        Calculate match score for this registration.

        Returns:
            2 = exact context match (highest)
            1 = subclass context match (medium)
            0 = no context match (lowest/default)
            -1 = no match
        """
        if self.context is None and request_context is None:
            return 0  # Default match
        elif self.context is request_context:
            return 2  # Exact match
        elif self.context is None:
            return 0  # Default fallback
        elif request_context and issubclass(request_context, self.context):
            return 1  # Subclass match
        return -1  # No match


@dataclass
class ServiceLocator:
    """
    Single locator that tracks multiple implementations across all service types.

    This is the ONE locator for the entire application. Implementations are stored in LIFO
    order (most recent first). Selection uses three-tier precedence: exact > subclass > default.
    """

    registrations: list[FactoryRegistration] = field(default_factory=list)

    def register(
        self,
        service_type: type,
        implementation: type,
        context: Optional[type] = None
    ) -> None:
        """Register an implementation class for a service type with optional context. LIFO ordering (insert at front)."""
        self.registrations.insert(0, FactoryRegistration(service_type, implementation, context))

    def get_implementation(
        self,
        service_type: type,
        request_context: Optional[type] = None
    ) -> Optional[type]:
        """
        Find best matching implementation class for a service type using three-tier precedence.

        Returns the implementation class from the first registration with highest score.
        """
        best_score = -1
        best_impl = None

        for reg in self.registrations:
            if reg.service_type is not service_type:
                continue  # Skip registrations for other service types

            score = reg.matches(request_context)
            if score > best_score:
                best_score = score
                best_impl = reg.implementation
                if score == 2:  # Exact match, can't do better
                    break

        return best_impl


def get_from_locator[T](
    container: svcs.Container,
    service_type: type[T],
    request_context: Optional[type] = None,
) -> T:
    """
    Get a service from the locator with automatic construction.

    The ServiceLocator is registered as a service in the registry.

    Usage:
        # Setup (once per application)
        registry = svcs.Registry()
        locator = ServiceLocator()
        locator.register(Greeting, DefaultGreeting)
        locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
        locator.register(Database, PostgresDB)
        locator.register(Database, TestDB, context=TestContext)
        registry.register_value(ServiceLocator, locator)

        # Get service (per request)
        container = svcs.Container(registry)
        greeting = get_from_locator(container, Greeting, request_context=EmployeeContext)
        db = get_from_locator(container, Database, request_context=TestContext)
    """
    locator = container.get(ServiceLocator)

    implementation = locator.get_implementation(service_type, request_context)

    if implementation is None:
        raise LookupError(
            f"No implementation found for {service_type.__name__} with context {request_context}"
        )

    # Construct the instance from the implementation class
    return implementation()  # type: ignore[return-value]


@dataclass
class HopscotchInjector:
    """
    Injector that extends KeywordInjector with locator-based multi-implementation resolution.

    Implements three-tier precedence for value resolution:
    1. kwargs passed to injector (highest priority - overrides everything)
    2. ServiceLocator for Injectable[T] types with multiple implementations, falling back to container.get(T)
    3. default values from field definitions (lowest priority)

    When resolving Injectable[T] fields, it first tries ServiceLocator.get_implementation()
    with context obtained from container. If no locator or no matching implementation is found,
    falls back to standard container.get(T) or container.get_abstract(T) behavior.
    """

    container: svcs.Container
    context_key: Optional[type] = None  # Optional: type to get from container for context (e.g., RequestContext)

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )

    def _get_request_context(self) -> Optional[type]:
        """Get the request context type from container if context_key is configured."""
        if self.context_key is None:
            return None

        try:
            context_instance = self.container.get(self.context_key)
            return type(context_instance)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    def _resolve_field_value_sync(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Resolve a single field's value using three-tier precedence with locator support.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        field_name = field_info.name

        # Tier 1: kwargs (highest priority)
        if field_name in kwargs:
            return (True, kwargs[field_name])

        # Tier 2: Injectable from container (with locator support)
        if field_info.is_injectable:
            inner_type = field_info.inner_type
            if inner_type is None:
                raise TypeError(f"Injectable field '{field_name}' has no inner type")

            # Try locator first for types with multiple implementations
            try:
                locator = self.container.get(ServiceLocator)
                request_context = self._get_request_context()

                implementation = locator.get_implementation(inner_type, request_context)
                if implementation is not None:
                    # Construct instance using the injector recursively (for nested injection)
                    return (True, implementation())
            except svcs.exceptions.ServiceNotFoundError:
                pass  # No locator registered, fall through to normal resolution

            # Fall back to standard container resolution
            try:
                if field_info.is_protocol:
                    value = self.container.get_abstract(inner_type)
                else:
                    value = self.container.get(inner_type)
                return True, value
            except svcs.exceptions.ServiceNotFoundError:
                # Not in container either, fall through to defaults
                pass

        # Tier 3: default value
        if field_info.has_default:
            default_val = field_info.default_value
            # Handle default_factory (callable) or regular default
            if callable(default_val):
                return True, default_val()
            else:
                return True, default_val

        return (False, None)

    def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Inject dependencies and construct target instance.

        Args:
            target: The class or callable to construct
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Injectable field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = self._resolve_field_value_sync(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


@dataclass
class HopscotchAsyncInjector:
    """
    Async version of HopscotchInjector.

    Like HopscotchInjector but uses async container methods (aget, aget_abstract)
    for resolving Injectable[T] dependencies.

    Implements the same three-tier precedence as HopscotchInjector:
    1. kwargs passed to injector (highest priority)
    2. ServiceLocator for Injectable[T] types, falling back to container.aget(T)
    3. default values from field definitions (lowest priority)
    """

    container: svcs.Container
    context_key: Optional[type] = None

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )

    async def _get_request_context(self) -> Optional[type]:
        """Get the request context type from container if context_key is configured."""
        if self.context_key is None:
            return None

        try:
            context_instance = await self.container.aget(self.context_key)
            return type(context_instance)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    async def _resolve_field_value_async(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Async version of field value resolution with three-tier precedence and locator support.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        field_name = field_info.name

        # Tier 1: kwargs (highest priority)
        if field_name in kwargs:
            return (True, kwargs[field_name])

        # Tier 2: Injectable from container (async, with locator support)
        if field_info.is_injectable:
            inner_type = field_info.inner_type
            if inner_type is None:
                raise TypeError(f"Injectable field '{field_name}' has no inner type")

            # Try locator first for types with multiple implementations
            try:
                locator = await self.container.aget(ServiceLocator)
                request_context = await self._get_request_context()

                implementation = locator.get_implementation(inner_type, request_context)
                if implementation is not None:
                    # Construct instance using the injector recursively (for nested injection)
                    return (True, implementation())
            except svcs.exceptions.ServiceNotFoundError:
                pass  # No locator registered, fall through to normal resolution

            # Fall back to standard async container resolution
            try:
                if field_info.is_protocol:
                    value = await self.container.aget_abstract(inner_type)
                else:
                    value = await self.container.aget(inner_type)
                return True, value
            except svcs.exceptions.ServiceNotFoundError:
                # Not in container either, fall through to defaults
                pass

        # Tier 3: default value
        if field_info.has_default:
            default_val = field_info.default_value
            # Handle default_factory (callable) or regular default
            if callable(default_val):
                return True, default_val()
            else:
                return True, default_val

        return (False, None)

    async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Async inject dependencies and construct target instance.

        Args:
            target: The class or callable to construct
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Injectable field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await self._resolve_field_value_async(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)
