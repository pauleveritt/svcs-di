# Task Breakdown: Minimal svcs.auto() Helper for Automatic Dependency Injection

## Overview

Total Tasks: 32 sub-tasks across 4 major task groups

## Task List

### Core Infrastructure

#### Task Group 1: Inject Marker and Type Introspection

**Dependencies:** None

- [x] 1.0 Complete core type infrastructure
    - [x] 1.1 Write 2-8 focused tests for Inject marker and type introspection
        - Limit to 2-8 highly focused tests maximum
        - Test only critical behaviors: Inject generic wrapping, type extraction from Inject, protocol detection
        - Skip exhaustive coverage of all edge cases
    - [x] 1.2 Create `Inject[T]` generic type marker
        - Define as `TypeAlias` or `Generic` wrapper
        - Must preserve the inner type T for runtime extraction
        - Example: `db: Inject[Database]` marks db as injectable
    - [x] 1.3 Implement type extraction utilities
        - Function to extract inner type from `Inject[T]`
        - Function to detect if a type is wrapped in `Inject`
        - Handle `Optional[Inject[T]]` and similar nested generics
    - [x] 1.4 Implement protocol detection utility
        - Use `typing.get_origin()` and `typing.get_args()` to unwrap Inject
        - Use `inspect.isclass()` and check for `_is_protocol` attribute
        - Alternative: use `typing.get_protocol_members()` if available in Python 3.12+
        - Return True if inner type of `Inject[T]` is a Protocol
    - [x] 1.5 Implement parameter/field introspection
        - For functions: use `inspect.signature()` + `typing.get_type_hints(eval_str=True)`
        - For dataclasses: use `dataclasses.fields()` + `typing.get_type_hints(eval_str=True)`
        - Create unified `FieldInfo` structure (NamedTuple or dataclass)
        - Fields: name, type_hint, is_injectable, inner_type, is_protocol, has_default, default_value
        - Follow Hopscotch pattern: single interface for both dataclasses and functions
        - Handle forward references with graceful fallback (try eval_str=True, then without)
    - [x] 1.6 Ensure core infrastructure tests pass
        - Run ONLY the 2-8 tests written in 1.1
        - Verify Inject marker works correctly
        - Verify type extraction and protocol detection work
        - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**

- The 2-8 tests written in 1.1 pass
- `Inject[T]` can wrap any type T
- Type extraction correctly unwraps Inject to get inner type
- Protocol detection correctly identifies Protocol types
- Parameter introspection works for both functions and dataclasses
- Field info includes all necessary metadata for dependency resolution

**Implementation Notes:**
- Single module implementation in `src/svcs_di/auto.py`
- No imports beyond stdlib (`inspect`, `dataclasses`, `typing`) and `svcs`
- Follow Hopscotch patterns for unified field inspection
- Follow svcs patterns for robust signature inspection with eval_str=True

**After Implementation:**
Update the tasks.md file at `/Users/pauleveritt/projects/pauleveritt/svcs-di/agent-os/specs/2025-12-24-core-type-safe-dependency-injection/tasks.md` to mark all completed subtasks with `- [x]`.

### Dependency Resolution

#### Task Group 2: Default Injector Implementation

**Dependencies:** Task Group 1

