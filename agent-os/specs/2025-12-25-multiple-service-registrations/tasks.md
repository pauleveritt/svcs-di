# Task Breakdown: Multiple Service Registrations

## Overview
Total Task Groups: 8
Estimated Size: Large (Roadmap Item 5)

This feature implements multiple service registrations with metadata-driven resolution, building on the KeywordInjector pattern and adapting patterns from Hopscotch Registry. The implementation focuses on a three-tier precedence algorithm (high/medium/low) while storing metadata placeholders for future context and location-based resolution (Items 6-7).

## Task List

### Core Data Structures

#### Task Group 1: Registration Dataclass and Storage Infrastructure
**Dependencies:** None

- [x] 1.0 Complete core data structures
  - [x] 1.1 Write 2-8 focused tests for Registration and storage
    - Test Registration creation with singleton vs class
    - Test automatic field_infos extraction in __post_init__
    - Test IsNoneType marker usage for no-context registrations
    - Test KindGroups structure initialization
    - Test nested defaultdict storage behavior
    - Test LIFO ordering (insert at position 0)
  - [x] 1.2 Create IsNoneType marker class
    - Marker class for no-context registrations
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 32-35
  - [x] 1.3 Create Registration dataclass
    - Fields: implementation, kind, context, field_infos, is_singleton
    - Use slots for performance optimization
    - Implement __post_init__ to extract field_infos automatically
    - Call get_field_infos from svcs_di.auto unless is_singleton is True
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 38-53
  - [x] 1.4 Create KindGroups TypedDict
    - Define with "singletons" and "classes" keys
    - Each maps to dict[Union[type, IsNoneType], list[Registration]]
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 167-172
  - [x] 1.5 Implement make_singletons_classes factory
    - Returns initialized KindGroups structure
    - Uses defaultdict(list) for second level
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 174-180
  - [x] 1.6 Create Registrations type alias
    - Type alias: dict[type, KindGroups]
    - Defines the top-level storage structure
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` line 183
  - [x] 1.7 Ensure data structure tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify Registration creation works correctly
    - Verify field_infos extraction happens automatically
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- Registration dataclass properly extracts field_infos in __post_init__
- IsNoneType marker distinguishes no-context registrations
- KindGroups structure separates singletons and classes
- Nested defaultdict storage initializes correctly
- LIFO ordering supported via list.insert(0, registration)

**Implementation Notes:**
- Store context metadata for future Item 6 (not used for resolution yet)
- Store location placeholder for future Item 7 (not used at all yet)
- Keep auto.py unchanged to avoid default implementation coupling
- Use slots on Registration for performance

### Resolution Algorithm

#### Task Group 2: Three-Tier Precedence Matching
**Dependencies:** Task Group 1 (COMPLETED)

- [x] 2.0 Complete resolution algorithm
  - [x] 2.1 Write 2-8 focused tests for get_best_match
    - Test high precedence: exact context match (this_context is context_class)
    - Test medium precedence: subclass match (issubclass)
    - Test low precedence: no context (IsNoneType)
    - Test precedence ordering: high + medium + low concatenation
    - Test LIFO within same precedence tier
    - Test parent registry fallback when no match
    - Test allow_singletons=False filters out singleton registrations
  - [x] 2.2 Implement get_best_match method
    - Create three precedence lists: high, medium, low
    - High: this_context is context_class (exact identity match)
    - Medium: issubclass(context_class, this_context) for inheritance
    - Low: this_context is IsNoneType (default/fallback)
    - Return first match from: high + medium + low
    - Support allow_singletons parameter to filter registrations
    - Fall back to parent registry if no match found
    - Return None if no match in current or parent registries
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 235-291
  - [x] 2.3 Implement register method
    - Add Registration instances to nested storage
    - Automatically infer kind from getmro() if not specified
    - Distinguish singletons from classes using isclass()
    - Use context parameter or IsNoneType for storage key
    - Insert at position 0 for LIFO override behavior
    - Extract field_infos automatically unless singleton
  - [x] 2.4 Ensure resolution algorithm tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify three-tier precedence works correctly
    - Verify LIFO ordering respected within tiers
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- get_best_match correctly implements three-tier precedence
- Exact context matches have highest priority
- Subclass matches have medium priority
- No-context registrations have lowest priority
- LIFO ordering maintained within each tier
- Parent registry fallback works when no local match

**Implementation Notes:**
- Defer advanced scoring with weights/priorities to Item 8
- Only basic three-tier precedence in this spec
- Context matching uses identity (is) and subclass checks only
- No location-based resolution yet (deferred to Item 7)

**Key Reference:**
- Hopscotch Registry get_best_match: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 235-291

### Injection and Construction

#### Task Group 3: Field Resolution and inject_callable Pattern
**Dependencies:** Task Groups 1, 2 (COMPLETED)

- [x] 3.0 Complete injection logic
  - [x] 3.1 Write 2-8 focused tests for inject_callable
    - Test three-tier field resolution: props > registry > defaults
    - Test __hopscotch_factory__ custom construction
    - Test registry lookup via inject_field_registry
    - Test fallback to inject_field_no_registry for unregistered deps
    - Test ValueError when required field cannot be resolved
    - Test singleton vs class construction paths
  - [x] 3.2 Implement inject_field_registry helper
    - Resolve field from registry using field_info
    - Special case: return registry itself when field type is Registry
    - Support operator-based resolution for Annotated types (defer operators to Item 12)
    - Use registry.get() for normal dependencies
    - Fall back to parent registry on LookupError
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 81-110
  - [x] 3.3 Implement inject_field_no_registry helper
    - Handle dependencies not in registry (functions, NamedTuples, dataclasses)
    - Create temporary Registration for unregistered dependency
    - Recursively call inject_callable to construct
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 58-78
  - [x] 3.4 Implement inject_callable function
    - Iterate through registration.field_infos to resolve each field
    - Three-tier precedence: props (highest), registry lookup, defaults (lowest)
    - Check for __hopscotch_factory__ method and use if present
    - Use inject_field_registry for registry lookups
    - Use inject_field_no_registry for non-registered dependencies
    - Validate all fields resolved or have defaults
    - Raise ValueError with descriptive message if field missing
    - Construct target with resolved kwargs
    - Reuse pattern from: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 113-164
  - [x] 3.5 Implement get method for resolution and construction
    - Use get_best_match to locate appropriate registration
    - If no match, recursively check parent registry
    - Raise LookupError with descriptive message when no match
    - Return singleton instances directly without construction
    - Construct class registrations using inject_callable
    - Support props/kwargs with highest precedence via allow_singletons=False
  - [x] 3.6 Ensure injection tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify three-tier field resolution works
    - Verify custom __hopscotch_factory__ construction
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- inject_callable implements three-tier field precedence
- inject_field_registry resolves from registry with parent fallback
- inject_field_no_registry handles unregistered dependencies
- get method combines resolution and construction correctly
- Singletons returned directly, classes constructed
- Props/kwargs override registry and default values

**Implementation Notes:**
- Defer operator support to Item 12
- Support __hopscotch_factory__ custom construction like __svcs__
- Follow Hopscotch's recursive injection pattern
- Provide clear error messages for missing dependencies

**Key References:**
- Hopscotch Registry inject_callable: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` lines 113-164
- Hopscotch inject_field_registry: lines 81-110
- Hopscotch inject_field_no_registry: lines 58-78

