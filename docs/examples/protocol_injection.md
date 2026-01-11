# Protocol-Based Injection

**Complexity: Intermediate**

This example demonstrates using Python protocols for abstract dependencies in `svcs-di`. You'll learn how to:

- Define a `Protocol` to specify a service interface
- Register concrete implementations for protocol types
- Use `Injectable[ProtocolType]` for loose coupling and interface-driven design
- Swap implementations by changing registrations without modifying dependent code

This pattern enables flexible, testable architectures where components depend on interfaces rather than concrete types.

Why does this matter? We hope to build a broad, quality ecosystem of interchangeable themes, components, and tools.
Protocols are a good alternative to inheritance for this.

## Source Code

The complete example is available at `examples/protocol_injection.py`:

```{literalinclude} ../../examples/protocol_injection.py
:start-at: from dataclasses
:end-at: return app
```

## Key Concepts

### Protocol-Based Abstraction

Python protocols (PEP 544) define structural interfaces without inheritance. In `svcs` and thus `svcs-di`, you can use
protocols to specify service contracts:

```{literalinclude} ../../examples/protocol_injection.py
:start-at: class Greeter(Protocol)
:end-at: ...
```

Any class that implements this interface (has a matching `greet` method) automatically satisfies the protocol — no
explicit inheritance required. This is "structural subtyping", also known as "duck typing" with type safety.

```{literalinclude} ../../examples/protocol_injection.py
:start-at: DefaultGreeter:
:end-at: return f
```

### Registering Concrete Implementation for Protocol Interface

To use a protocol with `svcs`, register a concrete implementation under the protocol type:

```{literalinclude} ../../examples/protocol_injection.py
:start-at: Register protocol with concrete implementation
:end-at: registry.register
```

The key insight: you register using `Greeter` as the key, but provide `DefaultGreeter` as the factory. When
`svcs-di` later needs to resolve `Injectable[Greeter]` in `App`, it finds the `DefaultGreeter` dataclass and calls it.

```{literalinclude} ../../examples/protocol_injection.py
:start-at: A service that depends
:end-at: app_name
:emphasize-lines: 6
```

The `Application` class knows nothing about `DefaultGreeter`. It only knows that it needs something matching the
`Greeter` interface. This loose coupling makes the code:

- **Testable**: Swap in mock implementations during testing
- **Flexible**: Change implementations without modifying dependents
- **Maintainable**: Clear contracts between components

## Type Safety

### Protocol Type Checking at Compile Time

Python's type checkers verify that concrete implementations match the protocol at compile time:

```python
from typing import Protocol


class Greeter(Protocol):
    def greet(self, name: str) -> str:
        ...


class ValidGreeter:
    def greet(self, name: str) -> str:  # Matches protocol signature
        return "Hello!"


class InvalidGreeter:
    def greet(self, name: int) -> str:  # WRONG: parameter type doesn't match
        return "Hello!"
```

Type checkers like `ty`, `pyrefly`, `mypy` or `pyright` will flag `InvalidGreeter` as not satisfying `Greeter` because
the method signature doesn't match. This catches interface mismatches before runtime.
