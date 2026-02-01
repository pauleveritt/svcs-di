# Shape: default_factory Bug Analysis

## Problem Statement

When using `field(default_factory=...)` in dataclasses resolved through the DI container, the factory function is not being called. Instead, the factory itself (e.g., `list`, `dict`, or a lambda) is passed as the field value.

## Expected Behavior

```python
@dataclass
class MyService:
    items: list = field(default_factory=list)
    config: dict = field(default_factory=dict)

# When resolved through DI:
service = container.get(MyService)
assert service.items == []  # Should be an empty list
assert service.config == {}  # Should be an empty dict
```

## Actual Behavior

```python
service = container.get(MyService)
assert service.items == list  # BUG: Gets the type `list` itself
assert service.config == dict  # BUG: Gets the type `dict` itself
```

## Root Cause

In `src/svcs_di/auto.py`, the `_resolve_field_value()` function checks:

```python
if callable(default_val) and hasattr(default_val, "__self__"):
    return True, default_val()
```

The `hasattr(default_val, "__self__")` check is too restrictive:

| Factory Type | `callable()` | `hasattr(__self__)` | Result |
|-------------|--------------|---------------------|--------|
| `list` | True | False | NOT called (bug) |
| `dict` | True | False | NOT called (bug) |
| `lambda: []` | True | False | NOT called (bug) |
| bound method | True | True | Called (correct) |

## Why `__self__` Was Used

The original implementation seems to have assumed that `default_factory` values would always be bound methods (which dataclasses internally creates). However, the actual value stored in `field_info.default_value` comes from analyzing the field, and the factory passed by the user (e.g., `list`, `dict`, lambda) is what gets stored.

## Solution

Remove the `__self__` check entirely. All callable `default_factory` values should be called:

```python
if callable(default_val):
    return True, default_val()
```

This correctly handles:
- Built-in types: `list`, `dict`, `set`
- Lambda functions: `lambda: [1, 2, 3]`
- Regular functions: `def make_items(): return []`
- Bound methods: `some_instance.method`

## Impact

- **Low risk**: The fix is simple and isolated
- **No breaking changes**: Existing code that works will continue to work
- **Fixes broken behavior**: Dataclasses with `default_factory` will now work correctly

## Test Cases Needed

1. `field(default_factory=list)` creates `[]`
2. `field(default_factory=dict)` creates `{}`
3. `field(default_factory=lambda: [1, 2, 3])` creates `[1, 2, 3]`
4. Multiple instances get independent lists (not shared)
5. End-to-end test through full DI container resolution
