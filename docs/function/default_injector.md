# DefaultInjector with Functions

**Complexity: Beginner**

The `DefaultInjector` supports function factories with two-tier precedence for parameter resolution:

1. **Container** (higher priority): `Inject[T]` parameters are resolved via `container.get(T)`
2. **Default values** (lower priority): Non-injectable parameters use their default values

This example demonstrates using functions as factory providers with the `DefaultInjector`.

## Source Code

The complete example is available at `examples/function/default_injector.py`:

```{literalinclude} ../../examples/function/default_injector.py
:start-at: from dataclasses
:end-at: return Greeting(message=f"Hello from {db.host}:{db.port}")
```

## Quick Example

Here is a minimal doctest-compatible example:

```python
>>> from dataclasses import dataclass
>>> from svcs import Container, Registry
>>> from svcs_di import DefaultInjector, Inject

>>> @dataclass
... class Database:
...     host: str = "localhost"
...     port: int = 5432

>>> @dataclass
... class Greeting:
...     message: str = "Hello"

>>> def create_greeting(db: Inject[Database]) -> Greeting:
...     return Greeting(message=f"Hello from {db.host}:{db.port}")

>>> registry = Registry()
>>> registry.register_factory(Database, Database)
>>> container = Container(registry)
>>> injector = DefaultInjector(container=container)
>>> greeting = injector(create_greeting)
>>> greeting.message
'Hello from localhost:5432'

```

## Key Concepts

### Direct Function Calls

The `DefaultInjector` can call functions directly, resolving `Inject[T]` parameters:

```{literalinclude} ../../examples/function/default_injector.py
:start-at: # Call the factory function directly
:end-at: greeting = injector(create_greeting)
```

### With HopscotchRegistry

Function factories can be registered in `HopscotchRegistry` for ServiceLocator-based resolution:

```{literalinclude} ../../examples/function/default_injector.py
:start-at: # Setup HopscotchRegistry and register services
:end-at: registry.register_implementation(Greeting, create_greeting)
```

When a service with an `Inject[Greeting]` field is injected, the locator finds and calls the function factory.

### The @injectable Decorator

Functions can be decorated with `@injectable(for_=T)` for automatic discovery:

```{literalinclude} ../../examples/function/default_injector.py
:start-at: @injectable(for_=Greeting)
:end-at: return Greeting(message=f"Decorated factory on {db.host}")
```

The `for_` parameter is **required** for functions (return type inference is not supported).
