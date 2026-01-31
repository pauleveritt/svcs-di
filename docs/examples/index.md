# Examples

This section provides practical examples demonstrating the core features of svcs-di, organized by complexity from
beginner to advanced. Each example includes full executable code, key concepts, and type safety notes.

## Example Overview

The examples progress from simple dependency injection patterns to advanced customization:

1. **[Basic Injection](basic_injection.md)** - Learn the fundamentals of dependency injection with dataclasses and the
   `Inject` marker.

2. **[Function Injection](basic_function.md)** - `svcs` can't register functions but you can still call them via an
   injector.

3. **[Registered Injector](registered_injector.md)** - Put the injector itself into a container.

4. **[Override Registration](override_registration.md)** - Customize your site by replacing a service without forking.

5. **[Protocol-Based Injection](protocol_injection.md)** - *Intermediate*
   Discover how to use protocols for loose coupling and interface-driven design.

6. **[Asynchronous Injection](async_injection.md)** - *Intermediate*
   Explore async/await support for services with asynchronous dependencies.

7. **[Overriding Dependencies with Kwargs](kwargs_override.md)** - *Intermediate-Advanced*
   Master runtime dependency overrides for flexible testing and customization.

8. **[Custom Injector Implementations](custom_injector.md)** - *Advanced*
   Extend svcs-di with custom injection logic for advanced use cases.

9. **[Multiple Service Implementations](multiple_implementations.md)** - *Advanced*
   Register and resolve multiple implementations for the same service type using resource-based resolution.

10. **[Scanning Examples](scanning.md)** - *Intermediate-Advanced*
    Automatically discover and register services using the `@injectable` decorator and `scan()` function.

11. **[InitVar Injection](init_var.md)** - *Intermediate*
    Use `InitVar[Inject[T]]` to inject dependencies only during initialization for computing derived values.

## Getting Started

If you're new to svcs-di, start with the [Basic Dataclass Injection](basic_injection.md) example and work your way
through in order. Each example builds on concepts from previous ones while introducing new patterns.

All example source code is available in the `/examples/` directory of the repository.

```{toctree}
:maxdepth: 1
:hidden:

basic_injection
basic_function
registered_injector
override_registration
protocol_injection
async_injection
kwargs_override
custom_injector
multiple_implementations
scanning
init_var
```
