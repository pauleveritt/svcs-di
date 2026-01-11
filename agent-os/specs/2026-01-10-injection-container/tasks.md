# Task Breakdown: InjectorContainer

## Overview
Total Tasks: 21

This feature implements an `InjectorContainer` class that extends `svcs.Container` to provide dependency injection capabilities by integrating an injector into the container's `get()` and `aget()` methods, enabling kwargs support for service resolution.

## Task List

### Core Implementation Layer

#### Task Group 1: InjectorContainer Class Definition
**Dependencies:** None

- [x] 1.0 Complete InjectorContainer class definition
  - [x] 1.1 Write 4-6 focused tests for basic class structure
    - Test that InjectorContainer can be instantiated with a Registry
    - Test that InjectorContainer has an `injector` attribute
    - Test that default injector is `KeywordInjector` when not specified
    - Test that custom injector class can be passed via constructor
    - Test that InjectorContainer is a subclass of `svcs.Container`
    - Test that attrs-style subclassing is used (verify `__attrs_attrs__` exists)
  - [x] 1.2 Create `src/svcs_di/injector_container.py` file with basic structure
    - Import required modules: `attrs`, `svcs`, `KeywordInjector`, `KeywordAsyncInjector`
    - Import `Injector` and `AsyncInjector` protocols from `svcs_di.auto`
    - Add module-level docstring explaining the purpose
  - [x] 1.3 Implement `InjectorContainer` class using attrs
    - Use `@attrs.define` decorator to match `svcs.Container` implementation
    - Subclass `svcs.Container`
    - Add `injector: type[Injector] = KeywordInjector` attribute as keyword-only with default
    - Add `async_injector: type[AsyncInjector] = KeywordAsyncInjector` attribute
    - Follow pattern from existing `svcs.Container` attrs definition
  - [x] 1.4 Ensure class definition tests pass
    - Run ONLY the 4-6 tests written in 1.1
    - Verify attrs integration works correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 1.1 pass
- `InjectorContainer` can be instantiated with a Registry
- Default injector is `KeywordInjector`
- Custom injector can be passed as keyword argument
- Uses attrs-style definition matching `svcs.Container`

---

#### Task Group 2: Synchronous get() Method Implementation
**Dependencies:** Task Group 1

- [x] 2.0 Complete `get()` method with kwargs support
  - [x] 2.1 Write 4-6 focused tests for `get()` method
    - Test `get()` without kwargs delegates to `super().get()` (standard svcs behavior)
    - Test `get()` with single service type + kwargs uses injector
    - Test `get()` with multiple service types + kwargs raises `ValueError`
    - Test `get()` with kwargs but no injector configured raises `ValueError` (edge case)
    - Test three-tier precedence: kwargs > container > defaults
    - Test that resolved service is correctly returned
  - [x] 2.2 Implement `get()` method signature
    - Signature: `get(self, svc_type: type, /, *svc_types: type, **kwargs: Any) -> object`
    - Use positional-only separator `/` for `svc_type`
    - Use `*svc_types` for additional service types
    - Use `**kwargs` for injection overrides
  - [x] 2.3 Implement `get()` method logic
    - If no kwargs: delegate to `super().get(svc_type, *svc_types)`
    - If kwargs with additional service types: raise `ValueError("Cannot pass kwargs when requesting multiple service types")`
    - If kwargs with no injector: raise `ValueError("Cannot pass kwargs without an injector configured")`
    - If kwargs with single type: use `self.injector(container=self)(svc_type, **kwargs)`
  - [x] 2.4 Add docstring with usage examples
    - Document the three scenarios (no kwargs, single type + kwargs, error cases)
    - Reference `KeywordInjector` for kwargs override behavior
  - [x] 2.5 Ensure `get()` method tests pass
    - Run ONLY the 4-6 tests written in 2.1
    - Verify all kwargs scenarios work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 2.1 pass
