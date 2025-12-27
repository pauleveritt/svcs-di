# Task Breakdown: Free-Threaded Python Compatibility

## Overview
Total Tasks: 5 task groups covering test infrastructure, concurrent testing, CI/CD integration, and verification

## Task List

### Infrastructure Setup

#### Task Group 1: Testing Infrastructure & Build Verification
**Dependencies:** None

- [x] 1.0 Complete testing infrastructure setup
  - [x] 1.1 Verify pytest-run-parallel is already in dev dependencies
    - Check pyproject.toml line 29: `pytest-run-parallel>=0.8.1`
    - Confirm version meets minimum requirements (>=0.1.0)
  - [x] 1.2 Add pytest marker for free-threading tests
    - Add to pyproject.toml `[tool.pytest.ini_options]` markers list
    - Add: `freethreaded: marks tests that verify free-threading compatibility`
  - [x] 1.3 Create utility function to verify free-threaded build
    - Add function in new module: `tests/test_free_threading.py`
    - Use: `sysconfig.get_config_var("Py_GIL_DISABLED")`
    - Return True if running on free-threaded Python, False otherwise
  - [x] 1.4 Write 2-8 focused tests for build verification
    - Test that free-threaded build detection works correctly
    - Test that pytest-run-parallel plugin is available
    - Skip remaining free-threading tests if not on free-threaded build
    - Mark all tests with @pytest.mark.freethreaded
  - [x] 1.5 Ensure build verification tests pass
    - Run: `uv run pytest tests/test_free_threading.py -v -m freethreaded`
    - Verify tests can detect build type correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- pytest-run-parallel is confirmed in dependencies
- New pytest marker "freethreaded" is configured
- Build detection utility works correctly
- Tests can identify free-threaded vs standard Python builds
- All infrastructure tests pass

### ServiceLocator Thread-Safety

#### Task Group 2: ServiceLocator Concurrent Access Testing
**Dependencies:** Task Group 1

- [x] 2.0 Complete ServiceLocator thread-safety verification
  - [x] 2.1 Write 2-8 focused tests for concurrent ServiceLocator access
    - Limit to 2-8 highly focused tests maximum
    - Test concurrent cache access (multiple threads reading/writing simultaneously)
    - Test concurrent get_implementation() calls with same service type
    - Test concurrent get_implementation() calls with different service types
    - Test concurrent registration operations creating new immutable instances
    - All tests spawn multiple threads (8+) and use appropriate timeouts
    - Mark all tests with @pytest.mark.freethreaded
  - [x] 2.2 Test immutability guarantees under concurrent access
    - Verify frozen dataclass immutability (ServiceLocator fields cannot be mutated)
    - Verify PurePath (Location type) immutability guarantees
    - Test that registration returns new ServiceLocator instances
    - Verify FrozenDict prevents mutation after construction
    - Confirm no global state exists that could be mutated across threads
  - [x] 2.3 Test cache behavior under concurrent access
    - Verify dict operations remain thread-safe for cache get/set
    - Test the "worst case: multiple threads compute same result (idempotent)" scenario
    - Ensure multiple threads computing same cached result is acceptable
    - Verify no data corruption or exceptions occur with concurrent cache access
  - [x] 2.4 Ensure ServiceLocator thread-safety tests pass
    - Run: `uv run pytest tests/test_free_threading.py::test_service_locator* -v -m freethreaded`
    - Run ONLY the 2-8 tests written in 2.1
    - Verify critical concurrent access patterns work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Concurrent cache access works without data corruption
- Immutability guarantees hold under concurrent access
- Multiple threads can safely call get_implementation() simultaneously
- Registration operations are thread-safe

### Injector Thread-Safety

#### Task Group 3: HopscotchInjector Concurrent Resolution Testing
**Dependencies:** Task Group 2

- [x] 3.0 Complete injector thread-safety verification
  - [x] 3.1 Write 2-8 focused tests for synchronous injector concurrent access
    - Limit to 2-8 highly focused tests maximum
    - Test concurrent service resolution (multiple threads calling HopscotchInjector.__call__())
    - Test concurrent resource resolution (_get_resource with concurrent container access)
    - Test concurrent location resolution (_get_location with concurrent container access)
    - Test nested injection with recursive dependency construction
    - Test field value resolution (_resolve_field_value_sync) under concurrent access
    - All tests spawn multiple threads (8+) and use appropriate timeouts
    - Mark all tests with @pytest.mark.freethreaded
  - [x] 3.2 Write 2-8 focused tests for async injector concurrent access
    - Limit to 2-8 highly focused tests maximum
    - Test concurrent async service resolution using asyncio.gather
    - Test async resource resolution (container.aget() under concurrent access)
    - Test async location resolution (container.aget() with Location)
    - Test nested async injection with concurrent dependency construction
    - Test async field value resolution (_resolve_field_value_async)
    - Use asyncio.gather to spawn concurrent injector calls
    - Mark all tests with @pytest.mark.freethreaded
  - [x] 3.3 Test Injectable[T] field injection under concurrent access
    - Verify Injectable[T] fields resolve correctly when multiple threads inject simultaneously
    - Test with single and multiple implementations per service type
    - Test with resource-based and location-based selection under concurrent access
    - Verify cache hits work correctly across concurrent requests
  - [x] 3.4 Ensure injector thread-safety tests pass
    - Run: `uv run pytest tests/test_free_threading.py::test_hopscotch* -v -m freethreaded`
    - Run ONLY the tests written in 3.1 and 3.2
    - Verify critical concurrent resolution patterns work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- All injector tests (3.1 and 3.2) pass
