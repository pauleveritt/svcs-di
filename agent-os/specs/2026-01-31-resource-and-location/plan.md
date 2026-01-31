# Plan: Resource and Location on HopscotchContainer

## Summary

Store `resource` and `location` as attributes on `HopscotchContainer`. Introduced `Resource[T]` type marker for
resource injection, separating it from `Inject[T]`.

## Implementation (Completed)

### Resource[T] Type Marker

Added `Resource[T]` as a generic type alias in `src/svcs_di/auto.py`:

```python
type Resource[T] = T
```

This separates concerns:
- `Inject[T]` = "resolve service of type T from registry"
- `Resource[T]` = "give me the current resource, typed as T"

### FieldInfo Updates

Updated `FieldInfo` NamedTuple to include `is_resource: bool` field for detecting `Resource[T]` annotations.

### Injector Resolution

Both `HopscotchInjector` and `HopscotchAsyncInjector` check `field_info.is_resource` and return
`getattr(self.container, 'resource', None)` for resource fields.

### HopscotchContainer

- Stores `resource` and `location` as attrs fields
- `__attrs_post_init__` only registers `Location` (resource handled by injector)
- `inject()` derives `type(self.resource)` for ServiceLocator matching

## Usage

```python
from svcs_di import Inject, Resource

@dataclass
class MyService:
    greeting: Inject[Greeting]      # Resolve from registry
    customer: Resource[Customer]    # Get container.resource, typed as Customer

container = HopscotchContainer(registry, resource=FrenchCustomer())
service = container.inject(MyService)
# service.customer is the FrenchCustomer instance
```

## Files Modified

| File                                        | Change                                      |
|---------------------------------------------|---------------------------------------------|
| `src/svcs_di/auto.py`                       | Added `Resource[T]`, updated `FieldInfo`    |
| `src/svcs_di/__init__.py`                   | Export `Resource`                           |
| `src/svcs_di/injectors/__init__.py`         | Export `Resource` from auto                 |
| `src/svcs_di/injectors/locator.py`          | Removed old `Resource` class                |
| `src/svcs_di/injectors/hopscotch.py`        | Handle `is_resource` in resolution          |
| `src/svcs_di/hopscotch_registry.py`         | Simplified `__attrs_post_init__`            |
| `tests/test_hopscotch_resource_location.py` | Updated tests for `Resource[T]`             |
| `examples/hopscotch/resource_resolution.py` | Updated to use `Resource[T]`                |
| `docs/hopscotch/*.md`                       | Updated documentation                       |

## Verification

All tests pass (393 tests), type checking passes, examples run successfully.
