# Task Breakdown: Optional Scanning Module

## Overview
Total Tasks: 21 core tasks across 4 major phases
Feature: Venusian-inspired scanning for auto-discovery of services via decorators

## Task List

### Phase 1: Core Decorator Infrastructure

#### Task Group 1: @injectable Decorator Implementation
**Dependencies:** None
**Location:** `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/locator.py`

- [x] 1.0 Complete @injectable decorator infrastructure
  - [x] 1.1 Write 2-8 focused tests for @injectable decorator
    - Test bare decorator: `@injectable` marks class for registration
    - Test decorator with resource parameter: `@injectable(resource=CustomerContext)`
    - Test decorator without resource (default registration)
    - Test metadata storage without immediate registration
    - Test multiple decorators on same service type
    - Limit to 2-8 highly focused tests - no exhaustive edge case testing
  - [x] 1.2 Create @injectable decorator class
    - Accept optional `resource` parameter for resource-specific implementations
    - Support both `@injectable` and `@injectable()` syntax (bare and called)
    - Store metadata on decorated class via `__injectable_metadata__` attribute
    - Metadata format: `{"resource": Optional[type]}`
    - Defer all registration - NO registry interaction at decoration time
    - Return decorated class unchanged (decorator is transparent)
  - [x] 1.4 Ensure decorator tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify metadata is stored correctly
    - Verify no registration happens at decoration time
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- `@injectable` and `@injectable(resource=X)` work correctly
- Metadata stored but no registration occurs
- Both bare and called decorator syntax supported

**Reference Patterns:**
- Similar to dataclass decorator pattern (transparent class wrapper)
- Follow frozen dataclass pattern from locator.py for immutability concepts
- Metadata storage pattern similar to Flask route decorators

---

### Phase 2: Package Scanning Implementation

#### Task Group 2: Module Discovery and Import
**Dependencies:** Task Group 1
**Location:** `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/locator.py`

- [x] 2.0 Complete module discovery and scanning logic
  - [x] 2.1 Write 2-8 focused tests for scan() function
    - Test scanning a single module with decorated classes
    - Test scanning a package (multiple modules)
    - Test scan() returns registry for method chaining
    - Test decorated items are registered to registry
    - Test resource-based registrations go to ServiceLocator
    - Test scan handles missing/empty packages gracefully
    - Limit to 2-8 tests - focus on critical scanning behaviors
  - [x] 2.2 Create scan() standalone function signature
    - Parameters: `scan(registry: svcs.Registry, *packages: str | ModuleType, injector_type: type = DefaultInjector)`
    - Accept registry instance (does NOT extend Registry class)
    - Accept package/module references as strings or ModuleType objects
    - Accept optional injector_type parameter (default: DefaultInjector)
    - Return registry for method chaining pattern
    - Type hints: use proper typing for all parameters
  - [x] 2.3 Implement package discovery using importlib.metadata
    - Use `importlib.import_module()` for module loading
    - Use `pkgutil.walk_packages()` for package traversal
    - Support both string package names ("myapp.services") and ModuleType objects
    - Handle top-level modules and nested packages
    - Skip __pycache__, .pyc files, and non-Python files
    - Follow Python 3.14+ standards for import mechanisms
  - [x] 2.4 Implement module import and decorator execution
    - Import each discovered module to trigger decorator execution
    - Decorator execution attaches metadata to classes
    - Handle import errors gracefully (log warning, continue scanning)
    - No attempt to construct services during scan phase
    - Thread-safe: all registration before containers created
  - [x] 2.5 Ensure scanning tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify modules are discovered and imported
    - Verify scan() returns registry for chaining
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- scan() accepts registry, packages, and injector type
- Packages are discovered using stdlib importlib.metadata
- Modules are imported to execute decorators
- scan() returns registry for chaining
- Thread-safe: no container interaction during scan

**Reference Patterns:**
- Use `pkgutil.walk_packages()` like venusian does for package traversal
- Follow importlib.metadata patterns from Python 3.14+ documentation
- Error handling pattern from auto.py TypeHintResolutionError

