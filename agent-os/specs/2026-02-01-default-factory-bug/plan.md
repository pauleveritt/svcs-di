# Plan: Fix default_factory Bug

## Summary

Fix the bug where `field(default_factory=...)` doesn't work correctly when instantiating dataclasses through the DI container. The type itself (e.g., `list`) gets passed instead of calling the factory to create an instance (e.g., `[]`).

## Spec Folder

`agent-os/specs/2026-02-01-default-factory-bug/`

---

## Task 1: Save Spec Documentation

Create `agent-os/specs/2026-02-01-default-factory-bug/` with:

- **plan.md** — This plan
- **shape.md** — Shaping notes and bug analysis
- **references.md** — Reference to auto.py bug location

---

## Task 2: Fix `_resolve_field_value()` in auto.py

**File**: `src/svcs_di/auto.py`

**Location**: Lines 570-573

**Current code**:
```python
if field_info.has_default:
    default_val = field_info.default_value
    if callable(default_val) and hasattr(default_val, "__self__"):
        return True, default_val()
    return True, default_val
```

**Problem**: The check `hasattr(default_val, "__self__")` is too restrictive. Built-in types like `list`, `dict`, `set` and lambda functions don't have `__self__`, so they're returned as-is instead of being called.

**Fix**: Remove the `__self__` check - all `default_factory` values are meant to be called:
```python
if field_info.has_default:
    default_val = field_info.default_value
    if callable(default_val):
        return True, default_val()
    return True, default_val
```

---

## Task 3: Fix `_resolve_field_value_async()` in auto.py

**File**: `src/svcs_di/auto.py`

**Location**: Lines 608-611

Apply the same fix to the async version.

---

## Task 4: Add Tests for default_factory Resolution

**File**: `tests/test_auto.py`

Add tests that verify:
1. `field(default_factory=list)` creates `[]` not `<class 'list'>`
2. `field(default_factory=dict)` creates `{}` not `<class 'dict'>`
3. `field(default_factory=lambda: [1, 2, 3])` creates `[1, 2, 3]`
4. Each call creates a new instance (not shared)

---

## Task 5: Add Integration Test with Injector

**File**: `tests/test_auto.py` or new file

Test end-to-end that a dataclass with `default_factory` works through the full DI container resolution path.

---

## Verification

1. Run tests: `uv run pytest tests/test_auto.py -v -k factory`
2. Run all tests: `uv run pytest`
3. Type check: `uv run ty check src/`

---

## Key Files

| File | Change |
|------|--------|
| `src/svcs_di/auto.py` | Fix `_resolve_field_value()` and `_resolve_field_value_async()` |
| `tests/test_auto.py` | Add tests for default_factory resolution |

## Root Cause Analysis

The bug is in the check `callable(default_val) and hasattr(default_val, "__self__")`:

- `list`, `dict`, `set` are callable but don't have `__self__`
- Lambda functions are callable but don't have `__self__`
- Only bound methods have `__self__`

The original code comment says "Call default_factory if it's a callable (bound method from dataclass field)" - but this is incorrect. All `default_factory` values (types, lambdas, functions) should be called, not just bound methods.
