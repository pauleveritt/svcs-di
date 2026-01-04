"""
Service Locator - Multiple implementation registrations with resource and location-based selection.

This module provides three key capabilities:

1. **ServiceLocator**: A thread-safe, immutable locator for managing multiple service
   implementations with resource and location-based selection. This allows different implementations
   to be selected based on business entity types (Customer, Employee, Product) and hierarchical
   locations (URL paths like /admin, /public).

2. **Location Type**: A type alias for `PurePath` representing hierarchical request context
   (URL paths, filesystem-like paths). Location is treated as a special service type that
   containers have access to via value service registration.

3. **Package Scanning**: Decorator-based auto-discovery of services via the @injectable
   decorator and scan() function. This eliminates manual registration code by automatically
   discovering and registering decorated classes.

The ServiceLocator provides precedence scoring that combines:
- Location matches (exact location: 100 points)
- Resource matches (exact: 10 points, subclass: 2 points)
- Base registration (1 point)

Services registered with locations are ONLY available at that location or its children (hierarchical fallback).
More specific locations (deeper in hierarchy) always take precedence over less specific locations.

Location as Special Service:
- `Location` (aliased from `PurePath`) represents hierarchical request context
- Containers can have Location registered as a value service: `registry.register_value(Location, PurePath("/admin"))`
- Services can depend on Location via `Inject[Location]` to access current request location
- The Location service represents "where" the current request is happening in the application hierarchy
- PurePath is immutable and thread-safe, compatible with free-threaded Python
- Supports hierarchy operations: `.parents` for traversal, `.is_relative_to()` for relationships

Precedence Scoring:
- Location: 1000 (exact/hierarchical match) or 0 (global) or -1 (no match)
- Resource: 100 (exact) or 10 (subclass) or 0 (default) or -1 (no match)
- Combined score = location_score + resource_score
- Possible scores: 1100 (location+exact), 1010 (location+subclass), 1000 (location+default),
                   100 (exact), 10 (subclass), 0 (default), -1 (no match)
- LIFO ordering breaks ties (most recent registration wins)

Performance Optimization:
- ServiceLocator automatically uses a fast O(1) lookup path for service types with a single registration
- When a second implementation is registered for the same service type, it switches to an O(m) scoring
  path where m is the number of registrations for that specific service (not all services)
- This makes the single-implementation case nearly as fast as using svcs.Registry directly
- Multiple service types can coexist: some using the fast path, others using the scoring path
- The optimization is transparent - no API changes required

The scanning functionality provides a venusian-inspired decorator pattern that:
- Marks services with @injectable decorator at class definition time
- Discovers and registers them at application startup via scan()
- Supports resource-based registrations with @injectable(resource=...)
- Supports location-based registrations with @injectable(location=PurePath(...))
- Supports combined resource+location: @injectable(resource=X, location=PurePath(...))
- Works seamlessly with Inject[T] dependency injection

Also includes HopscotchInjector which extends KeywordInjector to support automatic
locator-based resolution for Inject[T] fields with multiple implementations.

Examples:
    >>> # Setup for doctests
    >>> from pathlib import PurePath
    >>> from dataclasses import dataclass
    >>> import svcs
    >>> from svcs_di.injectors.locator import ServiceLocator, Location, scan
    >>> from svcs_di.injectors.decorators import injectable
    >>>
    >>> # Define example classes
    >>> class Greeting: pass
    >>> class DefaultGreeting(Greeting): pass
    >>> class EmployeeGreeting(Greeting): pass
    >>> class AdminGreeting(Greeting): pass
    >>> class PublicGreeting(Greeting): pass
    >>> class EnhancedGreeting(Greeting): pass
    >>> class EmployeeContext: pass
    >>> class CustomerContext: pass
    >>> class AuthenticatedContext: pass

    Basic usage with ServiceLocator:
        >>> locator = ServiceLocator()
        >>> locator = locator.register(Greeting, DefaultGreeting)
        >>> locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
        >>> registry = svcs.Registry()
        >>> registry.register_value(ServiceLocator, locator)

    Location-based registration:
        >>> locator = ServiceLocator()
        >>> locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
        >>> locator = locator.register(Greeting, PublicGreeting, location=PurePath("/public"))
        >>> registry = svcs.Registry()
        >>> registry.register_value(ServiceLocator, locator)
        >>> registry.register_value(Location, PurePath("/admin"))  # Current request location

    Combined resource + location:
        >>> locator = ServiceLocator()
        >>> locator = locator.register(
        ...     Greeting, EnhancedGreeting,
        ...     resource=AuthenticatedContext,
        ...     location=PurePath("/admin")
        ... )
        >>> registry = svcs.Registry()
        >>> registry.register_value(ServiceLocator, locator)

    Location as special service:
        >>> from pathlib import PurePath
        >>> registry = svcs.Registry()
        >>> registry.register_value(Location, PurePath("/admin"))
        >>> container = svcs.Container(registry)
        >>> current_location = container.get(Location)  # Returns PurePath("/admin")

    Basic usage with scanning:
        >>> @injectable
        ... @dataclass
        ... class Database:
        ...     host: str = "localhost"
        ...
        >>> registry = svcs.Registry()
        >>> scan(registry, "myapp.services")  # doctest: +SKIP

    Resource-based scanning:
        >>> @injectable(resource=CustomerContext)
        ... @dataclass
        ... class CustomerGreeting(Greeting):
        ...     salutation: str = "Hello"
        ...
        >>> scan(registry, "myapp.services")  # doctest: +SKIP

    Location-based scanning:
        >>> @injectable(location=PurePath("/admin"))
        ... @dataclass
        ... class AdminService:
        ...     name: str = "Admin"
        ...
        >>> scan(registry, "myapp.services")  # doctest: +SKIP

For complete examples, see:
- examples/location_based_resolution.py (location-based service selection)
- examples/multiple_implementations.py (ServiceLocator usage)
- examples/scanning/basic_scanning.py (simple scanning workflow)
- examples/scanning/context_aware_scanning.py (resource-based resolution)
"""