### Injector Implementation

#### Task Group 4: HopscotchInjector and HopscotchAsyncInjector
**Dependencies:** Task Groups 1, 2, 3 (COMPLETED)

- [x] 4.0 Complete injector classes
  - [x] 4.1 Write 2-8 focused tests for HopscotchInjector (10 tests written in test_locator.py lines 234-462)
    - Test dataclass structure with container field
    - Test kwargs validation against field_infos
    - Test three-tier resolution: kwargs > container > defaults
    - Test Inject field resolution via container.get/get_abstract
    - Test async version with aget/aget_abstract
    - Test unknown parameter rejection
  - [x] 4.2 Implement HopscotchInjector (implemented as ServiceLocator in src/svcs_di/injectors/locator.py lines 135-252)
    - Dataclass with container field and context_key parameter for dynamic context resolution
    - Implement _validate_kwargs to reject unknown parameters
    - Implement _resolve_field_value_sync for three-tier resolution
    - Tier 1: kwargs (highest priority)
    - Tier 2: locator.get() for Inject fields (using context from container)
    - Tier 3: default values from field definitions
    - Implement __call__ to construct target with resolved dependencies
    - Use get_field_infos from svcs_di.auto for introspection
    - Follow pattern from: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/keyword.py` lines 22-113
  - [x] 4.3 Implement HopscotchAsyncInjector (implemented as ServiceLocatorAsync in src/svcs_di/injectors/locator.py lines 254-370)
    - Dataclass with container field and context_key parameter
    - Implement _validate_kwargs (same as sync version)
    - Implement _resolve_field_value_async using async locator methods
    - Use locator.aget() with dynamic context resolution
    - Implement async __call__ for async construction
    - Follow pattern from: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/keyword.py` lines 115-207
  - [x] 4.4 Ensure injector tests pass (22 tests total: 10 HopscotchInjector + 12 ServiceLocator = all passing)
    - Run ONLY the 2-8 tests written in 4.1
    - Verify three-tier precedence works in injectors
    - Verify kwargs validation rejects unknown parameters
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass ✅
- HopscotchInjector implements three-tier kwargs > container > defaults precedence ✅
- HopscotchAsyncInjector provides async version with aget methods ✅
- Kwargs validation ensures unknown parameters are rejected ✅
- Both injectors use get_field_infos for field introspection ✅
- Inject fields resolved via container.get/get_abstract ✅