- `get()` without kwargs behaves like standard `svcs.Container.get()`
- `get()` with kwargs uses the injector for dependency resolution
- Proper errors raised for invalid usage (multiple types + kwargs, no injector + kwargs)

---

#### Task Group 3: Asynchronous aget() Method Implementation
**Dependencies:** Task Group 1

- [x] 3.0 Complete `aget()` method with kwargs support
  - [x] 3.1 Write 4-6 focused tests for `aget()` method
    - Test `aget()` without kwargs delegates to `super().aget()` (standard svcs behavior)
    - Test `aget()` with single service type + kwargs uses async injector
    - Test `aget()` with multiple service types + kwargs raises `ValueError`
    - Test `aget()` with kwargs but no async_injector configured raises `ValueError` (edge case)
    - Test three-tier precedence: kwargs > container > defaults (async)
    - Test that resolved service is correctly returned (await properly)
  - [x] 3.2 Implement `aget()` method signature
    - Signature: `async aget(self, svc_type: type, /, *svc_types: type, **kwargs: Any) -> object`
    - Match the same separator pattern as `get()` for consistency
  - [x] 3.3 Implement `aget()` method logic
    - If no kwargs: delegate to `await super().aget(svc_type, *svc_types)`
    - If kwargs with additional service types: raise `ValueError("Cannot pass kwargs when requesting multiple service types")`
    - If kwargs with no async_injector: raise `ValueError("Cannot pass kwargs without an injector configured")`
    - If kwargs with single type: `await self.async_injector(container=self)(svc_type, **kwargs)`
  - [x] 3.4 Add docstring with usage examples
    - Document async-specific behavior
    - Reference `KeywordAsyncInjector` for async kwargs override behavior
  - [x] 3.5 Ensure `aget()` method tests pass
    - Run ONLY the 4-6 tests written in 3.1
    - Use `pytest.mark.anyio` for async tests
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 3.1 pass
- `aget()` without kwargs behaves like standard `svcs.Container.aget()`
- `aget()` with kwargs uses the async injector for dependency resolution
- Proper errors raised for invalid usage
- Async flow is correctly implemented with proper await

---

### Integration Layer

#### Task Group 4: Error Handling and Edge Cases
**Dependencies:** Task Groups 2, 3

- [x] 4.0 Complete error handling verification
  - [x] 4.1 Write 4-6 focused tests for error scenarios
    - Test `ValueError` message content for multiple types + kwargs
    - Test `ValueError` message content for no injector + kwargs
    - Test that injector's own validation errors (unknown kwargs) propagate naturally
    - Test duck typing: invalid kwargs types surface during target construction
    - Test that standard svcs errors (ServiceNotFoundError) propagate correctly
  - [x] 4.2 Verify error messages match spec requirements
    - `"Cannot pass kwargs when requesting multiple service types"` for multiple types
    - `"Cannot pass kwargs without an injector configured"` for no injector
  - [x] 4.3 Ensure error propagation is correct
    - Injector validation errors bubble up unchanged
    - Container errors from `super().get()` / `super().aget()` propagate
    - Python type errors surface naturally (duck typing approach)
  - [x] 4.4 Ensure error handling tests pass
    - Run ONLY the 4-6 tests written in 4.1
    - Verify all error messages are correct
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 4.1 pass
- Error messages match spec requirements exactly
- Errors propagate naturally without wrapping/hiding
- Duck typing approach is followed for kwargs validation

---

#### Task Group 5: Module Exports and Integration
**Dependencies:** Task Groups 1-4

- [x] 5.0 Complete module exports and package integration
  - [x] 5.1 Write 2-4 focused tests for module integration
    - Test that `InjectorContainer` can be imported from `svcs_di`
    - Test that `InjectorContainer` works with existing `KeywordInjector`
    - Test that `InjectorContainer` works with existing `KeywordAsyncInjector`
    - Test basic end-to-end workflow (create container, register service, get with kwargs)
  - [x] 5.2 Update `src/svcs_di/__init__.py`
    - Import `InjectorContainer` from `svcs_di.injector_container`
    - Add `InjectorContainer` to `__all__` list
  - [x] 5.3 Add type hints and stub file if needed
    - Ensure proper type annotations for IDE support
    - Consider if `.pyi` stub file is needed for complex generics
  - [x] 5.4 Ensure integration tests pass
    - Run ONLY the 2-4 tests written in 5.1
    - Verify imports work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-4 tests written in 5.1 pass
