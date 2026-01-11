# Specification: Hopscotch Registry

## Goal

Create `HopscotchRegistry` and `HopscotchContainer` classes that provide pre-wired integration between svcs registry/container and ServiceLocator for multi-implementation service resolution with minimal setup.

## Derived From InjectorContainer

**HopscotchContainer is derived from the InjectorContainer pattern** and inherits the same API signature:

```python
container.inject(ServiceType, **kwargs) -> T
container.ainject(ServiceType, **kwargs) -> T
```

This ensures consistency across the library - users familiar with `InjectorContainer` will immediately understand `HopscotchContainer`. The key difference is that HopscotchContainer defaults to `HopscotchInjector` (instead of `KeywordInjector`) to enable ServiceLocator-based multi-implementation resolution with resource and location context.

## User Stories

- As a developer, I want to use a pre-configured registry that automatically manages a ServiceLocator so that I do not need to manually wire up locator registrations
- As a developer, I want a container that resolves services through the locator using context (resource/location) from the container itself so that I get automatic multi-implementation resolution

## Specific Requirements

**HopscotchRegistry extends svcs.Registry**
- Use `@attrs.define` to subclass svcs.Registry (same pattern as InjectorContainer)
- Add internal `_locator: ServiceLocator` field with `attrs.field(factory=ServiceLocator, init=False)`
- Expose `locator` property for read-only access to internal ServiceLocator
- Inherit all standard svcs.Registry methods (register_factory, register_value, etc.) unchanged
- The internal locator is auto-registered as a value service when first implementation is registered

**register_implementation() method**
- Signature: `register_implementation(service_type: type, implementation: type, *, resource: type | None = None, location: PurePath | None = None) -> None`
- Registers the implementation to the internal ServiceLocator
- Updates `_locator` immutably (locator.register returns new instance)
- Re-registers updated locator as value service: `self.register_value(ServiceLocator, self._locator)`
- No return value (mutates internal state, unlike ServiceLocator.register)

**HopscotchContainer extends svcs.Container**
- Use `@attrs.define` to subclass svcs.Container (same pattern as InjectorContainer)
- Add `injector` field defaulting to `HopscotchInjector`
- Add `async_injector` field defaulting to `HopscotchAsyncInjector`
- NO `resource` attribute on HopscotchContainer - resolved dynamically at inject() time
- Inherit all standard svcs.Container methods (get, aget, get_abstract, etc.) unchanged

**inject() method - dynamic resource resolution**
- Signature: `inject[T](svc_type: type[T], /, **kwargs) -> T`
- Resolve resource type dynamically from container by looking for a registered resource type
- Pass dynamically-resolved resource to the injector: `self.injector(container=self, resource=resolved_resource)`
- No per-call resource overrides - resource comes from container state
- Raise `ValueError` if no injector configured

**ainject() method - async dynamic resource resolution**
- Signature: `async ainject[T](svc_type: type[T], /, **kwargs) -> T`
- Same dynamic resource resolution pattern as inject() but async
- Use `aget()` for async container lookups
- Pass resolved resource to async_injector

**scan() auto-detection of HopscotchRegistry**
- Modify `_get_or_create_locator()` to detect HopscotchRegistry and return its internal locator
- Modify `_register_decorated_items()` to use `registry.register_implementation()` when registry is HopscotchRegistry
- For HopscotchRegistry: call `registry.register_implementation()` directly instead of creating new locator
- For standard registry: keep existing behavior (create locator, register as value)
- Simple registrations (no resource/location/for_) still go directly to registry.register_factory()

**Module exports**
- Add HopscotchRegistry to `src/svcs_di/__init__.py` exports
- Add HopscotchContainer to `src/svcs_di/__init__.py` exports
- Update `__all__` list to include both new classes

## Existing Code to Leverage

**src/svcs_di/injector_container.py - InjectorContainer pattern**
- Follow exact same `@attrs.define` subclassing pattern for both new classes
- Copy field definition style: `attrs.field(default=..., kw_only=True)`
- Match docstring style and examples format
- Use same error handling pattern for missing injector

**src/svcs_di/injectors/hopscotch.py - HopscotchInjector**
- Already implements resource-based resolution via `_get_resource()` and `_get_location()`
- Container passes `resource` parameter to injector constructor
- No changes needed to HopscotchInjector itself

**src/svcs_di/injectors/locator.py - ServiceLocator**
- Immutable registration pattern: `locator = locator.register(...)` returns new instance
- `get_implementation()` for resolving with resource/location
- Thread-safe frozen dataclass pattern

**src/svcs_di/injectors/scanning.py - scan() function**
- `_get_or_create_locator()` is the integration point for HopscotchRegistry detection
- `_register_decorated_items()` handles locator vs direct registration logic
- Keep the existing simple registration path for classes without resource/location/for_

## Out of Scope

- Do NOT add a `resource` attribute to HopscotchContainer (resolved dynamically from container)
- Do NOT support per-call resource overrides in inject() - resource comes from container
- Do NOT modify HopscotchInjector or HopscotchAsyncInjector
- Do NOT modify ServiceLocator
- Do NOT create convenience methods for register_factory/register_value on HopscotchRegistry
- Do NOT refactor existing examples to use HopscotchRegistry/HopscotchContainer (separate task)
- Do NOT update README.md (separate follow-up task)
- Do NOT change the existing scan() behavior for standard svcs.Registry
- Do NOT add location parameter to inject/ainject methods
- Do NOT add async versions of register_implementation
