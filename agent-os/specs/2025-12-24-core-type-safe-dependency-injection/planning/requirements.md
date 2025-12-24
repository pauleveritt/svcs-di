# Spec Requirements: Core Type-Safe Dependency Injection

## Initial Description

Implement the minimal `svcs.auto()` helper method for automatic dependency resolution that could potentially be accepted
into svcs itself. This is Phase 0 from the roadmap - a single module with no imports beyond Python stdlib and svcs,
providing automatic dependency resolution based on type hints.

**Key Goal:** Create a helper that enables `registry.register_factory(Wrapper, svcs.auto(Wrapper))` to automatically
resolve constructor dependencies without requiring manual factory functions.

**Design Philosophy:** Optional convenience helper that maintains svcs' non-magical approach, with minimal
implementation that could be proposed upstream.

## Requirements Discussion

### First Round Questions

**Q1:** I assume we'll use the newest Python techniques for inspecting parameters (using `inspect.signature()` with
`get_type_hints()` including `include_extras=True` for `Annotated` support) and for dataclass fields (using
`dataclasses.fields()` with `get_type_hints()`). Is that correct?

**Answer:** Yes, confirmed. Use modern inspection techniques.

**Q2:** For factory behavior, I'm thinking we make it pluggable via a protocol in the registry, where factories only
accept keyword arguments. Should we follow that pattern?

**Answer:** Yes, make factory behavior pluggable via protocol. Only keyword arguments.

**Q3:** I assume we'll follow svcs' patterns for async: provide both sync (`svcs.auto()`) and async-aware versions that
work with both sync and async factories. Correct?

**Answer:** Yes, follow svcs patterns for async.

**Q4:** For dependencies not registered in the container, I'm assuming we try the container first, then fall back to
using the default value if available. Should we allow this fallback?

**Answer:** Yes, try container first, fall back to default if not registered.

**Q5:** I'm thinking we follow svcs' protocol handling patterns using `get_abstract()` when protocols are involved. Does
that sound right?

**Answer:** Yes, follow svcs patterns for protocols.

**Q6:** For dependencies with `Any` type annotation, I assume we allow them (for when users want to override via
kwargs). Correct?

**Answer:** Yes, allow `Any` type annotations for kwargs override.

**Q7:** For error handling, I'm assuming we let exceptions from the container (like `ServiceNotFoundError`) propagate
as-is, and raise `TypeError` for signature/async mismatches. Should we add any custom exceptions?

**Answer:** No custom exceptions, let them propagate as-is.

