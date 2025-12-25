# Specification: Custom Construction with `__svcs__`

## Goal

Enable classes to define a `__svcs__` classmethod for custom construction with container access, providing an escape
hatch for complex initialization logic that cannot be expressed through simple Injectable field resolution.

## User Stories

- As a developer, I want to define complex initialization logic in a `__svcs__` method so that I can perform
  manual validation or conditional service resolution
- As a library user, I want `__svcs__` to replace automatic field injection so that I have complete control over
  construction when needed

## Specific Requirements

**Detection of `__svcs__` Method**

- Use `getattr(target, "__svcs__", None)` to detect the presence of the method
- Detection happens in the `auto()` factory function during service resolution
- If `__svcs__` is not found, proceed with normal Injectable field injection
- Method must be a classmethod with signature
  `@classmethod def __svcs__(cls, container: svcs.Container, **kwargs) -> Self`

**Complete Replacement of Field Injection**

- When `__svcs__` exists, skip all automatic Injectable field resolution entirely
- Do not process dataclass fields or callable parameters for injection
- The `__svcs__` method is solely responsible for constructing and returning the instance
- This provides a clean escape hatch when automatic injection is insufficient

**Container Access Within `__svcs__`**

- Pass the svcs.Container instance as the first argument after cls
- Allow the method to call `container.get()` or `container.aget_abstract()` for dynamic service resolution
- Container provides access to all registered services during construction
- Enable conditional construction based on what services are available in the container

**Kwargs Support for Overrides**

- Accept **kwargs in `__svcs__` signature to maintain consistency with normal factory interface
- Forward kwargs from the factory call to the `__svcs__` method
- Allow callers to override specific values during construction
- Maintain the same three-tier precedence: kwargs override container lookups which override defaults

**Return Contract**

- Method must return a fully constructed instance of the class (Self type)
- Instance should be ready for immediate use without additional initialization
- Type hints should properly reflect the return type using typing.Self (Python 3.11+)

**Integration with auto() System**

- Modify the factory function created by `auto()` to detect and invoke `__svcs__`
- Detection occurs before attempting field injection
- If `__svcs__` found: invoke it and return the result immediately
- If `__svcs__` not found: proceed with existing DefaultInjector logic

**Error Handling**

- If `__svcs__` exists but is not a classmethod, raise TypeError with clear message
- If `__svcs__` exists but has wrong signature, raise TypeError with expected signature
- If `__svcs__` raises an exception during construction, propagate it with context
- If container.get() fails within `__svcs__`, propagate ServiceNotFoundError normally

**Type Safety**

- Use typing.Self for return type annotation (requires Python 3.11+)
- Ensure type checkers understand the factory returns the correct type
- Maintain compatibility with existing type hints in the codebase

## Visual Design

No visual assets provided for this feature.

## Existing Code to Leverage

**Hopscotch `__hopscotch_factory__` Pattern**

- Detection pattern: `factory = getattr(target, "__hopscotch_factory__", None)`
- Conditional invocation: only call factory if both factory and registry exist
- Factory receives full registry/container for maximum flexibility
- Factory completely bypasses normal field injection when present
- Located in `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` (lines 122-128)

**Existing `auto()` Factory Function**

- Located in `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (lines 338-358)
- Returns factory function that creates injector and delegates to it
- Accepts **kwargs and forwards them through injection process
- Integration point: add `__svcs__` detection before calling injector
- Maintain backward compatibility with existing behavior

**DefaultInjector Implementation**

- Located in `/Users/pauleveritt/projects/pauleveritt/svcs-di/src/svcs_di/auto.py` (lines 79-94)
- Processes field_infos to resolve Injectable dependencies
- Validates kwargs against actual field names
- This logic should be skipped entirely when `__svcs__` is present

**Field Info Resolution System**

- Function `get_field_infos()` extracts dataclass fields and callable parameters
- Used by injectors to determine what needs injection
- When `__svcs__` exists, skip calling this function to avoid unnecessary processing

**Existing Test Patterns**

- Tests in `/Users/pauleveritt/projects/pauleveritt/svcs-di/tests/test_auto.py` show registration and retrieval patterns
- Example files in `/Users/pauleveritt/projects/pauleveritt/svcs-di/examples/` demonstrate usage patterns
- Follow existing test structure for new `__svcs__` tests

## Out of Scope

- Asynchronous `async def __svcs__` support (future enhancement, not in v1)
- Partial injection where Injectable fields are auto-injected before calling `__svcs__`
- Helper decorators or utilities for common `__svcs__` patterns
- Framework-specific integrations or adapters
- Complex real-world examples beyond simple demonstration
- Automatic parameter inspection of `__svcs__` to inject its dependencies
- Support for instance methods or static methods (only classmethod)
- Mixing `__svcs__` with automatic field injection in the same class
- Validation that `__svcs__` signature matches expected pattern at registration time
- Caching or memoization of `__svcs__` detection results
