# Task Breakdown: Hopscotch Registry

## Overview
Total Tasks: 4 Task Groups with approximately 20 sub-tasks

This spec creates `HopscotchRegistry` and `HopscotchContainer` classes that provide pre-wired integration between svcs registry/container and ServiceLocator for multi-implementation service resolution with minimal setup.

## Key Design Points
- HopscotchRegistry extends svcs.Registry with internal ServiceLocator management
- HopscotchContainer extends svcs.Container with HopscotchInjector defaults
- Resource is resolved dynamically at inject() time (NOT stored on container)
- scan() auto-detects HopscotchRegistry and uses its internal locator

## Task List

### Core Classes Layer

#### Task Group 1: HopscotchRegistry Implementation
**Dependencies:** None

- [x] 1.0 Complete HopscotchRegistry class
  - [x] 1.1 Write 4-6 focused tests for HopscotchRegistry
    - Test HopscotchRegistry can be instantiated (inherits svcs.Registry)
    - Test `locator` property returns internal ServiceLocator
    - Test `register_implementation()` registers to internal locator
    - Test `register_implementation()` auto-registers locator as value service
    - Test immutable update pattern (locator.register returns new instance, internal ref updated)
    - Test inherited methods (register_factory, register_value) work unchanged
  - [x] 1.2 Create HopscotchRegistry class in new module `src/svcs_di/hopscotch_registry.py`
    - Use `@attrs.define` to subclass svcs.Registry (follow InjectorContainer pattern)
    - Add `_locator: ServiceLocator` field with `attrs.field(factory=ServiceLocator, init=False)`
    - Add `locator` property for read-only access to `_locator`
    - Reference: `src/svcs_di/injector_container.py` for @attrs.define subclassing pattern
  - [x] 1.3 Implement `register_implementation()` method
    - Signature: `register_implementation(service_type: type, implementation: type, *, resource: type | None = None, location: PurePath | None = None) -> None`
    - Call `self._locator = self._locator.register(service_type, implementation, resource=resource, location=location)`
    - Call `self.register_value(ServiceLocator, self._locator)` to update registry
    - No return value (mutates internal state)
  - [x] 1.4 Add docstrings and type annotations
    - Match docstring style from InjectorContainer
    - Include usage examples in docstring
  - [x] 1.5 Ensure HopscotchRegistry tests pass
    - Run ONLY the 4-6 tests written in 1.1
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 1.1 pass
- HopscotchRegistry subclasses svcs.Registry correctly
- `locator` property provides read-only access
- `register_implementation()` updates internal locator and re-registers as value

---

#### Task Group 2: HopscotchContainer Implementation
**Dependencies:** Task Group 1

- [x] 2.0 Complete HopscotchContainer class
  - [x] 2.1 Write 5-7 focused tests for HopscotchContainer
    - Test HopscotchContainer can be instantiated with HopscotchRegistry
    - Test `injector` field defaults to HopscotchInjector
    - Test `async_injector` field defaults to HopscotchAsyncInjector
    - Test `inject()` resolves resource dynamically from container
    - Test `inject()` raises ValueError when no injector configured
    - Test `ainject()` resolves resource dynamically from container (async)
    - Test `ainject()` raises ValueError when no async_injector configured
  - [x] 2.2 Create HopscotchContainer class in `src/svcs_di/hopscotch_registry.py`
    - Use `@attrs.define` to subclass svcs.Container (follow InjectorContainer pattern)
    - Add `injector` field defaulting to HopscotchInjector
    - Add `async_injector` field defaulting to HopscotchAsyncInjector
    - NO `resource` attribute on HopscotchContainer
    - Reference: `src/svcs_di/injector_container.py` for exact field definition style
  - [x] 2.3 Implement `inject()` method with dynamic resource resolution
    - Signature: `inject[T](svc_type: type[T], /, **kwargs) -> T`
    - Resolve resource type dynamically from container (look for registered resource type)
    - Call `self.injector(container=self, resource=resolved_resource)(svc_type, **kwargs)`
    - Raise ValueError if no injector configured
    - Reference: HopscotchInjector._get_resource() for resolution pattern
  - [x] 2.4 Implement `ainject()` method with async dynamic resource resolution
    - Signature: `async ainject[T](svc_type: type[T], /, **kwargs) -> T`
    - Same dynamic resource resolution pattern as inject() but async
    - Use `aget()` for async container lookups
    - Raise ValueError if no async_injector configured
  - [x] 2.5 Add docstrings and type annotations
    - Match docstring style from InjectorContainer
    - Include usage examples showing dynamic resource resolution
  - [x] 2.6 Ensure HopscotchContainer tests pass
    - Run ONLY the 5-7 tests written in 2.1
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 5-7 tests written in 2.1 pass
- HopscotchContainer subclasses svcs.Container correctly
- Default injectors are HopscotchInjector/HopscotchAsyncInjector
- inject()/ainject() resolve resource dynamically from container
- No resource attribute stored on container

---

### Integration Layer

#### Task Group 3: scan() Integration and Module Exports
**Dependencies:** Task Groups 1-2

