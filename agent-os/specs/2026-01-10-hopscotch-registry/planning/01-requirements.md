# Requirements Decisions: Hopscotch Registry (Spec #15)

## Overview

These decisions were made during requirements clarification for the Hopscotch Registry spec.

## Derived From InjectorContainer

**HopscotchContainer is derived from the InjectorContainer pattern** and inherits the same API signature:

```python
container.inject(ServiceType, **kwargs) -> T
container.ainject(ServiceType, **kwargs) -> T
```

The key difference is that HopscotchContainer defaults to `HopscotchInjector` (instead of `KeywordInjector`) to enable ServiceLocator-based multi-implementation resolution.

## Key Design Decisions

### 1. Auto-Detection of HopscotchRegistry

HopscotchContainer should auto-detect HopscotchRegistry and use its internal locator automatically.

### 2. Resource Handling (DESIGN CHANGE)

**Important architectural change from original plan:**

- **Original design:** `resource: type | None` as an attribute on HopscotchContainer
- **New design:** Resource should NOT be an attribute on HopscotchContainer

Instead, resource is resolved dynamically from the container as a service at `inject()` time (similar to how `HopscotchInjector._get_resource()` works).

### 3. scan() Behavior

- Simple registrations (no resource/location) go directly to the registry
- Items with resource/location/for_ go to ServiceLocator via `register_implementation()`

### 4. Scope Boundaries

Refactoring examples and updating README is a SEPARATE follow-up task, NOT part of this spec.

### 5. inject() Resource Resolution

No per-call resource overrides - rely on resource being resolved from container at inject() time.
