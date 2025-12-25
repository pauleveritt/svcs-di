# Protocol-Based Injection

**Complexity: Intermediate**

## Overview

This example demonstrates using Python protocols for abstract dependencies in svcs-di. You'll learn how to:

- Define a `Protocol` to specify a service interface
- Register concrete implementations for protocol types
- Use `Injectable[ProtocolType]` for loose coupling and interface-driven design
- Swap implementations by changing registrations without modifying dependent code

This pattern enables flexible, testable architectures where components depend on interfaces rather than concrete types.

## Source Code

The complete example is available at `/examples/protocol_injection.py`:

```python
"""Protocol-based injection example.

This example demonstrates using protocols for abstract dependencies:
- Define a Protocol for a service interface
- Provide a concrete implementation
- Use Injectable[ProtocolType] for loose coupling
"""

from dataclasses import dataclass
from typing import Protocol

import svcs

from svcs_di import Injectable, auto


class GreeterProtocol(Protocol):
    """Protocol defining the interface for a greeter service."""

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        ...


class EnglishGreeter:
    """Concrete implementation of GreeterProtocol."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class SpanishGreeter:
    """Alternative concrete implementation of GreeterProtocol."""

    def greet(self, name: str) -> str:
        return f"¡Hola, {name}!"


@dataclass
class Application:
    """Application that depends on a greeter (via protocol)."""

    greeter: Injectable[GreeterProtocol]
    app_name: str = "MyApp"


def main():
    """Demonstrate protocol-based injection."""
    # Create registry
    registry = svcs.Registry()

    # Register protocol with concrete implementation (English)
    registry.register_value(GreeterProtocol, EnglishGreeter())

    # Register application with auto()
    registry.register_factory(Application, auto(Application))

    # Get application - greeter is resolved via protocol
    container = svcs.Container(registry)
    app = container.get(Application)

    print(f"{app.app_name}: {app.greeter.greet('World')}")  # type: ignore[attr-defined]

    # Demonstrate swapping implementations
    registry2 = svcs.Registry()
    registry2.register_value(GreeterProtocol, SpanishGreeter())
    registry2.register_factory(Application, auto(Application))

    container2 = svcs.Container(registry2)
    app2 = container2.get(Application)

    print(f"{app2.app_name}: {app2.greeter.greet('Mundo')}")  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
```

## Key Concepts

### Protocol-Based Abstraction

Python protocols (PEP 544) define structural interfaces without inheritance. In svcs-di, you can use protocols to specify service contracts:

```python
from typing import Protocol

class GreeterProtocol(Protocol):
    """Protocol defining the interface for a greeter service."""

    def greet(self, name: str) -> str:
        """Return a greeting message."""
        ...
```

Any class that implements this interface (has a matching `greet` method) automatically satisfies the protocol—no explicit inheritance required. This is structural subtyping, also known as "duck typing" with type safety.

### Registering Concrete Implementation for Protocol Interface

To use a protocol with svcs-di, register a concrete implementation under the protocol type:

```python
from dataclasses import dataclass
from typing import Protocol
import svcs
from svcs_di import Injectable, auto

class GreeterProtocol(Protocol):
    def greet(self, name: str) -> str:
        ...

class EnglishGreeter:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

registry = svcs.Registry()
# Register the concrete implementation for the protocol type
registry.register_value(GreeterProtocol, EnglishGreeter())
```

The key insight: you register using `GreeterProtocol` as the key, but provide `EnglishGreeter()` as the value. When svcs-di later needs to resolve `Injectable[GreeterProtocol]`, it returns the `EnglishGreeter` instance.

### Injectable[ProtocolType] for Interface-Driven Design

Use `Injectable[ProtocolType]` to depend on the interface rather than the concrete type:

