# Examples

This section provides practical examples demonstrating the core features of svcs-di, organized by complexity from beginner to advanced. Each example includes full executable code, key concepts, and type safety notes.

## Example Overview

The examples progress from simple dependency injection patterns to advanced customization:

1. **[Basic Dataclass Injection](basic_dataclass.md)** - *Beginner*
   Learn the fundamentals of dependency injection with dataclasses and the `Injectable` marker.

2. **[Protocol-Based Injection](protocol_injection.md)** - *Intermediate*
   Discover how to use protocols for loose coupling and interface-driven design.

3. **[Asynchronous Injection](async_injection.md)** - *Intermediate*
   Explore async/await support for services with asynchronous dependencies.

4. **[Overriding Dependencies with Kwargs](kwargs_override.md)** - *Intermediate-Advanced*
   Master runtime dependency overrides for flexible testing and customization.

5. **[Custom Injector Implementations](custom_injector.md)** - *Advanced*
   Extend svcs-di with custom injection logic for advanced use cases.

## Getting Started

If you're new to svcs-di, start with the [Basic Dataclass Injection](basic_dataclass.md) example and work your way through in order. Each example builds on concepts from previous ones while introducing new patterns.

All example source code is available in the `/examples/` directory of the repository.

```{toctree}
:maxdepth: 1
:hidden:

basic_dataclass
protocol_injection
async_injection
kwargs_override
custom_injector
```