**Implementation Notes:**
- Follow KeywordInjector pattern very closely ✅
- Support both protocols (get_abstract) and concrete types (get) ✅
- Provide clear error messages for validation failures ✅
- Return tuple[bool, value] from resolution methods like KeywordInjector ✅
- **IMPLEMENTED as ServiceLocator approach (simplified from original HopscotchRegistry design)**
- **Three-tier precedence: kwargs > locator/container > defaults**
- **Context obtained dynamically from container via context_key parameter**
- **Located in: src/svcs_di/injectors/locator.py lines 135-370**
- **Tests in: tests/test_locator.py lines 234-462**
- **10 HopscotchInjector tests + 12 ServiceLocator tests = 22 total tests passing**

### Example Implementation

#### Task Group 5: HopscotchLocator Protocol and Example
**Dependencies:** Task Groups 1, 2, 3, 4

- [ ] 5.0 Complete HopscotchLocator example
  - [ ] 5.1 Write 2-8 focused tests for HopscotchLocator
    - Test HopscotchLocator protocol definition
    - Test multiple implementations registration
    - Test resolution with different contexts
    - Test LIFO override behavior
    - Test three-tier precedence with HopscotchLocator
    - Test singleton vs class registrations
  - [ ] 5.2 Define HopscotchLocator protocol/class
    - New protocol that represents the service type being registered
    - This is what gets requested from container, not the injector
    - Multiple implementations can be registered with different contexts
    - Follows initial_spec.md pattern where HopscotchLocator is svc_type
    - Example protocol for demonstrating multiple registrations
  - [ ] 5.3 Create example implementations
    - DefaultLocator (no context, low precedence)
    - Context-specific implementations for demonstration
    - Show singleton and class registration patterns
  - [ ] 5.4 Create example usage in examples/ directory
    - Demonstrate registration of multiple implementations
    - Show resolution with different contexts
    - Demonstrate LIFO override behavior
    - Show three-tier precedence in action
  - [ ] 5.5 Ensure HopscotchLocator tests pass
    - Run ONLY the 2-8 tests written in 5.1
    - Verify protocol definition works correctly
    - Verify multiple registrations resolve properly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 5.1 pass
- HopscotchLocator protocol/class defined
- Multiple implementations can be registered
- Resolution selects appropriate implementation based on context
- Example demonstrates all key features
- LIFO override behavior visible in example

**Implementation Notes:**
- HopscotchLocator is the protocol being registered, not the injector
- Follows initial_spec.md example with Request, Context, Greeting pattern
- Defer advanced context examples to Item 10
- Keep examples simple and focused on core functionality

### Container Infrastructure

#### Task Group 6: Basic Container Setup Foundation
**Dependencies:** Task Groups 1, 2, 3, 4, 5

