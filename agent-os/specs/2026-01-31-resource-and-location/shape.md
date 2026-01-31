# Shape: Resource and Location on HopscotchContainer

## Problem Statement

Originally, to use resource-based resolution, users could:

1. Use `Inject[Resource]` marker class pattern
2. Container auto-registered resource under `Resource` marker and concrete type

However, this caused subtype issues:
- If you pass `FrenchCustomer()`, it only registers under `FrenchCustomer`
- `Inject[Customer]` won't find it (wrong type in registry)
- Would need to register under every type in the hierarchy

## Solution: Resource[T] Type Marker

Introduced `Resource[T]` as a separate type marker:

```python
from svcs_di import Inject, Resource

@dataclass
class FrenchGreeting(Greeting):
    customer: Resource[FrenchCustomer]  # Gets container.resource, typed as FrenchCustomer

@dataclass
class GenericService:
    resource: Resource[Customer]  # Gets container.resource, typed as Customer
```

The injector simply returns `container.resource` for any `Resource[T]` - the `T` is only for static type checking.

## Key Design Decisions

### 1. Resource[T] is a Type Alias (like Inject[T])

Using Python 3.14's PEP 695 type alias syntax:

```python
type Resource[T] = T
```

This is:
- Detectable at runtime via `get_origin(Resource[T])`
- Transparent to type checkers (they see T directly)
- Consistent with how `Inject[T]` works

### 2. Separation of Concerns

- `Inject[T]` = "resolve service of type T from registry"
- `Resource[T]` = "give me the current resource, I expect type T"

This makes the intent clear and avoids registry lookup complexity.

### 3. Type Parameter is for Static Typing Only

At runtime, the injector doesn't use `T` at all - it just returns `container.resource`. The type parameter exists
purely for static type checking benefits.

### 4. Simplified Container

`HopscotchContainer.__attrs_post_init__` only registers `Location` now. Resource registration was removed since the
injector handles it directly.

## Alternatives Considered

### A. Keep Inject[Resource] marker class

Rejected: Required registering under multiple types, caused subtype issues

### B. Register under all parent types

Rejected: Complex, error-prone, performance overhead

### C. Resource[T] with runtime type checking

Rejected: Unnecessary complexity, static typing is sufficient
