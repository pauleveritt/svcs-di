# Task Breakdown: Keyword Injector

## Overview
Total Task Groups: 5
Estimated Total Tasks: ~35 sub-tasks

This feature extracts kwargs handling from DefaultInjector into a specialized KeywordInjector, simplifying DefaultInjector to only handle Inject[T] resolution. Helper functions remain in auto.py to keep DefaultInjector standalone.

**IMPORTANT ARCHITECTURE NOTE:** Helper functions STAY in auto.py. Do NOT extract to separate helpers.py file.

## Task List

### Infrastructure Layer

#### Task Group 1: Create Directory Structure for KeywordInjector (COMPLETED)
**Dependencies:** None
**Specialist:** Backend Engineer

- [x] 1.0 Create injectors module infrastructure (SIMPLIFIED - helpers stay in auto.py)
  - [x] 1.1 Create directory structure
    - Create `src/svcs_di/injectors/` directory
    - Create `src/svcs_di/injectors/__init__.py` with placeholder comment explaining this will export KeywordInjector
    - Create `src/svcs_di/injectors/keyword.py` as empty placeholder for now
    - Create `tests/injectors/` directory
    - Create `tests/injectors/__init__.py`
    - **DO NOT create helpers.py** - helpers stay in auto.py
  - [x] 1.2 Verify directory structure and test suite
    - Confirm `src/svcs_di/injectors/` exists with `__init__.py` and `keyword.py`
    - Confirm `tests/injectors/` exists with `__init__.py`
    - Run existing test suite to ensure no regressions
    - All 52 tests pass successfully

**Acceptance Criteria:**
- [x] Directory `src/svcs_di/injectors/` exists with `__init__.py` and `keyword.py` (both placeholder/empty)
- [x] Directory `tests/injectors/` exists with `__init__.py`
- [x] No helpers.py file created (helpers stay in auto.py)
- [x] Full test suite passes (52/52 tests pass - no regressions)
- [x] Clear comments in `__init__.py` explaining what will be exported later

---

### Core Injector Layer

#### Task Group 2: Implement KeywordInjector and KeywordAsyncInjector (COMPLETED)
**Dependencies:** Task Group 1
**Specialist:** Backend Engineer

