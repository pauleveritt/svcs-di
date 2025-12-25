# Multiple Service Implementations

This guide demonstrates how to register and resolve multiple implementations for the same service type using **ServiceLocator** and **HopscotchInjector**.

## Overview

The multiple implementations feature enables:

- **Multiple implementations per service type** - Register different implementations of the same protocol/interface
- **Context-based resolution** - Select implementations based on request context
- **Three-tier precedence** - Exact context > Subclass context > Default
- **LIFO ordering** - Later registrations override earlier ones
- **Seamless integration** - Works with `Injectable[T]` pattern
- **Dynamic context** - Context obtained from container at runtime

## Core Components

### ServiceLocator

Tracks multiple implementations across all service types.

**Example:** See [Quick Start](#quick-start) section below for complete registration example.

### HopscotchInjector

Injectable field resolution with locator support.

**Example:** See [Quick Start](#quick-start) section below for complete usage example.

## Quick Start

### 1. Define Service Protocol

```python
from dataclasses import dataclass

class Greeting:
    """Service protocol."""
    salutation: str

    def greet(self, name: str) -> str:
        return f"{self.salutation}, {name}!"
```

### 2. Create Implementations

```python
@dataclass
class DefaultGreeting(Greeting):
    salutation: str = "Hello"

@dataclass
class EmployeeGreeting(Greeting):
    salutation: str = "Hey"

@dataclass
class CustomerGreeting(Greeting):
    salutation: str = "Good Day"
```

### 3. Define Contexts

```python
class RequestContext:
    """Base context."""
    pass

class EmployeeContext(RequestContext):
    """Context for employee requests."""
    pass

class CustomerContext(RequestContext):
    """Context for customer requests."""
    pass
```

### 4. Register Implementations

```python
import svcs
from svcs_di.injectors.locator import ServiceLocator

registry = svcs.Registry()
locator = ServiceLocator()

# Register multiple implementations
locator.register(Greeting, DefaultGreeting)  # Default (no context)
locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
locator.register(Greeting, CustomerGreeting, context=CustomerContext)

# Register locator as a service
registry.register_value(ServiceLocator, locator)
```

### 5. Use Injectable Fields

```python
from dataclasses import dataclass
from svcs_di.auto import Injectable
from svcs_di.injectors.locator import HopscotchInjector

@dataclass
class WelcomeService:
    greeting: Injectable[Greeting]

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)

# Setup container with context
registry.register_value(RequestContext, EmployeeContext())
container = svcs.Container(registry)

# Create injector and resolve
injector = HopscotchInjector(container=container, context_key=RequestContext)
service = injector(WelcomeService)

print(service.welcome("Alice"))  # "Hey, Alice!" (uses EmployeeGreeting)
```

## Three-Tier Precedence

The resolution algorithm uses three precedence tiers:

### Tier 1: Exact Context Match (Highest)

```python
# Exact match: this_context is context_class
registry.register_value(RequestContext, EmployeeContext())
# Resolves to: EmployeeGreeting (exact match)
```

### Tier 2: Subclass Context Match (Medium)

```python
class AdminContext(EmployeeContext):
    """Admin inherits from Employee."""
    pass

# Subclass match: issubclass(AdminContext, EmployeeContext)
registry.register_value(RequestContext, AdminContext())
# Resolves to: EmployeeGreeting (subclass match)
```

### Tier 3: No Context/Default (Lowest)

```python
# No context key configured
injector = HopscotchInjector(container=container)  # No context_key
# Resolves to: DefaultGreeting (default fallback)
```

## LIFO Ordering

Later registrations override earlier ones - the example below is conceptual (see `examples/multiple_implementations.py` for runnable code):

```text
locator = ServiceLocator()

# System-level default
locator.register(Greeting, DefaultGreeting)

# Site-level override (inserted at position 0)
locator.register(Greeting, SiteGreeting)

# Resolution: SiteGreeting wins (LIFO)
```

This allows:
- System-level defaults
- Application-level overrides
- Site/tenant-specific customization

## Kwargs Override

Kwargs have the highest precedence, overriding locator and container.  See `examples/multiple_implementations.py` for complete runnable example.

```text
injector = HopscotchInjector(container=container, context_key=RequestContext)

# Normal resolution via locator
service1 = injector(WelcomeService)

# Kwargs override everything
custom_greeting = CustomGreeting()
service2 = injector(WelcomeService, greeting=custom_greeting)
```

Precedence order:
1. **Kwargs** (highest) - Explicit overrides
2. **Locator** (medium) - Context-based selection
3. **Container** (medium) - Standard svcs resolution
4. **Defaults** (lowest) - Field default values

## Fallback Behavior

HopscotchInjector works with or without ServiceLocator:

```text
registry = svcs.Registry()

# Without ServiceLocator - uses standard container.get()
registry.register_value(Greeting, DefaultGreeting())

container = svcs.Container(registry)
injector = HopscotchInjector(container=container)

service = injector(WelcomeService)  # Works seamlessly
```

Resolution flow:
1. Try ServiceLocator if registered
2. Fall back to container.get() if no locator
3. Fall back to default values if not in container
4. Raise error if required field has no value

## Advanced Patterns

### Multiple Service Types

One ServiceLocator tracks all service types:

```text
locator = ServiceLocator()

# Register multiple service types
locator.register(Greeting, DefaultGreeting)
locator.register(Database, ProductionDB)
locator.register(Cache, RedisCache)

# Each service type resolved independently
```

### Async Support

Use HopscotchAsyncInjector for async dependencies:

```text
from svcs_di.injectors.locator import HopscotchAsyncInjector

injector = HopscotchAsyncInjector(
    container=container,
    context_key=RequestContext
)

service = await injector(AsyncService)
```

### Context Hierarchy

Use inheritance for context hierarchies:

```text
class RequestContext:
    pass

class AuthenticatedContext(RequestContext):
    pass

class AdminContext(AuthenticatedContext):
    pass

# AdminContext matches:
# 1. AdminContext (exact)
# 2. AuthenticatedContext (subclass)
# 3. RequestContext (subclass)
# 4. No context (default)
```

## Best Practices

### 1. Explicit Context Keys

Configure context_key explicitly:

```text
# ✅ Good - explicit
injector = HopscotchInjector(container=container, context_key=RequestContext)

# ⚠️ Works but less clear
injector = HopscotchInjector(container=container)  # No context resolution
```

### 2. Register Defaults First

Use LIFO ordering strategically:

```text
# ✅ Good - defaults first, overrides last
locator.register(Greeting, SystemDefault)
locator.register(Greeting, ApplicationOverride)
locator.register(Greeting, SiteOverride)  # Wins due to LIFO
```

### 3. Use Type-Only Registrations

Register type classes, not instances:

```text
# ✅ Good - types
locator.register(Greeting, DefaultGreeting)

# ⚠️ Works but less flexible
registry.register_value(Greeting, DefaultGreeting())
```

### 4. Validate Context Hierarchies

Ensure context inheritance makes sense:

```text
# ✅ Good - logical hierarchy
class AnonymousContext(RequestContext): pass
class AuthenticatedContext(RequestContext): pass
class AdminContext(AuthenticatedContext): pass

# ❌ Bad - confusing hierarchy
class CustomerContext(EmployeeContext): pass  # Customers aren't employees
```

## Common Use Cases

### Multi-Tenancy

Different implementations per tenant:

```text
class TenantAContext: pass
class TenantBContext: pass

locator.register(Database, PostgresDB)  # Default
locator.register(Database, TenantADB, context=TenantAContext)
locator.register(Database, TenantBDB, context=TenantBContext)
```

### Environment-Based

Different implementations per environment:

```text
class ProductionContext: pass
class StagingContext: pass
class DevelopmentContext: pass

locator.register(Cache, RedisCache, context=ProductionContext)
locator.register(Cache, MemcachedCache, context=StagingContext)
locator.register(Cache, InMemoryCache, context=DevelopmentContext)
```

### Role-Based

Different implementations per user role:

```text
class AnonymousContext: pass
class UserContext: pass
class AdminContext: pass

locator.register(Dashboard, PublicDashboard, context=AnonymousContext)
locator.register(Dashboard, UserDashboard, context=UserContext)
locator.register(Dashboard, AdminDashboard, context=AdminContext)
```

## Complete Example

See [`examples/multiple_implementations.py`](../../examples/multiple_implementations.py) for a complete working example demonstrating:

- Multiple implementations per service type
- Context-based resolution
- Three-tier precedence
- LIFO override behavior
- Kwargs override
- Fallback behavior

Run the example:

```bash
uv run python examples/multiple_implementations.py
```

## API Reference

### ServiceLocator

**`register(service_type: type, implementation: type, context: Optional[type] = None)`**

Register an implementation for a service type.

- `service_type`: The protocol/interface type
- `implementation`: The concrete implementation class
- `context`: Optional context type for resolution

**`get_implementation(service_type: type, request_context: Optional[type] = None) -> Optional[type]`**

Get the best matching implementation using three-tier precedence.

- `service_type`: The protocol/interface type to resolve
- `request_context`: Optional context type for matching
- Returns: Implementation class or None

### HopscotchInjector

**`__init__(container: svcs.Container, context_key: Optional[type] = None)`**

Create injector with optional context key.

- `container`: The svcs Container instance
- `context_key`: Optional type to get from container for context

**`__call__[T](target: type[T], **kwargs: Any) -> T`**

Inject dependencies and construct target instance.

- `target`: The class to instantiate
- `**kwargs`: Optional overrides (highest precedence)
- Returns: Instance of target with dependencies injected

### HopscotchAsyncInjector

Same as HopscotchInjector but async:

**`async __call__[T](target: type[T], **kwargs: Any) -> T`**

Async version using `aget()` and `aget_abstract()`.

## Comparison with Other Patterns

### vs. Factory Pattern

**ServiceLocator + HopscotchInjector:**
- ✅ Declarative registration
- ✅ Automatic dependency injection
- ✅ Three-tier precedence built-in
- ✅ LIFO override behavior

**Factory Pattern:**
- ⚠️ Manual factory implementation
- ⚠️ Explicit dependency passing
- ⚠️ Custom precedence logic needed

### vs. svcs Standard Pattern

**ServiceLocator + HopscotchInjector:**
- ✅ Multiple implementations per type
- ✅ Context-based selection
- ✅ Dynamic resolution

**svcs Standard:**
- ⚠️ One implementation per type
- ⚠️ Static registration
- ⚠️ Container-local overrides only

### vs. Original HopscotchRegistry

**Current Implementation (Simplified):**
- ✅ ~240 lines total
- ✅ Flat structure
- ✅ Type-only registration
- ✅ Clear semantics

**Original HopscotchRegistry:**
- ⚠️ ~400+ lines
- ⚠️ Nested storage
- ⚠️ Singleton vs class complexity
- ⚠️ inject_callable pattern

## Troubleshooting

### "No implementation found"

**Problem:** LookupError when resolving

**Solution:** Check registration and context:

```text
# Ensure implementation is registered
locator.register(Greeting, DefaultGreeting)

# Ensure locator is registered as service
registry.register_value(ServiceLocator, locator)

# Check context matches
print(f"Request context: {type(context_instance)}")
```

### Wrong implementation selected

**Problem:** Unexpected implementation returned

**Solution:** Check LIFO ordering and precedence:

```text
# Debug: print all registrations
for reg in locator.registrations:
    print(f"{reg.service_type.__name__}: {reg.implementation.__name__} (context={reg.context})")

# Check context type
context = container.get(RequestContext)
print(f"Context type: {type(context)}")
```

### Type errors with Injectable[T]

**Problem:** Type checker complaints

**Solution:** Ensure proper type hints:

```text
from svcs_di.auto import Injectable

@dataclass
class Service:
    # ✅ Good
    greeting: Injectable[Greeting]

    # ❌ Bad - missing Injectable
    greeting: Greeting
```

## Migration Guide

### From svcs Standard Pattern

**Before:**

```text
registry.register_value(Greeting, DefaultGreeting())
```

**After:**

```text
locator = ServiceLocator()
locator.register(Greeting, DefaultGreeting)
registry.register_value(ServiceLocator, locator)
```

### From Factory Pattern

**Before:**

```text
def greeting_factory(context):
    if isinstance(context, EmployeeContext):
        return EmployeeGreeting()
    return DefaultGreeting()

registry.register_factory(Greeting, greeting_factory)
```

**After:**

```text
locator = ServiceLocator()
locator.register(Greeting, DefaultGreeting)
locator.register(Greeting, EmployeeGreeting, context=EmployeeContext)
registry.register_value(ServiceLocator, locator)
```

## Related Documentation

- [Basic Dependency Injection](./basic_dataclass.md)
- [Protocol Injection](./protocol_injection.md)
- [Async Injection](./async_injection.md)
- [Keyword Arguments Override](./kwargs_override.md)
- [Custom Injectors](./custom_injector.md)
