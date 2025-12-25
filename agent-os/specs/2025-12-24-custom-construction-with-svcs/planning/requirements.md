# Spec Requirements: Custom Construction with `__svcs__`

## Initial Description
Custom Construction with `__svcs__`

This feature will allow custom construction patterns using a `__svcs__` protocol/method.

## Requirements Discussion

### First Round Questions

**Q1:** What exactly is `__svcs__`? Is it a special method that classes can define to control how they're constructed when retrieved from the container?
**Answer:** Correct - `__svcs__` is a special method classes can define to control construction with container access

**Q2:** Should `__svcs__` be a classmethod (like `@classmethod def __svcs__(cls, container: svcs.Container) -> Self`) or an instance method?
**Answer:** classmethod - Should be `@classmethod def __svcs__(cls, container: svcs.Container) -> Self`

**Q3:** How should `__svcs__` interact with the existing `Injectable[T]` field resolution? Should it replace it entirely, or complement it (e.g., auto-inject fields first, then call `__svcs__`)?
**Answer:** Replace - If `__svcs__` exists, it replaces normal `Injectable[T]` field resolution

**Q4:** What are the primary use cases you envision for `__svcs__`? For example:
   - Complex initialization logic that can't be expressed through simple field injection
   - Post-construction validation or setup
   - Conditional construction (different logic based on what's available in the container)
   - Dynamic service fetching based on runtime conditions

**Answer:** Sounds good - Use cases are complex initialization, post-construction validation, conditional construction, dynamic service fetching

**Q5:** Should `__svcs__` support both synchronous and asynchronous construction (`async def __svcs__`)?
**Answer:** Just sync - Only synchronous construction initially

**Q6:** If a class has both `Injectable[T]` fields AND a `__svcs__` method, which takes precedence? Should we:
   - Auto-inject Injectable fields first, then call `__svcs__` with the partially-constructed instance
   - Skip field injection entirely and let `__svcs__` handle everything

**Answer:** First but accept any kwargs thus following same interface - Auto-inject Injectable fields first, then call `__svcs__` accepting kwargs

**Q7:** Should `__svcs__` be able to receive kwargs for overrides (similar to how factories can receive props in Hopscotch)?
**Answer:** Yes - `__svcs__` should be able to receive kwargs for overrides

**Q8:** For documentation and examples, would you prefer:
   - Simple example scenarios showing the pattern
   - Complex real-world scenarios demonstrating advanced use cases
   - Both simple and complex examples

**Answer:** Something simple - Add simple example scenarios

**Q9:** Are there existing features in your codebase with similar patterns we should reference?
**Answer:** Hopscotch has examples of using `__hopscotch_factory__` - Similar pattern to reference

**Q10:** Is there anything we should explicitly exclude from this feature? For example:
   - Not supporting async construction in v1
   - Not providing helper decorators for common patterns
   - Not integrating with specific frameworks

**Answer:** no - No features to explicitly exclude

### Existing Code to Reference

**Similar Features Identified:**
- Feature: Hopscotch `__hopscotch_factory__` pattern
- Location: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/`
- Key files:
  - `registry.py`: Implementation of factory detection and invocation (lines 122-128)
  - `fixtures/dataklasses.py`: Example usage in `GreetingFactory` class (lines 87-98)

**Hopscotch Pattern Analysis:**

The `__hopscotch_factory__` implementation in Hopscotch provides a clear reference:

```python
# Detection in inject_callable (registry.py:122-128)
factory = getattr(target, "__hopscotch_factory__", None)

if factory is not None and registry is not None:
    result: T = factory(registry)
    return result
```

Key characteristics:
1. Factory is detected via `getattr` with None default
2. Factory is only invoked if both factory exists AND registry is provided
3. Factory receives the full registry as its argument
4. Factory completely bypasses normal field injection
5. Factory returns the fully constructed instance

Example usage pattern:
```python
@dataclass()
class GreetingFactory:
    """Use the ``__hopscotch_factory__`` protocol to control creation."""

    salutation: str

    @classmethod
    def __hopscotch_factory__(cls, registry: Registry) -> GreetingFactory:
        """Manually construct this instance, instead of injection."""
        return cls(salutation="Hi From Factory")
```

### Follow-up Questions
No follow-up questions were needed based on the comprehensive initial answers.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
No visual files found - this is a purely code-based feature.

## Requirements Summary

### Functional Requirements

**Core Functionality:**
- Classes can define a `__svcs__` classmethod to control their own construction
- Signature: `@classmethod def __svcs__(cls, container: svcs.Container) -> Self`
- When `__svcs__` exists, it replaces the normal `Injectable[T]` field resolution
- The method receives the `svcs.Container` instance for access to other services
- The method must return a fully constructed instance of the class

**Construction Behavior:**
- Detection: Check for `__svcs__` method via `getattr(cls, "__svcs__", None)`
- Precedence: If `__svcs__` exists, skip automatic field injection entirely
- Container access: Pass the container to allow dynamic service resolution
- Kwargs support: `__svcs__` should accept kwargs for overrides following same interface as normal injection
- Return contract: Method must return `Self` (the class instance)

**Use Cases Supported:**
1. Complex initialization logic beyond simple field injection
2. Post-construction validation or setup steps
3. Conditional construction based on container contents
4. Dynamic service fetching based on runtime conditions

### Reusability Opportunities

**Patterns to Model After:**
- Hopscotch `__hopscotch_factory__` pattern provides proven design
- Detection via `getattr` with None default is clean and reliable
- Passing full container/registry enables maximum flexibility
- Classmethod decorator ensures proper signature and type hints

**Code to Reference:**
- `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py` (lines 122-128)
- `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/fixtures/dataklasses.py` (lines 87-98)

### Scope Boundaries

**In Scope:**
- Synchronous `__svcs__` classmethod support
- Container access within `__svcs__` method
- Complete replacement of automatic field injection when `__svcs__` exists
- Kwargs support for overrides
- Simple example demonstrating the pattern
- Documentation explaining use cases and best practices

**Out of Scope:**
- Asynchronous `async def __svcs__` support (future enhancement)
- Helper decorators for common `__svcs__` patterns (not requested)
- Partial injection (auto-inject fields then call `__svcs__` - user explicitly chose replacement model)
- Framework-specific integrations
- Complex real-world examples (user requested simple examples)

**Clarifications:**
- Original question about combining field injection with `__svcs__` was answered: complete replacement is desired
- The kwargs support follows the same interface as normal injection for consistency
- Focus on simplicity and clarity in initial implementation

### Technical Considerations

**Integration Points:**
- Must integrate with existing `svcs.auto()` factory creation
- Detection happens during factory construction phase
- Container must be passed to `__svcs__` method during resolution
- Type hints should properly reflect `Self` return type (Python 3.11+)

**Existing System Constraints:**
- Built on `svcs` library's Registry and Container abstractions
- Must work with both sync service resolution
- Should maintain `svcs`' non-magical approach (explicit protocol)
- Core feature for minimal viable product (roadmap item #2)

**Technology Preferences:**
- Python 3.12+ type hints required
- Use `typing.Self` for return type annotation
- Protocol-based approach (duck typing via method presence)
- Minimal, explicit API design

**Similar Code Patterns:**
- Follow Hopscotch's detection pattern: `getattr(target, "__svcs__", None)`
- Similar classmethod signature with container/registry argument
- Complete bypass of normal injection when factory exists
- Return fully constructed instance directly

**Design Alignment:**
- Aligns with product mission: "provide modern, protocol-based dependency injection"
- Supports use case: "complex conditional service resolution"
- Maintains principle: "Keep an escape hatch - users should always be able to write custom factory methods"
- Follows roadmap: Item #2 of minimal viable core features
