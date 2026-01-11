# Manual Locator

**Complexity: Beginner**

Same use case as `getting_started.py`, but using manual `ServiceLocator` and `HopscotchInjector` instead of
`HopscotchRegistry` and `HopscotchContainer`. In this example, you'll see:

- Using manual `ServiceLocator` and `HopscotchInjector`
- Registering implementations manually
- Using the default `svcs.Registry` and `svcs.Container`

## Source Code

The complete example is available at `examples/hopscotch/manual_locator.py`:

```{literalinclude} ../../examples/hopscotch/manual_locator.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Manual ServiceLocator Setup

The `ServiceLocator` is a simple dictionary that maps service names to implementations. `svcs` doesn't allow multiple
implementations of a service. The `ServiceLocator` fills this gap. It looks up the right implementation of a service.

Create and register implementations with the `ServiceLocator` manually:

```{literalinclude} ../../examples/hopscotch/manual_locator.py
:start-at: Create ServiceLocator
:end-at: register(Database
```

### Register Locator as Service

The locator itself is a service that can go in the registry. In fact, it can be replaced with a custom locator. Register
the locator with the `svcs` registry:

```{literalinclude} ../../examples/hopscotch/manual_locator.py
:start-at: Create registry
:end-at: register_value(ServiceLocator
```

### Create Injector Manually

We'll be showing the automated, convenient approach with a custom registry and container. But you can use the locator
approach "manually." Create the injector and use it:

```{literalinclude} ../../examples/hopscotch/manual_locator.py
:start-at: Create container
:end-at: injector(WelcomeService)
```