- [x] 2.0 Implement KeywordInjector with kwargs support
  - [x] 2.1 Write 2-8 focused tests for KeywordInjector
    - Limit to 2-8 highly focused tests maximum
    - Test only critical KeywordInjector behaviors:
      - Three-tier precedence (kwargs > container > defaults)
      - Kwargs validation (ValueError for unknown params)
      - Inject[T] resolution with kwargs override
      - Protocol-based injection with kwargs
      - Async version with mixed dependencies
    - Skip exhaustive testing of all combinations
    - Create `tests/injectors/test_keyword_injector.py`
    - Move kwargs tests from `tests/test_injector.py`:
      - `test_injector_kwarg_precedence` (lines 43-67)
      - `test_injector_kwargs_override_defaults` (lines 70-87)
      - `test_injector_validates_kwargs` (lines 90-103)
    - Adapt tests to use KeywordInjector instead of DefaultInjector
    - Add async injector test adapted from `test_async_injector_with_mixed_dependencies`
    - Do NOT use @runtime_checkable in tests
  - [x] 2.2 Create `src/svcs_di/injectors/keyword.py`
    - Import necessary types: `dataclasses`, `svcs`, `Any`, `Protocol`
    - Import helpers FROM auto.py: `FieldInfo`, `get_field_infos`, `is_injectable`, `extract_inner_type`, `is_protocol_type`
    - Define KeywordInjector class implementing Injector protocol
    - Signature: `def __call__[T](self, target: type[T], **kwargs: Any) -> T`
  - [x] 2.3 Implement KeywordInjector._validate_kwargs method
    - Extract logic from `_BaseInjector._validate_kwargs` in auto.py (lines 66-76)
    - Validate that all kwargs match actual field names from FieldInfo list
    - Raise ValueError with helpful message showing valid parameter names
    - Signature: `def _validate_kwargs(self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]) -> None`
  - [x] 2.4 Implement KeywordInjector.__call__ with three-tier precedence
    - Use `get_field_infos(target)` to extract field metadata (imported from auto.py)
    - Call `_validate_kwargs()` to validate kwargs
    - Loop through field_infos and resolve each field using helper function
    - Implement three-tier precedence:
      1. kwargs[field_name] if present (highest priority)
      2. container.get(inner_type) or container.get_abstract(inner_type) for Inject[T]
      3. default value from field definition (lowest priority)
    - Construct and return target instance with resolved kwargs
    - Reuse pattern from DefaultInjector.__call__ (lines 83-94)
  - [x] 2.5 Create helper method for field value resolution
    - Create `_resolve_field_value_sync()` method in KeywordInjector
    - Extract resolution logic adapted from `_resolve_field_value()` in auto.py (lines 265-296)
    - Keep three-tier precedence intact
    - Return tuple: `(has_value: bool, value: Any)`
  - [x] 2.6 Implement KeywordAsyncInjector wrapping sync logic
    - Define KeywordAsyncInjector class implementing AsyncInjector protocol
    - Signature: `async def __call__[T](self, target: type[T], **kwargs: Any) -> T`
    - Store reference to sync KeywordInjector logic where possible
    - Reuse `_validate_kwargs()` from KeywordInjector (composition)
    - Create `_resolve_field_value_async()` method using async container methods
    - Use container.aget() and container.aget_abstract() instead of sync versions
    - Adapt from DefaultAsyncInjector.__call__ pattern (lines 101-114)
  - [x] 2.7 Update `src/svcs_di/injectors/__init__.py`
    - Export: `from .keyword import KeywordInjector, KeywordAsyncInjector`
    - Add __all__ list: `["KeywordInjector", "KeywordAsyncInjector"]`
  - [x] 2.8 Update `src/svcs_di/__init__.py`
    - Add export: `from svcs_di.injectors import KeywordInjector, KeywordAsyncInjector`
    - Add to __all__ if present
  - [x] 2.9 Ensure KeywordInjector tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify three-tier precedence works correctly
    - Verify kwargs validation catches unknown parameters
    - Verify async version works with mixed dependencies
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- [x] The 8 tests written in 2.1 pass
- [x] KeywordInjector implements Injector protocol correctly
- [x] KeywordAsyncInjector implements AsyncInjector protocol correctly
- [x] Three-tier precedence works: kwargs > container > defaults
- [x] Kwargs validation raises ValueError for unknown params
- [x] Async version properly wraps sync logic
- [x] Proper exports in module __init__ files
- [x] KeywordInjector imports helpers FROM auto.py (not from separate helpers.py)

---

### Refactoring Layer

#### Task Group 3: Simplify DefaultInjector (Remove kwargs Support) (COMPLETED)
**Dependencies:** Task Group 2
**Specialist:** Backend Engineer

