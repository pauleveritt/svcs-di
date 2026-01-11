# Protocols

**Complexity: Intermediate**

Shows how to define Protocols as service interfaces, then register multiple implementations.

## What's The Big Idea?

So far, the examples have used concrete classes like `Greeting` with subclasses like `EmployeeGreeting`. This works, but
has a limitation: `EmployeeGreeting` must inherit from `Greeting`.

Python's `Protocol` provides a better approach for large-scale systems. A Protocol defines a *contract* - what
attributes
and methods a service must have - without requiring inheritance. Any class that has the same "shape" satisfies the
Protocol.

This is extra work, but Protocols provide:

- **Explicit contracts**: Clear documentation of what a service must do
- **Flexibility**: Implementations don't need to inherit from anything
- **Type safety**: Type checkers verify implementations match the contract
- **Replaceability**: Easy to swap implementations without changing consumers

## Source Code

The complete example is available at `examples/hopscotch/protocols.py`:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Defining a Service Protocol

Define a Protocol as the service contract. Include both attributes and methods:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: class Greeting(Protocol)
:end-at: ...
```

### Defining a Resource Protocol

Resources can also be Protocols. This lets you vary implementations based on the *type* of resource in the container,
not just a specific class:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: class Resource(Protocol)
:end-at: first_name: str
```

Then create concrete implementations, perhaps as a dataclass or an attrs class or even an SQLAlchemy model result:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: class DefaultResource
:end-at: first_name: str = "Team Member"
```

### Implementing the Service Protocol

Implementations don't need to inherit from the Protocol - they just need to have the same "shape":

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: class DefaultGreeting
:end-at: return f"{self.salutation}, {name}!"
```

### Registering Under a Protocol

Register implementations with the Protocol as the service type. Use `resource=` to constrain when an implementation
is selected:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: Register implementations under the Greeting protocol
:end-at: resource=EmployeeResource
```

### Resource-Based Selection

The key insight: when you pass `resource=Resource` to `container.inject()`, Hopscotch looks up the `Resource` from the
container and checks what *type* it actually is. Different resource types select different implementations:

**Request 1** - `DefaultResource` in container → selects `DefaultGreeting`:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: Request 1: DefaultResource
:end-at: assert service.greeting.salutation == "Hello"
```

**Request 2** - `EmployeeResource` in container → selects `EmployeeGreeting`:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: Request 2: EmployeeResource
:end-at: assert service.greeting.salutation == "Hey"
```

### Depending on the Protocol

Services depend on the Protocol, not specific implementations:

```{literalinclude} ../../examples/hopscotch/protocols.py
:start-at: class WelcomeService
:end-at: return self.greeting.greet
```
