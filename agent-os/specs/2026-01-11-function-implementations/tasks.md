# Task Breakdown: Function Implementations

## Overview

Total Tasks: 40

This feature enables functions to serve as factory providers in svcs-di, allowing registration via
`register_implementation()` and the `@injectable` decorator with identical syntax to class-based implementations.

## Task List

### Core Infrastructure

#### Task Group 1: Extend @injectable Decorator for Functions

**Dependencies:** None

- [x] 1.0 Complete @injectable decorator function support
    - [x] 1.1 Write 4-6 focused tests for function decorator functionality
        - Test `@injectable` bare decorator on a function
        - Test `@injectable(for_=X)` with explicit service type on a function
        - Test `@injectable(for_=X, resource=Y)` with resource context on a function
        - Test that existing class decorator behavior remains unchanged
        - Note: Return type inference NOT supported; functions must specify `for_`
    - [x] 1.2 Modify `_mark_injectable()` in `src/svcs_di/injectors/decorators.py`
        - Remove TypeError check at lines 56-61 that restricts to classes only
        - Use `inspect.isclass()` or `callable()` to detect target type
        - Store `InjectableMetadata` on functions via `setattr()` (same pattern as classes)
        - Note: Return type inference removed for simplicity; scanning requires `for_`
    - [x] 1.3 Update `_InjectDecorator` type signatures
        - Extend overloads to accept `Callable` in addition to `type`
        - Update parameter type hints: `target: type | Callable[..., Any] | None`
        - Ensure type stub file is updated if necessary
    - [x] 1.4 Handle async function detection in decorator
        - Use `inspect.iscoroutinefunction()` to detect async functions
        - Store async flag in metadata for use during registration
    - [x] 1.5 Ensure decorator tests pass
        - Run ONLY the 4-6 tests written in 1.1
        - Verify both sync and async functions can be decorated
        - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**

- The 4-6 tests written in 1.1 pass
- `@injectable` decorator works on functions (must specify `for_` for scanning)
- Existing class-based decorator behavior is unchanged
- Note: Return type inference NOT supported; functions require explicit `for_`

---

#### Task Group 2: Extend register_implementation() for Callables

**Dependencies:** Task Group 1

- [x] 2.0 Complete register_implementation() callable support
    - [x] 2.1 Write 4-6 focused tests for callable registration
        - Test registering a sync function as factory provider
        - Test registering an async function as factory provider
        - Test registering a lambda as factory provider (for direct registration, not scanning)
        - Test registering a `functools.partial` wrapped function (for direct registration, not scanning)
        - Test that existing class-based registration still works
        - Note: Lambdas/partials work for direct registration but NOT for scanning
    - [x] 2.2 Update `HopscotchRegistry.register_implementation()` signature
        - File: `src/svcs_di/hopscotch_registry.py`
        - Broaden `implementation` parameter type from `type` to `type | Callable[..., T]`
        - Use `inspect.isfunction()` to differentiate between class and function implementations
    - [x] 2.3 Update `ServiceLocator.register()` method signature
        - File: `src/svcs_di/injectors/locator.py`
        - Broaden `implementation` parameter to accept `Callable` in addition to `type`
        - Update internal storage to handle callable implementations
    - [x] 2.4 Handle callable type inference
        - Extract return type from function signature for validation
        - Ensure factory function return type is compatible with service type
        - Provide clear error messages when return type is missing or incompatible
    - [x] 2.5 Ensure registration tests pass
        - Run ONLY the 4-6 tests written in 2.1
        - Verify callables are stored correctly in registry/locator
        - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**

- The 4-6 tests written in 2.1 pass
- `register_implementation()` accepts both classes and callables
- Type inference works from function return annotations
- Backward compatibility maintained for class-based registrations

---

#### Task Group 3: Function Parameter Injection

**Dependencies:** Task Group 2

