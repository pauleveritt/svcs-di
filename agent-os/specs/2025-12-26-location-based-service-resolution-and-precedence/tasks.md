# Task Breakdown: Location-Based Service Resolution and Precedence

## Overview

Total Tasks: 4 major task groups with 21 sub-tasks

This feature adds hierarchical location-based service resolution using `pathlib.PurePath` to enable URL-path or filesystem-like service selection with intelligent precedence scoring. Location is treated as a special service in containers, and services can be registered with location constraints that restrict them to specific parts of the application hierarchy.

## Task List

### Core Location Infrastructure

#### Task Group 1: Location Type Alias and PurePath Integration
**Dependencies:** None

- [x] 1.0 Complete location type infrastructure
  - [x] 1.1 Write 2-5 focused tests for PurePath hierarchy operations
    - Test PurePath creation from strings (e.g., `PurePath("/admin")`, `PurePath("/admin/users")`)
    - Test hierarchy traversal using `.parents` (e.g., `/admin/users` -> `/admin` -> `/`)
    - Test `.is_relative_to()` for child/parent relationships
    - Test equality and comparison operations
    - Test root location representation as `PurePath("/")`
  - [x] 1.2 Add Location type alias in appropriate module
    - Create `Location = PurePath` type alias in `src/svcs_di/injectors/locator.py`
    - Add to `__all__` exports
    - Document that Location represents hierarchical request context (URL paths, filesystem-like)
  - [x] 1.3 Document PurePath as special service type
    - Add docstring explaining Location/PurePath as special service
    - Explain that containers have Location registered as value service
    - Document how services depend on Location via `Inject[Location]`
  - [x] 1.4 Ensure location infrastructure tests pass
    - Run ONLY the 2-5 tests written in 1.1
    - Verify PurePath hierarchy operations work correctly

**Acceptance Criteria:**
- The 2-5 tests written in 1.1 pass
- Location type alias created and exported
- PurePath hierarchy operations (parents, is_relative_to) work correctly
- Documentation explains Location as special service concept

### Service Registration Layer

#### Task Group 2: Registration with Location Parameter
**Dependencies:** Task Group 1

- [x] 2.0 Complete service registration with location support
  - [x] 2.1 Write 3-6 focused tests for location-based registration
    - Test registering service with location parameter (PurePath instance)
    - Test registering service with both resource AND location parameters
    - Test that location is stored in registration metadata
    - Test LIFO ordering preserved with location registrations
  - [x] 2.2 Extend FactoryRegistration dataclass
    - Add optional `location: Optional[PurePath]` field to FactoryRegistration
    - Field should be `None` by default (backward compatibility)
    - Update `matches()` method signature to accept optional location parameter
    - Preserve existing frozen=True immutability
  - [x] 2.3 Implement location matching logic in FactoryRegistration
    - Extend `matches()` method to score location matches
    - Return score combining resource match + location match
    - Use hard-coded weights: exact location match (100) + exact resource match (10) + registered (1)
    - Location matching: exact match only (no prefix or partial matching yet)
  - [x] 2.4 Extend ServiceLocator.register() method
    - Add optional `location: Optional[PurePath]` parameter
    - Pass location to FactoryRegistration constructor
    - Maintain immutable pattern (return new ServiceLocator)
    - Preserve LIFO ordering (prepend new registration)
  - [x] 2.5 Update ServiceLocator.with_registrations() factory
    - Extend tuple signature to include optional location: `tuple[type, type, Optional[type], Optional[PurePath]]`
    - Maintain backward compatibility with 3-tuple format
    - Support both formats: `(service, impl, resource)` and `(service, impl, resource, location)`
    - NOTE: This method doesn't exist in the codebase, so this subtask is marked complete as N/A
  - [x] 2.6 Ensure registration layer tests pass
    - Run ONLY the 3-6 tests written in 2.1
    - Verify services can be registered with location
    - Verify location stored in metadata correctly

**Acceptance Criteria:**
- The 3-6 tests written in 2.1 pass (6 tests created and passing)
- FactoryRegistration has location field
- ServiceLocator.register() accepts location parameter
- Location information stored in registration metadata
- Backward compatibility maintained (location is optional)

### Location Resolution and Precedence

#### Task Group 3: Hierarchical Lookup and Scoring System
**Dependencies:** Task Group 2 (completed)

