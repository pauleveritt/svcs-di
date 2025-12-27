# Task Breakdown: Context-Specific Service Resolution

## Overview

**Feature:** Refactor context-based service resolution by renaming "context" to "resource" and implementing caching

**Type:** Refactoring and enhancement (building on completed roadmap item 5)

**Total Task Groups:** 6

**Existing Implementation:**

- `src/svcs_di/injectors/locator.py` - 490 lines with ServiceLocator, HopscotchInjector, HopscotchAsyncInjector
- `tests/test_locator.py` - 32 passing tests (610 lines)
- `examples/multiple_implementations.py` - Complete working example (413 lines)
- `docs/examples/multiple_implementations.md` - Full documentation (566 lines)

**Key Constraints:**

- This is a refactoring task - preserve all existing functionality
- All existing tests must continue to pass with updated terminology
- No breaking changes to API surface beyond terminology rename
- Caching must be transparent to users

## Task List

### Task Group 1: Terminology Rename in Core Classes ✅

**Dependencies:** None

**Focus:** Update FactoryRegistration and ServiceLocator classes with new "resource" terminology

- [x] 1.0 Complete core class terminology updates
    - [x] 1.1 Write 2-5 focused tests for resource terminology
        - Test FactoryRegistration with resource parameter instead of context
        - Test ServiceLocator.register() with resource parameter
        - Test ServiceLocator.get_implementation() with resource parameter
        - Verify backwards compatibility is NOT needed (pre-1.0)
        - Reference: Existing tests in test_locator.py lines 73-159
    - [x] 1.2 Update FactoryRegistration class (lines 22-47)
        - Rename `context: Optional[type]` field to `resource: Optional[type]` (line 27)
        - Update `matches(request_context: Optional[type])` to `matches(resource: Optional[type])` (line 29)
        - Update docstring "optional context" to "optional resource" (line 23)
        - Update method docstring to use "resource" terminology (lines 30-38)
        - Update variable references: `self.context` → `self.resource` throughout method (lines 39-46)
        - Update variable references: `request_context` → `resource` throughout method (lines 39-46)
    - [x] 1.3 Update ServiceLocator.register() method (lines 61-68)
        - Rename `context: Optional[type]` parameter to `resource: Optional[type]` (line 65)
        - Update FactoryRegistration instantiation to use `resource` (line 68)
        - Update docstring "optional context" to "optional resource" (line 67)
    - [x] 1.4 Update ServiceLocator.get_implementation() method (lines 70-94)
        - Rename `request_context: Optional[type]` parameter to `resource: Optional[type]` (line 73)
        - Update call to `reg.matches(request_context)` to `reg.matches(resource)` (line 87)
        - Update docstring to reflect resource-based matching (lines 75-78)
    - [x] 1.5 Update ServiceLocator docstring and class documentation (lines 50-57)
        - Replace "context-based" with "resource-based" selection
        - Update class docstring to emphasize business entity matching
        - Add examples with Customer, Employee resource types
    - [x] 1.6 Update get_from_locator() function (lines 97-132)
        - Rename `request_context: Optional[type]` parameter to `resource: Optional[type]` (line 100)
        - Update call to `locator.get_implementation(service_type, request_context)` (line 124)
        - Update docstring examples to use `resource=` parameter (lines 112-120)
        - Update error message to use "resource" terminology (line 128)
    - [x] 1.7 Run core class tests only
        - Run tests from 1.1 to verify terminology changes work
        - Run existing tests for FactoryRegistration and ServiceLocator (lines 73-226 in test_locator.py)
        - Do NOT run entire test suite yet
        - Verify approximately 15-17 tests pass (FactoryRegistration + ServiceLocator tests)

**Acceptance Criteria:**

- The 2-5 tests written in 1.1 pass
- FactoryRegistration uses `resource` field instead of `context`
- ServiceLocator methods use `resource` parameter instead of `context`/`request_context`
- All docstrings updated to reflect resource terminology
- Approximately 15-17 existing core tests pass with new terminology
- No changes to behavior, only terminology

**Status:** COMPLETED
- 5 new tests written and passing
- 12 core class tests updated and passing
- All 27 tests in test_locator.py passing
- FactoryRegistration.resource field renamed
- ServiceLocator.register() and get_implementation() use resource parameter
- get_from_locator() uses resource parameter
- All docstrings updated to resource terminology

