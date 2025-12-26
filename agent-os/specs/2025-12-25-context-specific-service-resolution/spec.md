# Specification: Context-Specific Service Resolution

## Goal

Refactor context-based service resolution by renaming "context" to "resource" throughout the codebase to better
represent business entity matching, and implement svcs-style caching for improved performance of resource-based lookups.

## User Stories

- As a developer, I want clear "resource" terminology instead of "context" so that the API intuitively represents
  business entities like Customer, Employee, and Product
- As a developer, I want fast resource-based lookups with caching so that repeated service resolutions have minimal
  performance overhead

## Specific Requirements

**Terminology Rename: context to resource**

- Rename all occurrences of "context" to "resource" in parameter names, variable names, method names, and docstrings
- Update `FactoryRegistration.context` field to `FactoryRegistration.resource`
- Update `ServiceLocator.register()` context parameter to resource parameter
- Update `ServiceLocator.get_implementation()` request_context parameter to resource parameter
- Update `FactoryRegistration.matches()` request_context parameter to resource parameter
- Update HopscotchInjector and HopscotchAsyncInjector context_key attribute to resource attribute
- Update internal method `_get_request_context()` to `_get_resource()` in both injector classes
- Preserve all existing functionality while performing renames

**Resource Matching Strategy**

- Follow Hopscotch's proven matching patterns using `is` for exact match and `isinstance` for subclass match
- Maintain existing three-tier precedence: exact match score 2, subclass match score 1, default match score 0, no match
  score -1
- Keep LIFO ordering where most recent registrations are inserted at position 0 and checked first
- Early exit optimization when exact match (score 2) is found
- Filter registrations by service_type before scoring to avoid unnecessary checks

**Caching Implementation**

- Implement svcs-style caching for resource-based lookups since resource type information is static after import time
- Cache the resource-to-implementation mapping to achieve O(1) or near-O(1) lookups after initial construction
- Invalidate cache when new registrations are added via ServiceLocator.register()
- Consider using a simple dictionary cache keyed by (service_type, resource_type) tuple
- Cache should be transparent to users and not change existing API surface
- Avoid premature optimization - measure performance gains before complex caching strategies

**Integration Points**

- Update all 22 existing tests in `tests/test_locator.py` to use new "resource" terminology
- Update example file `examples/multiple_implementations.py` to use "resource" terminology
- Update documentation `docs/examples/multiple_implementations.md` to reflect resource-based thinking
- Ensure backward compatibility is not required since this is pre-1.0 release
- All error messages should use "resource" terminology for consistency

**Test Strategy**

- Adapt Hopscotch test patterns from `tests/test_registry.py` for resource matching validation
- Reuse existing 22 tests with updated terminology for regression coverage
- Add caching-specific tests to verify cache invalidation on new registrations
- Verify exact match and subclass match behavior mirrors Hopscotch implementation
- Test LIFO ordering with resource-specific registrations
- Validate that resource type extraction from container works correctly

## Existing Code to Leverage

**Hopscotch Registry matching logic at `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py`**

- Three-tier precedence system in `get_best_match()` method (lines 235-291) with high/medium/low buckets
- Exact context match using `is` operator (line 264: `this_context is context_class`)
- Subclass context match using `isinstance` and `issubclass` (lines 269-272)
- IsNoneType marker class pattern for representing None contexts (lines 32-35)
- LIFO ordering via `insert(0, registration)` pattern (line 377)

**Hopscotch test patterns at `/Users/pauleveritt/projects/pauleveritt/hopscotch/tests/test_registry.py`**

- Comprehensive context matching tests (lines 32-227) covering None, exact, and subclass cases
- Multiple context registration tests (lines 469-498) demonstrating precedence
- Nested registry parent/child tests for context inheritance (lines 276-285, 423-450)
- LIFO ordering validation tests (lines 350-372)
- Singleton vs class registration patterns for different use cases

**Current ServiceLocator implementation at `src/svcs_di/injectors/locator.py`**

- FactoryRegistration dataclass with matches() scoring method (lines 22-47)
- ServiceLocator LIFO registration via insert(0) pattern (line 68)
- Three-tier precedence in get_implementation() method (lines 70-94)
- HopscotchInjector integration with locator-based resolution (lines 136-256)
- HopscotchAsyncInjector async version following same patterns (lines 258-377)

**Existing test coverage at `tests/test_locator.py`**

- 22 passing tests covering all current functionality
- Factory registration matching tests (lines 73-94) for all precedence levels
- ServiceLocator registration and lookup tests (lines 97-159)
- HopscotchInjector integration tests (lines 254-421) with Injectable fields
- Async injector tests (lines 423-462) for async container methods
- LIFO override tests validating most-recent-wins behavior (lines 200-226, 375-400)

**svcs caching patterns for reference**

- Study svcs.Registry caching mechanisms for inspiration on implementation approach
- Resource type information is static after import time making it ideal for caching
- Simple dictionary-based cache should suffice for (service_type, resource_type) lookups
- Consider lazy cache construction on first get_implementation() call

## Out of Scope

- Complex scoring algorithms beyond existing three-tier precedence system
- Location-based matching or geographic context resolution
- Registration-time validation of implementation compatibility
- Resource lifecycle management or cleanup
- Middleware integration or hooks
- Changes to Injectable[T] field resolution logic
- Changes to async support patterns
- Modification of svcs.Container or svcs.Registry behavior
- Addition of new precedence tiers beyond exact/subclass/default
- Weighted scoring or priority values for registrations