- [ ] 6.0 Complete container infrastructure
  - [ ] 6.1 Write 2-8 focused tests for container setup
    - Test registration collection at configuration time
    - Test storage in registry during setup/scan phase
    - Test metadata placeholder storage (context, location)
    - Test basic registration processing
    - Test parent registry support
  - [ ] 6.2 Implement basic setup infrastructure
    - Provide infrastructure for collecting registrations at configuration time
    - Store registrations in registry during setup/scan phase
    - Support metadata storage for context (used in basic matching)
    - Support metadata placeholders for location (not used yet, deferred to Item 7)
    - Foundation for future container-local registration (defer two-pass to Item 9)
  - [ ] 6.3 Implement parent registry support
    - Registry can have optional parent reference
    - Fallback to parent when no match in current registry
    - Recursive resolution through registry hierarchy
  - [ ] 6.4 Ensure container infrastructure tests pass
    - Run ONLY the 2-8 tests written in 6.1
    - Verify registrations collected at configuration time
    - Verify parent registry fallback works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 6.1 pass
- Registrations can be collected at configuration time
- Registry stores registrations with metadata
- Parent registry fallback works correctly
- Foundation ready for future Item 9 (container-local processing)
- Context metadata stored and used for basic three-tier matching
- Location metadata stored but NOT used yet (deferred to Item 7)

**Implementation Notes:**
- Keep implementation minimal - just foundation for future work
- Defer two-pass matching logic to Item 9
- Defer location-based resolution to Item 7
- Defer advanced context resolution to Item 6
- Store location metadata but don't process it yet

### Integration Testing

#### Task Group 7: End-to-End Integration Tests and Coverage Analysis
**Dependencies:** Task Groups 1-6

- [ ] 7.0 Review integration and fill critical gaps
  - [ ] 7.1 Review tests from Task Groups 1-6
    - Review the 2-8 tests written by Task 1.1 (data structures)
    - Review the 2-8 tests written by Task 2.1 (resolution algorithm)
    - Review the 2-8 tests written by Task 3.1 (injection)
    - Review the 2-8 tests written by Task 4.1 (injectors)
    - Review the 2-8 tests written by Task 5.1 (HopscotchLocator)
    - Review the 2-8 tests written by Task 6.1 (container infrastructure)
    - Total existing tests: approximately 12-48 tests
  - [ ] 7.2 Analyze integration test coverage gaps
    - Identify critical end-to-end workflows lacking coverage
    - Focus ONLY on gaps for Multiple Service Registrations feature
    - Do NOT assess entire application test coverage
    - Prioritize workflows crossing multiple task groups
  - [ ] 7.3 Write up to 10 additional integration tests maximum
    - Add maximum of 10 new tests to fill identified critical gaps
    - Focus on end-to-end workflows:
      * Register multiple implementations → resolve → construct → use
      * Context-based resolution with three-tier precedence
      * LIFO override behavior in realistic scenarios
      * Parent registry fallback in multi-level hierarchies
      * Singleton vs class registration paths
      * Error cases (no match, missing dependencies)
    - Do NOT write comprehensive coverage for all scenarios
    - Skip edge cases unless business-critical
  - [ ] 7.4 Run feature-specific tests only
    - Run ONLY tests related to Multiple Service Registrations
    - Expected total: approximately 22-58 tests maximum
    - Do NOT run the entire application test suite
    - Verify critical workflows pass

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 22-58 tests total)
- Critical end-to-end workflows for Multiple Service Registrations covered
- No more than 10 additional tests added when filling gaps
- Testing focused exclusively on this feature's requirements
- LIFO behavior verified in integration scenarios
- Three-tier precedence verified across registration types
- Parent registry fallback verified in multi-level scenarios

**Implementation Notes:**
- Focus on integration points between task groups
- Test realistic usage patterns, not every permutation
- Verify examples/ code works as documented
- Defer performance and load testing
- Defer accessibility and security testing unless critical

### Quality and Documentation

#### Task Group 8: Type Checking, Linting, and Examples Documentation
**Dependencies:** Task Groups 1-7

