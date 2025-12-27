# Specification: Free-Threaded Python Compatibility

## Goal
Verify and formally test that the existing svcs-di codebase works correctly with PEP 703's free-threaded Python (no-GIL mode) through comprehensive concurrent access stress tests and CI/CD integration.

## User Stories
- As a library maintainer, I want to verify thread-safety of all components so that users can confidently use svcs-di in free-threaded Python environments
- As a developer, I want CI/CD to catch thread-safety regressions automatically so that free-threading compatibility is maintained across releases

## Specific Requirements

**Concurrent Access Testing Framework**
- Add pytest-freethreaded to dev dependencies (version >=0.1.0)
- Create dedicated test module at tests/test_free_threading.py for all free-threading verification tests
- Use threading.Thread to spawn multiple concurrent threads in stress tests
- Configure tests with appropriate timeout values to catch deadlocks (leverage existing 60s pytest timeout)
- Test both synchronous and asynchronous code paths under concurrent access
- Run free-threading tests with pytest -p freethreaded -p no:doctest --threads=8 --iterations=10
- Create utility to verify free-threaded build: sysconfig.get_config_var("Py_GIL_DISABLED")

**ServiceLocator Thread-Safety Verification**
- Test concurrent cache access from multiple threads reading and writing simultaneously
- Verify the "worst case: multiple threads compute same result (idempotent)" behavior is acceptable
- Test concurrent ServiceLocator.get_implementation() calls with same and different service types
- Verify frozen dataclass immutability guarantees under concurrent access
- Test concurrent registration operations creating new immutable ServiceLocator instances
- Verify dict operations remain thread-safe for cache get/set operations

**HopscotchInjector Concurrent Resolution Testing**
- Test concurrent service resolution with multiple threads calling HopscotchInjector.__call__() simultaneously
- Verify resource resolution (_get_resource) works correctly under concurrent container access
- Verify location resolution (_get_location) works correctly under concurrent container access
- Test nested injection scenarios where injector recursively constructs dependencies concurrently
- Verify field value resolution (_resolve_field_value_sync) handles concurrent cache and container access

**HopscotchAsyncInjector Concurrent Resolution Testing**
- Test concurrent async service resolution with asyncio.gather spawning multiple concurrent injector calls
- Verify async resource resolution works correctly under concurrent container.aget() access
- Verify async location resolution works correctly under concurrent container.aget() access
- Test nested async injection with concurrent dependency construction
- Verify async field value resolution (_resolve_field_value_async) handles concurrent access correctly

**Decorator and Scanning Thread-Safety**
- Test concurrent @injectable decorator application during module import
- Test concurrent scan() operations on same and different packages
- Verify _register_decorated_items handles concurrent locator mutations safely
- Test concurrent _get_or_create_locator calls accessing registry
- Verify metadata storage (__injectable_metadata__) is thread-safe during concurrent decorator application

**Immutability Verification Tests**
- Verify PurePath immutability guarantees (operations return new instances, original unchanged)
- Verify frozen dataclass fields cannot be mutated after construction
- Test that ServiceLocator registration returns new instances rather than mutating existing
- Verify FrozenDict prevents mutation after construction
- Confirm no global state exists that could be mutated across threads

**CI/CD Integration**
- Create new justfile recipe test-freethreaded that runs: pytest -p freethreaded -p no:doctest --threads=8 --iterations=10 --require-gil-disabled tests
- Create ci-checks-ft recipe that runs: just ci-checks && just test-freethreaded
- Update existing CI workflow to use python3.14t free-threaded build
- Configure pytest to run free-threading tests with -p freethreaded flag (opposite of current -p no:freethreaded)
- Ensure CI catches deadlocks using existing timeout configuration (60s pytest, 120s faulthandler)
- Add separate test marker "freethreaded" for tests that specifically verify free-threading behavior

**Test Organization and Markers**
- Create tests/test_free_threading.py as the main test module for all concurrent access tests
- Use pytest marker @pytest.mark.freethreaded for all free-threading specific tests
- Keep free-threading tests separate from existing functional tests to allow selective execution
- Document that free-threading tests may be slower due to concurrent execution patterns

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**ServiceLocator thread-safety design (src/svcs_di/injectors/locator.py)**
- Frozen dataclass with immutable data structures (lines 243-285)
- Cache mutation pattern using dict get/set (lines 373-460)
- Immutable registration pattern returning new ServiceLocator instances (lines 287-340)
- PurePath immutability for Location type (lines 164-188)
- Existing thread-safety documentation and design patterns to verify

**Test infrastructure patterns (tests/injectors/test_locator.py)**
- Existing test fixtures for registry, container, and service types (lines 308-311)
- Patterns for testing ServiceLocator with multiple registrations (lines 172-239)
- Patterns for testing HopscotchInjector with Injectable fields (lines 337-512)
- Async test patterns with @pytest.mark.anyio (lines 514-556)
- Cache behavior verification test patterns (lines 563-683)

**pytest configuration (pyproject.toml and conftest.py)**
- Existing pytest timeout configuration (timeout = 60, faulthandler_timeout = 120)
- Pytest markers configuration pattern for test categorization
- Current -p no:freethreaded flag that needs to be toggled for free-threading tests
- Sybil doctest integration pattern for testing code examples

**CI/CD infrastructure (.github/workflows/ci.yml)**
- Existing GitHub Actions workflow running on ubuntu-latest
- Setup for python3.14t free-threaded build (lines 14-15)
- Just command integration pattern (line 22: just ci-checks-ft)
- 30-minute timeout for full CI suite

**Async testing patterns (tests/test_injector.py)**
- Patterns for testing async factories with asyncio.sleep for timing
- Patterns for testing mixed sync/async dependencies
- Container async context manager usage with async with svcs.Container()
- Injectable[T] async resolution patterns

**Free-threading patterns from tdom-path reference project**
- Free-threaded build detection: sysconfig.get_config_var("Py_GIL_DISABLED")
- pytest-freethreaded plugin configuration with --threads=8 --iterations=10 --require-gil-disabled
- Justfile recipe pattern: test-freethreaded and ci-checks-ft
- pyproject.toml: pytest.ini_options with -p no:freethreaded as default (enable explicitly for free-threading tests)
- CI/CD: GitHub Actions with python3.14t free-threaded build and 30-minute timeout
- Timeout configuration for deadlock detection: timeout = 60, faulthandler_timeout = 120

## Out of Scope
- Documentation of thread-safety guarantees in API docs or user guides
- Specific guidance on when locks are needed in user code
- Performance optimization for multi-threaded workloads (verification only, not optimization)
- Support for exotic thread-local state patterns
- Major architectural changes to enable free-threading (existing design should work)
- Testing with thread-local storage patterns
- Benchmarking or performance comparison between GIL and no-GIL modes
- Testing with non-CPython implementations (PyPy, Jython, etc)
- Adding thread-safety primitives like locks or mutexes (existing design relies on immutability)
- Refactoring existing code for better thread-safety (only verify current design works)
