# References: Resource and Location on HopscotchContainer

## Implementation References

### Resource[T] Type Alias

- File: `src/svcs_di/auto.py`
- Definition: `type Resource[T] = T`
- Detection: `is_resource_type()` checks `get_origin(type_hint) is Resource`

### FieldInfo with is_resource

- File: `src/svcs_di/auto.py`
- Added: `is_resource: bool` field to `FieldInfo` NamedTuple
- Detection: `_create_field_info()` calls `is_resource_type()`

### HopscotchInjector Resolution

- File: `src/svcs_di/injectors/hopscotch.py`
- Both sync and async versions check `field_info.is_resource`
- Returns: `getattr(self.container, 'resource', None)`

### HopscotchContainer

- File: `src/svcs_di/hopscotch_registry.py`
- Stores: `resource: Any` and `location: PurePath | None`
- `__attrs_post_init__`: Only registers Location
- `inject()`: Derives `type(self.resource)` for ServiceLocator matching

### Location Type Alias

- File: `src/svcs_di/injectors/locator.py`
- Definition: `Location = PurePath`
- Used for hierarchical request context (URL paths)
- Registered via `register_local_value(Location, ...)`

## Example Patterns

### Resource Injection

```python
from svcs_di import Inject, Resource

@dataclass
class ResourceAwareService:
    greeting: Inject[Greeting]           # From registry
    customer: Resource[FrenchCustomer]   # From container.resource

container = HopscotchContainer(registry, resource=FrenchCustomer())
service = container.inject(ResourceAwareService)
```

### Location Injection

```python
@dataclass
class LocationAwareService:
    location: Inject[Location]

container = HopscotchContainer(registry, location=PurePath("/admin"))
service = container.inject(LocationAwareService)
```

## Related Tests

### test_hopscotch_resource_location.py

- 18 tests covering Resource[T] and Location injection
- Tests for resource type derivation
- Tests for decorator/scanning integration
- Async tests