```python
from dataclasses import dataclass
from typing import Protocol
import svcs
from svcs_di import Injectable, auto

class GreeterProtocol(Protocol):
    def greet(self, name: str) -> str:
        ...

class EnglishGreeter:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

@dataclass
class Application:
    greeter: Injectable[GreeterProtocol]  # Depends on protocol, not concrete class
    app_name: str = "MyApp"

registry = svcs.Registry()
registry.register_value(GreeterProtocol, EnglishGreeter())
registry.register_factory(Application, auto(Application))
```

The `Application` class knows nothing about `EnglishGreeter`—it only knows that it needs something matching the `GreeterProtocol` interface. This loose coupling makes the code:

- **Testable**: Swap in mock implementations during testing
- **Flexible**: Change implementations without modifying dependents
- **Maintainable**: Clear contracts between components

### Swapping Implementations

The power of protocol-based injection is the ability to swap implementations by changing registrations:

```python
from dataclasses import dataclass
from typing import Protocol
import svcs
from svcs_di import Injectable, auto

class GreeterProtocol(Protocol):
    def greet(self, name: str) -> str:
        ...

class EnglishGreeter:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

class SpanishGreeter:
    def greet(self, name: str) -> str:
        return f"¡Hola, {name}!"

@dataclass
class Application:
    greeter: Injectable[GreeterProtocol]
    app_name: str = "MyApp"

# English configuration
registry1 = svcs.Registry()
registry1.register_value(GreeterProtocol, EnglishGreeter())
registry1.register_factory(Application, auto(Application))

container1 = svcs.Container(registry1)
app1 = container1.get(Application)

# Spanish configuration - same Application class, different implementation
registry2 = svcs.Registry()
registry2.register_value(GreeterProtocol, SpanishGreeter())
registry2.register_factory(Application, auto(Application))

container2 = svcs.Container(registry2)
app2 = container2.get(Application)
```

The `Application` class remains unchanged—only the registry configuration differs. This is the essence of the dependency inversion principle: high-level code depends on abstractions, and concrete implementations are injected from the outside.

## Type Safety

### Protocol Type Checking at Compile Time

Python's type checkers verify that concrete implementations match the protocol at compile time:

```python
from typing import Protocol

class GreeterProtocol(Protocol):
    def greet(self, name: str) -> str:
        ...

class ValidGreeter:
    def greet(self, name: str) -> str:  # Matches protocol signature
        return "Hello!"

class InvalidGreeter:
    def greet(self, name: int) -> str:  # WRONG: parameter type doesn't match
        return "Hello!"
```

Type checkers like mypy or pyright will flag `InvalidGreeter` as not satisfying `GreeterProtocol` because the method signature doesn't match. This catches interface mismatches before runtime.

### Implementation Signature Requirements

For a class to satisfy a protocol, it must:

1. Implement all protocol methods
2. Match parameter types exactly
3. Match return types exactly
4. Match method names exactly

The implementation can have additional methods or attributes—the protocol only specifies the minimum required interface.

The `# type: ignore[attr-defined]` comment in the source code is needed because type checkers see `greeter` as type `Injectable[GreeterProtocol]` in the class definition, but at runtime it's an actual implementation instance (e.g., `EnglishGreeter`). This is a known limitation of the current type system and doesn't affect runtime type safety.

## Expected Output

Running this example produces:

```
MyApp: Hello, World!
MyApp: ¡Hola, Mundo!
```

This output demonstrates:

- **First container**: Used `EnglishGreeter` implementation, producing "Hello, World!"
- **Second container**: Used `SpanishGreeter` implementation, producing "¡Hola, Mundo!"
- **Same Application class**: Both containers used the same `Application` code with different implementations injected

The ability to swap implementations without touching the dependent code is the core benefit of protocol-based injection.

## Next Steps

Once you're comfortable with protocol-based injection, explore:

- [Basic Dataclass Injection](basic_dataclass.md) if you need to review the fundamentals
- [Asynchronous Injection](async_injection.md) for async/await support with protocols
- [Overriding Dependencies with Kwargs](kwargs_override.md) for testing with protocol mocks