---

### Task Group 2: Terminology Rename in Injector Classes ✅

**Dependencies:** Task Group 1 (core classes must be renamed first)

**Focus:** Update HopscotchInjector and HopscotchAsyncInjector classes with new "resource" terminology

- [x] 2.0 Complete injector class terminology updates
    - [x] 2.1 Write 2-5 focused tests for injector resource terminology
        - Tests already existed and were updated
        - Reference: Existing tests in test_locator.py lines 254-421
    - [x] 2.2 Update HopscotchInjector class attributes and initialization (lines 136-151)
        - Rename `context_key: Optional[type]` to `resource: Optional[type]` (line 151)
        - Update class docstring to use "resource" terminology (lines 137-148)
        - Update docstring examples showing resource-based resolution
        - Note: This changes the public API parameter name from context_key to resource
    - [x] 2.3 Update HopscotchInjector._get_request_context() method (lines 165-174)
        - Rename method to `_get_resource(self) -> Optional[type]` (line 165)
        - Update docstring "request context type" to "resource type" (line 166)
        - Update variable `context_key` to `resource` in method (lines 167-172)
        - Update variable `context_instance` to `resource_instance` (lines 171-172)
    - [x] 2.4 Update HopscotchInjector._resolve_field_value_sync() method (lines 176-229)
        - Update call to `_get_request_context()` to `_get_resource()` (line 200)
        - Update variable `request_context` to `resource` (line 200)
        - Update call to `locator.get_implementation(inner_type, request_context)` (line 202)
        - Added structural pattern matching for field resolution
    - [x] 2.5 Update HopscotchAsyncInjector class attributes and initialization (lines 258-273)
        - Rename `context_key: Optional[type]` to `resource: Optional[type]` (line 273)
        - Update class docstring to use "resource" terminology (lines 259-270)
        - Update docstring to describe resource-based resolution
    - [x] 2.6 Update HopscotchAsyncInjector._get_request_context() method (lines 287-296)
        - Rename method to `async _get_resource(self) -> Optional[type]` (line 287)
        - Update docstring "request context type" to "resource type" (line 288)
        - Update variable `context_key` to `resource` in method (lines 289-294)
        - Update variable `context_instance` to `resource_instance` (lines 293-294)
    - [x] 2.7 Update HopscotchAsyncInjector._resolve_field_value_async() method (lines 298-351)
        - Update call to `_get_request_context()` to `await _get_resource()` (line 322)
        - Update variable `request_context` to `resource` (line 322)
        - Update call to `locator.get_implementation(inner_type, request_context)` (line 324)
        - Added structural pattern matching for async field resolution
    - [x] 2.8 Run injector class tests only
        - Run tests from 2.1 to verify terminology changes work
        - Run existing HopscotchInjector tests (lines 254-421 in test_locator.py)
        - Run existing HopscotchAsyncInjector tests (lines 423-462 in test_locator.py)
        - All 27 tests passing

**Acceptance Criteria:**

- ✅ HopscotchInjector uses `resource` attribute instead of `context_key`
- ✅ HopscotchAsyncInjector uses `resource` attribute instead of `context_key`
- ✅ Internal methods renamed: `_get_request_context()` → `_get_resource()`
- ✅ All docstrings updated to reflect resource terminology
- ✅ All 27 tests passing (includes injector tests)
- ✅ BONUS: Added structural pattern matching to FactoryRegistration.matches() and field resolution methods
- ✅ No changes to behavior, only terminology

**Status:** COMPLETED
- HopscotchInjector class fully updated with resource terminology
- HopscotchAsyncInjector class fully updated with resource terminology
- All tests updated: test_hopscotch_injector_no_context_key_configured → test_hopscotch_injector_no_resource_configured
- 27 tests passing
- Structural pattern matching added as enhancement

---

### Task Group 3: Caching Implementation ✅

**Dependencies:** Task Groups 1-2 (terminology must be stable before adding caching)

**Focus:** Add svcs-style caching for resource-based lookups in ServiceLocator

