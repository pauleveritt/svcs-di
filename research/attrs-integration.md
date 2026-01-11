# How attrs Could Enhance a Dependency Injection System

## Current svcs-di Approach

svcs-di currently uses **dataclasses** for services and extracts field info via `dataclasses.fields()` and
`get_type_hints()`. The `FieldInfo` namedtuple captures name, type, defaults, and whether a field is injectable.

## attrs Features Relevant to DI

### 1. Validators for Service Configuration

attrs validators run *after* converters during `__init__`. For DI services:

```python
import attrs
from svcs_di import Inject


@attrs.define
class DatabaseService:
    connection_string: str = attrs.field(
        validator=attrs.validators.matches_re(r"^postgres://")
    )
    pool_size: int = attrs.field(
        validator=[attrs.validators.instance_of(int), attrs.validators.ge(1)]
    )
    cache: Inject[CacheService]  # Injected dependency
```

**DI benefit**: Validate service configuration at construction time, failing fast before the service enters the
container.

### 2. Converters for Flexible Injection

Converters transform values *before* validation. Could enable:

```python
@attrs.define
class ConfigService:
    # Accept string "true"/"false" from env vars, convert to bool
    debug_mode: bool = attrs.field(converter=attrs.converters.to_bool())

    # Accept comma-separated string, convert to list
    allowed_hosts: list[str] = attrs.field(
        converter=lambda s: s.split(",") if isinstance(s, str) else s
    )
```

**DI benefit**: Services can accept multiple input formats, making them more flexible when configured from environment
variables or config files.

### 3. `__attrs_post_init__` for Derived Attributes

Execute logic after all fields (including injected ones) are set:

```python
@attrs.define
class UserService:
    db: Inject[Database]
    cache: Inject[Cache]
    _connection_pool: ConnectionPool = attrs.field(init=False)

    def __attrs_post_init__(self):
        # Initialize derived state using injected dependencies
        self._connection_pool = ConnectionPool(self.db, self.cache)
```

**DI benefit**: Compose derived state from multiple injected dependencies after construction.

### 4. Field Metadata for DI Configuration

attrs allows arbitrary metadata on fields—a powerful extension point:

```python
# Define DI-specific metadata keys
DI_OPTIONAL = "svcs_di.optional"
DI_QUALIFIER = "svcs_di.qualifier"


@attrs.define
class PaymentService:
    primary_gateway: Inject[PaymentGateway] = attrs.field(
        metadata={DI_QUALIFIER: "stripe"}
    )
    fallback_gateway: Inject[PaymentGateway] = attrs.field(
        metadata={DI_QUALIFIER: "paypal", DI_OPTIONAL: True}
    )
```

**DI benefit**: Richer injection configuration without polluting the type system. The injector can read metadata via
`attrs.fields()`.

### 5. `field_transformer` for Automatic Injection Setup

The `field_transformer` hook runs at class definition time:

```python
def auto_inject_transformer(cls, fields):
    """Automatically mark Protocol-typed fields as injectable."""
    new_fields = []
    for f in fields:
        if is_protocol_type(f.type):
            # Add injection metadata automatically
            new_fields.append(f.evolve(
                metadata={**f.metadata, "auto_inject": True}
            ))
        else:
            new_fields.append(f)
    return new_fields


@attrs.define(field_transformer=auto_inject_transformer)
class MyService:
    repo: UserRepository  # Auto-detected as injectable Protocol
```

**DI benefit**: Reduce boilerplate by auto-detecting injectable fields based on type characteristics.

### 6. `attrs.fields()` for Introspection

More capable than `dataclasses.fields()`:

```python
def get_attrs_field_infos(target: type) -> list[FieldInfo]:
    """Extract field info from an attrs class."""
    for field in attrs.fields(target):
        # Access rich metadata
        validator = field.validator
        converter = field.converter
        metadata = field.metadata
        alias = field.alias  # For different __init__ param name
        # ...
```

**DI benefit**: Access to validators, converters, aliases, and custom metadata during injection.

### 7. `attrs.resolve_types()` for Forward References

Explicitly resolve string annotations:

```python
@attrs.define
class ServiceA:
    b: "ServiceB"  # Forward reference


attrs.resolve_types(ServiceA, globalns=globals())
# Now ServiceA's field types are resolved
```

**DI benefit**: Cleaner handling of circular dependencies and forward references.

### 8. Frozen Classes for Immutable Services

```python
@attrs.frozen  # Immutable, hashable
class ConfigService:
    api_key: str
    endpoint: str
```

