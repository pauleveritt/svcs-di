# Task Breakdown: Custom Construction with `__svcs__`

## Overview

Total Tasks: 4 major task groups
Focus: Enable classes to define a `__svcs__` classmethod for custom construction with container access

## Task List

### Core Implementation

#### Task Group 1: Detection and Invocation Logic
**Dependencies:** None

- [x] 1.0 Implement `__svcs__` detection and invocation in auto() factory
  - [x] 1.1 Write 2-8 focused tests for `__svcs__` detection and invocation
    - Test detection of `__svcs__` method using getattr
    - Test that `__svcs__` is invoked when present
    - Test that normal Injectable field injection is skipped when `__svcs__` exists
    - Test container is passed to `__svcs__` method
    - Test kwargs are forwarded to `__svcs__` method
    - Test `__svcs__` return value becomes the factory result
    - File: `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/test_auto.py`
  - [x] 1.2 Add `__svcs__` detection in auto() factory function
    - Location: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (lines 338-358)
    - Pattern: `svcs_factory = getattr(target, "__svcs__", None)`
    - Detection occurs immediately in factory function, before injector creation
    - Reference Hopscotch pattern: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` (lines 122-128)
  - [x] 1.3 Implement conditional invocation logic
    - If `__svcs__` found: invoke `svcs_factory(target, svcs_container, **kwargs)` and return immediately
    - If `__svcs__` not found: proceed with existing DefaultInjector logic
    - Skip get_field_infos() and injector creation when `__svcs__` exists
    - Maintain backward compatibility with existing behavior
  - [x] 1.4 Ensure kwargs forwarding to `__svcs__`
    - Pass **kwargs from factory call to `__svcs__` method
    - Maintain three-tier precedence within `__svcs__`: kwargs > container lookups > defaults
    - User code in `__svcs__` handles precedence logic
  - [x] 1.5 Ensure core implementation tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify `__svcs__` is detected and invoked correctly
    - Verify normal injection is bypassed when `__svcs__` exists
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- `__svcs__` method is detected using getattr pattern
- When `__svcs__` exists, it is invoked with container and kwargs
- Normal Injectable field injection is completely skipped when `__svcs__` exists
- Factory returns the instance returned by `__svcs__`

### Error Handling and Validation

#### Task Group 2: Error Handling and Type Safety
**Dependencies:** Task Group 1

- [x] 2.0 Implement error handling and validation
  - [x] 2.1 Write 2-8 focused tests for error conditions
    - Test TypeError when `__svcs__` is not a classmethod
    - Test TypeError when `__svcs__` has wrong signature
    - Test propagation of exceptions raised within `__svcs__`
    - Test propagation of ServiceNotFoundError from container.get() within `__svcs__`
    - Test clear error messages for common mistakes
    - File: `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/test_auto.py`
  - [x] 2.2 Add validation for `__svcs__` being a classmethod
    - Check if `__svcs__` is a classmethod using inspect module
    - Raise TypeError with message: "\_\_svcs\_\_ must be a classmethod"
    - Include class name in error message for clarity
  - [x] 2.3 Add signature validation for `__svcs__`
    - Expected signature: `@classmethod def __svcs__(cls, container: svcs.Container, **kwargs) -> Self`
    - Use inspect.signature() to validate parameters
    - Raise TypeError with expected signature if validation fails
    - Note: Signature validation is optional for v1 (may defer to runtime errors)
  - [x] 2.4 Ensure exception propagation
    - Exceptions raised in `__svcs__` should propagate naturally
    - ServiceNotFoundError from container.get() should propagate with full context
    - Do not wrap exceptions unnecessarily
  - [x] 2.5 Add type hints for Self return type
    - Import typing.Self (Python 3.11+)
    - Document that `__svcs__` should return Self type
    - Ensure type checkers understand factory returns correct type
  - [x] 2.6 Ensure error handling tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify error conditions are handled correctly
    - Verify clear error messages are provided
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- TypeError raised if `__svcs__` is not a classmethod
- Clear error messages guide users to correct usage
- Exceptions propagate correctly from `__svcs__` and container.get()
- Type hints properly reflect Self return type

### Async Support

#### Task Group 3: Async Factory Support
**Dependencies:** Task Group 1

- [x] 3.0 Implement `__svcs__` support in auto_async() factory
  - [x] 3.1 Write 2-8 focused tests for async `__svcs__` detection
    - Test `__svcs__` detection works in async context (synchronous `__svcs__` only)
    - Test container is passed to `__svcs__` in async factory
    - Test kwargs forwarding in async context
    - Test that normal async injection is skipped when `__svcs__` exists
    - Note: async def `__svcs__` is OUT OF SCOPE for v1
    - File: `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/test_auto.py`
  - [x] 3.2 Add `__svcs__` detection in auto_async() factory function
    - Location: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (lines 361-377)
    - Same detection pattern as sync: `svcs_factory = getattr(target, "__svcs__", None)`
    - Detection occurs before DefaultAsyncInjector creation
  - [x] 3.3 Implement conditional invocation in async context
    - If `__svcs__` found: invoke `svcs_factory(target, svcs_container, **kwargs)` (synchronous call)
    - Return value directly (no await needed - `__svcs__` is sync only in v1)
    - If `__svcs__` not found: proceed with DefaultAsyncInjector
    - Maintain backward compatibility
  - [x] 3.4 Document async limitations
    - Note: `async def __svcs__` is not supported in v1
    - Only synchronous `__svcs__` works in both auto() and auto_async()
    - Future enhancement: support `async def __svcs__` in auto_async()
  - [x] 3.5 Ensure async support tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify `__svcs__` works in async factory context
    - Verify synchronous `__svcs__` returns correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- `__svcs__` detection works in auto_async()
- Synchronous `__svcs__` works correctly with async factories
- Container and kwargs are passed correctly in async context
- Async limitations are documented

### Documentation and Examples

#### Task Group 4: Documentation and Examples
**Dependencies:** Task Groups 1-3

- [x] 4.0 Create documentation and examples
  - [x] 4.1 Create simple example demonstrating `__svcs__` usage
    - File: `/Users/pauleveritt/projects/pauleveritt/svcs-di/examples/custom_construction.py`
    - Example: Service with custom validation logic in `__svcs__`
    - Example: Service that conditionally fetches dependencies based on container contents
    - Example: Service with complex initialization requiring multiple container.get() calls
    - Show proper signature: `@classmethod def __svcs__(cls, container: svcs.Container, **kwargs) -> Self`
    - Demonstrate kwargs override pattern
  - [x] 4.2 Add docstring documentation to auto() function
    - Location: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (line 338)
    - Document `__svcs__` protocol in auto() docstring
    - Explain when to use `__svcs__` vs normal Injectable fields
    - Mention that `__svcs__` completely replaces field injection
    - Include signature example and return type expectations
  - [x] 4.3 Add docstring documentation to auto_async() function
    - Location: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (line 361)
    - Document `__svcs__` support in async context
    - Note that only synchronous `__svcs__` is supported in v1
    - Reference main auto() docstring for detailed `__svcs__` documentation
  - [x] 4.4 Update module docstring
    - Location: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (lines 1-6)
    - Mention `__svcs__` protocol as an escape hatch for custom construction
    - Brief description of when to use it
  - [x] 4.5 Add README example
    - Location: `/Users/pauleveritt/projects/pauleveritt/svcs-di/README.md`
    - Add brief section on custom construction with `__svcs__`
    - Link to examples/custom_construction.py for full examples
    - Show simple before/after comparison: Injectable fields vs `__svcs__`

**Acceptance Criteria:**
- Simple, clear example demonstrates `__svcs__` usage
- Examples show common use cases: validation, conditional construction, complex initialization
- Docstrings accurately document `__svcs__` protocol
- README includes basic `__svcs__` example
- Documentation explains when to use `__svcs__` vs normal injection

### Final Integration and Testing

#### Task Group 5: Integration Testing and Gap Analysis
**Dependencies:** Task Groups 1-4

- [x] 5.0 Review tests and fill critical gaps only
  - [x] 5.1 Review tests from Task Groups 1-3
    - Review the 2-8 tests written for core implementation (Task 1.1)
    - Review the 2-8 tests written for error handling (Task 2.1)
    - Review the 2-8 tests written for async support (Task 3.1)
    - Total existing tests: approximately 6-24 tests
  - [x] 5.2 Analyze test coverage gaps for `__svcs__` feature only
    - Identify integration scenarios not covered by unit tests
    - Focus on end-to-end workflows: registration -> retrieval -> construction
    - Check coverage of kwargs precedence within `__svcs__`
    - Verify container.get() and container.get_abstract() work within `__svcs__`
    - Assess coverage of `__svcs__` with nested dependencies
    - Do NOT assess entire application test coverage
  - [x] 5.3 Write up to 10 additional strategic tests maximum
    - Add integration test: `__svcs__` with complex dependency graph
    - Add integration test: `__svcs__` calling container.get_abstract() for protocols
    - Add integration test: kwargs override precedence within `__svcs__`
    - Add integration test: `__svcs__` returning instance with post-construction validation
    - Add integration test: `__svcs__` with conditional service resolution
    - Add edge case test: `__svcs__` returning different instance based on kwargs
    - Do NOT write comprehensive coverage for all scenarios
    - Focus on realistic integration workflows
    - File: `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/test_auto.py`
  - [x] 5.4 Run feature-specific tests only
    - Run ONLY tests related to `__svcs__` feature (tests from 1.1, 2.1, 3.1, and 5.3)
    - Expected total: approximately 16-34 tests maximum
    - Do NOT run the entire application test suite
    - Verify all `__svcs__` workflows pass
    - Check that existing auto() tests still pass (backward compatibility)
  - [x] 5.5 Manual testing with examples
    - Run examples/custom_construction.py to verify examples work
    - Test examples match documentation
    - Verify error messages are helpful when mistakes are made

**Acceptance Criteria:**
- All `__svcs__` feature tests pass (approximately 16-34 tests total)
- Critical integration workflows are covered
- No more than 10 additional tests added when filling gaps
- Existing auto() tests still pass (backward compatibility maintained)
- Examples run successfully and match documentation
- Feature is ready for production use

## Execution Order

Recommended implementation sequence:
1. **Core Implementation** (Task Group 1) - Detection and invocation logic in auto() factory
2. **Error Handling** (Task Group 2) - Validation and clear error messages
3. **Async Support** (Task Group 3) - Extend to auto_async() factory
4. **Documentation** (Task Group 4) - Examples and docstrings
5. **Integration Testing** (Task Group 5) - Fill test gaps and verify end-to-end workflows

## Implementation Notes

**Key Design Decisions:**
- `__svcs__` completely replaces Injectable field injection (not additive)
- Only synchronous `__svcs__` supported in v1 (async is future enhancement)
- Detection uses simple getattr pattern from Hopscotch
- No validation of `__svcs__` signature at registration time (runtime only)
- User code in `__svcs__` handles all precedence and validation logic

**Files to Modify:**
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` - Core implementation
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/test_auto.py` - Tests
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/README.md` - Documentation
- `/Users/pauleveritt/projects/pauleveritt/svcs-di/examples/custom_construction.py` - Example (new file)

**Files to Reference:**
- `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` (lines 122-128) - Pattern reference
- `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/fixtures/dataklasses.py` (lines 87-98) - Usage example

**Testing Strategy:**
- Write 2-8 focused tests per task group during development
- Focus tests on critical behaviors only, not exhaustive coverage
- Run only newly written tests during development phases
- Fill test gaps (max 10 additional tests) in final integration phase
- Verify backward compatibility with existing auto() tests

**Out of Scope for v1:**
- Asynchronous `async def __svcs__` support
- Partial injection (mixing Injectable fields with `__svcs__`)
- Helper decorators for common `__svcs__` patterns
- Signature validation at registration time
- Caching of `__svcs__` detection results