- [x] 3.0 Complete location-based resolution with precedence
  - [x] 3.1 Write 4-8 focused tests for location resolution
    - Test exact location match resolution
    - Test hierarchical fallback (child location using parent's service)
    - Test precedence: location+resource match > location-only match > default
    - Test LIFO ordering with tied scores (most recent wins)
    - Test service not available at location (distinct error)
    - Test root location fallback behavior
  - [x] 3.2 Implement hierarchical location matching in matches()
    - Update FactoryRegistration.matches() to accept request_location parameter
    - Walk up location hierarchy using `.parents` (most specific first)
    - Check for exact matches at each level
    - Stop at first level with matches (most specific wins)
    - Return combined score: location_score (100) + resource_score (10/2/1) + base (1)
  - [x] 3.3 Update ServiceLocator.get_implementation()
    - Add optional `location: Optional[PurePath]` parameter
    - Pass location to each registration's matches() call
    - Track best_score and best_impl across all registrations
    - Early exit optimization when perfect score found
    - Update cache key to include location: `(service_type, resource, location)`
  - [x] 3.4 Implement location hierarchy traversal
    - For each service type, filter registrations by service_type first
    - Walk location hierarchy from most specific to root using `.parents`
    - At each level, check all registrations for exact location match
    - Combine location score with resource score
    - Select highest combined score (LIFO for ties)
  - [x] 3.5 Add Location-aware error handling
    - Create distinct error messages for "service not at location" vs "service not registered"
    - Include location path in error message for debugging
    - Preserve existing LookupError patterns
  - [x] 3.6 Ensure location resolution tests pass
    - Run ONLY the 4-8 tests written in 3.1
    - Verify hierarchical fallback works
    - Verify precedence scoring works correctly
    - Verify LIFO tie-breaking works

**Acceptance Criteria:**
- The 4-8 tests written in 3.1 pass (8 tests created and all passing)
- Hierarchical location matching works (walks up .parents)
- Precedence scoring uses hard-coded weights correctly
- Most specific location wins (deeper in hierarchy takes precedence)
- LIFO ordering breaks ties
- Error messages distinguish location vs registration issues

### Integration with HopscotchInjector

#### Task Group 4: Container Location and Injector Integration
**Dependencies:** Task Group 3 (completed)

- [x] 4.0 Complete HopscotchInjector integration with Location
  - [x] 4.1 Write 3-6 focused tests for injector integration
    - Test Location registered as value service in container
    - Test Inject[Location] dependency resolution
    - Test HopscotchInjector uses Location during resolution
    - Test three-tier precedence preserved (kwargs > locator+location > defaults)
    - Test services restricted to location (ONLY mode)
  - [x] 4.2 Register Location as special service in container
    - Create pattern for registering PurePath as value service in container
    - Document container creation pattern: `registry.register_value(Location, PurePath("/path"))`
    - Add example showing Location registration at container creation
  - [x] 4.3 Update HopscotchInjector._resolve_field_value_sync()
    - Check if Location service exists in container
    - If present, retrieve Location: `location = container.get(Location)`
    - Pass location to `locator.get_implementation(service_type, resource, location)`
    - Fall back to resource-only resolution if Location not in container
    - Preserve existing three-tier precedence pattern
  - [x] 4.4 Update HopscotchAsyncInjector._resolve_field_value_async()
    - Mirror sync implementation with async container methods
    - Use `await container.aget(Location)` to retrieve location
    - Pass location to `locator.get_implementation(service_type, resource, location)`
    - Maintain async error handling patterns
  - [x] 4.5 Extend @injectable decorator for location parameter
    - Add `location: Optional[PurePath]` parameter to _mark_injectable()
    - Store location in `__injectable_metadata__` alongside resource
    - Support syntax: `@injectable(location=PurePath("/admin"))`
    - Support combined: `@injectable(resource=X, location=PurePath("/admin"))`
    - Update decorator overload signatures in decorators.py
  - [x] 4.6 Update scan() to handle location-decorated services
    - Extract location from `__injectable_metadata__`
    - Pass location to `locator.register()` when present
    - Services with location go to ServiceLocator (like resource-decorated services)
    - Update _register_decorated_items() to handle location parameter
  - [x] 4.7 Ensure injector integration tests pass
    - Run ONLY the 3-6 tests written in 4.1
    - Verify Location retrieved from container
    - Verify location passed to ServiceLocator
    - Verify Inject[Location] works
    - Verify @injectable(location=...) works with scanning

**Acceptance Criteria:**
- The 3-6 tests written in 4.1 pass (7 tests created and all passing)
- Location registered as value service in containers
- Services can depend on Inject[Location]
- HopscotchInjector retrieves and uses Location during resolution
- @injectable decorator accepts location parameter
- scan() discovers and registers location-decorated services
- Three-tier precedence preserved (kwargs > locator+location > defaults)

### Testing and Documentation

#### Task Group 5: Comprehensive Testing and Examples
**Dependencies:** Task Groups 1-4

- [x] 5.0 Review tests and add strategic coverage
  - [x] 5.1 Review tests from Task Groups 1-4
    - Review 2-5 tests from location infrastructure (Task 1.1)
    - Review 3-6 tests from registration layer (Task 2.1)
    - Review 4-8 tests from resolution layer (Task 3.1)
    - Review 3-6 tests from injector integration (Task 4.1)
    - Total existing tests: approximately 12-25 tests
  - [x] 5.2 Analyze test coverage gaps for location-based resolution ONLY
    - Identify critical workflows missing test coverage
    - Focus on end-to-end location-based service selection scenarios
    - Check integration between location matching and resource matching
    - Verify thread-safety (PurePath immutability, cache behavior)
  - [x] 5.3 Write up to 8 additional integration tests maximum
    - Add maximum of 8 new tests to fill critical gaps
    - Focus on end-to-end workflows: container creation -> registration -> resolution
    - Test combined location + resource precedence scoring
    - Test location hierarchy with multiple nesting levels
    - Test error cases: invalid location, circular dependencies
    - Skip exhaustive edge cases, focus on business-critical scenarios
  - [x] 5.4 Run feature-specific tests only
    - Run ONLY tests related to location-based resolution feature
    - Expected total: approximately 20-33 tests maximum
    - Do NOT run entire application test suite
    - Verify all critical location workflows pass
  - [x] 5.5 Create example demonstrating location-based resolution
    - Create example file showing URL-path-like service selection
    - Demonstrate `/admin` vs `/public` service routing
    - Show hierarchical fallback behavior
    - Show combined resource + location matching
    - Place in `examples/location_based_resolution.py`
  - [x] 5.6 Update documentation for location feature
    - Update module docstrings in locator.py
    - Document Location type alias and PurePath usage
    - Document @injectable(location=...) decorator syntax
    - Add usage examples to scan() docstring
    - Document precedence/scoring weights

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 20-33 tests total)
- Critical location-based workflows covered by tests
- No more than 8 additional tests added when filling testing gaps
- Example demonstrates practical location-based service selection
- Documentation updated with location feature usage

