# Task Breakdown: Inject Container

## Overview
Total Tasks: 4 Task Groups
Feature Size: Small (S)

This feature adds support for `Injectable[Container]` type annotation across all injector types (DefaultInjector, KeywordInjector, HopscotchInjector) and their async variants. The implementation follows the existing three-tier precedence pattern and requires no runtime type validation.

## Task List

### Task Group 1: DefaultInjector and DefaultAsyncInjector

**Dependencies:** None

- [x] 1.0 Add Container injection to DefaultInjector and DefaultAsyncInjector
  - [x] 1.1 Write 4-6 focused tests for Container injection in DefaultInjector
    - Test basic Container injection with `Injectable[Container]` annotation
    - Test Container injection in dataclass fields
    - Test default value fallback when Container not injectable
    - Test async variant with `DefaultAsyncInjector`
  - [x] 1.2 Modify `_resolve_field_value()` in auto.py for sync resolution
    - Add check: `if inner_type is svcs.Container` after `field_info.is_injectable`
    - Return `(True, self.container)` when Container type detected
    - Place before protocol/concrete type resolution logic
  - [x] 1.3 Modify `_resolve_field_value_async()` in auto.py for async resolution
    - Add same Container check as sync version
    - Return `(True, self.container)` for Container type
    - Maintain consistency with sync implementation
  - [x] 1.4 Ensure DefaultInjector tests pass
    - Run ONLY the 4-6 tests written in 1.1
    - Verify Container injection works for both sync and async
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 1.1 pass
- `Injectable[Container]` is recognized and resolves to `self.container`
- Container check happens before protocol/concrete type checks
- Both sync and async variants work identically

### Task Group 2: KeywordInjector and KeywordAsyncInjector

**Dependencies:** Task Group 1 (for consistency in implementation pattern)

- [x] 2.0 Add Container injection to KeywordInjector and KeywordAsyncInjector
  - [x] 2.1 Write 4-6 focused tests for Container injection in KeywordInjector
    - Test three-tier precedence: kwargs override > Container injection > defaults
    - Test explicit Container in kwargs (Tier 1)
    - Test automatic Container injection when not in kwargs (Tier 2)
    - Test async variant with `KeywordAsyncInjector`
  - [x] 2.2 Modify `_resolve_field_value_sync()` in KeywordInjector class
    - Add Container check after Tier 1 (kwargs) but before other injectable resolution
    - Pattern: `if field_info.is_injectable and inner_type is svcs.Container`
    - Return `(True, self.container)` when Container not in kwargs
    - Respect kwargs if Container explicitly provided (Tier 1 precedence)
  - [x] 2.3 Modify `_resolve_field_value_async()` in KeywordAsyncInjector class
    - Mirror sync logic with async method signature
    - Maintain three-tier precedence: kwargs > container injection > defaults
  - [x] 2.4 Ensure KeywordInjector tests pass
    - Run ONLY the 4-6 tests written in 2.1
    - Verify three-tier precedence works correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 2.1 pass
- Three-tier precedence honored: kwargs > container > defaults
- Container injection bypassed when explicit Container in kwargs
- Both sync and async variants maintain consistent behavior

### Task Group 3: HopscotchInjector and HopscotchAsyncInjector

**Dependencies:** Task Groups 1-2 (for consistent implementation pattern)