---

### Phase 3: Registration Integration

#### Task Group 3: Registration Logic with ServiceLocator
**Dependencies:** Task Groups 1, 2
**Location:** `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/locator.py`

- [x] 3.0 Complete registration integration with ServiceLocator
  - [x] 3.1 Write 2-8 focused tests for registration integration
    - Test resource-based registrations use ServiceLocator.register()
    - Test non-resource registrations use Registry.register_factory()
    - Test LIFO ordering is maintained
    - Test multiple implementations of same service type
    - Test registration creates proper factory functions
    - Test nested dependency injection with decorated services
    - Test scanning with existing test fixtures
    - Limit to 2-8 tests - focus on registration mechanics
  - [x] 3.2 Collect decorated items during scan
    - Walk through all imported modules
    - Check each class for `__injectable_metadata__` attribute
    - Collect tuples of (class, metadata) for registration
    - Preserve LIFO ordering (scan order = registration order)
  - [x] 3.3 Implement resource-based registration to ServiceLocator
    - For decorated items with `resource` in metadata:
      - Get or create ServiceLocator from registry
      - Use `ServiceLocator.register(service_type, impl, resource=X)`
      - Register updated locator back to registry via `register_value()`
    - Follow existing pattern from locator.py ServiceLocator.register()
    - Maintain LIFO ordering and caching behavior
    - Use existing FactoryRegistration dataclass
  - [x] 3.4 Implement non-resource registration to Registry
    - For decorated items without resource:
      - Create factory function: `lambda container: injector(decorated_class)`
      - Use `Registry.register_factory(decorated_class, factory_func)`
      - Factory signature: `(svcs_container: svcs.Container) -> T`
      - Follow existing auto() factory pattern from auto.py
    - Reuse get_field_infos and FieldInfo from auto.py
    - Support Injectable[T] fields in decorated classes
  - [x] 3.6 Ensure registration integration tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify resource-based items go to ServiceLocator
    - Verify non-resource items go to Registry
    - Verify LIFO ordering maintained
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 8 tests written in 3.1 pass
- Resource-based registrations use ServiceLocator.register()
- Non-resource registrations use Registry.register_factory()
- LIFO ordering maintained
- Factory functions follow auto() pattern

**Reference Patterns:**
- ServiceLocator.register() from locator.py lines 119-140
- auto() factory pattern from auto.py lines 432-457
- FactoryRegistration dataclass from locator.py lines 21-56
- get_field_infos from auto.py lines 232-356

---

### Phase 4: Context Integration and Examples

#### Task Group 4: HopscotchInjector Integration
**Dependencies:** Task Groups 1, 2, 3
**Location:** `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/locator.py`

- [x] 4.0 Complete context integration with HopscotchInjector
  - [x] 4.1 Write 2-8 focused tests for context integration
    - Test scan phase is context-agnostic (no context resolution)
    - Test HopscotchInjector resolves context at request time
    - Test resource matching follows three-tier precedence (exact > subclass > default)
    - Test decorated services work with existing HopscotchInjector
    - Test context resolution via _get_resource() method
    - Test decorated classes with Injectable[T] fields resolve correctly
    - Limit to 2-8 tests - focus on context resolution timing
  - [x] 4.2 Verify scan phase is context-agnostic
    - Scan phase only records resource metadata
    - No context detection or resolution during scanning
    - No invocation of HopscotchInjector during scan
    - Context is Optional[type] stored in FactoryRegistration
  - [x] 4.3 Verify request-time context resolution
    - HopscotchInjector._get_resource() obtains resource at request time
    - Resource obtained from container.get(self.resource)
    - Type of resource instance determines resolution path
    - Follow existing three-tier precedence from locator.py
  - [x] 4.4 Test decorated services with existing injector patterns
    - Decorated classes work with HopscotchInjector
    - Decorated classes work with auto() if needed
    - Injectable[T] fields in decorated classes resolve via existing logic
    - No changes needed to HopscotchInjector implementation
  - [x] 4.5 Ensure context integration tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify scan phase is context-agnostic
    - Verify context resolved at request time only
    - Verify three-tier precedence maintained
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- Scan phase records resource metadata only
- Context resolution happens at request time via HopscotchInjector
- Three-tier precedence maintained (exact > subclass > default)
- Decorated services work with existing injector patterns
- No changes needed to HopscotchInjector implementation