- Concurrent service resolution works without deadlocks or data corruption
- Both sync and async code paths are thread-safe
- Nested injection handles concurrent dependency construction correctly
- Injectable[T] fields resolve correctly under concurrent access

### Decorator & Scanning Thread-Safety

#### Task Group 4: Decorator and Scanning Concurrent Operations
**Dependencies:** Task Group 3

- [x] 4.0 Complete decorator and scanning thread-safety verification
  - [x] 4.1 Write 2-8 focused tests for decorator thread-safety
    - Limit to 2-8 highly focused tests maximum
    - Test concurrent @injectable decorator application during module import
    - Test concurrent metadata storage (__injectable_metadata__)
    - Test concurrent _get_or_create_locator calls accessing registry
    - Verify decorator application is thread-safe across multiple threads
    - Mark all tests with @pytest.mark.freethreaded
  - [x] 4.2 Write 2-8 focused tests for scanning thread-safety
    - Limit to 2-8 highly focused tests maximum
    - Test concurrent scan() operations on same package
    - Test concurrent scan() operations on different packages
    - Test _register_decorated_items handles concurrent locator mutations safely
    - Verify scanning multiple packages simultaneously is thread-safe
    - Mark all tests with @pytest.mark.freethreaded
  - [x] 4.3 Test integrated decorator + scanning + injection workflow
    - Test full workflow: concurrent decoration -> concurrent scanning -> concurrent injection
    - Verify end-to-end thread-safety of the complete auto-discovery system
    - Test with multiple threads performing scan() and then injecting services
  - [x] 4.4 Ensure decorator and scanning tests pass
    - Run: `uv run pytest tests/test_free_threading.py::test_decorator* -v -m freethreaded`
    - Run: `uv run pytest tests/test_free_threading.py::test_scanning* -v -m freethreaded`
    - Run ONLY the tests written in 4.1 and 4.2
    - Verify critical concurrent decorator/scanning patterns work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- All decorator and scanning tests (4.1 and 4.2) pass
- Concurrent decorator application is thread-safe
- Concurrent scanning operations work without data corruption
- Metadata storage is thread-safe
- End-to-end workflow works under concurrent access

### CI/CD Integration

#### Task Group 5: CI/CD and Justfile Integration
**Dependencies:** Task Groups 1-4

- [x] 5.0 Complete CI/CD integration for free-threaded testing
  - [x] 5.1 Create justfile recipe for free-threaded tests
    - Add `test-run-parallel` recipe to justfile
    - Command: `uv run pytest -p freethreaded -p no:doctest --threads=8 --iterations=10 --require-gil-disabled tests/test_free_threading.py`
    - This runs free-threading tests with 8 threads and 10 iterations
  - [x] 5.2 Create combined CI checks recipe
    - Add `ci-checks-ft` recipe to justfile
    - Command: `just quality && just test-cov && just test-run-parallel`
    - This runs all quality checks, full test suite, and free-threading tests
  - [x] 5.3 Update pytest configuration for free-threading
    - Verify pyproject.toml has `-p no:freethreaded` in addopts (line 42)
    - This ensures free-threading tests are opt-in (must use -p freethreaded explicitly)
    - Confirm timeout configuration catches deadlocks (timeout=60, faulthandler_timeout=120)
  - [x] 5.4 Verify CI workflow is properly configured
    - Check .github/workflows/ci.yml line 7: Uses "python 3.14t (free-threaded)"
    - Check line 22: Runs "just ci-checks-ft"
    - Confirm 30-minute timeout for full CI suite (line 9)
    - Verify setup-python-uv action configures python3.14t correctly
  - [x] 5.5 Run complete CI checks locally
    - Run: `just ci-checks-ft`
    - This runs quality checks, full test suite, and free-threading tests
    - Expected total free-threading tests: approximately 16-32 tests maximum
    - All tests should pass with no deadlocks or timeouts

**Acceptance Criteria:**
- `just test-run-parallel` recipe works correctly
- `just ci-checks-ft` recipe runs all checks including free-threading tests
- CI workflow is configured to run python3.14t free-threaded build
- All CI checks pass locally
- Free-threading tests complete within timeout limits