import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from pathlib import PurePath
from types import ModuleType
from typing import Any, Optional

import svcs

from svcs_di import DefaultInjector
from svcs_di.auto import FieldInfo, Injector, get_field_infos

log = logging.getLogger("svcs_di")


# ============================================================================
# Location Type Alias
# ============================================================================

Location = PurePath
"""
Type alias for PurePath representing hierarchical request context.

Location represents hierarchical paths (URL paths, filesystem-like paths) used for
location-based service resolution. It's a special service type that containers can
have registered as a value service.

Usage:
    # Register Location in container
    registry.register_value(Location, PurePath("/admin"))

    # Services depend on Location
    @dataclass
    class MyService:
        location: Inject[Location]

    # Use Location for hierarchical matching
    admin_location = PurePath("/admin")
    admin_users_location = PurePath("/admin/users")
    # Check hierarchy: admin_users_location.is_relative_to(admin_location) -> True

Thread-safety: PurePath is immutable and thread-safe, compatible with free-threaded Python.
Hierarchy operations: Use `.parents` for traversal, `.is_relative_to()` for relationships.
"""


@dataclass(frozen=True)
class FactoryRegistration:
    """A single implementation registration with service type, optional resource, and optional location.

    The resource represents a business entity type (e.g., Customer, Employee, Product)
    that determines which implementation to use.

    The location represents a hierarchical context (e.g., URL path like /admin, /public)
    that restricts service availability to specific parts of the application hierarchy.
    """

    service_type: type
    implementation: type
    resource: Optional[type] = None
    location: Optional[PurePath] = None

    def matches(
        self, resource: Optional[type], location: Optional[PurePath] = None
    ) -> int:
        """
        Calculate match score for this registration.

        Scoring weights (designed for clear precedence):
        - Location: 1000 (exact) or 0 (global/no-match)
        - Resource: 100 (exact), 10 (subclass), 0 (default)

        Returns -1 for no match, otherwise sum of location + resource scores.
        Higher scores indicate better matches.
        """
        # Location scoring: binary (match or no-match)
        match (self.location, location):
            case (None, _):  # Global registration - available everywhere
                location_score = 0
            case (
                loc,
                None,
            ):  # Location-specific registration, but no location requested
                return -1  # No match
            case (loc, req) if loc == req or req.is_relative_to(loc):
                location_score = 1000  # Match (exact or hierarchical)
            case _:
                return -1  # No match

        # Resource scoring: three-tier precedence
        match (self.resource, resource):
            case (None, _):  # Default/global
                resource_score = 0
            case (r, req) if r is req:  # Exact match
                resource_score = 100
            case (r, req) if req is not None and issubclass(req, r):  # Subclass
                resource_score = 10
            case _:
                return -1  # No match

        return location_score + resource_score


