# Registered Injector

**Complexity: Beginner**

We just saw how to [use an injector for a function](basic_function.md). In this example, you'll learn how to:

- Register the `DefaultInjector` as the `Injector` in a registry
- Get the injector from a container

Why might you want this, instead of making the `injector = DefaultInjector(container)` yourself?

- Faster (might already have been called and is in the cache)
- Pluggable (you can register an alternate injector)

## Source Code

The complete example is available at `examples/registered_injector.py`:

```{literalinclude} ../../examples/registered_injector.py
:start-at: from dataclasses
:end-at: return result
```

## Key Concepts

### Register an Injector

We start by registering `DefaultInjector` as the `Injector` in a registry.

```{literalinclude} ../../examples/registered_injector.py
:start-at: Register the DefaultInjector
:end-at: (Injector, DefaultInjector)
```

### Get the Injector

Later in a request where we have a container, we can ask the *container* for the injector.

```{literalinclude} ../../examples/registered_injector.py
:start-at: Create container
:end-at: result = 
```

It might seem strange to take "service-oriented architecture" to this extreme, where the SOA machinery itself is in the
container. But not only do you gain the two benefits mentioned above, you also get predictable testability. User code
doesn't grab a particular injector implementation, making it easier to stub out.