**Q8:** Are there any specific things this should NOT do? (e.g., don't support field metadata, don't handle special
operators, don't do scanning)

**Answer:** No exclusions specified - keep it minimal.

### Follow-up Questions

#### Follow-up 1: Kwargs Integration

**Question:** For the kwargs mechanism (renamed from "props"), which pattern should we use?

**Answer:** Pattern A with modification - add kwargs at call time, possibly via different method to avoid overriding
`svcs.Container.get`. Consider: `container.get(MyClass, **kwargs)` or a separate method. Need to check if svcs has
patterns for adding kwargs to get methods.

**Decision:** The injector itself will handle kwargs, not necessarily extending Container.get(). The kwargs are passed
to `svcs.auto()` which returns a factory that can accept them.

#### Follow-up 2: Kwargs Behavior

**Question:** How should kwargs behave with parameter matching?

**Answer:**

- Match parameter names exactly
- Raise exception if provided kwarg doesn't match any parameter in signature
- Override BOTH injected dependencies AND default values
- Must work for both function parameters AND dataclass fields
- Reference: How Hopscotch synthesizes values (need to look at Hopscotch code)

#### Follow-up 3: Pluggable Injector

**Question:** Should the injector itself be pluggable?

**Answer:** Yes, the injector itself should be pluggable and stored in the registry. Default to the injector we're
creating. Create a protocol for the injector interface. This is about creating custom injection strategies.

#### Follow-up 4: Registry Integration for Injector

**Question:** How should we integrate the injector with the registry?

**Answer:** Behind the scenes, check if injector exists in registry. If no custom injector found, use default injector.
This is automatic detection, not explicit registration like example code.

#### Follow-up 5: Keyword Arguments

**Question:** Should svcs.auto() inject via positional or keyword arguments?

**Answer:** Answer A confirmed - `svcs.auto()` injects via keyword arguments (not positional).

## Existing Code to Reference

### Similar Features Identified:

**Hopscotch Project** (`/Users/pauleveritt/projects/pauleveritt/hopscotch`):

- **Field inspection**: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/field_infos.py`
    - `get_field_infos()` - unified interface for both dataclasses and functions
    - `get_dataclass_field_infos()` - extracts field info from dataclasses
    - `get_non_dataclass_field_infos()` - extracts parameter info from functions
    - `FieldInfo` NamedTuple structure for normalized field metadata
- **Injection logic**: `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py`
    - `inject_callable()` - constructs target with registry or props
    - Props mechanism (lines 113-164): kwargs have highest precedence, then registry injection, then defaults
    - Registry lookup falls back to parent registries
    - `__hopscotch_factory__` pattern for custom construction

**svcs Project** (`/Users/pauleveritt/PycharmProjects/svcs/`):

- **Container patterns**: `/Users/pauleveritt/PycharmProjects/svcs/src/svcs/_core.py`
    - `Container.get()` and `Container.aget()` methods (lines 981-1168)
    - `_lookup()` method for registry resolution (lines 783-807)
    - `_takes_container()` pattern for detecting container dependencies (lines 523-540)
    - Protocol support via `get_abstract()` and `aget_abstract()` (lines 762-781)
- **Factory detection**: `_robust_signature()` function (lines 505-520)
    - Handles `eval_str=True` for forward references under `TYPE_CHECKING`
    - Graceful fallback when signature inspection fails
- **Async patterns**:
    - Both `get()` and `aget()` methods
    - Context manager support for both sync and async
    - `isawaitable()`, `iscoroutine()`, `isasyncgenfunction()` checks

## Visual Assets

### Files Provided:

No visual assets provided.

### Visual Insights:

No visual assets provided.

## Requirements Summary

### Functional Requirements

#### Core Auto-Resolution

- Create `svcs.auto(cls)` helper that returns a factory function
- Factory inspects `cls` constructor/dataclass fields for type hints
- Automatically resolves dependencies from container
- Works with both regular classes and dataclasses
- Supports both function parameters and dataclass fields

#### Parameter Inspection

- Use `inspect.signature()` with `get_type_hints(include_extras=True)` for functions
- Use `dataclasses.fields()` with `get_type_hints()` for dataclasses
- Extract parameter names, types, and default values
- Support `Annotated` type hints
- Handle `Optional[T]` and other generic types appropriately

#### Dependency Resolution

- For each parameter/field with a type hint:
    1. Try to resolve from container first
    2. If not in container and has default value, use default
    3. If kwarg provided with matching name, override everything (highest precedence)
- Support `Any` type annotation (allows kwargs override without container lookup)
- Raise exception if kwarg name doesn't match any parameter
- Use keyword arguments for injection (not positional)

#### Async Support

- Factory must work with both sync and async contexts
- Follow svcs patterns: factory detects if container lookup returns awaitable
- Support both `container.get()` and `container.aget()` usage

#### Protocol Support

- Follow svcs patterns for protocol types
- Use `get_abstract()` / `aget_abstract()` when appropriate
- Maintain type safety with protocols

#### Error Handling

- Propagate `ServiceNotFoundError` from container as-is
- Raise `TypeError` for async/sync mismatches
- Raise exception for unknown kwargs
- No custom exceptions for this minimal implementation

#### Pluggable Injector Design

- Define an `Injector` protocol interface
- Default injector implements auto-resolution logic
- Check registry for custom injector (automatic detection)
- If custom injector registered, use it; otherwise use default
- Injector protocol should define how to resolve dependencies and handle kwargs

### Reusability Opportunities

#### From Hopscotch:

- Field inspection patterns (`field_infos.py`)
    - Unified `FieldInfo` structure for both dataclasses and functions
    - Extraction of defaults, types, and metadata
    - Handling of `Optional` and generic types
- Props/kwargs precedence pattern (`inject_callable` in `registry.py`)
    - Kwargs override everything
    - Then registry lookup
    - Finally default values
    - Validate kwargs against actual parameters

#### From svcs:

- Container lookup patterns (`_lookup()` method)
- Factory detection patterns (`_takes_container()`, `_robust_signature()`)
- Async/sync handling patterns
- Protocol support via `get_abstract()`
- Error propagation patterns

### Scope Boundaries

**In Scope:**

- Minimal `svcs.auto()` helper function
- Automatic dependency resolution from type hints
- Support for both functions and dataclasses
- Kwargs mechanism for overriding dependencies
- Async/sync support following svcs patterns
- Protocol support
- Pluggable injector interface (protocol + default implementation)
- Default value fallback
- Single module implementation
- No imports beyond stdlib and svcs

**Out of Scope:**

- Field metadata/operators (Annotated metadata beyond type info)
- Scanning/auto-discovery
- Context-aware resolution (contexts, locations, precedence)
- Multiple registrations for same type
- Custom construction protocols (`__svcs__` method)
- venusian integration
- Anything requiring additional dependencies
- Complex precedence systems
- Registry hierarchies/parents

### Technical Considerations

#### Integration Points

- Must work with existing `svcs.Registry.register_factory()`
- Must work with existing `svcs.Container.get()` and `aget()`
- Must not modify svcs core classes (decorator/wrapper pattern only)
- Should be a standalone module that svcs could accept

#### Technology Constraints

- Python 3.12+ (for modern type hints)
- stdlib only: `inspect`, `dataclasses`, `typing`
- svcs library (no other dependencies)
- Must handle forward references in TYPE_CHECKING blocks
- Must work with free-threaded Python (no global state)

#### Design Patterns to Follow

- svcs' non-magical, explicit approach
- Optional helper (user opts in)
- Factory pattern (returns callable)
- Protocol-based extensibility (Injector protocol)
- Fail fast with clear errors

#### Code Patterns from Research

**From Hopscotch field_infos.py:**

```python
# Unified field info extraction
FieldInfo = NamedTuple
with: field_name, field_type, default_value, default_factory, operator, has_annotated, is_builtin


# For dataclasses:
def get_dataclass_field_infos(target):
    type_hints = get_type_hints(target, include_extras=True)
    fields_mapping = {f.name: f for f in fields(target)}
    # Extract FieldInfo for each field


# For functions:
def get_non_dataclass_field_infos(target):
    type_hints = get_type_hints(target, include_extras=True)
    sig = signature(target)
    parameters = sig.parameters.values()
    # Extract FieldInfo for each parameter
```

**From Hopscotch registry.py:**

```python
# Kwargs precedence pattern
def inject_callable(registration, props=None, registry=None):
    kwargs = {}
    for field_info in registration.field_infos:
        fn = field_info.field_name
        if props and fn in props:
            # Props have highest precedence
            field_value = props[fn]
        elif registry:
            field_value = inject_field_registry(field_info, registry)
        else:
            field_value = inject_field_no_registry(field_info, props)

        # Fallback to defaults if no value found
        if field_value is None:
            if field_info.default_value is not None:
                field_value = field_info.default_value
            elif field_info.default_factory is not None:
                field_value = field_info.default_factory()
            else:
                raise ValueError(f"Cannot inject...")

        kwargs[fn] = field_value

    return target(**kwargs)  # Keyword argument injection
```

**From svcs _core.py:**

```python
# Robust signature inspection with eval_str
def _robust_signature(factory):
    with suppress(Exception):
        return inspect.signature(
            factory,
            locals={"Container": Container},
            eval_str=True,  # Handle TYPE_CHECKING forward refs
        )
    # Retry without eval_str as fallback
    with suppress(Exception):
        return inspect.signature(factory)
    return None


# Container detection pattern
def _takes_container(factory):
    if not (sig := _robust_signature(factory)):
        return False
    try:
        (name, p) = next(iter(sig.parameters.items()))
    except StopIteration:
        return False
    return name == "svcs_container" or p.annotation in (
        Container, "svcs.Container", "Container",
    )
```

#### Implementation Strategy

1. **Create `svcs.auto()` function:**
    - Takes a class/callable as input
    - Returns a factory function
    - Factory function signature: `def factory(svcs_container: Container, **kwargs) -> T`

2. **Factory function behavior:**
    - Inspect target for parameters/fields
    - For each parameter:
        - Check kwargs first (highest precedence)
        - Then try container.get() or container.aget()
        - Finally use default value if available
    - Validate all kwargs match actual parameters
    - Call target with resolved kwargs
    - Return instance

3. **Injector protocol:**
   ```python
   class Injector(Protocol):
       def __call__(
           self,
           target: type[T],
           container: Container,
           **kwargs: Any
       ) -> T:
           ...
   ```

4. **Registry integration:**
    - Check if custom injector registered in container
    - Default injector implements the auto-resolution logic
    - `svcs.auto()` uses the active injector

#### Async Handling

Follow svcs patterns:

- Factory can be sync or async
- Detection: check if container.get() result is awaitable
- In async context, await the result
- Both dataclass construction and dependency resolution can be async

#### Example Usage

```python
from dataclasses import dataclass
import svcs


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432


@dataclass
class Database:
    config: DatabaseConfig
    pool_size: int = 10


# Setup
registry = svcs.Registry()
registry.register_factory(DatabaseConfig, svcs.auto(DatabaseConfig))
registry.register_factory(Database, svcs.auto(Database))

# Usage
container = svcs.Container(registry)
db = container.get(Database)
# db.config automatically injected from container
# db.pool_size uses default value

# With kwargs override
db2 = container.get(Database, pool_size=20)
# pool_size overridden to 20
```

### Open Questions for Spec Writer

1. **Single factory or separate functions?**
    - Option A: Single `svcs.auto()` that detects sync/async automatically
    - Option B: Separate `svcs.auto()` and `svcs.auto_async()`
    - Recommendation: Option A (following svcs pattern where `aget()` works with both)

2. **Kwargs validation strictness:**
    - Should we raise on unknown kwargs, or silently ignore?
    - Recommendation: Raise exception for unknown kwargs (fail fast)

3. **Injector registration:**
    - Should there be a special type key for the injector in the registry?
    - Recommendation: Use a sentinel type like `InjectorProtocol` as the service type

4. **Module location:**
    - Should this be `svcs.auto` (requires svcs upstream changes)?
    - Or `svcs_di.auto` (separate package, can propose to svcs later)?
    - Recommendation: Start with `svcs_di.auto`, design it to be upstreamable

5. **TYPE_CHECKING handling:**
    - Should we use eval_str=True by default like svcs?
    - Recommendation: Yes, follow svcs pattern exactly

## Research Findings

### Hopscotch Value Synthesis Pattern

From `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py`:

**Key Pattern:** The `inject_callable()` function (lines 113-164) shows how Hopscotch handles kwargs (called "props"):

1. **Precedence order (highest to lowest):**
    - Props/kwargs (passed at call time)
    - Registry lookup
    - Default values (from field default or default_factory)

2. **Validation:**
    - Iterates through all field_infos (extracted from target)
    - Only sets kwargs for fields that actually exist on target
    - Raises `ValueError` if no value can be determined

3. **Dataclass and function unification:**
    - Both use the same `FieldInfo` structure
    - Both follow same precedence rules
    - Both validate kwargs against actual parameters

### svcs Container Patterns

From `/Users/pauleveritt/PycharmProjects/svcs/src/svcs/_core.py`:

**No kwargs pattern in Container.get():**

- Current svcs `Container.get()` doesn't accept kwargs
- All configuration happens at registration time
- This makes sense for svcs' design (factories are fully responsible)

**Our approach:**

- `svcs.auto()` returns a factory
- The factory itself handles kwargs
- No modification to Container.get() needed
- Pattern: `registry.register_factory(MyClass, svcs.auto(MyClass))`
- Later extension could add: `container.get(MyClass, __inject_kwargs={'port': 5432})`

### Pluggable Injector Insights

**Design approach:**

1. Default injector is a function/callable, not a class
2. Protocol defines the interface
3. Registry can have custom injector registered
4. `svcs.auto()` checks registry for injector, uses default if none found

**Protocol design:**

```python
from typing import Protocol, TypeVar, Any
from svcs import Container

T = TypeVar('T')


class Injector(Protocol):
    """Protocol for custom dependency injection strategies."""

    def __call__(
            self,
            target: type[T],
            container: Container,
            **kwargs: Any
    ) -> T:
        """
        Construct an instance of target, resolving dependencies from container.

        Args:
            target: The class/callable to instantiate
            container: The svcs container for dependency lookup
            **kwargs: Override values for specific parameters

        Returns:
            Instance of target with dependencies injected
        """
        ...
```

### Free-Threaded Compatibility

**Requirements:**

- No global mutable state
- All state in Registry or Container (per svcs design)
- Injector is stateless (pure function)
- Field info extraction is stateless (pure function)

**svcs already handles:**

- Thread-safe container lifecycle
- Registry immutability after setup
- Cleanup coordination

**Our additions must:**

- Not introduce global caches
- Not mutate shared state
- Keep all inspection/resolution stateless