- [x] 2.0 Complete default injector implementation
    - [x] 2.1 Write 2-8 focused tests for default injector
        - Limit to 2-8 highly focused tests maximum
        - Test only critical injector behaviors: kwarg precedence, container resolution, default fallback
        - Skip exhaustive testing of all scenarios
    - [x] 2.2 Define `Injector` protocol interface
        - Signature: `def __call__(target: type[T], container: Container, **kwargs: Any) -> T`
        - Document protocol requirements in docstring
        - Protocol should be stateless (pure function)
    - [x] 2.3 Implement default sync injector function
        - Extract field infos from target using utilities from Task 1.5
        - For each field, resolve value using precedence:
            1. If field name in kwargs, use kwargs value (highest precedence)
            2. Else if field is Inject, resolve from container:
                - If is_protocol: use `container.get_abstract(inner_type)`
                - Else: use `container.get(inner_type)`
            3. Else if field has default, use default value
            4. Else raise error (required field not provided)
        - Validate all kwargs match actual field names (raise ValueError if not)
        - Build resolved_kwargs dict with all field values
        - Call `target(**resolved_kwargs)` and return instance
    - [x] 2.4 Add async support to default injector
        - Detect if container.get() returns awaitable using `inspect.isawaitable()`
        - Make injector function async if any dependency is async
        - Use `container.aget()` and `container.aget_abstract()` for async resolution
        - Handle mixed sync/async dependencies appropriately
    - [x] 2.5 Add error handling to injector
        - Propagate `ServiceNotFoundError` from container as-is (don't wrap)
        - Raise `ValueError` for unknown kwargs with clear message
        - Raise `TypeError` for async/sync mismatches
        - Provide clear error messages indicating which field failed
    - [x] 2.6 Ensure default injector tests pass
        - Run ONLY the 2-8 tests written in 2.1
        - Verify precedence order works correctly
        - Verify both sync and async resolution work
        - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**

- The 2-8 tests written in 2.1 pass
- Injector protocol is clearly defined
- Default injector correctly implements three-tier precedence
- Async dependencies are detected and awaited
- Protocol types use get_abstract() method
- All kwargs are validated against actual parameters
- Errors propagate cleanly with clear messages

### Public API

#### Task Group 3: svcs.auto() Factory Function

**Dependencies:** Task Groups 1, 2

- [x] 3.0 Complete public auto() factory API
    - [x] 3.1 Write 2-8 focused tests for auto() factory
        - Limit to 2-8 highly focused tests maximum
        - Test only critical auto() behaviors: factory generation, registry integration, end-to-end injection
        - Skip exhaustive testing of all patterns
    - [x] 3.2 Implement injector registry lookup
        - Check if custom injector is registered in container
        - Use sentinel type/key for injector service (e.g., `_InjectorService` class)
        - If custom injector found, use it; else use default injector
        - Gracefully handle missing injector (treat as "use default")
    - [x] 3.3 Create `svcs.auto()` function
        - Signature: `def auto(target: type[T]) -> Callable[[Container], T]`
        - Returns factory function compatible with `register_factory()`
        - Factory signature: `def factory(svcs_container: Container, **kwargs) -> T`
        - Factory uses injector (custom or default) to construct target
        - Factory passes container and kwargs to injector
        - Support both sync and async factories automatically
    - [x] 3.4 Add factory wrapping for async detection
        - Make factory async if target requires async dependencies
        - Detect by checking if any Inject field would return awaitable
        - Alternatively: create sync factory that becomes async if needed
        - Follow svcs pattern: `aget()` works with both sync and async factories
    - [x] 3.5 Add module exports to `svcs_di/__init__.py`
        - Export `auto` function
        - Export `Inject` marker type
        - Export `Injector` protocol (for custom injector implementations)
        - Add `__all__` list for explicit public API
    - [x] 3.6 Ensure auto() factory tests pass
        - Run ONLY the 2-8 tests written in 3.1
        - Verify factory generation works
        - Verify integration with svcs Registry/Container works
        - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**

- The 2-8 tests written in 3.1 pass
- `svcs.auto()` returns proper factory function
- Factory works with `register_factory()`
- Custom injectors can be registered and are used
- Both sync and async contexts work correctly
- Public API is clean and well-documented

### Testing & Documentation

#### Task Group 4: Comprehensive Testing and Examples

**Dependencies:** Task Groups 1-3

- [x] 4.0 Complete testing and examples
    - [x] 4.1 Review tests from Task Groups 1-3
        - Review the 2-8 tests written by infrastructure-engineer (Task 1.1)
        - Review the 2-8 tests written by injector-engineer (Task 2.1)
        - Review the 2-8 tests written by api-engineer (Task 3.1)
        - Total existing tests: approximately 6-24 tests
    - [x] 4.2 Analyze test coverage gaps for this feature only
        - Identify critical integration workflows that lack coverage
        - Focus ONLY on gaps related to svcs.auto() feature requirements
        - Do NOT assess entire application test coverage
        - Prioritize end-to-end workflows and edge cases
        - Key areas to check:
            - Function parameters vs dataclass fields
            - Multiple Inject dependencies
            - Mixed injectable/non-injectable parameters
            - Protocol-based dependencies
            - Error conditions (missing services, invalid kwargs)
            - Async dependencies with sync factories
    - [x] 4.3 Write up to 10 additional strategic tests maximum
        - Add maximum of 10 new tests to fill identified critical gaps
        - Focus on integration points and end-to-end workflows
        - Do NOT write comprehensive coverage for all scenarios
        - Test files: `tests/test_injectable.py`, `tests/test_auto.py`, `tests/test_injector.py`
        - Cover: dataclass injection, function injection, protocol injection, async injection, error cases
    - [x] 4.4 Create working example: basic dataclass injection
        - File: `examples/basic_dataclass.py`
        - Demonstrate: simple dataclass with Inject dependencies
        - Show: registration with auto(), retrieval with get()
        - Keep minimal (10-20 lines)
    - [x] 4.5 Create working example: protocol-based injection
        - File: `examples/protocol_injection.py`
        - Demonstrate: Inject[ProtocolType] usage
        - Show: abstract service registration and retrieval
        - Include: implementation and protocol
    - [x] 4.6 Create working example: async injection
        - File: `examples/async_injection.py`
        - Demonstrate: async factory and async dependencies
        - Show: usage with aget() and async context manager
        - Include: both sync and async service mix
    - [x] 4.7 Create working example: kwargs override
        - File: `examples/kwargs_override.py`
        - Demonstrate: precedence order (kwargs > container > defaults)
        - Show: overriding Inject parameters via kwargs
        - Include: test-friendly pattern for dependency injection
    - [x] 4.8 Create working example: custom injector
        - File: `examples/custom_injector.py`
        - Demonstrate: implementing custom Injector protocol
        - Show: registration and usage of custom injector
        - Include: use case like validation or logging injector
    - [x] 4.9 Add inline documentation
        - Add comprehensive docstrings to all public functions
        - Document `Inject` marker usage with examples
        - Document `Injector` protocol with implementation guide
        - Document `auto()` function with usage patterns
        - Include type hints in all signatures
    - [x] 4.10 Run feature-specific tests only
        - Run ONLY tests related to svcs.auto() feature (tests from 1.1, 2.1, 3.1, and 4.3)
        - Expected total: approximately 16-34 tests maximum
        - Do NOT run the entire application test suite
        - Verify all critical workflows pass
        - Fix any failures before proceeding

**Acceptance Criteria:**

- All feature-specific tests pass (approximately 16-34 tests total)
- Critical workflows are covered: dataclass injection, function injection, protocols, async, kwargs
- No more than 10 additional tests added when filling in testing gaps
- Five working examples demonstrate key usage patterns
- All public APIs have comprehensive docstrings with examples
- Examples run successfully and demonstrate real-world patterns

## Execution Order

Recommended implementation sequence:

1. **Task Group 1: Core Infrastructure** (Inject marker and type introspection)
    - Build foundation: type marker, extraction utilities, field introspection
    - Creates the building blocks for dependency resolution
    - No dependencies on other groups

2. **Task Group 2: Dependency Resolution** (Default injector implementation)
    - Build on Task 1: uses field introspection to resolve dependencies
    - Implements core logic: precedence, container lookup, async support
    - Creates reusable injector that can be customized

3. **Task Group 3: Public API** (svcs.auto() factory function)
    - Build on Tasks 1-2: uses injector to create factories
    - Implements registry integration and factory generation
    - Creates the main user-facing API

4. **Task Group 4: Testing & Documentation** (Comprehensive testing and examples)
    - Build on Tasks 1-3: tests and documents complete feature
    - Fills coverage gaps and creates working examples
    - Validates end-to-end functionality

## Implementation Notes

### Key Design Decisions

1. **Explicit Inject Marker**: Parameters must be explicitly marked with `Injectable[T]` to be injected from
   container. This prevents accidental injection and makes dependencies clear in code.

2. **Kwargs Override Everything**: Even `Injectable[T]` parameters can be overridden via kwargs. This enables testing
   and flexible configuration while maintaining type safety.

3. **Single Module Implementation**: All code lives in `src/svcs_di/auto.py` (or similar). No imports beyond stdlib (
   `inspect`, `dataclasses`, `typing`) and `svcs`. This keeps the implementation minimal and upstreamable.

4. **Stateless Design**: No global state, no caches. All inspection happens per-call. This ensures free-threaded
   compatibility and follows svcs patterns.

5. **Protocol-Based Extensibility**: The `Injector` protocol allows custom injection strategies without modifying core
   code. Default injector handles common cases.

6. **Graceful Async Handling**: Single `auto()` function works in both sync and async contexts. Detection is automatic
   based on container method return types.

### Critical Patterns to Follow

From **Hopscotch** (`field_infos.py`):

- Unified `FieldInfo` structure for both dataclasses and functions
- Single interface: `get_field_infos(target)` returns consistent metadata
- Normalize defaults, default factories, and type information

From **Hopscotch** (`registry.py`):

- Three-tier precedence: kwargs > registry/container > defaults
- Validate all kwargs match actual field names (fail fast)
- Use keyword arguments exclusively for injection

From **svcs** (`_core.py`):

- Robust signature inspection with `eval_str=True` for forward references
- Graceful fallback when inspection fails (try with eval_str, then without)
- Use `isawaitable()` to detect async results
- Protocol support via `get_abstract()` methods

### Testing Strategy

**Per-Task-Group Testing** (Tasks 1.1, 2.1, 3.1):

- Each engineer writes 2-8 focused tests for their component
- Tests verify critical behaviors only, not exhaustive coverage
- Tests run in isolation (only that component's tests)
- Purpose: Catch obvious errors early in development

**Gap Analysis Testing** (Task 4.2-4.3):

- After all components built, test engineer reviews coverage
- Identifies critical integration gaps and edge cases
- Adds maximum 10 strategic tests to fill gaps
- Purpose: Ensure end-to-end workflows and error handling work

**Total Expected Tests**: 16-34 tests maximum

- Focus on critical paths and integration points
- Skip exhaustive unit testing of every method
- Prioritize real-world usage patterns from examples

### File Structure

```
src/svcs_di/
├── __init__.py          # Exports: auto, Injectable, Injector
├── auto.py              # Main implementation (all code in one module)
└── py.typed             # Existing marker file

tests/
├── test_injectable.py   # Tests for Injectable marker and type introspection
├── test_injector.py     # Tests for Injector protocol and default implementation
└── test_auto.py         # Tests for auto() factory and integration

examples/
├── basic_dataclass.py   # Simple dataclass injection example
├── protocol_injection.py # Protocol-based dependency example
├── async_injection.py   # Async dependencies example
├── kwargs_override.py   # Precedence and override example
└── custom_injector.py   # Custom injector implementation example
```

### Integration with svcs

**Registry Integration:**

```python
# User code
registry = svcs.Registry()
registry.register_factory(Database, svcs_di.auto(Database))
registry.register_factory(WebService, svcs_di.auto(WebService))

# Later
container = registry.get_container()
db = container.get(Database)  # Auto-resolves dependencies
```

**Custom Injector Registration:**

```python
# Optional: register custom injector
registry.register_value(_InjectorService, my_custom_injector)

# Now all auto() factories will use custom injector
registry.register_factory(MyClass, svcs_di.auto(MyClass))
```

### Free-Threaded Compatibility

**Ensured by:**

- No global mutable state (no module-level caches)
- All stateful data in Registry/Container (per svcs design)
- Injector is pure function (stateless)
- Field inspection is stateless (happens per-call)

**Thread-safe operations:**

- `svcs.auto()` can be called from any thread
- Factory functions can be called from any thread
- Container lifecycle is already thread-safe per svcs

### Upstream Compatibility

**Design choices for svcs acceptance:**

- Single module, minimal implementation
- No dependencies beyond stdlib + svcs
- Optional helper (users opt in)
- Non-magical explicit approach (Injectable marker required)
- Follows existing svcs patterns (async, protocols, errors)
- No modification to svcs core classes
- Pluggable via protocol for extensibility

## Success Criteria

1. All 16-34 feature-specific tests pass
2. Examples run successfully and demonstrate real-world usage
3. Implementation is single module with no extra dependencies
4. Works with existing svcs Registry and Container
5. Supports both sync and async contexts automatically
6. Protocol-based dependencies work correctly
7. Custom injectors can be registered and used
8. Free-threaded compatible (no global state)
9. Documentation is comprehensive with examples
10. Code is clean, maintainable, and upstreamable

## Next Steps After Implementation

1. **Performance Testing**: Measure overhead of auto() vs manual factories
2. **Real-World Usage**: Test with actual applications to find edge cases
3. **Upstream Proposal**: If successful, propose to svcs maintainer
4. **Advanced Features**: Consider Phase 1+ features (Annotated metadata, context-aware resolution)
