# Plan: Inject in Post Init (Roadmap Item 17)

## Overview

Support `InitVar[Inject[T]]` pattern in dataclasses, allowing dependencies to be injected into `__post_init__` for computing derived values with fallback behavior.

**Pattern (Optional with Fallback):**
```python
@dataclass
class MyService:
    other_service: InitVar[Inject[OtherService]]
    final_value: int | None = None  # Allows override via kwargs

    def __post_init__(self, other_service: OtherService) -> None:
        if self.final_value is None:
            self.final_value = other_service.value + 1
```

This pattern allows both:
- **Auto-resolution**: `injector(MyService)` → computes `final_value` from `OtherService`
- **Manual override**: `injector(MyService, final_value=42)` → uses provided value

## Critical Files

- `src/svcs_di/auto.py` - Core field detection and `FieldInfo` type
- `src/svcs_di/injectors/keyword.py` - KeywordInjector implementation
- `src/svcs_di/injectors/hopscotch.py` - HopscotchInjector implementation
- `src/svcs_di/injectors/_helpers.py` - Shared helper functions

---

## Task 1: Save Spec Documentation

Create `agent-os/specs/2026-01-25-inject-post-init/` with:

- **plan.md** - This full plan
- **shape.md** - Shaping notes (scope, decisions, context)
- **standards.md** - Skills/standards that apply (references)
- **references.md** - Pointers to reference implementations

---

## Task 2: Add InitVar Detection to auto.py

**Location:** `src/svcs_di/auto.py`

**2a. Add helper functions** (after line 271, near other helper functions):

```python
def is_init_var(type_hint: Any) -> bool:
    """Check if a type hint is InitVar[T]."""
    return get_origin(type_hint) is dataclasses.InitVar

def unwrap_init_var(type_hint: Any) -> Any | None:
    """Extract T from InitVar[T]."""
    if not is_init_var(type_hint):
        return None
    args = get_args(type_hint)
    return args[0] if args else None
```

**2b. Update `FieldInfo` NamedTuple** (line 240-249):
```python
class FieldInfo(NamedTuple):
    """Field metadata for both dataclass fields and function parameters."""

    name: str
    type_hint: Any
    is_injectable: bool
    inner_type: type | None
    is_protocol: bool
    has_default: bool
    default_value: Any
    is_init_var: bool = False  # NEW: default False for backward compat
```

**2c. Update `_create_field_info`** (line 274-298) to accept and pass through `is_init_var` parameter

---

## Task 3: Update _get_dataclass_field_infos() for InitVar

**Location:** `src/svcs_di/auto.py` (lines 345-374)

Modify `_get_dataclass_field_infos()` to also extract `InitVar` fields:

```python
def _get_dataclass_field_infos(target: type) -> list[FieldInfo]:
    """Extract field information from a dataclass, including InitVar fields."""
    type_hints = _safe_get_type_hints(target, f"dataclass {target.__name__!r}")
    fields = dataclasses.fields(cast(Any, target))

    # Get names of regular fields (to exclude from InitVar scan)
    regular_field_names = {f.name for f in fields}

    field_infos = []

    # Process regular fields (existing logic)
    for field in fields:
        # ... existing code ...
        field_infos.append(
            _create_field_info(field.name, type_hint, has_default, default_value, is_init_var=False)
        )

    # NEW: Process InitVar fields from type hints
    for name, type_hint in type_hints.items():
        if name in regular_field_names:
            continue  # Already processed as regular field
        if not is_init_var(type_hint):
            continue  # Not an InitVar

        # Unwrap InitVar[T] to get T
        inner_hint = unwrap_init_var(type_hint)

        # InitVar fields have no default (must be provided at construction)
        field_infos.append(
            _create_field_info(name, inner_hint, has_default=False, default_value=None, is_init_var=True)
        )

    return field_infos
```

**Key insight:** `dataclasses.fields()` excludes InitVar, so we scan `type_hints` for `InitVar[...]` entries not already in regular fields.

---

## Task 4: Verify Injector Resolution Works

**Locations:**
- `src/svcs_di/auto.py` (DefaultInjector)
- `src/svcs_di/injectors/keyword.py` (KeywordInjector)
- `src/svcs_di/injectors/hopscotch.py` (HopscotchInjector)

**Expected behavior:** No changes needed to injectors! The resolution logic should work automatically:

1. `get_field_infos()` now returns InitVar fields with:
   - `is_injectable=True` (if `InitVar[Inject[T]]`)
   - `inner_type=T`
   - `is_init_var=True`

2. `_resolve_field_value()` resolves T from container (same as regular Inject fields)

3. Resolved value passed to `target(**kwargs)` -> dataclass routes InitVar args to `__post_init__()`

**Verify manually:** Write a simple test to confirm the flow works end-to-end.

---

## Task 5: Write Tests

**Location:** `tests/test_init_var_injection.py` (new file)

Test cases:
1. Basic `InitVar[Inject[T]]` resolution
2. Mix of regular `Inject[T]` fields and `InitVar[Inject[T]]`
3. `InitVar[Inject[T]]` with kwargs override
4. Multiple `InitVar` fields
5. `InitVar` without `Inject` (should not be resolved)
6. Error cases (missing registration, etc.)

---

## Task 6: Add Examples

**Location:** `examples/init_var/` (new directory)

Create examples demonstrating:
1. `basic_init_var.py` - Simple derived value pattern
2. `mixed_injection.py` - Regular fields + InitVar fields together

---

## Task 7: Write Documentation

**Location:** `docs/examples/init_var.md`

Document:
- The pattern and when to use it
- How it differs from regular injection
- Examples with explanations

---

## Verification

1. Run `just check` - all linting/type checks pass
2. Run `just test` - all tests pass including new InitVar tests
3. Run examples manually to verify they work
4. Build docs with `just docs` and verify new page renders

---

## Design Decisions

1. **Inject marker location:** `InitVar[Inject[T]]` - the Inject is inside InitVar, consistent with regular field patterns
2. **No changes to __post_init__ signature detection:** The injector resolves fields, dataclass handles routing to __post_init__
3. **Backward compatible:** Existing code without InitVar continues working unchanged
