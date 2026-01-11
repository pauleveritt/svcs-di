# Function Implementations

Functions can serve as factory providers in svcs-di, offering a lighter-weight alternative to class-based factories.
Instead of defining a class just to create a service instance, you can write a simple function.

## When to Use Functions vs Classes

**Use functions when:**

- You need a simple factory that creates an instance from injected dependencies
- The creation logic is straightforward (no complex initialization)
- You prefer functional programming patterns
- You want less boilerplate for simple cases

**Use classes when:**

- You need instance state beyond the created service
- The factory itself needs multiple methods
- You want inheritance or protocol implementation on the factory
- The creation logic is complex with multiple steps

## Quick Example

Here is a complete example showing a function factory with `DefaultInjector`:

```python
>>> from dataclasses import dataclass
>>> from svcs import Container, Registry
>>> from svcs_di import DefaultInjector, Inject

>>> @dataclass
... class Database:
...     host: str = "localhost"

>>> @dataclass
... class Greeting:
...     message: str = "Hello"

>>> def create_greeting(db: Inject[Database]) -> Greeting:
...     """Factory function that creates Greeting with injected Database."""
...     return Greeting(message=f"Hello from {db.host}")

>>> # Setup and use
>>> registry = Registry()
>>> registry.register_factory(Database, Database)
>>> container = Container(registry)
>>> injector = DefaultInjector(container=container)
>>> greeting = injector(create_greeting)
>>> greeting.message
'Hello from localhost'

```

## Key Concepts

### Inject[T] Parameters

Function parameters annotated with `Inject[T]` are automatically resolved from the container. For example, a function
like `create_service(db: Inject[Database], config: Inject[Config]) -> Service` will have both `db` and `config`
parameters resolved automatically when called through an injector.

### The @injectable Decorator

Functions can be decorated with `@injectable` for automatic discovery via `scan()`. Functions **must** specify the
`for_` parameter (return type inference is not supported). For example: `@injectable(for_=Greeting)` tells the scanner
which service type this factory produces.

### Direct Registration

Functions can also be registered directly without the decorator using `HopscotchRegistry.register_implementation()`.
This method accepts both classes and functions as factory providers.

## Supported Function Types

- **Named functions** (`def`): Fully supported
- **Async functions** (`async def`): Fully supported
- **Lambda functions**: NOT supported (lack proper introspection)
- **functools.partial**: NOT supported (do not pass `inspect.isfunction()`)

## Examples

```{toctree}
:maxdepth: 2
:hidden:

default_injector
keyword_injector
hopscotch_injector
```