- [x] 3.0 Remove kwargs support from DefaultInjector
  - [x] 3.1 Write 2-8 focused tests for simplified DefaultInjector
    - Limit to 2-8 highly focused tests maximum
    - Test only critical DefaultInjector behaviors WITHOUT kwargs:
      - Inject[T] resolution from container
      - Protocol-based resolution
      - Default value fallback
      - NO kwargs parameter usage
    - Skip tests that use kwargs (those are now in KeywordInjector tests)
    - Update existing DefaultInjector tests in `tests/test_injector.py`
    - Ensure no kwargs parameters are passed to DefaultInjector
  - [x] 3.2 Remove _BaseInjector class from `src/svcs_di/auto.py`
    - Delete _BaseInjector class definition (lines 60-76)
    - _validate_kwargs is now only in KeywordInjector
    - Check if _BaseInjector has any other uses before deleting
  - [x] 3.3 Update DefaultInjector class definition
    - Change from `class DefaultInjector(_BaseInjector):` to standalone `@dataclasses.dataclass class DefaultInjector:`
    - Keep `container: svcs.Container` field
    - Keep docstring updated: "Resolves Inject[T] fields from container. No kwargs override support."
  - [x] 3.4 Simplify DefaultInjector.__call__ method
    - Remove `self._validate_kwargs(target, field_infos, kwargs)` call
    - Remove kwargs tier from field resolution
    - Update `_resolve_field_value()` calls to NOT check kwargs
    - Keep only two-tier precedence: container.get(T) then defaults
    - Signature remains: `def __call__[T](self, target: type[T], **kwargs: Any) -> T`
    - Note: **kwargs stays in signature for protocol compliance but is ignored
  - [x] 3.5 Simplify _resolve_field_value function
    - Update function in `auto.py` to remove Tier 1 (kwargs) logic
    - Keep only Tier 2 (Inject from container) and Tier 3 (defaults)
    - Remove kwargs parameter from function signature
    - Update signature: `def _resolve_field_value(field_info: FieldInfo, container: svcs.Container) -> tuple[bool, Any]`
    - Update call sites in DefaultInjector.__call__
  - [x] 3.6 Update DefaultAsyncInjector class definition
    - Change from `class DefaultAsyncInjector(_BaseInjector):` to standalone `@dataclasses.dataclass class DefaultAsyncInjector:`
    - Keep `container: svcs.Container` field
    - Keep docstring updated: "Async version. Resolves Inject[T] fields from container. No kwargs override support."
  - [x] 3.7 Simplify DefaultAsyncInjector.__call__ method
    - Remove `self._validate_kwargs(target, field_infos, kwargs)` call
    - Remove kwargs tier from field resolution
    - Update `_resolve_field_value_async()` calls to NOT check kwargs
    - Keep only two-tier precedence: container.aget(T) then defaults
    - Signature remains: `async def __call__[T](self, target: type[T], **kwargs: Any) -> T`
    - Note: **kwargs stays in signature for protocol compliance but is ignored
  - [x] 3.8 Simplify _resolve_field_value_async function
    - Update function in `auto.py` to remove Tier 1 (kwargs) logic
    - Keep only Tier 2 (Inject from container) and Tier 3 (defaults)
    - Remove kwargs parameter from function signature
    - Update signature: `async def _resolve_field_value_async(field_info: FieldInfo, container: svcs.Container) -> tuple[bool, Any]`
    - Update call sites in DefaultAsyncInjector.__call__
  - [x] 3.9 Update Inject[T] docstring
    - Update docstring in `auto.py` (lines 122-134) to reflect two-tier precedence
    - Remove mention of kwargs (Tier 1)
    - Document: "Two-tier precedence: container.get(T), then default values"
    - Note KeywordInjector for kwargs support
  - [x] 3.10 Ensure simplified DefaultInjector tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify Inject[T] resolution still works
    - Verify defaults still work
    - Verify kwargs are silently ignored (not an error)
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- [x] The tests pass for simplified DefaultInjector
- [x] _BaseInjector class removed
- [x] DefaultInjector has no kwargs validation or usage
- [x] DefaultAsyncInjector has no kwargs validation or usage
- [x] Two-tier precedence implemented: container > defaults
- [x] **kwargs in signature preserved for protocol compliance
- [x] Docstrings updated to reflect new behavior

---

### Test Cleanup Layer

#### Task Group 4: Remove kwargs Tests from Existing Test Files (COMPLETED)
**Dependencies:** Task Group 3
**Specialist:** Backend Engineer / Test Engineer

- [x] 4.0 Clean up existing test files
  - [x] 4.1 Review tests moved to KeywordInjector in Task 2.1
    - Confirm tests were successfully moved to `tests/injectors/test_keyword_injector.py`
    - List of tests that should have been moved:
      - `test_injector_kwarg_precedence`
      - `test_injector_kwargs_override_defaults`
      - `test_injector_validates_kwargs`
      - Async kwargs test adapted from mixed dependencies
  - [x] 4.2 Remove kwargs tests from `tests/test_injector.py`
    - Delete `test_injector_kwarg_precedence` (lines 43-67)
    - Delete `test_injector_kwargs_override_defaults` (lines 70-87)
    - Delete `test_injector_validates_kwargs` (lines 90-103)
    - Keep all other DefaultInjector tests that don't use kwargs
    - Update any remaining tests to ensure they DON'T pass kwargs to DefaultInjector
  - [x] 4.3 Review and update `tests/test_auto.py`
    - Scan for any kwargs usage with auto() function
    - Remove kwargs-related assertions
    - Keep all other auto() factory tests
    - Ensure no tests rely on kwargs behavior
  - [x] 4.4 Update test fixtures and helpers if needed
    - Check if any test fixtures or helper functions use kwargs with DefaultInjector
    - Update to use KeywordInjector if kwargs needed
    - Or remove kwargs usage if not essential to test
  - [x] 4.5 Run affected test files to verify cleanup
    - Run `tests/test_injector.py` - should pass with kwargs tests removed
    - Run `tests/test_auto.py` - should pass with no kwargs usage
    - Run `tests/injectors/test_keyword_injector.py` - should pass with moved tests
    - Do NOT run the entire test suite yet