**Reference Patterns:**
- HopscotchInjector from locator.py lines 242-366
- _get_resource() method from locator.py lines 274-283
- Three-tier precedence from FactoryRegistration.matches() lines 33-56
- Resource resolution from ServiceLocator.get_implementation() lines 142-190

---

### Phase 5: Documentation and Examples

#### Task Group 5: Examples and Documentation
**Dependencies:** Task Groups 1-4
**Location:** `/Users/pauleveritt/projects/pauleveritt/svcs-di/examples/scanning/` (new directory)

- [x] 5.0 Complete examples and documentation
  - [x] 5.1 Create basic scanning example
    - File: `examples/scanning/basic_scanning.py`
    - Simple classes with `@injectable` decorator
    - Call scan() to discover and register
    - Retrieve services from container
    - Show both bare `@injectable` and `@injectable()` syntax
    - Include comments explaining each step
  - [x] 5.2 Create context-aware scanning example
    - File: `examples/scanning/context_aware_scanning.py`
    - Multiple implementations with resource parameter
    - Use CustomerContext and EmployeeContext
    - Show `@injectable(resource=CustomerContext)` syntax
    - Demonstrate three-tier precedence in action
    - Show default implementation fallback
  - [x] 5.3 Add docstrings to all new functions and classes
    - Document scan() function with full parameter descriptions
    - Document @injectable decorator
    - Document integration points with ServiceLocator
    - Follow existing docstring style from locator.py and auto.py
    - Include usage examples in docstrings
  - [x] 5.4 Update module docstring in locator.py
    - Add section about scanning functionality
    - Explain decorator-based auto-discovery
    - Link to examples
    - Maintain existing documentation structure

**Acceptance Criteria:**
- Two complete working examples created
- Basic scanning example demonstrates simple workflow
- Context-aware example shows resource-based resolution
- All new code has comprehensive docstrings
- Examples are runnable and self-documenting

**Reference Patterns:**
- Docstring style from locator.py lines 1-9 and auto.py lines 1-9
- Example structure from existing svcs-di examples
- Code comment style from test files

---

### Phase 6: Test Review and Integration Testing

#### Task Group 6: Test Coverage Review and Integration Tests
**Dependencies:** Task Groups 1-5

- [ ] 6.0 Review existing tests and add strategic integration tests
  - [ ] 6.1 Review tests from Task Groups 1-4
    - Review 2-8 tests from Task 1.1 (decorator tests)
    - Review 2-8 tests from Task 2.1 (scanning tests)
    - Review 2-8 tests from Task 3.1 (registration tests)
    - Review 2-8 tests from Task 4.1 (context integration tests)
    - Total existing tests: approximately 8-32 tests
  - [ ] 6.2 Analyze test coverage gaps for scanning feature only
    - Identify critical end-to-end workflows that lack coverage
    - Focus ONLY on scanning feature, NOT entire application
    - Prioritize integration tests over unit test gaps
    - Check for gaps in error handling and edge cases
  - [ ] 6.3 Write up to 10 additional strategic tests maximum
    - End-to-end test: scan package -> retrieve service -> verify injection
    - Error case: scan package with import errors
    - Error case: decorated class with missing dependencies
    - Integration: scanning + ServiceLocator + HopscotchInjector workflow
    - Edge case: empty package (no decorated classes)
    - Edge case: nested packages with multiple decorated services
    - Performance: verify caching works after scanning
    - Thread safety: verify scan results are thread-safe
    - Method chaining: verify scan().register_factory().register_value() works
    - Integration with auto(): verify decorated classes work with auto() helper
    - Maximum 10 additional tests - do NOT write exhaustive coverage
  - [ ] 6.4 Run scanning feature tests only
    - Run tests from Tasks 1.1, 2.1, 3.1, 4.1, and 6.3
    - Expected total: approximately 18-42 tests maximum
    - Do NOT run entire application test suite
    - Verify all critical scanning workflows pass
    - Fix any failing tests

