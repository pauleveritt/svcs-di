# Specification: InjectorContainer

## Goal

Implement an `InjectorContainer` class that extends `svcs.Container` to provide dependency injection capabilities by
integrating an injector into the container's `get()` and `aget()` methods, enabling kwargs support for service
resolution.

## User Stories

- As a developer, I want to use a container that supports kwargs when resolving services so that I can override injected
  dependencies at resolution time
- As a developer, I want a drop-in replacement for `svcs.Container` that automatically uses `KeywordInjector` for
  dependency resolution

## Specific Requirements

**InjectorContainer Class Definition**

- Subclass `svcs.Container` using attrs style (`@attrs.define`) to match svcs.Container's implementation pattern
- Add `injector` attribute with type `Injector` and default value `KeywordInjector`
- The injector must be initialized with the container instance (self) when used
- File location: `src/svcs_di/injector_container.py`

**Constructor Signature**

- Accept `registry: Registry` as first positional argument (inherited from svcs.Container)
- Accept `injector: type[Injector] = KeywordInjector` as keyword-only argument
- Store the injector class/factory, not an instance, since the container needs to pass itself during resolution
- Example: `InjectorContainer(registry, injector=KeywordInjector)`

**get() Method Implementation**

- Override `svcs.Container.get(*svc_types)` to accept `**kwargs`
- Signature: `get(self, svc_type: type, /, *svc_types: type, **kwargs: Any) -> object`

> **Note on `/` and `*` separators:** The signature uses Python's positional-only (`/`) and keyword-only (`*`) parameter
> separators. The `/` after `svc_type` ensures the first service type is positional-only, while `*svc_types` collects
> additional positional arguments. The `**kwargs` are keyword-only by nature. This allows clear separation between
> service types (positional) and injection overrides (keyword).
- If kwargs provided with additional service types (len(svc_types) > 0): raise `ValueError`
- If kwargs provided but no injector configured: raise `ValueError`
- If single service type with kwargs: use `self.injector(container=self)(svc_type, **kwargs)`
- If no kwargs: delegate to `super().get(svc_type, *svc_types)` for standard svcs behavior

**aget() Method Implementation**

- Override `svcs.Container.aget(*svc_types)` to accept `**kwargs`
- Signature: `async aget(self, svc_type: type, /, *svc_types: type, **kwargs: Any) -> object`
- Same `/` and `*` separator pattern as `get()` for consistency
- Follow same pattern as `get()` but use async injector (`KeywordAsyncInjector` by default)
- If kwargs provided with additional service types (len(svc_types) > 0): raise `ValueError`
- If kwargs provided but no injector configured: raise `ValueError`
- If single service type with kwargs: await the async injector call: `await self.async_injector(container=self)(svc_type, **kwargs)`
- If no kwargs: delegate to `await super().aget(svc_type, *svc_types)` for standard svcs behavior

**Error Handling Strategy**

- Raise `ValueError("Cannot pass kwargs when requesting multiple service types")` when kwargs + additional types (svc_types > 0)
- Raise `ValueError("Cannot pass kwargs without an injector configured")` when kwargs + no injector
- Duck typing for kwargs validation: let Python's natural type errors surface during construction
- Let injector's own validation (e.g., unknown kwargs) propagate naturally

**Type Annotations**

- Use standard Python `*args`/`**kwargs` notation
- Return type should match svcs.Container patterns (single value or tuple)
- Use generics where possible for type safety

## Visual Design

N/A - No visual assets provided.

## Existing Code to Leverage

**svcs.Container (external package)**

- Base class using `@attrs.define` decorator
- Provides `get(*svc_types)` and `aget(*svc_types)` methods that resolve services from registry
- Uses `_instantiated` dict for caching, `_on_close` list for cleanup tracking
- Context manager support with `close()` and `aclose()` methods

**KeywordInjector from `src/svcs_di/injectors/keyword.py`**

- Default sync injector implementation with three-tier precedence (kwargs > container > defaults)
- Constructor takes `container: svcs.Container`
- `__call__(target, **kwargs)` interface for injection
- Validates unknown kwargs via `validate_kwargs()` helper

**KeywordAsyncInjector from `src/svcs_di/injectors/keyword.py`**

- Async version of KeywordInjector with same interface
- Uses `container.aget()` and `container.aget_abstract()` for async resolution
- `async __call__(target, **kwargs)` interface

**Injector Protocol from `src/svcs_di/auto.py`**

- Protocol defining `__call__[T](target: InjectionTarget[T], **kwargs: Any) -> T`
- AsyncInjector protocol for async variant
- Use these for type hints on the injector parameter

## Out of Scope

- Type validation of kwargs values (use duck typing approach)
- New injector implementations beyond using existing KeywordInjector/KeywordAsyncInjector
- Changes to existing injector classes
- Framework-specific integrations (FastAPI, Flask, etc.)
- Documentation beyond docstrings
- Custom injector registration patterns (use existing Injector protocol)
- Modifying svcs.Container's caching behavior
- Adding new cleanup/lifecycle hooks
- Support for kwargs with multiple service type requests
