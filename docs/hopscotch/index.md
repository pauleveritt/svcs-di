# Hopscotch Injection

The `HopscotchInjector` extends dependency injection with resource-based and location-based resolution. This allows
multiple implementations of the same service type, with the correct one selected based on context.

## Why?

Imagine a broad ecosystem of quality, cross-framework web themes, components, and tooling. A site might want to replace
just one component. Or replace, but only in parts of the site.

The HopscotchInjector lets you register callables that replace/augment previous registrations.

## Features

### ServiceLocator

A thread-safe, immutable registry for multiple service implementations:

- **Multiple implementations per type**: Register several implementations for the same service type
- **LIFO ordering**: Later registrations override earlier ones (useful for layered configurations)
- **Immutable updates**: Each `register()` call returns a new locator instance
- **Performance optimized**: O(1) fast path for single-implementation types, O(m) scoring for multiple implementations
- **LRU caching**: Resolution results are cached for performance

### Resource-Based Resolution

Select implementations based on business context types:

- **Exact match**: `Customer` matches registrations for `Customer`
- **Subclass match**: `Manager(Employee)` matches `Employee` registrations
- **Default fallback**: No resource matches registrations without a resource constraint
- **Three-tier precedence**: exact (100 points) > subclass (10 points) > default (0 points)

#### Container API for Resources

Pass resource instances directly to `HopscotchContainer`:

```python
# Pass resource instance to container
container = HopscotchContainer(registry, resource=Employee())
service = container.inject(WelcomeService)  # Uses Employee for matching
```

The container automatically derives `type(resource)` for ServiceLocator matching.

#### Injecting Resources with Resource[T]

Services can access the current resource via `Resource[T]`:

```python
from svcs_di import Resource

@dataclass
class AuditService:
    employee: Resource[Employee]  # Gets container.resource, typed as Employee
```

This separates concerns from `Inject[T]`:
- `Inject[T]` = "resolve service of type T from registry"
- `Resource[T]` = "give me the current resource, typed as T"

The type parameter is for static type checking only - at runtime, the injector returns `container.resource`.

### Location-Based Resolution

Select implementations based on hierarchical URL-like paths:

- **Path matching**: `/admin` matches registrations at `/admin`
- **Hierarchical fallback**: `/admin/users/profile` walks up to `/admin/users`, then `/admin`, then `/`
- **Location as service**: Inject `Location` to access the current request path
- **Combined matching**: Use both resource and location for fine-grained control

#### Container API for Locations

Pass location directly to `HopscotchContainer`:

```python
from pathlib import PurePath

# New API: pass location to container
container = HopscotchContainer(registry, location=PurePath("/admin"))
service = container.inject(PageRenderer)  # Uses /admin for location matching
```

The container automatically registers the location for both injection and ServiceLocator matching.

#### Combined Resource and Location

Use both for fine-grained context:

```python
container = HopscotchContainer(
    registry,
    resource=Employee(),
    location=PurePath("/admin")
)
service = container.inject(WelcomeService)
```

### Three-Tier Value Precedence

When resolving `Inject[T]` fields, HopscotchInjector uses:

1. **kwargs** (highest priority): Values passed directly to the injector
2. **ServiceLocator/Container**: Locator for multi-implementation types, fallback to `container.get()`
3. **Default values** (lowest priority): Field defaults from class definitions

### Auto-Discovery with Scanning

Use decorators for declarative service registration:

- **`@injectable`**: Mark a class for auto-discovery
- **`@injectable(resource=...)`**: Register with a resource context
- **`@injectable(location=...)`**: Register at a specific location
- **`@injectable(for_=...)`**: Register as an implementation of a protocol/base class
- **`scan(registry)`**: Discover and register all decorated classes

### Async Support

Full async support via `HopscotchAsyncInjector`:

- Uses `container.aget()` and `container.aget_abstract()` for async resolution
- Same three-tier precedence as sync version
- Properly awaits async callables

## Use Cases

The HopscotchInjector pattern is useful when:

- Different user contexts need different service implementations (e.g., customer vs employee greetings)
- URL paths should influence which services are used (e.g., admin vs public pages)
- You want to override services at specific locations in a hierarchy
- You need LIFO (last-in-first-out) override behavior for layered configurations

## Examples

```{toctree}
:maxdepth: 2
:hidden:

getting_started
manual_locator
resource_resolution
location_resolution
protocols
scanning
```