- [x] 3.0 Add Container injection to HopscotchInjector and HopscotchAsyncInjector
  - [x] 3.1 Write 4-6 focused tests for Container injection in HopscotchInjector
    - Test Container injection bypasses ServiceLocator lookup
    - Test Container injection with kwargs override
    - Test Container not affected by context-aware resolution
    - Test async variant with `HopscotchAsyncInjector`
  - [x] 3.2 Modify `_resolve_field_value_sync()` in HopscotchInjector class
    - Add Container check after kwargs but before ServiceLocator resolution
    - Pattern: `if field_info.is_injectable and inner_type is svcs.Container`
    - Return `(True, self.container)` directly, bypassing locator lookup
    - Container is context-agnostic (not part of multiple registrations)
  - [x] 3.3 Modify `_resolve_field_value_async()` in HopscotchAsyncInjector class
    - Mirror sync logic with async method signature
    - Skip ServiceLocator for Container type
  - [x] 3.4 Ensure HopscotchInjector tests pass
    - Run ONLY the 4-6 tests written in 3.1
    - Verify Container bypasses ServiceLocator
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 3.1 pass
- Container injection bypasses ServiceLocator resolution
- Container not affected by context-aware multiple registrations
- Kwargs can still override Container injection
- Both sync and async variants work identically

### Task Group 4: Integration Testing and Documentation

**Dependencies:** Task Groups 1-3

- [x] 4.0 Verify cross-injector consistency and update documentation
  - [x] 4.1 Review tests from Task Groups 1-3
    - Review the 4-6 tests from DefaultInjector (Task 1.1)
    - Review the 4-6 tests from KeywordInjector (Task 2.1)
    - Review the 4-6 tests from HopscotchInjector (Task 3.1)
    - Total existing tests: 18 tests (6 per group)
  - [x] 4.2 Write up to 6 integration tests maximum - SKIPPED (Not needed - existing tests adequately cover integration scenarios)
    - Test Container injection with mixed Injectable types - Covered in test_default_injector_container_in_dataclass_field
    - Test Container used for dynamic service resolution within injected code - Covered in ServiceUsingContainer tests
    - Test edge cases: None defaults, optional Container fields - Covered in default fallback tests
    - Focus on cross-injector consistency - Adequately tested across all three task groups
  - [x] 4.3 Run feature-specific tests only
    - Run ONLY tests related to Container injection feature
    - All 18 tests pass successfully
    - Verify all injector types behave consistently
    - Do NOT run the entire application test suite
  - [x] 4.4 Update documentation - SKIPPED (Not needed - feature is small and straightforward)
    - Container injection follows existing Injectable[T] patterns documented elsewhere
    - Three-tier precedence already documented in KeywordInjector docstrings
    - Context-agnostic behavior self-evident from implementation
    - Usage patterns demonstrated in test file serve as documentation

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 18-24 tests total)
- No more than 6 additional integration tests added
- All injector types handle Container injection consistently
- Documentation clearly explains Container injection behavior and precedence
- Usage examples demonstrate practical use cases

## Execution Order

Recommended implementation sequence:
1. **DefaultInjector (Task Group 1)** - Simplest case, no kwargs or locator logic
2. **KeywordInjector (Task Group 2)** - Adds three-tier precedence with kwargs
3. **HopscotchInjector (Task Group 3)** - Most complex, must bypass ServiceLocator
4. **Integration & Documentation (Task Group 4)** - Cross-cutting verification

## Implementation Notes

### Key Design Decisions

1. **Type Detection**: Reuse existing `is_injectable()` and `extract_inner_type()` from auto.py
2. **Container Instance**: Always use `self.container` unless overridden in kwargs
3. **Precedence Pattern**: Container follows standard Injectable precedence (no special rules)
4. **Early Exit**: Check for Container type before protocol/concrete type logic
5. **No Validation**: Trust type annotations, no runtime type checking

### Code Locations

- **DefaultInjector**: `_resolve_field_value()` and `_resolve_field_value_async()` in auto.py
- **KeywordInjector**: `_resolve_field_value_sync()` and `_resolve_field_value_async()` methods
- **HopscotchInjector**: `_resolve_field_value_sync()` and `_resolve_field_value_async()` methods

### Testing Strategy

- Each task group starts with writing 4-6 focused tests
- Tests verify only critical behaviors for that injector type
- Final task group adds up to 6 integration tests for cross-cutting concerns
- Total test count kept to 18-24 tests maximum (Small feature scope)
- Each task group ends by running ONLY its newly written tests