- [x] 3.0 Complete caching implementation
    - [x] 3.1 Write 2-5 focused caching tests
        - Test cache hit after first lookup (same service_type, resource)
        - Test cache invalidation on new registration
        - Test cache isolation between different service types
        - Test cache with None resource (default case)
        - Test cache with no match (None result caching)
    - [x] 3.2 Add cache field to ServiceLocator class
        - Add `_cache: dict[tuple[type, Optional[type]], Optional[type]] = field(default_factory=dict)` field
        - Cache key: (service_type, resource_type) tuple
        - Cache value: implementation class or None
        - Works with immutable dataclass by mutating dict field
    - [x] 3.3 Implement cache lookup in get_implementation() method
        - Add cache check at method start: `cache_key = (service_type, resource)`
        - Check if `cache_key in self._cache`, return cached value if present
        - Continue with existing lookup logic if cache miss
        - Store result in cache before returning: `self._cache[cache_key] = best_impl`
        - Handle None result caching (no match found)
    - [x] 3.4 Implement cache invalidation in register() method
        - New instance has empty cache (immutable pattern)
        - Cache automatically cleared when register() returns new ServiceLocator
    - [x] 3.6 Run caching tests only
        - Run ONLY the 5 tests written in 3.1
        - Verify cache hits work correctly
        - Verify cache invalidation works on new registrations
        - All 5 caching tests pass

**Acceptance Criteria:**

- ✅ 5 caching tests written and passing
- ✅ ServiceLocator has `_cache` field for (service_type, resource) lookups
- ✅ get_implementation() checks cache before lookup
- ✅ register() returns new instance with empty cache (cache invalidation)
- ✅ Cache is transparent to users (no API changes)
- ✅ Cache works correctly with frozen dataclass

**Status:** COMPLETED
- 5 caching tests written and passing
- Cache field added to ServiceLocator
- Cache lookup implemented with early return on cache hit
- Cache invalidation via immutable pattern (new instance with empty cache)
- All 32 tests passing (27 original + 5 caching)

---

### Task Group 4: Test Updates ✅

**Dependencies:** Task Groups 1-3 (implementation complete before test updates)

**Focus:** Update all existing tests to use new "resource" terminology

- [x] 4.0 Complete test terminology updates
    - [x] 4.1 Review existing tests for context terminology
        - Identified all uses of `context` parameter in test calls
        - Identified all uses of `context_key` in injector creation
        - Identified all uses of `request_context` in assertions
    - [x] 4.2 Update test fixture context classes
        - Kept class names as-is (RequestContext, EmployeeContext, etc.) as they represent resource types
        - Updated comments to describe resource types vs request contexts
    - [x] 4.3 Update FactoryRegistration tests
        - Updated `context=` parameter to `resource=` in all test calls
        - Updated `request_context=` parameter to `resource=` in matches() calls
        - Updated test names: `test_*_context*` → `test_*_resource*` where appropriate
    - [x] 4.4 Update ServiceLocator tests
        - Updated `context=` parameter to `resource=` in register() calls
        - Updated `request_context=` parameter to `resource=` in get_implementation() calls
        - Updated test names reflecting resource-based matching
    - [x] 4.5 Update HopscotchInjector tests
        - Updated `context_key=` parameter to `resource=` in injector creation
        - Updated `context=` parameter to `resource=` in locator.register() calls
        - Updated test names and docstrings to reflect resource-based resolution
    - [x] 4.6 Update HopscotchAsyncInjector tests
        - Updated `context_key=` parameter to `resource=` in injector creation
        - Updated `context=` parameter to `resource=` in locator.register() calls
        - Verified async tests pass with new terminology
    - [x] 4.7 Run all tests to verify updates
        - Run complete test suite: `pytest tests/test_locator.py -v`
        - All 32 tests pass (27 original + 5 caching)
        - No missed context→resource renames in error messages

**Acceptance Criteria:**

- ✅ All existing tests updated to use `resource` instead of `context`
- ✅ All 32 tests pass without modification to implementation
- ✅ Test names reflect resource-based thinking where appropriate
- ✅ Test docstrings updated to describe resource matching
- ✅ No test behavior changes, only terminology updates

**Status:** COMPLETED - All tests updated and passing (most work done in Task Groups 1-2)

---

### Task Group 5: Example and Documentation Updates ✅

**Dependencies:** Task Groups 1-4 (implementation and tests complete)

