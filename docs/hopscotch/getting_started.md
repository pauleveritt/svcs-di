# Getting Started

**Complexity: Beginner**

The simplest example using `HopscotchRegistry` and `HopscotchContainer` for service resolution with dependency
injection. In this example, you'll see:

- Using `HopscotchRegistry` and `HopscotchContainer`
- Resolving injection just the same as always

We don't yet introduce multiple registrations for the same service. We're just showing how these can be used "like
normal."

## Source Code

The complete example is available at `examples/hopscotch/getting_started.py`:

```{literalinclude} ../../examples/hopscotch/getting_started.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### HopscotchRegistry

`HopscotchRegistry` extends `svcs.Registry` with an internal `ServiceLocator` for multi-implementation support:

```{literalinclude} ../../examples/hopscotch/getting_started.py
:start-at: registry = HopscotchRegistry
:end-at: register_implementation(Database
```

### HopscotchContainer

`HopscotchContainer` extends `svcs.Container` with `inject()` method that uses `HopscotchInjector`:

```{literalinclude} ../../examples/hopscotch/getting_started.py
:start-at: container = HopscotchContainer
:end-at: container.inject
```