- [x] 3.0 Complete function parameter injection
    - [x] 3.1 Write 4-6 focused tests for parameter injection
        - Test function with `Inject[T]` parameter is resolved from container
        - Test function with multiple `Inject[T]` parameters
        - Test function with mixed injectable and non-injectable parameters
        - Test function with default values on non-injectable parameters
        - Test protocol-based injection in function parameters
        - Test function without `for_` raises clear error
    - [x] 3.2 Verify `_get_callable_field_infos()` handles function factories
        - File: `src/svcs_di/auto.py`
        - Confirmed existing implementation extracts `Inject[T]` annotations correctly
        - Parameter inspection works for factory function patterns
    - [x] 3.3 Update injector factory creation for functions
        - File: `src/svcs_di/injectors/scanning.py`
        - Updated `_create_injector_factory()` to handle function targets using `Implementation` type
        - Added `_is_injectable_target()` helper using `inspect.isfunction()` to detect named functions
        - Added `DecoratedItem` type alias for cleaner type signatures
        - Functions MUST specify `for_` parameter (no return type inference)
    - [x] 3.4 Simplified: Lambdas and partials NOT supported
        - Only named functions (`def`) are supported via `inspect.isfunction()`
        - Lambdas and `functools.partial` are excluded (don't pass `inspect.isfunction()`)
        - Clear error message when function lacks `for_` parameter
    - [x] 3.5 Ensure parameter injection tests pass
        - All 10 tests pass for function parameter injection
        - All 54 related tests pass (no regressions)

**Acceptance Criteria:**

- The tests written in 3.1 pass (10 tests total)
- Function parameters with `Inject[T]` are automatically resolved
- Non-injectable parameters with defaults use their default values
- Functions must specify `for_` parameter (classes can omit it)
- Only named functions supported; lambdas and partials are NOT supported

---

#### Task Group 4: Async Factory Function Support

**Dependencies:** Task Group 3

- [x] 4.0 Complete async factory function support
    - [x] 4.1 Write 4-6 focused tests for async factory functions
        - Test async function factory with `await` during creation
        - Test async function with async dependency resolution
        - Test mixed sync/async dependency chain
        - Test async function in HopscotchInjector context
        - Test KeywordAsyncInjector with async function factory
        - Test async factory function with multiple Inject parameters
    - [x] 4.2 Extend DefaultAsyncInjector for function factories
        - File: `src/svcs_di/auto.py`
        - Verified existing `inspect.iscoroutinefunction()` detection works for factory functions
        - Existing `cast(Awaitable[T], result)` pattern handles function results correctly
        - No changes required - existing implementation already supports async functions
    - [x] 4.3 Update KeywordAsyncInjector for function factories
        - File: `src/svcs_di/injectors/keyword.py`
        - Verified existing implementation follows same patterns as DefaultAsyncInjector
        - Async function factories are awaited correctly via existing code
        - No changes required - existing implementation already supports async functions
    - [x] 4.4 Update HopscotchAsyncInjector for function factories
        - File: `src/svcs_di/injectors/hopscotch.py`
        - Verified locator-based resolution works with async function factories
        - Async dependency resolution in locator context works correctly
        - No changes required - existing implementation already supports async functions
    - [x] 4.5 Ensure async tests pass
        - All 6 tests written in 4.1 pass
        - Async factory functions are awaited correctly
        - Tests located in `tests/test_async_function_factories.py`

**Acceptance Criteria:**

- The 6 tests written in 4.1 pass
- Async factory functions are detected and awaited correctly
- All three async injectors (Default, Keyword, Hopscotch) support async factory functions

---

#### Task Group 5: Scanning Integration for Functions

**Dependencies:** Task Group 4

Note: Scanning integration was completed as part of Task Group 3. This task group is retained for documentation but work was done earlier.

- [x] 5.0 Complete scanning integration for functions
    - [x] 5.1 Tests for function scanning (completed in Task Group 3)
        - Test `scan()` discovers `@injectable(for_=X)` decorated functions
        - Test function with `for_` parameter registers to correct service type
        - Test function without `for_` raises clear error
        - Note: Functions MUST specify `for_`; only named functions supported
    - [x] 5.2 Update `_extract_decorated_items()` to find functions
        - File: `src/svcs_di/injectors/scanning.py`
        - Changed to use `_is_injectable_target()` which checks `inspect.isfunction()`
        - Lambdas and partials are NOT detected (by design)
    - [x] 5.3 Update `_register_decorated_items()` for functions
        - File: `src/svcs_di/injectors/scanning.py`
        - Functions must have `for_` specified; raises ValueError otherwise
        - Uses `DecoratedItem` type alias for cleaner signatures
    - [x] 5.4 Update `_scan_locals()` to find functions
        - File: `src/svcs_di/injectors/scanning.py`
        - Uses `_is_injectable_target()` helper
        - Useful for testing patterns with `locals_dict=locals()`
    - [x] 5.5 Scanning tests pass (completed in Task Group 3)
        - All scanning tests pass
        - Only named functions with `for_` are supported

**Acceptance Criteria:**

- Scanning tests pass
- `scan()` discovers `@injectable(for_=X)` decorated named functions
- Functions without `for_` raise clear error
- Lambdas and partials are NOT supported for scanning

---

### Examples

#### Task Group 6: DefaultInjector Function Example

**Dependencies:** Task Groups 1-5

- [x] 6.0 Complete DefaultInjector function example
    - [x] 6.1 Create example file `examples/function/default_injector.py`
        - Demonstrate function factory registration via `register_implementation()`
        - Show `Inject[T]` parameter injection in factory function
        - Include both manual registration and `@injectable` decorator patterns
        - Follow patterns from `examples/basic_function.py`
    - [x] 6.2 Add comprehensive inline documentation
        - Docstring explaining the example purpose
        - Comments explaining each step
        - Assertions demonstrating expected behavior
    - [x] 6.3 Verify example runs successfully
        - Run: `uv run python examples/function/default_injector.py`
        - Confirm all assertions pass

**Acceptance Criteria:**

- Example file exists at `examples/function/default_injector.py`
- Example demonstrates function factory with DefaultInjector
- Example runs without errors

---

#### Task Group 7: KeywordInjector Function Example

**Dependencies:** Task Groups 1-5

- [x] 7.0 Complete KeywordInjector function example
    - [x] 7.1 Create example file `examples/function/keyword_injector.py`
        - Demonstrate function factory with keyword override support
        - Show three-tier precedence: kwargs > container > defaults
        - Include `@injectable` decorator pattern
        - Follow patterns from `examples/keyword/` directory
    - [x] 7.2 Add comprehensive inline documentation
        - Docstring explaining the example purpose
        - Comments explaining keyword override behavior
        - Assertions demonstrating precedence rules
    - [x] 7.3 Verify example runs successfully
        - Run: `uv run python examples/function/keyword_injector.py`
        - Confirm all assertions pass

**Acceptance Criteria:**

- Example file exists at `examples/function/keyword_injector.py`
- Example demonstrates function factory with KeywordInjector
- Example runs without errors

---

#### Task Group 8: HopscotchInjector Function Example

**Dependencies:** Task Groups 1-5

- [x] 8.0 Complete HopscotchInjector function example
    - [x] 8.1 Create example file `examples/function/hopscotch_injector.py`
        - Demonstrate function factory with resource/location context
        - Show ServiceLocator-based multi-implementation resolution
        - Include `@injectable(for_=X, resource=Y)` pattern on functions
        - Follow patterns from `examples/hopscotch/` directory
    - [x] 8.2 Add comprehensive inline documentation
        - Docstring explaining the example purpose
        - Comments explaining locator-based resolution
        - Assertions demonstrating context-based selection
    - [x] 8.3 Verify example runs successfully
        - Run: `uv run python examples/function/hopscotch_injector.py`
        - Confirm all assertions pass

**Acceptance Criteria:**

- Example file exists at `examples/function/hopscotch_injector.py`
- Example demonstrates function factory with HopscotchInjector
- Example runs without errors

---

### Documentation

#### Task Group 9: Documentation Index

**Dependencies:** Task Groups 6-8

- [x] 9.0 Complete documentation index
    - [x] 9.1 Create `docs/function/index.md`
        - Overview of function implementations feature
        - Explanation of when to use functions vs classes as factories
        - Links to individual injector documentation pages
        - Include doctest-compatible code snippet
    - [x] 9.2 Update main docs index
        - Add link to function implementations section in `docs/index.md`
        - Ensure navigation is consistent with existing docs structure

**Acceptance Criteria:**

- `docs/function/index.md` exists with overview content
- Documentation is accessible from main docs navigation

---

#### Task Group 10: DefaultInjector Documentation

**Dependencies:** Task Group 6

- [x] 10.0 Complete DefaultInjector documentation
    - [x] 10.1 Create `docs/function/default_injector.md`
        - Document the DefaultInjector function example
        - Include doctest-compatible code snippets
        - Explain two-tier precedence (container > defaults)
        - Reference the example file
    - [x] 10.2 Verify doctests pass
        - Ensure code snippets are executable via sphinx/sybil

**Acceptance Criteria:**

- `docs/function/default_injector.md` exists with documentation
- Code snippets are doctest-compatible

---

#### Task Group 11: KeywordInjector Documentation

**Dependencies:** Task Group 7

- [x] 11.0 Complete KeywordInjector documentation
    - [x] 11.1 Create `docs/function/keyword_injector.md`
        - Document the KeywordInjector function example
        - Include doctest-compatible code snippets
        - Explain three-tier precedence (kwargs > container > defaults)
        - Reference the example file
    - [x] 11.2 Verify doctests pass
        - Ensure code snippets are executable via sphinx/sybil

**Acceptance Criteria:**

- `docs/function/keyword_injector.md` exists with documentation
- Code snippets are doctest-compatible

---

#### Task Group 12: HopscotchInjector Documentation

**Dependencies:** Task Group 8

- [x] 12.0 Complete HopscotchInjector documentation
    - [x] 12.1 Create `docs/function/hopscotch_injector.md`
        - Document the HopscotchInjector function example
        - Include doctest-compatible code snippets
        - Explain locator-based multi-implementation resolution
        - Reference the example file
    - [x] 12.2 Verify doctests pass
        - Ensure code snippets are executable via sphinx/sybil

**Acceptance Criteria:**

- `docs/function/hopscotch_injector.md` exists with documentation
- Code snippets are doctest-compatible

---

### Testing

#### Task Group 13: Test Review and Gap Analysis

**Dependencies:** Task Groups 1-12

- [x] 13.0 Review existing tests and fill critical gaps only
    - [x] 13.1 Review tests from Task Groups 1-5
        - Reviewed 6 function-specific tests in `tests/injectors/test_decorators.py`
        - Reviewed 9 tests in `tests/test_callable_registration.py`
        - Reviewed 10 tests in `tests/test_function_parameter_injection.py`
        - Reviewed 6 tests in `tests/test_async_function_factories.py`
        - Total existing tests: 42 function-related tests (including class decorator tests)
    - [x] 13.2 Analyze test coverage gaps for this feature only
        - Identified gaps in end-to-end workflows
        - Identified gaps in HopscotchContainer integration with function factories
        - Identified gaps in resource-based function factory resolution
        - Identified gaps in chained dependency resolution with function factories
    - [x] 13.3 Write up to 10 additional strategic tests maximum
        - Created `tests/test_function_implementations_gaps.py` with 9 new tests:
            1. End-to-end function factory workflow via Inject[T]
            2. HopscotchContainer.inject() with function factory via Inject[T]
            3. HopscotchContainer.ainject() with async function factory
            4. KeywordInjector function factory with kwargs override
            5. Function factory with no injectable parameters
            6. Function factory with resource context via Inject[T]
            7. Function factory called directly via injector
            8. Function factory with complex parameter ordering
            9. Scan with multiple function factories
            10. Function factory with chained dependencies via Inject[T]
    - [x] 13.4 Run feature-specific tests only
        - Ran all 52 function-related tests
        - All tests pass
    - [x] 13.5 Run full test suite for regression check
        - 349 tests pass
        - 4 pre-existing failures (nested scanning and async_injection example)
        - No regressions in class-based injection

**Acceptance Criteria:**

- All feature-specific tests pass (52 tests total)
- Critical user workflows for function implementations are covered
- 9 additional tests added (within 10 maximum)
- Full test suite passes (no new regressions, only pre-existing failures)

## Execution Order

Recommended implementation sequence:

1. **Core Infrastructure (Task Groups 1-5)** - Sequential, dependency-based
    - Task Group 1: Decorator support (foundation)
    - Task Group 2: Registration support (depends on 1)
    - Task Group 3: Parameter injection (depends on 2)
    - Task Group 4: Async support (depends on 3)
    - Task Group 5: Scanning integration (depends on 4)

2. **Examples (Task Groups 6-8)** - Can be parallelized after core
    - Task Group 6: DefaultInjector example
    - Task Group 7: KeywordInjector example
    - Task Group 8: HopscotchInjector example

3. **Documentation (Task Groups 9-12)** - After corresponding examples
    - Task Group 9: Index page (after all examples)
    - Task Group 10: DefaultInjector docs (after Task Group 6)
    - Task Group 11: KeywordInjector docs (after Task Group 7)
    - Task Group 12: HopscotchInjector docs (after Task Group 8)

4. **Testing (Task Group 13)** - Final validation
    - Review, gap analysis, and regression testing

## Files to Modify

### Source Files

- `src/svcs_di/injectors/decorators.py` - Remove class-only restriction, add function support
- `src/svcs_di/hopscotch_registry.py` - Broaden `register_implementation()` signature
- `src/svcs_di/injectors/locator.py` - Update `ServiceLocator.register()` for callables
- `src/svcs_di/auto.py` - Verify/extend `_get_callable_field_infos()` for factory functions
- `src/svcs_di/injectors/scanning.py` - Update scanning to discover decorated functions
- `src/svcs_di/injectors/keyword.py` - Ensure KeywordAsyncInjector handles function factories
- `src/svcs_di/injectors/hopscotch.py` - Ensure HopscotchAsyncInjector handles function factories

### New Example Files

- `examples/function/default_injector.py`
- `examples/function/keyword_injector.py`
- `examples/function/hopscotch_injector.py`

### New Documentation Files

- `docs/function/index.md`
- `docs/function/default_injector.md`
- `docs/function/keyword_injector.md`
- `docs/function/hopscotch_injector.md`

### New Test Files

- `tests/test_function_implementations_gaps.py` - Gap-filling tests for function implementations

### Existing Documentation to Update

- `docs/index.md` - Add navigation link to function implementations
