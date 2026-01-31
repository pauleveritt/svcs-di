# Standards: Resource and Location on HopscotchContainer

## Type Alias Standards

### PEP 695 Generic Type Aliases

Using Python 3.14's type alias syntax:

```python
type Resource[T] = T
```

This creates a `TypeAliasType` that is:
- Detectable at runtime via `get_origin(Resource[T])`
- Transparent to type checkers (they see T directly)

### Detection Pattern

```python
def is_resource_type(type_hint: Any) -> bool:
    """Check if a type hint is Resource[T]."""
    return get_origin(type_hint) is Resource
```

## FieldInfo Standards

### NamedTuple with Optional Defaults

```python
class FieldInfo(NamedTuple):
    name: str
    type_hint: Any
    is_injectable: bool
    is_resource: bool       # NEW: detect Resource[T]
    inner_type: type | None
    is_protocol: bool
    has_default: bool
    default_value: Any
    is_init_var: bool = False
```

## Injector Resolution Standards

### Resource Resolution Pattern

```python
# In _resolve_field_value_sync / _resolve_field_value_async
if field_info.is_resource:
    resource_instance = getattr(self.container, "resource", None)
    if resource_instance is not None:
        return True, resource_instance
```

- Check `is_resource` before `is_injectable`
- Use `getattr` with default to handle containers without resource
- Return instance directly (no registry lookup)

## HopscotchContainer Standards

### attrs Field Definition

```python
@attrs.define
class HopscotchContainer(InjectorMixin, svcs.Container):
    resource: Any = attrs.field(default=None, kw_only=True)
    location: PurePath | None = attrs.field(default=None, kw_only=True)
```

### Post-Init Registration

```python
def __attrs_post_init__(self) -> None:
    """Auto-register location as local value."""
    from svcs_di.injectors.locator import Location
    if self.location is not None:
        self.register_local_value(Location, self.location)
```

Note: Resource is NOT registered here - handled by injector directly.

## Export Standards

### Public API

`Resource` exported from:
- `svcs_di` (main package)
- `svcs_di.injectors` (for backward compat)

Both import from `svcs_di.auto` where it's defined.

## Testing Standards

### Test Naming

- `test_container_with_resource_makes_it_available_via_resource_marker`
- `test_async_inject_with_resource_marker`
- `test_scanning_with_resource_marker`

### Test Fixtures

```python
@dataclass
class ResourceAwareService:
    resource: Resource[Employee]
```
