# Plan: HopscotchRegistry and HopscotchContainer

## Goal

Create `HopscotchRegistry` and `HopscotchContainer` to make it easy to:

1. Register service variations (multiple implementations with resource/location)
2. Resolve services with automatic locator support
3. Integrate seamlessly with the `scan()` function

## Design Decisions

1. **Keep get() as-is**: HopscotchContainer inherits standard `get()` from svcs.Container; `inject()` is the new method
   for locator-aware resolution
2. **Use inherited methods**: For simple services, use `registry.register_factory()` and `registry.register_value()` -
   no extra convenience methods needed
3. **Auto-detect in scan()**: `scan()` detects if registry is HopscotchRegistry and automatically uses its internal
   locator

## Design Overview

Follow the `InjectorContainer` pattern:

- Use `@attrs.define` for clean subclassing
- Extend svcs classes with new methods
- Default to Hopscotch injectors

## New Files

### 1. `src/svcs_di/hopscotch_registry.py`

```python
@attrs.define
class HopscotchRegistry(svcs.Registry):
    """Registry with integrated ServiceLocator for multi-implementation support."""

    _locator: ServiceLocator = attrs.field(factory=ServiceLocator, init=False)

    def register_implementation(
            self,
            service_type: type,
            implementation: type,
            *,
            resource: type | None = None,
            location: PurePath | None = None,
    ) -> None:
        """Register an implementation with optional resource/location."""
        self._locator = self._locator.register(
            service_type, implementation, resource=resource, location=location
        )
        # Auto-register the locator as a service
        self.register_value(ServiceLocator, self._locator)

    @property
    def locator(self) -> ServiceLocator:
        """Access the internal ServiceLocator."""
        return self._locator
```

Key features:

- Internal `ServiceLocator` managed automatically
- `register_implementation()` convenience method
- Locator auto-registered as value service
- Compatible with existing `svcs.Registry` methods

### 2. `src/svcs_di/hopscotch_container.py`

```python
@attrs.define
class HopscotchContainer(svcs.Container):
    """Container with HopscotchInjector for multi-implementation resolution."""

    injector: type[Injector] | None = attrs.field(default=HopscotchInjector, kw_only=True)
    async_injector: type[AsyncInjector] | None = attrs.field(default=HopscotchAsyncInjector, kw_only=True)
    resource: type | None = attrs.field(default=None, kw_only=True)

    def inject[T](self, svc_type: type[T], /, **kwargs: Any) -> T:
        """Resolve service with locator and kwargs support."""
        if self.injector is None:
            raise ValueError("Cannot inject without an injector configured")
        return self.injector(container=self, resource=self.resource)(svc_type, **kwargs)

    async def ainject[T](self, svc_type: type[T], /, **kwargs: Any) -> T:
        """Async resolve service with locator and kwargs support."""
        if self.async_injector is None:
            raise ValueError("Cannot inject without an async injector configured")
        return await self.async_injector(container=self, resource=self.resource)(svc_type, **kwargs)
```

Key features:

- Defaults to `HopscotchInjector` and `HopscotchAsyncInjector`
- Passes `resource` to injector for context-based resolution
- Same `inject()`/`ainject()` API as `InjectorContainer`

### 3. Update `src/svcs_di/injectors/scanning.py`

Enhance `scan()` to work better with `HopscotchRegistry`:

```python
def scan(
        registry: svcs.Registry,
        *packages: str | ModuleType | None,
        locals_dict: dict[str, Any] | None = None,
) -> svcs.Registry:
    """
    Scan packages for @injectable decorated classes.

    If registry is a HopscotchRegistry, uses its internal locator directly.
    Otherwise creates a ServiceLocator and registers it as a value service.
    """
    # Auto-detect HopscotchRegistry
    if isinstance(registry, HopscotchRegistry):
        # Use registry's register_implementation() which updates internal locator
        for item, metadata in decorated_items:
            registry.register_implementation(
                service_type, item,
                resource=metadata.get('resource'),
                location=metadata.get('location')
            )
    else:
        # Existing behavior: create locator, register as value
        locator = ServiceLocator()
        # ... existing registration logic
        registry.register_value(ServiceLocator, locator)
```

**Key benefit**: Users can pre-configure a `HopscotchRegistry` and `scan()` will add to its existing locator rather than
creating a new one.

## Implementation Tasks

### Task Group 1: HopscotchRegistry

1.1. Write tests for HopscotchRegistry class structure
1.2. Create `src/svcs_di/hopscotch_registry.py`
1.3. Implement `register_implementation()` method
1.4. Add property access to internal locator
1.5. Run tests, verify attrs subclassing works

### Task Group 2: HopscotchContainer

2.1. Write tests for HopscotchContainer (follow InjectorContainer test pattern)
2.2. Create `src/svcs_di/hopscotch_container.py`
2.3. Implement `inject()` and `ainject()` methods
2.4. Ensure resource parameter is passed to injector
2.5. Run tests

### Task Group 3: Scanner Integration

3.1. Write tests for scan() with HopscotchRegistry
3.2. Update scan() to detect HopscotchRegistry
3.3. Use registry's internal locator when available
3.4. Run tests

### Task Group 4: Module Exports

4.1. Update `src/svcs_di/__init__.py` to export new classes
4.2. Add integration tests
4.3. Run full test suite

## Files to Modify/Create

| File                                 | Action |
|--------------------------------------|--------|
| `src/svcs_di/hopscotch_registry.py`  | Create |
| `src/svcs_di/hopscotch_container.py` | Create |
| `src/svcs_di/injectors/scanning.py`  | Modify |
| `src/svcs_di/__init__.py`            | Modify |
| `tests/test_hopscotch_registry.py`   | Create |
| `tests/test_hopscotch_container.py`  | Create |

## Usage Example

```python
from svcs_di import HopscotchRegistry, HopscotchContainer, Inject
from pathlib import PurePath

# Setup registry with multi-implementation support
registry = HopscotchRegistry()

# Register implementations with resource/location
registry.register_implementation(Greeting, DefaultGreeting)
registry.register_implementation(Greeting, CustomerGreeting, resource=CustomerContext)
registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))

# Or use scanning
scan(registry, "myapp.services")  # Works seamlessly

# Create container with resource context
registry.register_value(RequestContext, CustomerContext())
container = HopscotchContainer(registry, resource=RequestContext)

# Resolve with automatic locator support
service = container.inject(WelcomeService)
# service.greeting is CustomerGreeting (matched by resource)
```

## Extra Work

- Refactor `examples/hopscotch` to keep a couple of current manual examples but switch `getting_started` and others to
  use these additions
- Change the `README.md` to use the pre-wired registry and container

## Verification

1. Run `uv run pytest tests/test_hopscotch_registry.py -v`
2. Run `uv run pytest tests/test_hopscotch_container.py -v`
3. Run `uv run ruff check src/ tests/`
4. Run `uv run ty check src/`
5. Test example: `uv run python examples/hopscotch/multiple_implementations.py`