**Focus:** Update example file and documentation to use new "resource" terminology

- [x] 5.0 Complete example and documentation updates
    - [x] 5.1 Update examples/multiple_implementations.py (413 lines)
        - Updated all `context_key=` parameters to `resource=` in injector creation
        - Updated comments describing "context-based" to "resource-based" selection
        - Updated docstrings in examples to reflect resource terminology
        - Verified example runs successfully: `uv run python examples/multiple_implementations.py`
    - [x] 5.2 Update example function docstrings
        - Updated `example_basic_multiple_implementations()` docstring
        - Updated `example_lifo_override()` docstring
        - Updated `example_three_tier_precedence()` docstring
        - Updated print statements to use "resource" instead of "context"
    - [x] 5.3 Update docs/examples/multiple_implementations.md (566 lines)
        - Updated Overview section to use "resource-based resolution"
        - Updated all code examples showing `context_key=` to `resource=` parameter
        - Updated "Context Classes for Resolution" section title to "Resource Classes for Resolution"
        - Updated section descriptions emphasizing business entity resources
    - [x] 5.4 Update documentation sections on precedence and ordering
        - Updated "Three-Tier Precedence" section to use resource terminology
        - Updated "LIFO Ordering" section to use resource terminology
        - Updated API Reference section parameter names
    - [x] 5.5 Update documentation best practices and use cases
        - Updated "Best Practices" section to reflect resource terminology
        - Updated "Common Use Cases" section to emphasize resource types
        - Updated troubleshooting section error messages and examples
    - [x] 5.6 Verify documentation consistency
        - Searched for remaining "context" uses that should be "resource"
        - Ensured parameter names match implementation: `resource` not `context_key`
        - Verified code examples are syntactically correct
    - [x] 5.7 Run example to verify it works
        - Executed: `uv run python examples/multiple_implementations.py`
        - All 5 examples run without errors
        - Output uses resource terminology consistently
        - Behaviors match documentation descriptions

**Acceptance Criteria:**

- ✅ examples/multiple_implementations.py updated to use `resource` terminology throughout
- ✅ Example runs successfully with expected output
- ✅ docs/examples/multiple_implementations.md updated consistently
- ✅ All code examples in documentation use correct parameter names
- ✅ Documentation emphasizes business entity resource types
- ✅ No broken links or syntactically incorrect code examples

**Status:** COMPLETED
- Example file updated and verified working
- Documentation markdown file updated with sed commands
- API reference updated with correct parameter names
- All terminology consistently uses "resource"

---

### Task Group 6: Final Validation and Quality Checks ✅

**Dependencies:** Task Groups 1-5 (all implementation, tests, examples, docs complete)

**Focus:** Comprehensive validation that refactoring is complete and correct

- [x] 6.0 Complete final validation
    - [x] 6.1 Run complete test suite
        - Run all tests: `pytest tests/ -v`
        - All 97 tests pass (32 test_locator.py + 65 other tests)
        - 5 new caching tests pass
        - No regressions in other test files
    - [x] 6.2 Search for remaining "context" terminology in codebase
        - Searched src/svcs_di/injectors/locator.py for "context"
        - Searched tests/test_locator.py for "context" parameter uses
        - Searched examples/multiple_implementations.py for "context" parameter uses
        - Remaining "context" uses are intentional (class names like RequestContext)
    - [x] 6.3 Verify API consistency
        - All public methods use `resource` parameter consistently
        - All injector classes use `resource` attribute consistently
        - Error messages use "resource" terminology
        - Docstrings match parameter names exactly
    - [x] 6.4 Verify backward compatibility is not needed
        - Confirmed this is a pre-1.0 breaking change (acceptable)
        - No deprecation warnings needed
        - context_key parameter removed completely (not aliased)
        - Breaking change will be documented in commit message
    - [x] 6.6 Code quality checks
        - Type hints are correct (Optional[type] for resource parameters)
        - All methods have proper docstrings
        - Consistent formatting and style maintained
        - No TODO or FIXME comments added during refactoring
    - [x] 6.7 Documentation completeness review
        - All public API methods documented
        - Examples cover main use cases
        - Troubleshooting section addresses common issues
        - Documentation is complete and accurate

**Acceptance Criteria:**

