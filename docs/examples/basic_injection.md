# Basic Injection

**Complexity: Beginner**

This example demonstrates the simplest use case of svcs-di: injecting dependencies into a dataclass using the
`Injectable` marker. You'll learn how to:

- Mark dependencies with `Injectable[T]` to enable automatic resolution
- Use the `auto()` factory to create services with injected dependencies
- Register and retrieve services through the container

This is the foundation for all other `svcs-di` patterns.

## Source Code

The complete example is available at `examples/basic_injection.py`:

```{literalinclude} ../../examples/basic_injection.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Default Injector

This package proposes a minimal `DefaultInjector` as part of the `auto.py` module, along with an `Injector` protocol to
allow another injector. If there's no alternate injector in the registry, the default injector is used.

### Injectable Marker

The `Injectable[T]` type marker identifies parameters that should be resolved from the dependency injection container:

```{literalinclude} ../../examples/basic_injection.py
:start-at: The `db` is injected from the container
:end-at: timeout: int
:emphasize-lines: 6
```

When svcs-di sees `Injectable[Database]`, it knows to retrieve a `Database` instance from the container instead of
requiring the caller to provide it.

### auto() Factory

The `auto()` function creates a *wrapper* factory that automatically inspects the class constructor and resolves any
`Injectable` parameters:

```{literalinclude} ../../examples/basic_injection.py
:start-at: registry = Registry()
:end-at: auto(Service)
:emphasize-lines: 3
```

For the `Service` class, `auto(Service)` uses a `svcs` factory that:

1. Checks the constructor signature
2. Finds the `db: Injectable[Database]` parameter
3. Calls `container.get(Database)` to resolve it
4. Constructs `Service` with the resolved `db` dependency

### Registry and Container

The `Registry` stores factory functions for each service type. The `Container` uses these factories to resolve and
instantiate services:

```{literalinclude} ../../examples/basic_injection.py
:start-at: container =
:end-at: service =
```

When you call `container.get(Service)`:

1. The container looks up the factory for `Service`
2. The factory identifies the `db: Injectable[Database]` dependency
3. The container recursively calls `container.get(Database)`
4. Both services are instantiated and `Service` receives the `Database` instance

### Alternate Path: Register the Injector

## Type Safety

`svcs-di` preserves full type information throughout the injection process. Type checkers like mypy and pyright
understand that `container.get(Service)` returns a `Service` instance with properly typed attributes.