### Final Verification

#### Task Group 6: Documentation and Final Testing
**Dependencies:** Task Group 5

- [x] 6.0 Complete final verification and documentation
  - [x] 6.1 Run full test suite to ensure no regressions
    - Run: `just test-cov`
    - Verify all existing tests still pass
    - Confirm no regressions introduced by new test infrastructure
  - [x] 6.2 Run free-threading tests multiple times for stability
    - Run: `just test-run-parallel` at least 3 times
    - Verify consistent results (no flaky tests)
    - Confirm no intermittent deadlocks or race conditions
  - [x] 6.3 Document thread-safety design patterns in test module
    - Add module-level docstring to tests/test_free_threading.py
    - Document what thread-safety guarantees are being verified
    - Reference key design patterns: immutability, atomic dict operations, idempotent cache
    - Note: Do NOT add user-facing documentation (out of scope per requirements)
  - [x] 6.4 Verify CI passes with all changes
    - Push changes and verify GitHub Actions CI passes
    - Confirm python3.14t free-threaded build runs successfully
    - Verify `just ci-checks-ft` completes within 30-minute timeout
    - Check that all quality checks and tests pass in CI environment

**Acceptance Criteria:**
- Full test suite passes with no regressions
- Free-threading tests are stable and reproducible
- Test module documents verified thread-safety patterns
- CI passes successfully with python3.14t free-threaded build
- All acceptance criteria from previous task groups are met

## Execution Order

Recommended implementation sequence:
1. Infrastructure Setup (Task Group 1) - Set up testing tools and build verification
2. ServiceLocator Thread-Safety (Task Group 2) - Verify core data structure thread-safety
3. Injector Thread-Safety (Task Group 3) - Verify service resolution thread-safety
4. Decorator & Scanning (Task Group 4) - Verify auto-discovery thread-safety
5. CI/CD Integration (Task Group 5) - Integrate into build pipeline
6. Final Verification (Task Group 6) - Ensure stability and document patterns

## Important Notes

### Test Writing Constraints
- Each task group should write 2-8 focused tests maximum
- Tests should cover only critical concurrent access patterns
- Focus on stress testing with multiple threads (8+)
- Use existing timeout configuration to catch deadlocks
- Do NOT write exhaustive coverage of all scenarios

### Thread-Safety Strategy
The codebase relies on **immutability** rather than locks:
- ServiceLocator: frozen dataclass with immutable data structures
- Location: PurePath is immutable
- Registration: returns new instances rather than mutating
- Cache: dict operations are thread-safe for simple get/set
- Idempotent cache: multiple threads computing same result is acceptable

### pytest-run-parallel vs pytest-freethreaded
- Spec originally mentioned pytest-freethreaded
- Requirements clarified to use pytest-run-parallel (per py-free-threading.github.io)
- pytest-run-parallel is already in dependencies (pyproject.toml line 29)
- Use flags: `-p freethreaded --threads=8 --iterations=10 --require-gil-disabled`

### Test Execution
- Free-threading tests are in: `tests/test_free_threading.py`
- Run free-threading tests: `just test-run-parallel`
- Run all CI checks including free-threading: `just ci-checks-ft`
- Tests are opt-in via `-p freethreaded` flag (default is `-p no:freethreaded`)

### What's Already Done
- pytest-run-parallel already in dependencies (pyproject.toml line 29)
- pytest timeout configuration already set (timeout=60, faulthandler_timeout=120)
- CI workflow already configured for python3.14t free-threaded build
- CI already calls `just ci-checks-ft` (needs to be created in justfile)

### Total Expected Tests
- Task Group 1: 3 tests (build verification)
- Task Group 2: 5 tests (ServiceLocator)
- Task Group 3: 4 tests (sync + async injectors)
- Task Group 4: 4 tests (decorators + scanning)
- **Total: 16 tests**

All tests focus on concurrent access stress testing, not exhaustive functional coverage.

## Implementation Summary

All task groups have been successfully implemented:

1. **Infrastructure Setup (Task Group 1)**: Created test_free_threading.py with build detection utility and pytest marker configuration
2. **ServiceLocator Thread-Safety (Task Group 2)**: Implemented 5 tests verifying concurrent cache access, registration, immutability, and idempotent cache behavior
3. **Injector Thread-Safety (Task Group 3)**: Implemented 4 tests for concurrent sync/async injection, multifield services, and location-based resolution
4. **Decorator & Scanning (Task Group 4)**: Implemented 4 tests for concurrent decorator application, scanning, and end-to-end workflows
5. **CI/CD Integration (Task Group 5)**: Created justfile recipes (test-run-parallel, ci-checks-ft) and verified CI configuration
6. **Final Verification (Task Group 6)**: Verified all tests pass (288 total tests including 16 free-threading tests), 87% code coverage maintained