- [x] 3.0 Complete scan() integration and exports
  - [x] 3.1 Write 4-6 focused tests for scan() HopscotchRegistry integration
    - Test scan() detects HopscotchRegistry and uses its internal locator
    - Test scan() with HopscotchRegistry: simple registrations go to registry.register_factory()
    - Test scan() with HopscotchRegistry: items with resource/location use registry.register_implementation()
    - Test scan() with standard svcs.Registry: existing behavior unchanged
    - Test locator is NOT re-registered as separate value (uses registry's internal locator)
  - [x] 3.2 Modify `_get_or_create_locator()` in `src/svcs_di/injectors/scanning.py`
    - Detect if registry is HopscotchRegistry (isinstance check)
    - If HopscotchRegistry: return `registry.locator` (its internal locator)
    - If standard Registry: keep existing behavior (get from container or create new)
  - [x] 3.3 Modify `_register_decorated_items()` in `src/svcs_di/injectors/scanning.py`
    - Detect if registry is HopscotchRegistry
    - For HopscotchRegistry with resource/location/for_: call `registry.register_implementation()` directly
    - For HopscotchRegistry: do NOT call `registry.register_value(ServiceLocator, locator)` at end (already handled)
    - For standard Registry: keep existing behavior unchanged
  - [x] 3.4 Update `src/svcs_di/__init__.py` exports
    - Import HopscotchRegistry from hopscotch_registry module
    - Import HopscotchContainer from hopscotch_registry module
    - Add both to `__all__` list
    - Update module docstring to mention new exports
  - [x] 3.5 Ensure scan() integration tests pass
    - Run ONLY the 4-6 tests written in 3.1
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 4-6 tests written in 3.1 pass
- scan() auto-detects HopscotchRegistry and uses its internal locator
- HopscotchRegistry.register_implementation() called for resource/location items
- Standard svcs.Registry behavior unchanged
- Both classes exported from main package

---

### Testing Layer

#### Task Group 4: Test Review and Gap Analysis
**Dependencies:** Task Groups 1-3

- [x] 4.0 Review existing tests and fill critical gaps only
  - [x] 4.1 Review tests from Task Groups 1-3
    - Review the 4-6 tests written in Task 1.1 (HopscotchRegistry)
    - Review the 5-7 tests written in Task 2.1 (HopscotchContainer)
    - Review the 4-6 tests written in Task 3.1 (scan() integration)
    - Total existing tests: 21 tests
  - [x] 4.2 Analyze test coverage gaps for THIS feature only
    - Identified gaps: end-to-end location workflows, scan() with location, kwargs override, for_ parameter, hierarchical location, combined resource+location, HopscotchContainer with standard svcs.Registry
    - Focus ONLY on gaps related to HopscotchRegistry/HopscotchContainer
    - Prioritize end-to-end workflows: registry -> container -> inject -> resolution
    - Do NOT assess entire application test coverage
  - [x] 4.3 Write up to 8 additional strategic tests maximum
    - End-to-end test: HopscotchRegistry + HopscotchContainer + location-based resolution
    - End-to-end test: Hierarchical location matching (/admin/users matches /admin)
    - Integration test: scan() + HopscotchRegistry + @injectable with location
    - Integration test: scan() + HopscotchRegistry + @injectable with for_ parameter
    - Edge case: HopscotchContainer inject() with kwargs override
    - Edge case: register_implementation with combined resource AND location
    - Edge case: HopscotchContainer with standard svcs.Registry (fallback behavior)
    - Async end-to-end test: ainject with location
  - [x] 4.4 Run feature-specific tests only
    - Run ONLY tests related to HopscotchRegistry and HopscotchContainer
    - Total: 29 tests (21 original + 8 gap tests)
    - Do NOT run the entire application test suite
    - All 29 tests pass

**Acceptance Criteria:**
- All feature-specific tests pass (29 tests total)
- End-to-end workflow: registry -> container -> inject -> multi-implementation resolution works
- scan() integration with HopscotchRegistry works correctly
- 8 additional tests added when filling in testing gaps

---

## Execution Order

Recommended implementation sequence:
1. **Task Group 1: HopscotchRegistry** - Core registry class with internal locator
2. **Task Group 2: HopscotchContainer** - Container with dynamic resource resolution
3. **Task Group 3: scan() Integration** - Auto-detection and module exports
4. **Task Group 4: Test Review** - Gap analysis and integration tests

## Files to Create/Modify

**New Files:**
- `src/svcs_di/hopscotch_registry.py` - HopscotchRegistry and HopscotchContainer classes
- `tests/test_hopscotch_registry.py` - Tests for new classes

**Files to Modify:**
- `src/svcs_di/injectors/scanning.py` - Update _get_or_create_locator() and _register_decorated_items()
- `src/svcs_di/__init__.py` - Add exports for new classes

## Reference Files (Read-Only)

- `src/svcs_di/injector_container.py` - Pattern for @attrs.define subclassing
- `src/svcs_di/injectors/hopscotch.py` - HopscotchInjector (no modifications needed)
- `src/svcs_di/injectors/locator.py` - ServiceLocator (no modifications needed)

## Out of Scope Reminders

- Do NOT modify HopscotchInjector or HopscotchAsyncInjector
- Do NOT modify ServiceLocator
- Do NOT refactor existing examples
- Do NOT update README.md
- Do NOT add resource attribute to HopscotchContainer
- Do NOT add location parameter to inject/ainject methods
