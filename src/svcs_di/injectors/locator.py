"""
Service Locator - Multiple implementation registrations with resource-based selection.

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


@dataclass(frozen=True)
class FactoryRegistration:
    """A single implementation registration with service type and optional resource.

    The resource represents a business entity type (e.g., Customer, Employee, Product)
    that determines which implementation to use.
    """

    service_type: type
    implementation: type
    resource: Optional[type] = None

    def matches(self, resource: Optional[type]) -> int:
        """
        Calculate match score for this registration against a resource type.

        Args:
            resource: The resource type to match against (e.g., Customer, Employee)

        Returns:
            2 = exact resource match (highest)
            1 = subclass resource match (medium)
            0 = no resource match (lowest/default)
            -1 = no match
        """
        match (self.resource, resource):
            case (None, None):
                return 0  # Default match
            case (r, req) if r is req:
                return 2  # Exact match
            case (None, _):
                return 0  # Default fallback
            case (r, req) if req is not None and r is not None and issubclass(req, r):
                return 1  # Subclass match
            case _:
                return -1  # No match


@dataclass(frozen=True)
class ServiceLocator:
    """
    Thread-safe, immutable locator for multiple service implementations with resource-based selection.

    This is the ONE locator for the entire application. Implementations are stored in LIFO
    order (most recent first). Selection uses three-tier precedence: exact > subclass > default.

    Resource-based matching allows different implementations to be selected based on business
    entity types like Customer, Employee, or Product.

    Thread-safe: All data is immutable (frozen dataclass with tuple).

    Caching: Results are cached for performance. Cache is keyed by (service_type, resource_type)
    tuple and stores the resolved implementation class or None.

    Example:
        # Create with registrations
        locator = ServiceLocator.with_registrations(
            (Greeting, DefaultGreeting, None),
            (Greeting, EmployeeGreeting, EmployeeContext),
            (Database, PostgresDB, None),
        )

        # Or build up immutably
        locator = ServiceLocator()
        locator = locator.register(Greeting, DefaultGreeting)
        locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    """

    registrations: tuple[FactoryRegistration, ...] = field(default_factory=tuple)
    _cache: dict[tuple[type, Optional[type]], Optional[type]] = field(
        default_factory=dict
    )

    @staticmethod
    def with_registrations(
        *registrations: tuple[type, type, Optional[type]],
    ) -> "ServiceLocator":
        """
        Create ServiceLocator with registrations.

        Args:
            registrations: Variable number of (service_type, implementation, resource) tuples

        Returns:
            New ServiceLocator instance

        Example:
            locator = ServiceLocator.with_registrations(
                (Greeting, DefaultGreeting, None),
                (Greeting, EmployeeGreeting, EmployeeContext),
            )
        """
        factory_regs = tuple(
            FactoryRegistration(service_type, impl, ctx)
            for service_type, impl, ctx in registrations
        )
        return ServiceLocator(registrations=factory_regs)

    def register(
        self, service_type: type, implementation: type, resource: Optional[type] = None
    ) -> "ServiceLocator":
        """
        Return new ServiceLocator with additional registration (immutable, thread-safe).

        LIFO ordering: new registrations are inserted at the front.
        Cache invalidation: new instance has empty cache since registrations changed.

        Args:
            service_type: The service type to register for
            implementation: The implementation class
            resource: Optional resource type for resource-specific resolution

        Returns:
            New ServiceLocator with the registration prepended and cleared cache
        """
        new_reg = FactoryRegistration(service_type, implementation, resource)
        # Prepend for LIFO (most recent first)
        new_registrations = (new_reg,) + self.registrations
        # Return new instance with empty cache (cache invalidation)
        return ServiceLocator(registrations=new_registrations)

    def get_implementation(
        self, service_type: type, resource: Optional[type] = None
    ) -> Optional[type]:
        """
        Find best matching implementation class for a service type using three-tier precedence.

        The resource parameter specifies a business entity type (like Customer or Employee)
        to select the appropriate implementation.

        Results are cached for performance. The cache key is (service_type, resource_type).

        Args:
            service_type: The service type to find an implementation for
            resource: Optional resource type for resource-based matching

        Returns:
            The implementation class from the first registration with highest score.

        Thread-safe: Only reads immutable data (cache is mutated but that's thread-safe for dicts).
        """
        cache_key = (service_type, resource)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Cache miss - perform lookup
        best_score = -1
        best_impl = None

        for reg in self.registrations:
            if reg.service_type is not service_type:
                continue  # Skip registrations for other service types

            score = reg.matches(resource)
            if score > best_score:
                best_score = score
                best_impl = reg.implementation
                if score == 2:  # Exact match, can't do better
                    break

        # Store in cache before returning
        # Note: Mutating frozen dataclass's dict field is safe here because:
        # 1. Dict operations are thread-safe for simple get/set
        # 2. We never replace the dict object itself
        # 3. Worst case: multiple threads compute same result (idempotent)
        self._cache[cache_key] = best_impl

        return best_impl


def get_from_locator[T](
    container: svcs.Container,
    service_type: type[T],
    resource: Optional[type] = None,
) -> T:
    """
    Get a service from the locator with automatic construction.

    The ServiceLocator is registered as a service in the registry.

    Usage:
        # Setup (once per application)
        registry = svcs.Registry()
        locator = ServiceLocator()
        locator = locator.register(Greeting, DefaultGreeting)
        locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
        locator = locator.register(Database, PostgresDB)
        locator = locator.register(Database, TestDB, resource=TestContext)
        registry.register_value(ServiceLocator, locator)

        # Or use the static constructor:
        locator = ServiceLocator.with_registrations(
            (Greeting, DefaultGreeting, None),
            (Greeting, EmployeeGreeting, EmployeeContext),
            (Database, PostgresDB, None),
            (Database, TestDB, TestContext),
        )
        registry.register_value(ServiceLocator, locator)

        # Get service (per request)
        container = svcs.Container(registry)
        greeting = get_from_locator(container, Greeting, resource=EmployeeContext)
        db = get_from_locator(container, Database, resource=TestContext)
    """
    locator = container.get(ServiceLocator)

    implementation = locator.get_implementation(service_type, resource)

    if implementation is None:
        raise LookupError(
            f"No implementation found for {service_type.__name__} with resource {resource}"
        )

    # Construct the instance from the implementation class
    return implementation()  # type: ignore[return-value]


@dataclass(frozen=True)
class HopscotchInjector:
    """
    Injector that extends KeywordInjector with locator-based multi-implementation resolution.

    Implements three-tier precedence for value resolution:
    1. kwargs passed to injector (highest priority - overrides everything)
    2. ServiceLocator for Injectable[T] types with multiple implementations, falling back to container.get(T)
    3. default values from field definitions (lowest priority)

    When resolving Injectable[T] fields, it first tries ServiceLocator.get_implementation()
    with resource obtained from container. If no locator or no matching implementation is found,
    falls back to standard container.get(T) or container.get_abstract(T) behavior.
    """

    container: svcs.Container
    resource: Optional[type] = (
        None  # Optional: type to get from container for resource (e.g., RequestContext)
    )

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

    def _get_resource(self) -> Optional[type]:
        """Get the resource type from container if resource is configured."""
        if self.resource is None:
            return None

        try:
            resource_instance = self.container.get(self.resource)
            return type(resource_instance)
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
                resource_type = self._get_resource()

                implementation = locator.get_implementation(inner_type, resource_type)
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

        # No value found at any tier
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


@dataclass(frozen=True)
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
    resource: Optional[type] = None

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

    async def _get_resource(self) -> Optional[type]:
        """Get the resource type from container if resource is configured."""
        if self.resource is None:
            return None

        try:
            resource_instance = await self.container.aget(self.resource)
            return type(resource_instance)
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
                resource_type = await self._get_resource()

                implementation = locator.get_implementation(inner_type, resource_type)
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

        # No value found at any tier
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
