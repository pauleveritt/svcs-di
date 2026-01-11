# The Injection Container

**Complexity: Beginner**

Creating the injector yourself, and manually using it to create your services, isn't in the spirit of `svcs`.
To make this easier, `svcs-di` has a special `InjectorContainer` which automates this and provides
`.inject()` to allow `**kwargs`. In this example, you'll see:

- Using an `InjectorContainer`
- Which registers the `KeywordInjector` as the `Injector`
- Using the container's `.inject()` method to fetch a service but with keyword arguments
- No longer needing to use `auto` to wrap injectable services
- How you can pass in a different injector to `InjectorContainer`

## How It Works

The `InjectorContainer` is a subclass of `Container` which adds `.inject()` to allow keyword arguments. Behind the
scenes, it gets the `Injector` from the container and uses it to create the instance, passing in the keyword arguments.

By default, `InjectorContainer(registry)` uses the `KeywordInjector.` If you want a different `Injector`, you can pass
that in. For example, `InjectorContainer(regsistry, injector=HopscotchInjector)`.

## Source Code

The complete example is available at `examples/keyword/injection_container.py`:

```{literalinclude} ../../examples/keyword/injection_container.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Use the `InjectorContainer`

We start with using a different flavor of container:

```{literalinclude} ../../examples/keyword/injection_container.py
:start-at: container = InjectorContainer
:end-at: container = InjectorContainer
```

Behind the scenese, this registers the `KeywordInjector` with the container.

### Use `.inject()` with keyword arguments

When you want to get a service with keyword arguments, use `.inject()` method:

```{literalinclude} ../../examples/keyword/injection_container.py
:start-at: service = 
:end-at: service = 
```

Of course, you can still use `container.get()` if you want to get a service without keyword arguments. And as you'd
expect, `InjectorContainer` also has a `.ainject()` method for async injection.

### Not using `auto`

Careful readers will also notice that we didn't use `auto` as a wrapper when registering `Service`:

```{literalinclude} ../../examples/keyword/injection_container.py
:start-at: registry.register_factory(Service, Service)
:end-at: registry.register_factory(Service, Service) 
```

The `InjectorContainer` doesn't need that wrapper function on the factory, as it has already taken over the factory
construction that `get()` provided.
