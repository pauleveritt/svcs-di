# Raw Idea: Hopscotch Registry

## Spec Information
- **Spec Number**: #15
- **Spec Name**: Hopscotch Registry
- **Date Created**: 2026-01-10
- **Plan Document**: `docs/hopscotch_registry_plan.md`

## Feature Description

Create `HopscotchRegistry` and `HopscotchContainer` to make it easy to:
1. Register service variations (multiple implementations with resource/location)
2. Resolve services with automatic locator support
3. Integrate seamlessly with the `scan()` function

## Design Decisions Already Made

1. **Keep get() as-is**: HopscotchContainer inherits standard `get()` from svcs.Container; `inject()` is the new method for locator-aware resolution
2. **Use inherited methods**: For simple services, use `registry.register_factory()` and `registry.register_value()` - no extra convenience methods needed
3. **Auto-detect in scan()**: `scan()` detects if registry is HopscotchRegistry and automatically uses its internal locator

## Key Goals

- Make it easy to register service variations with different implementations
- Support resource and location-based service resolution
- Provide automatic locator support in the registry
- Integrate seamlessly with existing `scan()` function
- Follow the `InjectorContainer` pattern for consistency

## References

- Full plan document: `docs/hopscotch_registry_plan.md`
- Related feature: Service Locator (already implemented)
- Pattern to follow: InjectorContainer implementation