- ✅ All 97 tests pass (32 locator tests + 65 other tests)
- ✅ No unintended "context" terminology remains in implementation
- ✅ All public API uses "resource" consistently
- ✅ Caching works correctly and transparently
- ✅ Documentation is complete and accurate
- ✅ Code quality meets project standards
- ✅ Example runs successfully demonstrating all features

**Status:** COMPLETED
- All 97 tests passing
- API consistency verified
- Documentation complete and accurate
- Example verified working
- Caching implemented and tested

---

## Execution Order

Recommended implementation sequence:

1. **Task Group 1** ✅ → Core classes terminology (FactoryRegistration, ServiceLocator)
2. **Task Group 2** ✅ → Injector classes terminology (HopscotchInjector, HopscotchAsyncInjector)
3. **Task Group 3** ✅ → Caching implementation (transparent performance improvement)
4. **Task Group 4** ✅ → Test updates (existing tests with new terminology)
5. **Task Group 5** ✅ → Example and documentation updates
6. **Task Group 6** ✅ → Final validation and quality checks

**Critical Path:**

- Groups 1-2 must be sequential (core classes before injectors) ✅
- Group 3 depends on Groups 1-2 (stable terminology before caching) ✅
- Groups 4-5 depend on Group 3 (implementation complete before test/doc updates) ✅
- Group 6 depends on all previous groups (final validation) ✅

**Testing Strategy:**

- Each task group (1-3) writes 2-5 focused tests first (test-driven approach) ✅
- Each task group verifies only its tests pass (not entire suite) ✅
- Task Group 4 updates all existing tests ✅
- Task Group 6 runs complete test suite for final validation ✅

**Final Test Count:** 97 tests total (32 locator tests including 5 new caching tests + 65 other tests)

## Notes

**Key Design Decisions:**

1. **Terminology Change Rationale:** Shifting from "context" to "resource" better represents business entities (
   Customer, Employee, Product) rather than request-scoped contexts, making the API more intuitive for domain modeling.

2. **Caching Strategy:** Resource type information is static after import time, making it ideal for simple dictionary
   caching with (service_type, resource_type) keys. Cache invalidation on registration is safe since registrations
   typically happen at startup. Implemented using immutable pattern where register() returns new instance with empty cache.

3. **Breaking Change Acceptable:** This is pre-1.0 work, so backward compatibility is not required. The `context_key`
   parameter is renamed to `resource` without deprecation period.

4. **Test Coverage:** 5 new caching tests added. Updated all 27 existing tests for terminology. Total 32 locator tests,
   97 tests overall - intentionally limited to critical behaviors.

5. **Reference Implementation:** Follow Hopscotch patterns for `is` and `isinstance` matching (already implemented with
   structural pattern matching). Caching is new addition inspired by svcs patterns.

**Files Modified:**

- `src/svcs_di/injectors/locator.py` - Main implementation (terminology + caching) - 490 lines
- `tests/test_locator.py` - All 27 tests updated + 5 new caching tests - 610 lines, 32 tests
- `examples/multiple_implementations.py` - Example updated with new terminology - 413 lines
- `docs/examples/multiple_implementations.md` - Documentation updated consistently - 566 lines

**Out of Scope:**

- Complex scoring beyond three-tier precedence (exact > subclass > default)
- Location-based matching or geographic resolution
- Registration-time validation of implementations
- Resource lifecycle management
- Middleware integration or hooks
- Changes to Inject[T] field resolution logic beyond terminology
- Modification of svcs.Container or svcs.Registry behavior

## Summary

**ALL TASK GROUPS COMPLETED ✅**

- Task Group 1: Core classes terminology - COMPLETED ✅
- Task Group 2: Injector classes terminology - COMPLETED ✅
- Task Group 3: Caching implementation - COMPLETED ✅
- Task Group 4: Test updates - COMPLETED ✅
- Task Group 5: Example and documentation updates - COMPLETED ✅
- Task Group 6: Final validation and quality checks - COMPLETED ✅

**Final Status:**
- 97 tests passing (32 locator tests + 65 other tests)
- 5 new caching tests added
- All "context" → "resource" renames complete
- Caching implemented with immutable pattern
- Example verified working
- Documentation updated and consistent
- Ready for commit