- [ ] 8.0 Complete quality checks and documentation
  - [ ] 8.1 Run type checking
    - Execute: `just mypy` or `mypy src/`
    - Execute: `just pyright` or `pyright`
    - Fix all type errors in new code
    - Ensure full type safety with modern Python 3.14+ hints
  - [ ] 8.2 Run linting and formatting
    - Execute: `just lint` or equivalent
    - Execute: `just format` or equivalent
    - Fix all linting violations
    - Ensure code follows project standards
  - [ ] 8.3 Verify examples run correctly
    - Execute example code in `examples/` directory
    - Verify examples match documented behavior
    - Ensure examples demonstrate key features:
      * Multiple registrations with different contexts
      * Three-tier precedence resolution
      * LIFO override behavior
      * Singleton vs class registrations
      * Parent registry fallback
  - [ ] 8.4 Run full test suite
    - Execute: `just test` or `pytest`
    - Verify NO regressions in existing functionality
    - All tests pass (both new and existing)
    - Coverage goals met (aim for 100% on new code)
  - [ ] 8.5 Update code comments and docstrings
    - Add docstrings to all public functions and classes
    - Document three-tier precedence algorithm clearly
    - Explain LIFO override behavior
    - Document metadata storage for future Items 6-7
    - Add type hints to all function signatures
  - [ ] 8.6 Review scope boundaries documentation
    - Document what IS implemented (basic three-tier precedence)
    - Document what is NOT yet implemented:
      * Advanced context resolution (Item 6)
      * Location-based resolution (Item 7)
      * Advanced scoring/weights (Item 8)
      * Two-pass matching (Item 9)
      * Operators (Item 12)
    - Add notes for future enhancement areas

**Acceptance Criteria:**
- All type checking passes (mypy, pyright)
- All linting passes with no violations
- Code formatted according to project standards
- Examples run without errors and demonstrate features
- Full test suite passes with no regressions
- Coverage on new code at or near 100%
- All public APIs documented with clear docstrings
- Scope boundaries clearly documented

**Implementation Notes:**
- Use `just` commands where available (just test, just lint, etc.)
- Follow existing project conventions for documentation
- Ensure examples are self-contained and runnable
- Document deferred features clearly to guide future work
- Make scope boundaries explicit in code comments

## Execution Order

Recommended implementation sequence:

1. **Core Data Structures (Task Group 1)** - Foundation
   - Registration dataclass, IsNoneType, KindGroups, storage structure
   - CRITICAL: Must be completed before any other work

2. **Resolution Algorithm (Task Group 2)** - Core Logic
   - get_best_match with three-tier precedence
   - register method with LIFO support
   - DEPENDS ON: Task Group 1

3. **Injection and Construction (Task Group 3)** - Construction Pattern
   - inject_callable, field helpers, get method
   - DEPENDS ON: Task Groups 1, 2

4. **Injector Implementation (Task Group 4)** - Sync/Async Injectors
   - HopscotchInjector, HopscotchAsyncInjector
   - DEPENDS ON: Task Groups 1, 2, 3

5. **Example Implementation (Task Group 5)** - HopscotchLocator
   - Protocol definition, implementations, examples
   - DEPENDS ON: Task Groups 1, 2, 3, 4

6. **Container Infrastructure (Task Group 6)** - Setup Foundation
   - Basic infrastructure, parent registry support
   - DEPENDS ON: Task Groups 1, 2, 3, 4, 5

7. **Integration Testing (Task Group 7)** - Verify End-to-End
   - Integration tests, coverage analysis
   - DEPENDS ON: Task Groups 1-6

8. **Quality and Documentation (Task Group 8)** - Polish
   - Type checking, linting, documentation
   - DEPENDS ON: Task Groups 1-7

## Implementation Strategy

**Test-Driven Approach:**
- Each task group starts with writing 2-8 focused tests (x.1 sub-task)
- Development follows to make those tests pass
- Each task group ends with running ONLY its tests (final sub-task)
- Integration testing (Task Group 7) fills critical gaps with max 10 additional tests
- Full test suite run only in final quality check (Task Group 8)

**Reference Patterns:**
- KeywordInjector: `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/injectors/keyword.py`
- Hopscotch Registry: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py`
- Initial Spec: `/Users/pauleveritt/projects/pauleveritt/svcs-di/docs/initial_spec.md`

**Key Constraints:**
- Python 3.14+ type hints required
- Must work with free-threaded Python (PEP 703)
- Follow svcs non-magical, explicit approach
- Keep auto.py unchanged to avoid coupling
- Defer advanced features to future roadmap items (6, 7, 8, 9, 10, 11, 12)

## Success Criteria

Feature is complete when:
- All 8 task groups completed
- Approximately 22-58 tests pass (12-48 from development + up to 10 from integration)
- Full test suite passes with no regressions
- Type checking passes (mypy, pyright)
- Linting passes with no violations
- Examples run and demonstrate key features
- Documentation clearly explains three-tier precedence
- Scope boundaries documented (what's deferred to Items 6-12)
- Coverage at or near 100% on new code
