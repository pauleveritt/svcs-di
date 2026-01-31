# Standards: Inject in Post Init

## Applicable Skills

This implementation follows these project standards:

### Python Development
- **File:** `agent-os/skills/python.md`
- **Key points:**
  - Python 3.14+ features
  - Modern type hinting with `type` statements
  - Frozen dataclasses with `kw_only=True`
  - `TypeGuard` for type narrowing
  - Keyword-only arguments

### Services with svcs
- **File:** `agent-os/skills/svcs.md`
- **Key points:**
  - `Inject[T]` marker for dependencies
  - `auto()` factory for registration
  - `__post_init__` with `InitVar` and `field(init=False)` pattern
  - Protocol-based injection

### Testing
- **File:** `agent-os/skills/testing/testing.md`
- **Key points:**
  - Test functions, not classes
  - Run via `uv run pytest`
  - Fakes over mocks
  - 100% coverage target

### Documentation
- **File:** `agent-os/skills/documentation.md`
- **Key points:**
  - Sphinx with MyST
  - Docstrings for public APIs
  - Examples in docs

### T-Strings
- **File:** `agent-os/skills/t-strings.md`
- **Note:** Not directly applicable to this feature, but included for completeness

## Code Style Requirements

1. **Type hints:** All functions fully typed
2. **Docstrings:** All public functions have docstrings
3. **Imports:** Module-level, absolute paths
4. **Tests:** Function-based, descriptive names
5. **Dataclasses:** `frozen=True`, `kw_only=True` where appropriate

## Quality Gates

- `just check` passes (ruff lint/format, ty type check)
- `just test` passes (all tests including new ones)
- Coverage remains at 100%