@dataclass(frozen=True)
class ServiceLocator:
    """
    Thread-safe, immutable locator for multiple service implementations with resource and location-based selection.

    This is the ONE locator for the entire application. Implementations are stored in LIFO
    order (most recent first). Selection uses three-tier precedence: exact > subclass > default.

    Resource-based matching allows different implementations to be selected based on business
    entity types like Customer, Employee, or Product.

    Location-based matching allows different implementations to be selected based on hierarchical
    context like URL paths (/admin, /public). Hierarchical matching walks up the location tree
    from most specific to least specific, stopping at the first level where matches are found.

    Thread-safe: All data is immutable (frozen dataclass with dicts).

    Performance Optimization: The system automatically uses a fast O(1) lookup path for service
    types with a single registration, and switches to an O(m) scoring path only when a second
    implementation is registered for the same service type (where m is the number of registrations
    for that specific service). This makes the single-implementation case nearly as fast as using
    svcs directly.

    Caching: Results are cached for performance. Cache is keyed by (service_type, resource_type, location)
    tuple and stores the resolved implementation class or None.

    Example:
        locator = ServiceLocator()
        locator = locator.register(Greeting, DefaultGreeting)
        locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
        locator = locator.register(Greeting, AdminGreeting, location=PurePath("/admin"))
        locator = locator.register(Database, PostgresDB)
    """

    # Internal storage: service types with single registration use fast path
    _single_registrations: dict[type, FactoryRegistration] = field(default_factory=dict)
    # Internal storage: service types with multiple registrations use scoring path
    _multi_registrations: dict[type, tuple[FactoryRegistration, ...]] = field(
        default_factory=dict
    )
    _cache: dict[tuple[type, Optional[type], Optional[PurePath]], Optional[type]] = (
        field(default_factory=dict)
    )

    def register(
        self,
        service_type: type,
        implementation: type,
        resource: Optional[type] = None,
        location: Optional[PurePath] = None,
    ) -> "ServiceLocator":
        """
        Return new ServiceLocator with additional registration (immutable, thread-safe).

        LIFO ordering: new registrations are inserted at the front.
        Cache invalidation: new instance has empty cache since registrations changed.

        Performance: First registration for a service type uses fast O(1) path. Second and
        subsequent registrations switch to O(m) scoring path where m is registrations for
        that specific service type.

        Args:
            service_type: The service type to register for
            implementation: The implementation class
            resource: Optional resource type for resource-specific resolution
            location: Optional location (PurePath) for location-specific resolution

        Returns:
            New ServiceLocator with the registration prepended and cleared cache
        """
        new_reg = FactoryRegistration(service_type, implementation, resource, location)

        # Copy existing dicts (immutable update pattern)
        new_single = dict(self._single_registrations)
        new_multi = {k: v for k, v in self._multi_registrations.items()}

        # Case 1: First registration for this service_type (fast path)
        if service_type not in new_single and service_type not in new_multi:
            new_single[service_type] = new_reg

        # Case 2: Second registration for this service_type (promote to multi)
        elif service_type in new_single:
            existing = new_single[service_type]
            # LIFO: new registration first, then existing
            new_multi[service_type] = (new_reg, existing)
            del new_single[service_type]

        # Case 3: Third+ registration for this service_type (add to multi)
        else:  # service_type in new_multi
            existing_tuple = new_multi[service_type]
            # LIFO: prepend new registration
            new_multi[service_type] = (new_reg,) + existing_tuple

        # Return new instance with empty cache (cache invalidation)
        return ServiceLocator(
            _single_registrations=new_single,
            _multi_registrations=new_multi,
        )

    def get_implementation(
        self,
        service_type: type,
        resource: Optional[type] = None,
        location: Optional[PurePath] = None,
    ) -> Optional[type]:
        """
        Find best matching implementation class for a service type using precedence scoring.

        The resource parameter specifies a business entity type (like Customer or Employee)
        to select the appropriate implementation.

        The location parameter specifies a hierarchical context (like PurePath("/admin"))
        to select location-specific implementations. Location matching uses hierarchical
        traversal: walks up the location tree from most specific to root, checking all
        registrations at each level.

        Results are cached for performance. The cache key is (service_type, resource_type, location).

        Performance: Uses O(1) fast path for service types with single registration, O(m) scoring
        path for multiple registrations (where m is registrations for that specific service type).

        Args:
            service_type: The service type to find an implementation for
            resource: Optional resource type for resource-based matching
            location: Optional location for location-based matching

        Returns:
            The implementation class from the first registration with highest score.

        Thread-safe: Only reads immutable data (cache is mutated but that's thread-safe for dicts).
        """
        cache_key = (service_type, resource, location)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        best_impl = None

        # Fast path: single registration for this service type (O(1) lookup)
        if service_type in self._single_registrations:
            reg = self._single_registrations[service_type]
            score = reg.matches(resource, location)
            if score >= 0:  # Valid match (score 0 is valid for default registrations)
                best_impl = reg.implementation

        # Slow path: multiple registrations for this service type (O(m) scoring with hierarchical location matching)
        elif service_type in self._multi_registrations:
            best_score = -1

            # If location is provided, walk up the hierarchy from most specific to root
            # At each level, check all registrations for matches
            # Most specific location wins (deeper in hierarchy)
            if location is not None:
                # Generate hierarchy: current location, then all parents up to root
                # Example: /admin/users/profile -> [/admin/users/profile, /admin/users, /admin, /]
                hierarchy = [location] + list(location.parents)

                # Track the best match found at each hierarchy level
                # We want the most specific location to win
                level_best_impl = None  # Track best global match as fallback
                level_best_score = -1

                for current_location in hierarchy:
                    location_best_score = -1
                    location_best_impl = None
                    found_location_specific = (
                        False  # Track if we found a location-specific match
                    )

                    # Check all registrations at this hierarchy level
                    for reg in self._multi_registrations[service_type]:
                        # At this level, consider:
                        # 1. Registrations at exactly this location (highest priority)
                        # 2. Global registrations (location=None) as fallback (lower priority)
                        if reg.location == current_location:
                            # Exact location match - this level has a location-specific service
                            found_location_specific = True
                            score = reg.matches(resource, current_location)
                            if score > location_best_score:
                                location_best_score = score
                                location_best_impl = reg.implementation
                        elif reg.location is None:
                            # Global registration - available everywhere, but lower priority
                            score = reg.matches(resource, current_location)
                            if score > level_best_score:
                                level_best_score = score
                                level_best_impl = reg.implementation

                    # Only stop if we found a location-specific match at this level
                    # (not just a global match - we want to continue searching up the hierarchy)
                    if found_location_specific and location_best_impl is not None:
                        best_impl = location_best_impl
                        best_score = location_best_score
                        break  # Stop at first level with location-specific matches (most specific wins)

                # If we never found a location-specific match, use the best global match
                if best_impl is None and level_best_impl is not None:
                    best_impl = level_best_impl
                    best_score = level_best_score
            else:
                # No location specified - use standard scoring
                for reg in self._multi_registrations[service_type]:
                    score = reg.matches(resource, location)
                    if score > best_score:
                        best_score = score
                        best_impl = reg.implementation
                        # Early exit optimization for perfect score
                        # Perfect score: exact location (1000) + exact resource (100) = 1100
                        if score >= 1100:
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
    # Type ignore needed: implementation is type[T], calling it returns T,
    # but type checkers can't infer constructor signatures generically
    return implementation()  # type: ignore[return-value]


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
    resource: Optional[type] = (
        None  # Optional: type to get from container for resource (e.g., RequestContext)
    )

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names, except 'children' which is ignored."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            # Special case: 'children' is allowed even if not a field (for template systems)
            if kwarg_name == "children":
                continue
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

    def _get_location(self) -> Optional[PurePath]:
        """Get the Location from container if registered."""
        try:
            return self.container.get(Location)
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

        # Tier 2: Inject from container (with locator support)
        if field_info.is_injectable:
            inner_type = field_info.inner_type
            if inner_type is None:
                raise TypeError(f"Inject field '{field_name}' has no inner type")

            # Check for Container injection first (bypasses locator)
            if inner_type is svcs.Container:
                return (True, self.container)

            # Try locator first for types with multiple implementations
            try:
                locator = self.container.get(ServiceLocator)
                resource_type = self._get_resource()
                location = self._get_location()

                implementation = locator.get_implementation(
                    inner_type, resource_type, location
                )
                if implementation is not None:
                    # Construct instance using the injector recursively (for nested injection)
                    return (True, self(implementation))
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
            **kwargs: Keyword arguments that override any resolved dependencies.
                     The 'children' kwarg is ignored if not a valid field.

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs (other than 'children') are provided
            TypeError: If an Inject field has no inner type
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
    for resolving Inject[T] dependencies.

    Implements the same three-tier precedence as HopscotchInjector:
    1. kwargs passed to injector (highest priority)
    2. ServiceLocator for Inject[T] types, falling back to container.aget(T)
    3. default values from field definitions (lowest priority)

    Special handling: The 'children' kwarg is silently ignored if not a valid field, to support
    template rendering systems (like tdom) that always pass children even when not needed.
    """

    container: svcs.Container
    resource: Optional[type] = None

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names, except 'children' which is ignored."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            # Special case: 'children' is allowed even if not a field (for template systems)
            if kwarg_name == "children":
                continue
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

    async def _get_location(self) -> Optional[PurePath]:
        """Get the Location from container if registered."""
        try:
            return await self.container.aget(Location)
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

        # Tier 2: Inject from container (async, with locator support)
        if field_info.is_injectable:
            inner_type = field_info.inner_type
            if inner_type is None:
                raise TypeError(f"Inject field '{field_name}' has no inner type")

            # Check for Container injection first (bypasses locator)
            if inner_type is svcs.Container:
                return (True, self.container)

            # Try locator first for types with multiple implementations
            try:
                locator = await self.container.aget(ServiceLocator)
                resource_type = await self._get_resource()
                location = await self._get_location()

                implementation = locator.get_implementation(
                    inner_type, resource_type, location
                )
                if implementation is not None:
                    # Construct instance using the injector recursively (for nested injection)
                    return (True, await self(implementation))
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
            **kwargs: Keyword arguments that override any resolved dependencies.
                     The 'children' kwarg is ignored if not a valid field.

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs (other than 'children') are provided
            TypeError: If an Inject field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await self._resolve_field_value_async(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


# ============================================================================
# Package Scanning Implementation
# ============================================================================


def _create_injector_factory(target_class: type) -> Any:
    """Create a factory function for a decorated class."""

    def factory(svcs_container: svcs.Container) -> Any:
        try:
            injector = svcs_container.get(Injector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultInjector(container=svcs_container)
        return injector(target_class)

    return factory


def _get_or_create_locator(registry: svcs.Registry) -> ServiceLocator:
    """Get existing ServiceLocator from registry or create new one."""
    try:
        temp_container = svcs.Container(registry)
        return temp_container.get(ServiceLocator)
    except svcs.exceptions.ServiceNotFoundError:
        return ServiceLocator()


def _register_decorated_items(
    registry: svcs.Registry,
    decorated_items: list[tuple[type, dict[str, Any]]],
) -> None:
    """Register all decorated items to registry and/or locator."""
    locator = _get_or_create_locator(registry)
    locator_modified = False

    for decorated_class, metadata in decorated_items:
        resource = metadata.get("resource")
        location = metadata.get("location")
        service_type = (
            metadata.get("for_") or decorated_class
        )  # Default to self if None

        # Use ServiceLocator for:
        # 1. Resource-based registrations (resource != None)
        # 2. Location-based registrations (location != None)
        # 3. Multi-implementation scenarios (for_ != None, service_type != decorated_class)
        if (
            resource is not None
            or location is not None
            or service_type != decorated_class
        ):
            locator = locator.register(
                service_type, decorated_class, resource=resource, location=location
            )
            locator_modified = True
        else:
            # Direct registry registration (no resource, no location, no service type override)
            factory = _create_injector_factory(decorated_class)
            registry.register_factory(decorated_class, factory)

    if locator_modified:
        registry.register_value(ServiceLocator, locator)


def _caller_module(level: int = 2) -> ModuleType | None:
    """
    Return the module of the caller at a specific frame level.

    Uses sys._getframe to inspect the call stack and find the module
    that called the current function.

    Args:
        level: Frame level to inspect (2 = caller's caller by default)

    Returns:
        The ModuleType of the caller, or None if in special contexts like doctests
    """
    import sys

    try:
        frame = sys._getframe(level)
        module_globals = frame.f_globals
        module_name = module_globals.get("__name__") or "__main__"

        # Special case: doctest/Sybil execution
        if module_name == "__test__":
            return None

        return sys.modules.get(module_name)
    except (AttributeError, ValueError, KeyError):
        return None


def _caller_package(level: int = 2) -> ModuleType | None:
    """
    Return the package of the caller at a specific frame level.

    This is useful for automatically detecting the calling package when
    scan() is called without arguments, enabling convenient usage like:
        scan(registry)  # Automatically scans the caller's package

    Args:
        level: Frame level to inspect (2 = caller's caller by default)

    Returns:
        The package ModuleType of the caller, or None if detection fails
    """
    module = _caller_module(level + 1)
    if module is None:
        return None

    # Check if this module is itself a package (has __init__.py)
    module_file = getattr(module, "__file__", "")
    if "__init__.py" in module_file or "__init__$py" in module_file:
        return module

    # Not a package, go up one level to get the containing package
    module_name = module.__name__
    if "." in module_name:
        package_name = module_name.rsplit(".", 1)[0]
        import sys

        return sys.modules.get(package_name)

    return module


def _scan_locals(frame_locals: dict[str, Any]) -> list[tuple[type, dict[str, Any]]]:
    """Scan local variables for @injectable decorated classes."""
    return [
        (obj, obj.__injectable_metadata__)
        for obj in frame_locals.values()
        if isinstance(obj, type) and hasattr(obj, "__injectable_metadata__")
    ]


def _import_package(pkg: str) -> ModuleType | None:
    """Import a package by string name, logging warnings on failure."""
    try:
        return importlib.import_module(pkg)
    except ImportError as e:
        log.warning(f"Failed to import package '{pkg}': {e}")
        return None


def _collect_modules_to_scan(
    packages: tuple[str | ModuleType | None, ...],
) -> list[ModuleType]:
    """Collect and import all packages to scan."""
    modules = []
    for pkg in packages:
        match pkg:
            case None:
                continue
            case str():
                if module := _import_package(pkg):
                    modules.append(module)
            case ModuleType():
                modules.append(pkg)
            case _:
                log.warning(
                    f"Invalid package type: {type(pkg)}. Must be str, ModuleType, or None"
                )
    return modules


def _discover_submodules(module: ModuleType) -> list[ModuleType]:
    """Discover all submodules within a package."""
    if not hasattr(module, "__path__"):
        return []

    submodules = []
    try:
        for _, modname, _ in pkgutil.walk_packages(
            path=module.__path__,  # type: ignore[attr-defined]
            prefix=module.__name__ + ".",
            onerror=lambda name: None,
        ):
            if submodule := _import_package(modname):
                submodules.append(submodule)
    except Exception as e:
        log.warning(f"Error walking package '{module.__name__}': {e}")

    return submodules


def _discover_all_modules(modules_to_scan: list[ModuleType]) -> list[ModuleType]:
    """Discover all modules including submodules from packages."""
    discovered = list(modules_to_scan)
    for module in modules_to_scan:
        discovered.extend(_discover_submodules(module))
    return discovered


def _extract_decorated_items(module: ModuleType) -> list[tuple[type, dict[str, Any]]]:
    """Extract @injectable decorated classes from a module."""
    items = []
    for attr_name in dir(module):
        try:
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and hasattr(attr, "__injectable_metadata__"):
                items.append((attr, attr.__injectable_metadata__))
        except (AttributeError, ImportError):
            continue
    return items


def _collect_decorated_items(
    modules: list[ModuleType],
) -> list[tuple[type, dict[str, Any]]]:
    """Collect all @injectable decorated items from modules."""
    return [item for module in modules for item in _extract_decorated_items(module)]


def scan(
    registry: svcs.Registry,
    *packages: str | ModuleType | None,
    locals_dict: dict[str, Any] | None = None,
) -> svcs.Registry:
    """
    Scan packages/modules for @injectable decorated classes and register them.

    Discovers and registers services marked with @injectable decorator. Classes with
    resource or location metadata are registered to ServiceLocator for resource-based or
    location-based resolution. Classes without resource/location metadata are registered
    directly to Registry.

    Args:
        registry: svcs.Registry to register services into
        *packages: Package/module references to scan:
                   - String names: "myapp.services" (auto-imported)
                   - ModuleType objects: myapp.services
                   - None/empty: Auto-detects caller's package
                   - Multiple: scan(registry, "app.models", "app.views")
        locals_dict: Dictionary of local variables to scan (useful for testing)

    Returns:
        The registry instance for method chaining.

    Examples:
        scan(registry)                           # Auto-detect caller's package
        scan(registry, "myapp.services")         # Specific package
        scan(registry, locals_dict=locals())     # Test pattern

    See examples/scanning/ for complete examples.
    """
    # Handle locals_dict scanning for testing
    if locals_dict is not None:
        decorated_items = _scan_locals(locals_dict)
        _register_decorated_items(registry, decorated_items)
        return registry

    # Auto-detect caller's package if not specified
    if not packages or (len(packages) == 1 and packages[0] is None):
        if caller_pkg := _caller_package(level=2):
            packages = (caller_pkg,)
        else:
            log.warning(
                "Could not auto-detect caller's package. No scanning performed."
            )
            return registry

    # Collect, discover, and register
    modules_to_scan = _collect_modules_to_scan(packages)
    discovered_modules = _discover_all_modules(modules_to_scan)
    decorated_items = _collect_decorated_items(discovered_modules)
    _register_decorated_items(registry, decorated_items)
    return registry
