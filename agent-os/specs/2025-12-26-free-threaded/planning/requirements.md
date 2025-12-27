# Spec Requirements: Free-Threaded Python Compatibility

## Initial Description
Free threaded

## Requirements Discussion

### First Round Questions

**Q1:** I assume the primary goal is to **verify and formally test** that the existing code works with PEP 703's free-threaded Python (no-GIL mode), rather than making major architectural changes. Is that correct, or do you anticipate discovering issues that need fixing?
**Answer:** Yes - Verify and formally test that existing code works with PEP 703's free-threaded Python (no-GIL mode)

**Q2:** I'm thinking we should add **pytest-run-parallel** to the dev dependencies (as mentioned in tech-stack.md) and create a dedicated test suite that runs with `python3.13t` (free-threaded build). Should we also add CI/CD testing with free-threaded Python builds to catch regressions?
**Answer:** Use pytest-run-parallel as recommended in the free threaded guide https://py-free-threading.github.io (not pytest-freethreaded)

**Q3:** For the existing code that already mentions thread-safety (like ServiceLocator's cache), should we add **concurrent access stress tests** that spawn multiple threads to verify these claims, or just document the existing design patterns?
**Answer:** Yes - Add concurrent access stress tests that spawn multiple threads

**Q4:** I assume we need to document thread-safety guarantees in both **API documentation** (docstrings) and **user-facing guides** (docs/guides/). Should this include specific guidance on when locks might be needed in user code (like factory functions)?
**Answer:** No

**Q5:** The locator.py file mentions that dict operations and cache mutations are thread-safe with the caveat "worst case: multiple threads compute same result (idempotent)". Should we verify this behavior is acceptable under free-threading, or should we consider adding explicit locks for cache updates?
**Answer:** Verify - Verify the cache behavior is acceptable under free-threading

**Q6:** Should we test both **synchronous and asynchronous** code paths under free-threading (HopscotchInjector and HopscotchAsyncInjector), since async code might have different threading implications?
**Answer:** Yes - Test both synchronous and asynchronous code paths

**Q7:** I'm assuming we should focus on the **core injectors and locator** as the primary thread-safety surface area. Should we also audit and test any scanning/decorator code for thread-safety?
**Answer:** Yes all - Audit and test all code including scanning/decorator code for thread-safety

**Q8:** What should we explicitly **exclude from this work**? For example: performance optimization for multi-threaded workloads, or supporting exotic thread-local state patterns?
**Answer:** No

### Existing Code to Reference

No similar existing features identified for reference.

### Follow-up Questions

None needed - all questions were answered with sufficient clarity.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
Not applicable - this is a technical testing and verification feature without UI components.

## Requirements Summary

### Functional Requirements

#### Core Testing Infrastructure
- Add **pytest-run-parallel** to dev dependencies (NOT pytest-freethreaded)
- Follow guidance from https://py-free-threading.github.io for test configuration
- Create dedicated test suite for free-threaded Python verification
- Set up testing with free-threaded Python builds (python3.13t or later)
- Add CI/CD testing with free-threaded Python builds to catch regressions

#### Concurrent Access Stress Tests
- Create **multi-threaded stress tests** that spawn multiple threads
- Test **ServiceLocator cache** with concurrent access from multiple threads
- Test **HopscotchInjector** with concurrent service resolution
- Test **HopscotchAsyncInjector** with concurrent async service resolution
- Test **scanning/decorator code** with concurrent access patterns

#### Thread-Safety Verification Areas
- **ServiceLocator**: Verify immutable data structures and cache thread-safety
- **HopscotchInjector**: Test synchronous injection under concurrent access
- **HopscotchAsyncInjector**: Test asynchronous injection under concurrent access
- **Registration system**: Test concurrent registration operations
- **Decorator system** (`@injectable`): Test concurrent decorator application
- **Scanning system**: Test concurrent scanning operations
- **Cache behavior**: Verify the "worst case: multiple threads compute same result (idempotent)" behavior is acceptable

#### Existing Thread-Safety Claims to Verify
From `src/svcs_di/injectors/locator.py`:
- PurePath is immutable and thread-safe
- ServiceLocator is thread-safe with immutable data (frozen dataclass with dicts)
- Dict operations are thread-safe for simple get/set
- FrozenDict prevents mutation after construction
- Multiple threads computing same cached result is acceptable (idempotent)

### Reusability Opportunities

No existing similar features were identified. This is the first comprehensive thread-safety verification effort for the codebase.

### Scope Boundaries

**In Scope:**
- Verify existing code works with PEP 703 free-threaded Python
- Add pytest-run-parallel for concurrent testing
- Create concurrent access stress tests for all components
- Test synchronous code paths (HopscotchInjector)
- Test asynchronous code paths (HopscotchAsyncInjector)
- Test ServiceLocator cache behavior under concurrent access
- Test scanning and decorator code for thread-safety
- Verify PurePath immutability guarantees
- Verify frozen dataclass thread-safety guarantees
- Add CI/CD testing with free-threaded Python builds
- Document any issues discovered and their fixes

**Out of Scope:**
- Documentation of thread-safety guarantees (no API docs or user guides needed)
- Specific guidance on locks in user code
- Performance optimization for multi-threaded workloads (verification only, not optimization)
- Support for exotic thread-local state patterns
- Major architectural changes to enable free-threading (existing design should already work)

### Technical Considerations

#### Testing Framework
- Use **pytest-run-parallel** as recommended by py-free-threading.github.io
- Configure pytest to run tests under free-threaded Python (python3.13t+)
- Ensure timeout configuration (already at 60s) catches deadlocks under free-threading

#### Free-Threaded Python Version
- Minimum Python version already 3.14+ (per pyproject.toml)
- Free-threaded builds available as python3.13t and later
- Need to test with actual free-threaded interpreter builds

#### Thread-Safety Design Patterns Already Present
- **Immutability**: PurePath, frozen dataclasses
- **Atomic operations**: Dict get/set operations
- **Idempotent cache**: Multiple threads can compute same result safely

#### Areas Requiring Verification
- ServiceLocator._cache dict mutations under concurrent access
- Registration operations (locator.register()) creating new immutable instances
- Container.get() operations under concurrent access
- Factory function invocations under concurrent access
- Decorator application during import time vs runtime

#### Integration Points
- svcs.Container and svcs.Registry thread-safety (upstream dependency)
- Python's dict implementation thread-safety guarantees in free-threaded mode
- PurePath immutability guarantees across Python versions

#### CI/CD Requirements
- Add free-threaded Python to test matrix
- Ensure CI can install and run python3.13t or later
- Configure pytest to use pytest-run-parallel in CI environment
- Set up appropriate timeout values for concurrent tests
