# Plan: Container Setup Functions

## Summary

Add convention-based setup functions (`svcs_registry` and `svcs_container`) discovered during `scan()` to enable registry-time and container-time configuration by packages.

## Spec Folder

`agent-os/specs/2026-01-31-container-setup/`

---

## Task 1: Save Spec Documentation

Create `agent-os/specs/2026-01-31-container-setup/` with:

- **plan.md** — This plan
- **shape.md** — Shaping notes and decisions
- **references.md** — Reference to scanning.py patterns

---

## Task 2: Add Storage to HopscotchRegistry

**File**: `src/svcs_di/hopscotch_registry.py`

Add `_container_setup_funcs` attribute and property:

```python
_container_setup_funcs: list[Callable[[Any], None]] = attrs.field(
    factory=list, init=False
)

@property
def container_setup_funcs(self) -> list[Callable[[Any], None]]:
    """Read-only access to container setup functions."""
    return self._container_setup_funcs
```

---

## Task 3: Implement Discovery in scanning.py

**File**: `src/svcs_di/injectors/scanning.py`

1. Add constants for convention function names
2. Add `_extract_convention_functions(module)` helper
3. Modify `scan()` to:
   - Discover `svcs_registry` and `svcs_container` functions
   - Call `svcs_registry(registry)` immediately during scan
   - Store `svcs_container` functions in `registry._container_setup_funcs`
   - Raise `TypeError` if functions found with plain `svcs.Registry`

---

## Task 4: Invoke Setup in HopscotchContainer

**File**: `src/svcs_di/hopscotch_registry.py`

Update `__attrs_post_init__` to call stored container setup functions:

```python
def __attrs_post_init__(self) -> None:
    # ... existing location registration ...

    # Invoke container setup functions if registry is HopscotchRegistry
    if hasattr(self.registry, 'container_setup_funcs'):
        for setup_func in self.registry.container_setup_funcs:
            setup_func(self)
```

---

## Task 5: Create Test Fixtures

**Files**:
- `tests/test_fixtures/scanning_test_package/with_setup_funcs/__init__.py`
- `tests/test_fixtures/scanning_test_package/with_registry_only/__init__.py`
- `tests/test_fixtures/scanning_test_package/with_container_only/__init__.py`

Test packages with various combinations of convention functions.

---

## Task 6: Write Tests

**Files**:
- `tests/injectors/test_scanning.py` — Add `TestContainerSetupFunctions` class
- `tests/test_hopscotch_registry.py` — Add integration tests

Test cases:
1. `svcs_registry` called during scan
2. `svcs_container` stored and called on container creation
3. Each container gets its own setup call
4. TypeError with plain svcs.Registry
5. Package order determines priority
6. Both @injectable and setup functions work together

---

## Task 7: Add Example

**File**: `examples/scanning/setup_functions.py`

Demonstrate convention functions for registry and container setup.

---

## Task 8: Update Documentation

**File**: `docs/scanning/index.md` (or create new doc)

Document:
- `svcs_registry(registry)` convention
- `svcs_container(container)` convention
- Package order priority
- HopscotchRegistry requirement

---

## Verification

1. Run tests: `uv run pytest tests/injectors/test_scanning.py -v -k setup`
2. Run all tests: `uv run pytest`
3. Type check: `uv run ty check src/`
4. Run example: `uv run python examples/scanning/setup_functions.py`

---

## Key Design Decisions

1. **Convention over configuration** — Functions named `svcs_registry` and `svcs_container` are discovered automatically
2. **Integrated with scan()** — No new APIs, extends existing scanning mechanism
3. **Order = priority** — Later packages in `scan()` override earlier ones
4. **HopscotchRegistry required** — Error if convention functions found with plain svcs.Registry
5. **Per-container invocation** — `svcs_container` called for each new container instance

## Files to Modify

| File | Change |
|------|--------|
| `src/svcs_di/hopscotch_registry.py` | Add `_container_setup_funcs`, update `__attrs_post_init__` |
| `src/svcs_di/injectors/scanning.py` | Add convention function discovery |
| `tests/injectors/test_scanning.py` | Add setup function tests |
| `tests/test_hopscotch_registry.py` | Add integration tests |
| `tests/test_fixtures/scanning_test_package/...` | New test fixture packages |
| `examples/scanning/setup_functions.py` | New example |
| `docs/scanning/index.md` | Documentation |