**DI benefit**: Thread-safe, immutable configuration services (svcs-di already uses `frozen=True` dataclasses).

## Implementation Considerations for svcs-di

### Option A: Add attrs Support Alongside Dataclasses

Extend `get_field_infos()` to detect and handle attrs classes:

```python
def get_field_infos(target: type | Callable) -> list[FieldInfo]:
    if attrs.has(target):  # Check for attrs class
        return _get_attrs_field_infos(target)
    elif dataclasses.is_dataclass(target):
        return _get_dataclass_field_infos(target)
    else:
        return _get_callable_field_infos(target)
```

### Option B: Use attrs Metadata for DI Markers

Instead of `Inject[T]`, use attrs metadata:

```python
def injectable(**kw):
    """Mark a field for injection."""
    return attrs.field(metadata={"inject": True}, **kw)


@attrs.define
class Service:
    db: Database = injectable()  # Marked for injection
    timeout: int = 30  # Regular field
```

### Option C: Field Transformer for Automatic Inject Detection

Create a class decorator that auto-detects `Inject[T]` fields and adds metadata:

```python
@svcs_injectable  # Applies field_transformer
@attrs.define
class Service:
    db: Inject[Database]
```

## Summary Table

| attrs Feature         | DI Use Case                             |
|-----------------------|-----------------------------------------|
| Validators            | Validate service config at construction |
| Converters            | Flexible config from env vars/files     |
| `__attrs_post_init__` | Derive state from injected deps         |
| Field metadata        | Qualifiers, optional deps, scopes       |
| `field_transformer`   | Auto-detect injectable fields           |
| `attrs.fields()`      | Rich introspection for injector         |
| `resolve_types()`     | Handle forward references               |
| Frozen classes        | Thread-safe immutable services          |

The most powerful features for DI are **field metadata** (for qualifiers/scopes), **validators** (for config
validation), and **`field_transformer`** (for reducing boilerplate).

## The Registration Challenge: Getting Classes into a Registry

The core challenge with decorator-based scanning is: **how do we register a class into a `Registry` instance at class
definition time, without requiring a global registry or thread-local storage?**

### The Timing Problem

Class decorators run at **import time**, but the `Registry` typically exists at **runtime** (application startup):

```python
# This runs at import time - no registry exists yet!
@injectable(for_=Greeting, resource=CustomerContext)
@attrs.define
class CustomerGreeting:
    salutation: str = "Hello"


# This runs later at application startup
def create_app():
    registry = svcs.Registry()  # Registry created here
    scan(registry, "myapp")  # Classes registered here
```

### Current svcs-di Approach: Two-Phase Registration

svcs-di solves this with deferred registration:

1. **Phase 1 (import time)**: `@injectable` stores metadata on the class via `__injectable_metadata__`
2. **Phase 2 (runtime)**: `scan(registry, ...)` finds marked classes and registers them

This avoids globals but requires explicit scanning.

### Could attrs Help?

attrs provides several extension points, but none directly solve the "no registry at import time" problem:

| attrs Feature         | Runs When         | Has Registry Access? |
|-----------------------|-------------------|----------------------|
| `field_transformer`   | Class definition  | No                   |
| `__attrs_pre_init__`  | Instance creation | No (wrong time)      |
| `__attrs_post_init__` | Instance creation | No (wrong time)      |

However, attrs **could** help with alternative patterns:

### Approach 1: `__init_subclass__` with Collection Base Class

Python's `__init_subclass__` (works with attrs) can collect classes as they're defined:

```python
import attrs
from pathlib import PurePath


class Injectable:
    """Base class that collects subclasses for later registration."""

    _pending: ClassVar[list[tuple[type, dict]]] = []

    def __init_subclass__(
            cls,
            for_: type | None = None,
            resource: type | None = None,
            location: PurePath | None = None,
            **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        Injectable._pending.append((cls, {
            "for_": for_,
            "resource": resource,
            "location": location,
        }))


@attrs.define
class CustomerGreeting(Injectable, for_=Greeting, resource=CustomerContext):
    salutation: str = "Hello"


# Later, at app startup:
def register_all(registry: svcs.Registry):
    for cls, metadata in Injectable._pending:
# ... register cls with metadata
```

**Pros:**

- Class-level metadata via subclass arguments
- No decorator needed (inheritance is explicit)
- Works naturally with attrs

**Cons:**

- Requires inheritance (some consider this intrusive)
- `_pending` is effectively a global (on the base class)
- Multiple inheritance can get tricky

