# Specification: Minimal svcs.auto() Helper for Automatic Dependency Injection

## Goal

Create a minimal, upstream-compatible `svcs.auto()` helper that enables automatic dependency resolution based on type
hints, allowing `registry.register_factory(Wrapper, svcs.auto(Wrapper))` to automatically resolve constructor
dependencies without manual factory functions. Keep this very thin.

## User Stories

- As a svcs user, I want to register factories without writing manual factory functions, so that I can reduce
  boilerplate when dependencies are clearly expressed via type hints
- As a library author, I want a minimal auto-injection helper that could be accepted into svcs upstream, so that the
  community benefits from optional convenience without compromising svcs' non-magical philosophy

## Specific Requirements

**Auto Factory Creation**

- `svcs.auto(target)` accepts a class or callable and returns a factory function
- Factory signature must be `def factory(svcs_container: Container, **kwargs) -> T`
- Factory inspects target's constructor parameters (functions) or dataclass fields
- Factory resolves only parameters marked with `Injectable[T]` from container
- Non-injectable parameters must be provided via kwargs or have defaults
- Implementation must be a single module with no imports beyond Python stdlib and svcs
- Factory uses keyword arguments for injection (not positional)

**Type Hint Introspection**

- Use `inspect.signature()` combined with `typing.get_type_hints()` for function parameters
- Use `dataclasses.fields()` combined with `typing.get_type_hints()` for dataclass fields
- No support for `Annotated` type hints in this minimal implementation
- Follow svcs pattern: use `eval_str=True` for forward reference resolution with graceful fallback
- Handle `Optional[T]` and other generic types appropriately
- Allow `Any` type annotations for parameters that users intend to override via kwargs

**Injectable Parameter Marking**

- Users must explicitly mark parameters as injectable using a marker type (e.g., `Injectable[T]`)
- Only parameters marked with `Injectable` will be resolved from the container
- Non-marked parameters must be provided via kwargs or have default values
- This explicit opt-in prevents accidental injection and makes dependencies clear
- `Injectable` is a generic type that wraps the actual dependency type
- Example: `def __init__(self, db: Injectable[Database], timeout: int = 30)`
- The `timeout` parameter would not be injected (normal parameter)
- The `db` parameter would be injected from the container (marked with `Injectable`)
- **Important:** kwargs take precedence over injection - even `Injectable[T]` parameters can be overridden via kwargs

**Dependency Resolution Order**

- Only process parameters marked with `Injectable[T]` for container resolution
- **Precedence (highest to lowest):**
    1. **kwargs** passed to factory - override everything, including injectable parameters
    2. **container lookup** via `container.get()` or `container.aget()` - only for `Injectable[T]` parameters
    3. **default values** from parameter/field definition
- For injectable parameters (`Injectable[T]`):
    - If kwarg provided, use it (highest precedence)
    - Else if in container, resolve from container
    - Else if has default value, use default
    - Else let container's `ServiceNotFoundError` propagate
- For non-injectable parameters:
    - Must be provided via kwargs or have a default value
    - Never resolved from container
- Validate that all provided kwargs match actual parameter names
- Raise exception if kwarg name doesn't match any parameter

**Async Support**

- Single `svcs.auto()` function detects sync/async automatically
- Factory can work in both sync and async contexts
- Detect if container method returns awaitable and await accordingly
- Follow svcs patterns where `aget()` works with both sync and async factories
- Support async dataclass construction and async dependency resolution

**Protocol Support**

- Detect when `Injectable[T]` wraps a protocol type using `typing.get_abstract()`
- Use `container.get_abstract()` or `container.aget_abstract()` for protocol types
- Follow svcs patterns for protocol handling
- Maintain type safety with protocol-based dependencies
- Example: `Injectable[GreeterProtocol]` where `GreeterProtocol` is a Protocol class

**Pluggable Injector Protocol**

- Define `Injector` protocol with signature `(target: type[T], container: Container, **kwargs: Any) -> T`
- Default injector implements the auto-resolution logic described above
- Registry can optionally have custom injector registered
- `svcs.auto()` checks registry for custom injector, uses default if none found
- Injector lookup is automatic (no explicit registration API needed in phase 0)

**Error Handling**

- Propagate `ServiceNotFoundError` from container as-is
- Raise `TypeError` for async/sync mismatches
- Raise `ValueError` or `TypeError` for unknown kwargs (strict validation)
- No custom exception types in this minimal implementation
- Fail fast with clear error messages

**Free-Threaded Compatibility**

- No global mutable state
- All stateful data lives in Registry or Container (per svcs design)
- Injector is stateless (pure function)
- Field info extraction is stateless (inspection happens per-call)
- Follow svcs patterns for thread-safe container lifecycle

## Visual Design

No visual assets provided.

## Existing Code to Leverage

**Hopscotch field_infos.py patterns**

- Unified `FieldInfo` structure combining dataclass fields and function parameters
- `get_field_infos()` provides single interface for extracting parameters from both dataclasses and functions
- `get_dataclass_field_infos()` extracts field metadata using `dataclasses.fields()` and `get_type_hints()`
- `get_non_dataclass_field_infos()` extracts parameter metadata using `inspect.signature()` and `get_type_hints()`
- Pattern normalizes default values, default factories, and type information into consistent structure

**Hopscotch registry.py injection precedence**

- `inject_callable()` demonstrates three-tier precedence: props (kwargs) > registry lookup > default values
- Validates that all props/kwargs match actual field names from extracted field info
- Iterates through field infos to build kwargs dict, then calls `target(**kwargs)`
- Raises `ValueError` if no value can be determined for required field
- Uses keyword argument calling convention exclusively

**svcs _core.py signature inspection**

- `_robust_signature()` function handles `eval_str=True` for forward references in `TYPE_CHECKING` blocks
- Graceful fallback when signature inspection fails (try with eval_str, then without)
- `_takes_container()` pattern detects special container parameter by name or annotation
- Pattern suppresses exceptions during inspection and provides fallback behavior

**svcs _core.py container patterns**

- `Container.get()` and `Container.aget()` methods for sync/async service retrieval
- `_lookup()` method resolves service from registry with proper caching
- `get_abstract()` and `aget_abstract()` for protocol-based lookups
- Detect awaitable results with `inspect.isawaitable()` and handle accordingly
- Context manager support for both sync and async container lifecycle

**svcs _core.py async detection**

- Use `inspect.iscoroutine()`, `inspect.isawaitable()`, and `inspect.isasyncgenfunction()` for async detection
- Factory can return either sync value or awaitable
- Container's `aget()` handles both sync and async factories transparently

## Out of Scope

- `Annotated` type hint support (not needed for minimal implementation)
- Field metadata beyond type information (custom metadata, operators)
- Scanning or auto-discovery of services (venusian integration)
- Context-aware resolution (contexts, locations, request-specific registries)
- Multiple registrations for same service type with precedence/scoring
- Custom construction protocols (`__svcs__` or `__hopscotch_factory__` methods)
- Registry hierarchies or parent registry lookups
- Complex precedence systems beyond three-tier (kwargs > container > defaults)
- Additional dependencies beyond stdlib and svcs
- Modification of svcs core classes (Container.get() with kwargs)
- Global caches or mutable state
