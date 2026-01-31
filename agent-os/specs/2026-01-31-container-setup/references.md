# References: Container Setup Functions

## Key Source Files

### scanning.py Patterns

**File**: `src/svcs_di/injectors/scanning.py`

Key patterns to follow:

1. **Helper function pattern**: `_extract_decorated_items(module)` extracts items from modules
2. **Type checking pattern**: `_is_hopscotch_registry(registry)` checks registry type by name
3. **Module iteration**: Uses `dir(module)` and `getattr()` to inspect module contents
4. **Package resolution**: `_resolve_packages_to_modules()` handles string/ModuleType/None

### hopscotch_registry.py Patterns

**File**: `src/svcs_di/hopscotch_registry.py`

Key patterns to follow:

1. **attrs field with factory**: `_locator: ServiceLocator = attrs.field(factory=ServiceLocator, init=False)`
2. **Read-only property**: `@property def locator(self)` exposes internal state
3. **Post-init hook**: `__attrs_post_init__` for initialization after attrs creates instance

## Test Patterns

### test_scanning.py

**File**: `tests/injectors/test_scanning.py`

Key patterns:

1. **Test fixtures path setup**: Adds test_fixtures to sys.path
2. **Test class organization**: Groups related tests in classes
3. **locals_dict pattern**: Tests use `scan(registry, locals_dict=locals())`

### test_hopscotch_registry.py

**File**: `tests/test_hopscotch_registry.py`

Key patterns:

1. **Shared fixtures at module level**: Common dataclasses defined once
2. **Task group comments**: Organize tests by feature area
3. **Descriptive test names**: `test_<what>_<expected_behavior>`

## Test Fixtures

### scanning_test_package Structure

```
tests/test_fixtures/scanning_test_package/
├── __init__.py
├── service_a.py          # Simple @injectable classes
├── service_b.py          # @injectable with resource
├── no_decorators.py      # Empty module
└── nested/
    ├── __init__.py
    └── nested_service.py
```

New fixtures needed:

```
tests/test_fixtures/scanning_test_package/
├── with_setup_funcs/
│   └── __init__.py       # Has both svcs_registry and svcs_container
├── with_registry_only/
│   └── __init__.py       # Has only svcs_registry
└── with_container_only/
    └── __init__.py       # Has only svcs_container
```

## Documentation Patterns

### docs/scanning/index.md

Key patterns:

1. **Why section first**: Explains motivation
2. **Code examples**: Show before/after
3. **toctree at bottom**: Links to sub-pages
