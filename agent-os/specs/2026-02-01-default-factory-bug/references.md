# References: default_factory Bug

## Bug Location

**File**: `src/svcs_di/auto.py`

**Sync version**: Lines 567-573
```python
# Tier 2: default value
if field_info.has_default:
    default_val = field_info.default_value
    # Call default_factory if it's a callable (bound method from dataclass field)
    if callable(default_val) and hasattr(default_val, "__self__"):
        return True, default_val()
    return True, default_val
```

**Async version**: Lines 605-611
```python
# Tier 2: default value
if field_info.has_default:
    default_val = field_info.default_value
    # Call default_factory if it's a callable (bound method from dataclass field)
    if callable(default_val) and hasattr(default_val, "__self__"):
        return True, default_val()
    return True, default_val
```

## Related Functions

- `_resolve_field_value()` - Sync field resolution (line 530)
- `_resolve_field_value_async()` - Async field resolution (line 578)
- `_create_field_info()` - Creates FieldInfo from dataclass fields (line 478)

## Test File

**File**: `tests/test_auto.py`

Existing test that stores factory but doesn't test invocation:
- `test_create_field_info_with_default_factory()` (line 442)

## Roadmap Reference

The bug is documented in `ROADMAP.md` under "Bugs to Fix":
- "default_factory bug - field(default_factory=...) doesn't work correctly"