## Execution Order

Recommended implementation sequence:

1. **Location Infrastructure (Task Group 1)** - Establishes Location type alias and PurePath foundations
2. **Registration Layer (Task Group 2)** - Extends registration to accept location parameter
3. **Resolution and Precedence (Task Group 3)** - Implements hierarchical matching and scoring
4. **Injector Integration (Task Group 4)** - Connects location to HopscotchInjector and decorator
5. **Testing and Documentation (Task Group 5)** - Validates feature and provides examples

## Key Technical Decisions

**Location Representation:**
- Use `pathlib.PurePath` directly instead of custom Location class
- PurePath is immutable, thread-safe, and compatible with free-threaded Python
- Provides built-in hierarchy operations (`.parents`, `.is_relative_to()`)

**Precedence Scoring (Hard-coded weights):**
- Exact location match: 100 points
- Exact resource match: 10 points
- Subclass resource match: 2 points
- Default registration (no resource): 1 point
- Base registration: 1 point
- Combined score = location_score + resource_score + base_score

**Location Matching Strategy:**
- Walk up PurePath hierarchy using `.parents` (most specific first)
- Check for exact matches only (no prefix or wildcard matching)
- Stop at first level where match found
- More specific locations (deeper) always win over less specific (shallower)

**ONLY Mode:**
- Services registered with location are ONLY available at that location or its children
- Not available elsewhere (no PREFERRED mode)

**Thread Safety:**
- PurePath instances are immutable (thread-safe by design)
- Cache mutations safe (dict operations thread-safe for simple get/set)
- No shared mutable state during location matching

## Implementation Notes

**Backward Compatibility:**
- All location parameters are optional (default to None)
- Services without location work as before (global/default services)
- Existing tests should pass without modification

**Data Structure Considerations:**
- Current implementation keeps flat list iteration for simplicity
- Cache optimization with (service_type, resource, location) keys
- Future optimization opportunity: tree-based or ChainMap structure for location lookup

**Integration Points:**
- ServiceLocator (FactoryRegistration, register(), get_implementation())
- HopscotchInjector (_resolve_field_value_sync, _resolve_field_value_async)
- @injectable decorator (decorators.py)
- scan() function (locator.py)

**Error Handling:**
- Distinguish "service not at location" from "service not registered"
- Include location path in error messages for debugging
- Preserve existing exception patterns (LookupError)