### Approach 2: `field_transformer` as Collection Hook

Use attrs' `field_transformer` to collect classes during definition:

```python
_pending_registrations: list[tuple[type, dict]] = []


def collecting_transformer(for_=None, resource=None, location=None):
    """Create a field_transformer that collects the class."""

    def transformer(cls, fields):
        _pending_registrations.append((cls, {
            "for_": for_,
            "resource": resource,
            "location": location,
        }))
        return fields

    return transformer


# Usage requires passing transformer to attrs.define
@attrs.define(field_transformer=collecting_transformer(for_=Greeting))
class CustomerGreeting:
    salutation: str = "Hello"
```

**Pros:**

- Leverages attrs extension point
- Metadata passed at decoration time

**Cons:**

- Verbose syntax
- Module-level `_pending_registrations` is still global state
- Awkward to use

### Approach 3: Contextvar-Based Registry (For Controlled Import)

If you control when modules are imported, a contextvar could work:

```python
from contextvars import ContextVar

_current_registry: ContextVar[svcs.Registry | None] = ContextVar(
    "current_registry", default=None
)


def injectable(
        for_: type | None = None,
        resource: type | None = None,
        location: PurePath | None = None,
):
    def decorator(cls):
        if registry := _current_registry.get():
            # Register immediately if registry is available
            _do_registration(registry, cls, for_, resource, location)
        else:
            # Fall back to metadata marking for later scan()
            cls.__injectable_metadata__ = {
                "for_": for_,
                "resource": resource,
                "location": location,
            }
        return cls

    return decorator


# Usage: import modules within registry context
def create_app():
    registry = svcs.Registry()
    token = _current_registry.set(registry)
    try:
        import myapp.services  # Classes register as they're imported!
    finally:
        _current_registry.reset(token)
```

**Pros:**

- No global state (contextvar is scoped)
- Registration happens at import time when registry is available
- Falls back gracefully when no registry

**Cons:**

- Requires controlled import timing
- Unusual pattern
- Won't work with normal top-level imports

### Approach 4: attrs Class Variable for Metadata (No Global Collection)

Store metadata on the class itself, let `scan()` find it later:

```python
from typing import ClassVar


@attrs.define
class CustomerGreeting:
    # Class-level DI configuration
    __di_config__: ClassVar[dict] = {
        "for_": Greeting,
        "resource": CustomerContext,
        "location": None,
    }

    salutation: str = "Hello"
```

This is essentially what `@injectable` does, but explicit. The scanner looks for `__di_config__` or
`__injectable_metadata__`.

**Pros:**

- No magic, completely explicit
- No decorator needed
- Works with any class system

**Cons:**

- Verbose
- Easy to forget or typo

### Approach 5: Hybrid - Combined `@attrs_injectable` Decorator

Combine attrs decoration with injectable marking in one decorator:

```python
def attrs_injectable(
        maybe_cls=None,
        *,
        for_: type | None = None,
        resource: type | None = None,
        location: PurePath | None = None,
        frozen: bool = False,
        **attrs_kwargs,
):
    """Combined @attrs.define + @injectable decorator."""

    def wrap(cls):
        # Apply attrs.define
        attrs_cls = attrs.define(frozen=frozen, **attrs_kwargs)(cls)
        # Mark for scanning (no immediate registration)
        attrs_cls.__injectable_metadata__ = {
            "for_": for_,
            "resource": resource,
            "location": location,
        }
        return attrs_cls

    if maybe_cls is None:
        return wrap
    return wrap(maybe_cls)


# Usage
@attrs_injectable(for_=Greeting, resource=CustomerContext, frozen=True)
class CustomerGreeting:
    salutation: str = "Hello"
```

**Pros:**

- Single decorator
- Passes through attrs options
- Compatible with existing `scan()` infrastructure

**Cons:**

- Still requires `scan()` call
- Another decorator to learn

### Conclusion: attrs Doesn't Solve the Fundamental Problem

The challenge of "register without globals" is a **Python timing problem**, not an attrs problem. Class decorators run
at import time before the registry exists.

**attrs' contribution** is primarily in the *introspection phase* (during `scan()`), where `attrs.fields()` and
`attrs.has()` provide richer metadata than `dataclasses.fields()`.

The most practical solutions remain:

1. **Two-phase (current)**: Mark at import, scan at startup
2. **Base class collection**: `__init_subclass__` collects, bulk register later
3. **Controlled imports**: Contextvar + import within registry scope

All approaches require *some* form of deferred registration or controlled timing.