**Acceptance Criteria:**
- All scanning feature tests pass (approximately 18-42 tests total)
- Critical end-to-end workflows for scanning are covered
- Error handling and edge cases tested
- No more than 10 additional tests added
- Testing focused exclusively on scanning feature
- Thread safety verified
- Integration with existing ServiceLocator and HopscotchInjector verified

**Reference Patterns:**
- Test structure from tests/injectors/test_locator.py
- Integration test patterns from existing svcs-di test suite
- Error handling tests from test_auto.py TypeHintResolutionError tests

---

## Execution Order

Recommended implementation sequence:
1. **Phase 1: Core Decorator Infrastructure** (Task Group 1) ✅ COMPLETE
   - Implement @injectable decorator with metadata storage
   - Add @injectable.classmethod support
   - Verify metadata storage without registration

2. **Phase 2: Package Scanning Implementation** (Task Group 2) ✅ COMPLETE
   - Implement scan() function with package discovery
   - Add module import and decorator execution
   - Verify scan returns registry for chaining

3. **Phase 3: Registration Integration** (Task Group 3) ✅ COMPLETE
   - Implement resource-based registration to ServiceLocator
   - Implement non-resource registration to Registry
   - Add classmethod factory registration
   - Verify LIFO ordering and factory patterns

4. **Phase 4: Context Integration** (Task Group 4) ✅ COMPLETE
   - Verify scan phase is context-agnostic
   - Verify HopscotchInjector resolves context at request time
   - Test three-tier precedence with decorated services

5. **Phase 5: Documentation and Examples** (Task Group 5) ✅ COMPLETE
   - Create two complete examples
   - Add comprehensive docstrings
   - Update module documentation

6. **Phase 6: Test Review and Integration Testing** (Task Group 6)
   - Review existing test coverage
   - Add up to 10 strategic integration tests
   - Run and verify all scanning feature tests

---

## Implementation Notes

### Key Design Constraints
- **No Registry Extension**: scan() is standalone function, NOT a Registry method
- **Defer Registration**: Decorators only store metadata, registration happens during scan()
- **Thread Safety**: All registration happens before containers are created
- **stdlib Only**: Use importlib.metadata and pkgutil, no external dependencies
- **Minimal Scope**: No venusian features like categories, depth, ignore, callbacks

### Integration Points
- **ServiceLocator.register()**: For resource-based registrations (lines 119-140 in locator.py)
- **Registry.register_factory()**: For non-resource registrations
- **auto() factory pattern**: Follow signature `(svcs_container: svcs.Container) -> T`
- **get_field_infos**: Reuse from auto.py for introspecting decorated classes
- **HopscotchInjector**: Context resolution at request time, NOT during scanning

### Testing Strategy
- Each phase writes 2-8 focused tests during development
- Final integration phase adds maximum 10 strategic tests
- Total expected tests: approximately 18-42 tests for entire scanning feature
- Focus on critical workflows, NOT exhaustive coverage
- Test verification runs ONLY newly written tests, NOT entire suite

### File Locations
- Implementation: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/locator.py`
- Tests: `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/injectors/test_locator.py`
- Examples: `/Users/pauleveritt/projects/pauleveritt/svcs-di/examples/scanning/`

### Out of Scope (Do Not Implement)
- Venusian features: depth, ignore, categories, action callbacks, onerror
- Extending Registry class with scan methods
- Separate installable extra or package structure
- Scan-time dependency injection or service construction
- Automatic context detection during scanning
- Path-based or location-based registration
- Configuration file-based registration
- Decorator support for functions (only classes)
- Classmethod decorator alternative for decoration configuration
- Multiple scan passes or incremental scanning
- Unregistration or decorator removal functionality