- `InjectorContainer` is importable from top-level `svcs_di` package
- Works seamlessly with existing injector implementations
- Type hints provide good IDE autocomplete support

---

### Testing Layer

#### Task Group 6: Test Review and Gap Analysis
**Dependencies:** Task Groups 1-5

- [x] 6.0 Review existing tests and fill critical gaps only
  - [x] 6.1 Review tests from Task Groups 1-5
    - Review the 4-6 tests from Task Group 1 (class definition)
    - Review the 4-6 tests from Task Group 2 (get method)
    - Review the 4-6 tests from Task Group 3 (aget method)
    - Review the 4-6 tests from Task Group 4 (error handling)
    - Review the 2-4 tests from Task Group 5 (integration)
    - Total existing tests: approximately 18-28 tests
  - [x] 6.2 Analyze test coverage gaps for THIS feature only
    - Identify critical user workflows that lack test coverage
    - Focus ONLY on gaps related to InjectorContainer feature
    - Do NOT assess entire application test coverage
    - Prioritize integration scenarios over edge cases
  - [x] 6.3 Write up to 6 additional strategic tests maximum
    - Test InjectorContainer with custom injector implementation (not just KeywordInjector)
    - Test InjectorContainer used as drop-in replacement for svcs.Container
    - Test InjectorContainer with mixed sync/async usage patterns
    - Test InjectorContainer context manager support (inherited from svcs.Container)
    - Focus on real-world usage scenarios
    - Skip performance tests and exhaustive edge cases
  - [x] 6.4 Run feature-specific tests only
    - Run ONLY tests related to InjectorContainer feature (tests from 1.1, 2.1, 3.1, 4.1, 5.1, and 6.3)
    - Expected total: approximately 24-34 tests maximum
    - Do NOT run the entire application test suite
    - Verify critical workflows pass

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 24-34 tests total)
- Critical user workflows for InjectorContainer are covered
- No more than 6 additional tests added when filling in testing gaps
- Testing focused exclusively on InjectorContainer feature requirements

---

## Execution Order

Recommended implementation sequence:

1. **Task Group 1**: InjectorContainer Class Definition (foundation)
2. **Task Group 2**: Synchronous get() Method (can parallel with 3)
3. **Task Group 3**: Asynchronous aget() Method (can parallel with 2)
4. **Task Group 4**: Error Handling and Edge Cases (depends on 2, 3)
5. **Task Group 5**: Module Exports and Integration (depends on 1-4)
6. **Task Group 6**: Test Review and Gap Analysis (depends on 1-5)

**Parallelization Notes:**
- Task Groups 2 and 3 can be implemented in parallel as they are independent
- Task Groups 4 and 5 must wait for 2 and 3 to complete
- Task Group 6 is the final verification step

---

## Implementation Notes

### File Locations
- New file: `src/svcs_di/injector_container.py`
- Update: `src/svcs_di/__init__.py`
- New test file: `tests/test_injector_container.py` (or extend existing)

### Patterns to Follow
- Use `@attrs.define` decorator like `svcs.Container`
- Use `@dataclass(frozen=True)` pattern from existing injectors for reference
- Follow error message patterns from `svcs_di/injectors/_helpers.py`
- Match test style from `tests/test_inject_container.py` and `tests/test_injector.py`

### Key Dependencies
- `svcs.Container` (base class)
- `svcs_di.injectors.keyword.KeywordInjector` (default sync injector)
- `svcs_di.injectors.keyword.KeywordAsyncInjector` (default async injector)
- `svcs_di.auto.Injector` and `svcs_di.auto.AsyncInjector` (protocols for type hints)
