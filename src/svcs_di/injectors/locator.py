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

import functools
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import cast

import svcs

# ============================================================================
# Scoring Constants
# ============================================================================

# Scoring weights for service resolution precedence
LOCATION_SCORE_MATCH = 1000  # Exact or hierarchical location match
LOCATION_SCORE_GLOBAL = 0  # Global registration (no location constraint)
RESOURCE_SCORE_EXACT = 100  # Exact resource type match
RESOURCE_SCORE_SUBCLASS = 10  # Subclass resource type match
RESOURCE_SCORE_DEFAULT = 0  # Default/global registration (no resource constraint)
SCORE_NO_MATCH = -1  # No match found
PERFECT_SCORE = LOCATION_SCORE_MATCH + RESOURCE_SCORE_EXACT  # 1100


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
    resource: type | None = None
    location: PurePath | None = None

    def matches(self, resource: type | None, location: PurePath | None = None) -> int:
        """
        Calculate match score for this registration.

        Uses named constants for scoring weights to indicate precedence:
        - Location: LOCATION_SCORE_MATCH (1000) or LOCATION_SCORE_GLOBAL (0)
        - Resource: RESOURCE_SCORE_EXACT (100), RESOURCE_SCORE_SUBCLASS (10), or RESOURCE_SCORE_DEFAULT (0)

        Returns SCORE_NO_MATCH (-1) for no match, otherwise sum of location + resource scores.
        Higher scores indicate better matches.
        """
        # Location scoring: binary (match or no-match)
        match (self.location, location):
            case (None, _):  # Global registration - available everywhere
                location_score = LOCATION_SCORE_GLOBAL
            case (
                loc,
                None,
            ):  # Location-specific registration, but no location requested
                return SCORE_NO_MATCH
            case (loc, req) if loc == req or req.is_relative_to(loc):
                location_score = LOCATION_SCORE_MATCH  # Match (exact or hierarchical)
            case _:
                return SCORE_NO_MATCH

        # Resource scoring: three-tier precedence
        match (self.resource, resource):
            case (None, _):  # Default/global
                resource_score = RESOURCE_SCORE_DEFAULT
            case (r, req) if r is req:  # Exact match
                resource_score = RESOURCE_SCORE_EXACT
            case (r, req) if req is not None and issubclass(req, r):  # Subclass
                resource_score = RESOURCE_SCORE_SUBCLASS
            case _:
                return SCORE_NO_MATCH

        return location_score + resource_score


@functools.lru_cache(maxsize=512)
def _resolve_implementation_cached(
    single_reg: FactoryRegistration | None,
    multi_regs: tuple[FactoryRegistration, ...] | None,
    service_type: type,
    resource: type | None,
    location: PurePath | None,
) -> type | None:
    """
    Cached helper for finding best implementation.

    Uses LRU cache with bounded size (512 entries) to prevent unbounded memory growth.
    All parameters must be hashable for caching.

    Args:
        single_reg: Single registration if using fast path
        multi_regs: Tuple of registrations if using scoring path
        service_type: The service type to resolve
        resource: Optional resource type
        location: Optional location path

    Returns:
        The best matching implementation class, or None
    """
    # Fast path: single registration
    if single_reg is not None:
        score = single_reg.matches(resource, location)
        if score >= 0:
            return single_reg.implementation
        return None

    # Slow path: multiple registrations with scoring
    if multi_regs is not None:
        if location is not None:
            return _resolve_hierarchical_cached(multi_regs, resource, location)
        else:
            return _resolve_no_location_cached(multi_regs, resource)

    return None


@functools.lru_cache(maxsize=256)
def _resolve_hierarchical_cached(
    registrations: tuple[FactoryRegistration, ...],
    resource: type | None,
    location: PurePath,
) -> type | None:
    """
    Cached hierarchical location resolution.

    Walks up the location hierarchy from most specific to root.
    """
    hierarchy = (location,) + tuple(location.parents)
    global_best_impl = None
    global_best_score = SCORE_NO_MATCH

    for current_location in hierarchy:
        location_best_score = SCORE_NO_MATCH
        location_best_impl = None
        found_location_specific = False

        for reg in registrations:
            if reg.location == current_location:
                found_location_specific = True
                score = reg.matches(resource, current_location)
                if score > location_best_score:
                    location_best_score = score
                    location_best_impl = reg.implementation
            elif reg.location is None:
                score = reg.matches(resource, current_location)
                if score > global_best_score:
                    global_best_score = score
                    global_best_impl = reg.implementation

        if found_location_specific and location_best_impl is not None:
            return location_best_impl

    return global_best_impl


@functools.lru_cache(maxsize=256)
def _resolve_no_location_cached(
    registrations: tuple[FactoryRegistration, ...],
    resource: type | None,
) -> type | None:
    """
    Cached resolution without location (standard scoring).

    Uses early exit optimization for perfect scores.
    """
    best_score = SCORE_NO_MATCH
    best_impl = None

    for reg in registrations:
        score = reg.matches(resource, None)
        if score > best_score:
            best_score = score
            best_impl = reg.implementation
            if score >= PERFECT_SCORE:
                break

    return best_impl


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

    def register(
        self,
        service_type: type,
        implementation: type,
        resource: type | None = None,
        location: PurePath | None = None,
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

        # Return new instance (no cache needed - caching handled by module-level functions)
        return ServiceLocator(
            _single_registrations=new_single,
            _multi_registrations=new_multi,
        )

    def get_implementation(
        self,
        service_type: type,
        resource: type | None = None,
        location: PurePath | None = None,
    ) -> type | None:
        """
        Find best matching implementation class for a service type using precedence scoring.

        The resource parameter specifies a business entity type (like Customer or Employee)
        to select the appropriate implementation.

        The location parameter specifies a hierarchical context (like PurePath("/admin"))
        to select location-specific implementations. Location matching uses hierarchical
        traversal: walks up the location tree from most specific to root, checking all
        registrations at each level.

        Results are cached via LRU cache (maxsize=512) in the helper functions for performance.

        Performance: Uses O(1) fast path for service types with single registration, O(m) scoring
        path for multiple registrations (where m is registrations for that specific service type).

        Args:
            service_type: The service type to find an implementation for
            resource: Optional resource type for resource-based matching
            location: Optional location for location-based matching

        Returns:
            The implementation class from the first registration with highest score.

        Thread-safe: All data is immutable and caching is handled by functools.lru_cache.
        """
        # Get registrations (or None if not present)
        single_reg = self._single_registrations.get(service_type)
        multi_regs = self._multi_registrations.get(service_type)

        # Delegate to cached resolution function
        return _resolve_implementation_cached(
            single_reg, multi_regs, service_type, resource, location
        )


def get_from_locator[T](
    container: svcs.Container,
    service_type: type[T],
    resource: type | None = None,
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

    # Construct the instance from the implementation class.
    # Cast needed: implementation is type (subclass of service_type), calling it
    # returns an instance, but type checkers can't verify this statically.
    return cast(T, implementation())


# ============================================================================
# Re-exports for backwards compatibility
# ============================================================================

# HopscotchInjector and HopscotchAsyncInjector have been moved to hopscotch.py
from svcs_di.injectors.hopscotch import (  # noqa: E402
    HopscotchAsyncInjector,
    HopscotchInjector,
)

# scan() and related functions have been moved to scanning.py
from svcs_di.injectors.scanning import scan  # noqa: E402

__all__ = [
    "Location",
    "FactoryRegistration",
    "ServiceLocator",
    "get_from_locator",
    "HopscotchInjector",
    "HopscotchAsyncInjector",
    "scan",
]
