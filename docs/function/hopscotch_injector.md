# HopscotchInjector with Functions

**Complexity: Intermediate-Advanced**

The `HopscotchInjector` extends function factory support with ServiceLocator-based multi-implementation resolution.
Multiple function factories can be registered for the same service type, with the correct one selected based on
resource and/or location context.

## Source Code

The complete example is available at `examples/function/hopscotch_injector.py`:

```{literalinclude} ../../examples/function/hopscotch_injector.py
:start-at: from dataclasses
:end-at: return self.greeting.greet(name)
```

## Quick Example

Here is a minimal doctest-compatible example showing resource-based resolution:

```python
>>> from dataclasses import dataclass
>>> from svcs_di import HopscotchContainer, HopscotchRegistry, Inject

>>> class CustomerContext:
...     """Resource type for customer requests."""

>>> @dataclass
... class Database:
...     host: str = "localhost"

>>> @dataclass
... class Greeting:
...     salutation: str = "Hello"
...     source: str = "default"

>>> @dataclass
... class WelcomeService:
...     greeting: Inject[Greeting]
...     def welcome(self, name: str) -> str:
...         return f"{self.greeting.salutation}, {name}!"

>>> def create_default_greeting(db: Inject[Database]) -> Greeting:
...     return Greeting(salutation="Hello", source="default")

>>> def create_customer_greeting(db: Inject[Database]) -> Greeting:
...     return Greeting(salutation="Welcome, valued customer", source="customer")

>>> registry = HopscotchRegistry()
>>> registry.register_implementation(Database, Database)
>>> registry.register_implementation(Greeting, create_default_greeting)
>>> registry.register_implementation(
...     Greeting, create_customer_greeting, resource=CustomerContext
... )

>>> # Without resource context - gets default factory
>>> container = HopscotchContainer(registry)
>>> service = container.inject(WelcomeService)
>>> service.greeting.source
'default'

>>> # With CustomerContext - gets customer factory
>>> registry.register_value(CustomerContext, CustomerContext())
>>> container = HopscotchContainer(registry)
>>> service = container.inject(WelcomeService, resource=CustomerContext)
>>> service.greeting.source
'customer'

```

## Key Concepts

### ServiceLocator-Based Resolution

The `HopscotchInjector` uses a `ServiceLocator` that can hold multiple implementations per service type.
When resolving `Inject[T]` fields, the locator selects the appropriate implementation based on context:

```{literalinclude} ../../examples/function/hopscotch_injector.py
:start-at: # Register multiple Greeting factories
:end-at: registry.register_implementation(
```

### Resource-Based Selection

Function factories can be registered with a `resource` context. The locator uses three-tier precedence:

- **Exact match** (100 points): Resource type matches exactly
- **Subclass match** (10 points): Resource is a subclass of the registered type
- **Default** (0 points): No resource constraint on registration

```{literalinclude} ../../examples/function/hopscotch_injector.py
:start-at: def create_customer_greeting
:end-at: return Greeting(
```

### The @injectable Decorator with Resources

Functions can use `@injectable` with both `for_` and `resource` parameters:

```{literalinclude} ../../examples/function/hopscotch_injector.py
:start-at: @injectable(for_=Greeting, resource=CustomerContext)
:end-at: return Greeting(salutation="Dear Customer"
```

### Scanning Decorated Functions

The `scan()` function discovers decorated functions and registers them with appropriate constraints:

```{literalinclude} ../../examples/function/hopscotch_injector.py
:start-at: # Scan discovers all @injectable decorated functions
:end-at: },
```

### Mixing Class and Function Implementations

The ServiceLocator can hold both class and function implementations for the same service type:

```{literalinclude} ../../examples/function/hopscotch_injector.py
:start-at: def demonstrate_mixed_class_and_function
:end-at: return results
```

## Use Cases

Function factories with `HopscotchInjector` are useful when:

- **Context-specific factories**: Different user types need different service creation logic
- **Layered configurations**: Override factories at specific locations in a hierarchy
- **Testing with isolation**: Register test factory functions for specific contexts
- **Lightweight customization**: Replace a class factory with a simpler function
