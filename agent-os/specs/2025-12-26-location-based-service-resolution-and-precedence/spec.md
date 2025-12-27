# Specification: Location-Based Service Resolution and Precedence

## Goal

Add hierarchical location-based service resolution to enable URL-path or filesystem-like service selection, with
intelligent precedence scoring when multiple registrations match a request based on both context and location
predicates.

## User Stories

- As a web application developer, I want to register different implementations of a service for different URL paths (
  e.g., `/admin` vs `/public`) so that requests are handled by location-appropriate services
- As a framework user, I want the most specific location match to automatically win when multiple services could satisfy
  my request, so that I don't have to manually specify which implementation to use

## Specific Requirements

**Location Using PurePath**

- Use Python's `pathlib.PurePath` directly to represent hierarchical locations
- PurePath provides immutable path objects with built-in hierarchy operations (`.parents`, `.is_relative_to()`)
- PurePath is thread-safe and works with free-threaded Python
- Accept PurePath instances in all location-related APIs
- Use PurePath's built-in comparison and hierarchy methods for location matching
- Root location is represented as `PurePath("/")`

**Location as Special Service**

- `PurePath` (aliased as `Location` for semantic clarity) is a special service type that containers have access to
- When a container is created, a `PurePath` instance is registered as a value service in the container
- Services can depend on `PurePath` (or `Location` type alias) using `Injectable[Location]` to access the current request location
- The Location service represents "where" the current request is happening in the application hierarchy

**Service Registration with Location**

- Extend the `@injectable` decorator to accept a `location` parameter: `@injectable(location=PurePath("/admin"))`
- Extend `ServiceLocator.register()` to accept an optional `location` parameter (PurePath instance)
- Services registered with a location are ONLY available when requested from that location or its children
- Services can be registered with both `resource` AND `location` parameters for combined filtering
- Store location information in registration metadata alongside existing resource information

**Location Hierarchy Matching**

- When resolving a service, walk up the PurePath hierarchy from the current location (most specific) to root (least specific) using `.parents`
- At each level, check for exact matches against registered service locations
- Stop at the first level where a match is found and evaluate all matches at that level
- More specific locations (deeper in hierarchy) always take precedence over less specific locations
- If no location-specific service is found, fall back to services registered without a location (default/global services)

**Precedence and Scoring System**

- Implement hard-coded scoring weights for predictable behavior (no configurable weights)
- Score each registration based on how well it matches the request: exact location match (weight: 100) + exact resource
  match (weight: 10) + registered at all (weight: 1)
- Services with both location AND resource matches score higher than services with only one predicate match
- When multiple services match, select the one with the highest combined score
- In case of tied scores, use LIFO ordering (most recently registered wins)

**Registration Storage and Lookup**

- Consider efficient data structures beyond flat list iteration: tree-based lookup indexed by location, ChainMap for
  layered resolution, or hybrid approaches
- Optimize for the common case: looking up services by location should not require iterating through all registrations
- Preserve backward compatibility: services registered without location should still work with existing flat-list lookup
- Balance memory usage vs lookup speed: avoid duplicating registration data across multiple data structures

**Integration with Existing HopscotchInjector**

- Extend `HopscotchInjector` to check for Location in the container and use it during service resolution
- Location matching works alongside existing resource-based matching in the injector
- Update `_resolve_field_value_sync` and `_resolve_field_value_async` to consider location when calling
  `locator.get_implementation()`
- Preserve existing three-tier precedence: kwargs override > container/locator resolution > default values

**API Consistency**

- Follow existing patterns: use `location` parameter name consistently across decorator, register methods, and internal
  APIs
- Location matching should feel natural alongside resource matching: both use similar predicate/matching patterns
- Error messages should clearly indicate when a service is not available at a location (distinct from "not registered at
  all")

**Thread Safety for Free-Threaded Python**

- PurePath instances are immutable and thread-safe by design
- Registration lookups must be thread-safe (existing cache pattern in ServiceLocator already handles this)
- No shared mutable state during location matching or hierarchy traversal

**Testing Strategy**

- Test PurePath hierarchy operations (`.parents`, equality, comparison)
- Test registration with location parameter using PurePath instances
- Test exact location matching at multiple hierarchy levels
- Test hierarchical fallback: child location can use parent location's service
- Test precedence scoring with various combinations of location and resource matches
- Test integration with HopscotchInjector's Injectable resolution
- Test error cases: service not available at location, invalid PurePath construction, circular dependencies

## Visual Design

No visual assets provided.

## Existing Code to Leverage

**ServiceLocator and FactoryRegistration**

- Extend `FactoryRegistration` dataclass to include an optional `location` field alongside existing `resource` field
- Extend `ServiceLocator.register()` method to accept `location` parameter
- Follow the same immutable pattern: return new ServiceLocator instances with updated registrations
- Leverage existing `_cache` pattern for performance, extending cache key to include location
- Follow the LIFO registration pattern (most recent first) that already exists

**HopscotchInjector Resolution Pattern**

- Extend `_resolve_field_value_sync` and `_resolve_field_value_async` to retrieve Location from container
- Follow existing pattern of trying ServiceLocator first, then falling back to standard container.get()
- Maintain the three-tier precedence that already exists (kwargs, locator/container, defaults)
- Use the same exception handling patterns for ServiceNotFoundError

**@injectable Decorator Pattern**

- Extend the decorator in `decorators.py` to accept `location` parameter (PurePath) in metadata dictionary
- Follow existing pattern: `@injectable(resource=X)` becomes `@injectable(location=PurePath(Y))` or
  `@injectable(resource=X, location=PurePath(Y))`
- Store location in `__injectable_metadata__` dictionary alongside resource
- Maintain decorator overload signatures for both bare `@injectable` and `@injectable(...)` syntax

**Scanning Infrastructure**

- Leverage existing `scan()` function in `locator.py` to discover location-decorated services
- Follow the pattern where resource-decorated services go to ServiceLocator, others go to Registry
- Services with location metadata should also be registered to ServiceLocator (possibly requiring both resource and
  location)
- Use existing `_register_decorated_items()` pattern to handle location-based registrations

**Matching and Scoring Pattern**

- Follow the `FactoryRegistration.matches()` method pattern that returns integer scores
- Extend scoring to include location matches: combine resource score and location score
- Use the same pattern of iterating registrations and tracking best_score/best_impl
- Maintain early-exit optimization when perfect match is found (score can't be beaten)

## Out of Scope

- Wildcard patterns in locations (e.g., `/admin/*` or `/users/*/profile`)
- Regex matching for location paths
- Dynamic location computation or resolution at runtime (locations are static at registration time)
- Custom scoring functions or configurable precedence weights (hard-coded only)
- Services that are PREFERRED at a location but available elsewhere (only ONLY mode supported)
- Complex query languages for location matching beyond hierarchical path matching
- Location-based access control, permissions, or security features
- Performance optimizations beyond data structure choice (no caching strategies, pre-compilation, etc.)
- Location aliasing or symlink-like behavior
- Middleware or hooks for location resolution lifecycle events