**Acceptance Criteria:**
- [x] All kwargs-related tests removed from `tests/test_injector.py`
- [x] All kwargs-related tests removed from `tests/test_auto.py`
- [x] No remaining tests use kwargs with DefaultInjector
- [x] All moved tests work correctly in `tests/injectors/test_keyword_injector.py`
- [x] Test files run successfully after cleanup

---

### Examples and Documentation Layer

#### Task Group 5: Update Examples and Final Integration (COMPLETED)
**Dependencies:** Task Groups 1-4
**Specialist:** Documentation Engineer / Full Stack Engineer

- [x] 5.0 Update examples and run full test suite
  - [x] 5.1 Create examples/keyword/ directory structure
    - Create `examples/keyword/` directory
    - This will house KeywordInjector examples
  - [x] 5.2 Move and update kwargs example
    - Move `examples/kwargs_override.py` to `examples/keyword/first_example.py`
    - Update imports: `from svcs_di.injectors import KeywordInjector`
    - Update code to use KeywordInjector instead of DefaultInjector
    - Update comments to explain three-tier precedence
    - Ensure example demonstrates kwargs validation
    - Keep example focused and simple
  - [x] 5.3 Update tests/test_examples.py
    - Update test paths to point to `examples/keyword/first_example.py`
    - Update any assertions about kwargs behavior
    - Ensure tests import and use KeywordInjector correctly
    - Keep existing tests for other examples unchanged
  - [x] 5.4 Review other examples for kwargs usage
    - Check `examples/basic_dataclass.py` - should use DefaultInjector, no kwargs
    - Check `examples/protocol_injection.py` - should use DefaultInjector, no kwargs
    - Check `examples/async_injection.py` - should use DefaultAsyncInjector, no kwargs
    - Check `examples/custom_injector.py` - update to mention KeywordInjector as example
    - Update any examples that incorrectly use kwargs with DefaultInjector
  - [x] 5.5 Update auto() and auto_async() docstrings
    - Update docstring in `auto.py` for `auto()` function (lines 338-347)
    - Mention that DefaultInjector doesn't support kwargs
    - Add note: "For kwargs override support, register KeywordInjector as custom injector"
    - Provide example of registering KeywordInjector
    - Update `auto_async()` docstring similarly (lines 361-365)
  - [x] 5.6 Run full test suite
    - Run entire test suite: `pytest tests/`
    - Verify all tests pass including:
      - KeywordInjector tests (tests/injectors/test_keyword_injector.py)
      - Simplified DefaultInjector tests (tests/test_injector.py)
      - Auto function tests (tests/test_auto.py)
      - Example tests (tests/test_examples.py)
    - Fix any failures that arise from the refactoring
  - [x] 5.7 Verify type checking passes
    - Run mypy or pyright on the codebase
    - Ensure KeywordInjector properly implements Injector protocol
    - Ensure KeywordAsyncInjector properly implements AsyncInjector protocol
    - Fix any type errors
  - [x] 5.8 Final smoke test
    - Manually run key examples to ensure they work
    - Test `examples/keyword/first_example.py` with KeywordInjector
    - Test `examples/basic_dataclass.py` with DefaultInjector
    - Test `examples/async_injection.py` with DefaultAsyncInjector
    - Verify no runtime errors

**Acceptance Criteria:**
- [x] Examples reorganized with `examples/keyword/` directory
- [x] `examples/keyword/first_example.py` demonstrates KeywordInjector usage
- [x] All other examples updated to not use kwargs with DefaultInjector
- [x] `tests/test_examples.py` passes with updated paths
- [x] Docstrings updated to guide users to KeywordInjector for kwargs support
- [x] Full test suite passes (58/58 tests pass - 100% pass rate)
- [x] Type checking passes with no errors
- [x] Manual smoke tests successful

---

## Execution Order

Recommended implementation sequence:

1. **Task Group 1: Infrastructure** - Create directory structure for KeywordInjector (COMPLETED)
2. **Task Group 2: Core Implementation** - Build KeywordInjector and KeywordAsyncInjector (COMPLETED)
3. **Task Group 3: Refactoring** - Simplify DefaultInjector by removing kwargs support (COMPLETED)
4. **Task Group 4: Test Cleanup** - Remove kwargs tests from existing files (COMPLETED)
5. **Task Group 5: Integration** - Update examples, documentation, and run final validation (COMPLETED)

## Implementation Summary

### All Task Groups COMPLETE

All 5 task groups have been successfully implemented and verified:

1. **Infrastructure (Group 1)**: Directory structure created for injectors module
2. **Core Implementation (Group 2)**: KeywordInjector and KeywordAsyncInjector fully implemented with 8 tests passing
3. **Refactoring (Group 3)**: DefaultInjector simplified, _BaseInjector removed, two-tier precedence implemented
4. **Test Cleanup (Group 4)**: All kwargs tests removed from DefaultInjector test files
5. **Integration (Group 5)**: Examples updated, full test suite passes (58/58 tests)

### Key Implementation Notes

#### Three-Tier Precedence (KeywordInjector only)
1. kwargs passed to injector (highest) - override everything
2. container.get(T) or container.get_abstract(T) for Inject[T]
3. default values from field definitions (lowest)

#### Two-Tier Precedence (DefaultInjector after refactoring)
1. container.get(T) or container.get_abstract(T) for Inject[T]
2. default values from field definitions

### Critical Design Decisions
- **Helpers stay in auto.py**: No separate helpers.py file - keep DefaultInjector standalone
- **KeywordInjector imports from auto.py**: Uses `from svcs_di.auto import ...` for helper functions
- **No @runtime_checkable**: Protocol compliance verified through static type checking and duck typing
- **Async wraps sync**: KeywordAsyncInjector reuses KeywordInjector logic where possible
- **Breaking changes accepted**: No backwards compatibility for DefaultInjector kwargs usage
- **Protocol signature preserved**: **kwargs remains in DefaultInjector signature for protocol compliance but is ignored

### Migration Path for Users
Users currently using kwargs with DefaultInjector must:
1. Import KeywordInjector: `from svcs_di.injectors import KeywordInjector`
2. Register as custom injector: `registry.register_factory(DefaultInjector, lambda c: KeywordInjector(container=c))`
3. Or use KeywordInjector directly in code

### Files Modified
- `src/svcs_di/auto.py` - Simplified DefaultInjector, removed kwargs logic (helpers remain here)
- `src/svcs_di/__init__.py` - Added KeywordInjector exports
- `tests/test_injector.py` - Removed kwargs tests
- `tests/test_auto.py` - Removed kwargs usage
- `tests/test_examples.py` - Updated example paths

### Files Created
- `src/svcs_di/injectors/__init__.py` - New module exports
- `src/svcs_di/injectors/keyword.py` - KeywordInjector implementations (imports helpers from auto.py)
- `tests/injectors/__init__.py` - Test module init
- `tests/injectors/test_keyword_injector.py` - KeywordInjector tests (8 tests)
- `examples/keyword/first_example.py` - Moved from kwargs_override.py

### Files NOT Created
- `src/svcs_di/injectors/helpers.py` - **NOT CREATED** - helpers stay in auto.py
- `tests/injectors/test_helpers.py` - **NOT CREATED** - no separate helper tests needed

### Test Results
- **Full Test Suite**: 58/58 tests pass (100% pass rate)
- **KeywordInjector Tests**: 8/8 tests pass
- **DefaultInjector Tests**: 9/9 tests pass (simplified, no kwargs)
- **Auto Function Tests**: 11/11 tests pass
- **Example Tests**: Multiple example tests pass including new keyword example
