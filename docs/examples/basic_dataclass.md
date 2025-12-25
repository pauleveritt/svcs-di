# Basic Dataclass Injection

**Complexity: Beginner**

## Overview

This example demonstrates the simplest use case of svcs-di: injecting dependencies into a dataclass using the `Injectable` marker. You'll learn how to:

- Mark dependencies with `Injectable[T]` to enable automatic resolution
- Use the `auto()` factory to create services with injected dependencies
- Register and retrieve services through the container

This is the foundation for all other svcs-di patterns.

## Source Code

The complete example is available at `/examples/basic_dataclass.py`:

```python
"""Basic dataclass injection example.

This example demonstrates the simplest use case of svcs-di:
- Define a dataclass with Injectable dependencies
- Register services with auto()
- Retrieve services with automatic dependency resolution
"""

from dataclasses import dataclass

import svcs

from svcs_di import Injectable, auto


@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service that depends on a database."""

    db: Injectable[Database]
    timeout: int = 30


def main():
    """Demonstrate basic dataclass injection."""
    # Create registry and register services
    registry = svcs.Registry()
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Service, auto(Service))

    # Get the service - dependencies are automatically resolved
    container = svcs.Container(registry)
    service = container.get(Service)

    print(f"Service created with timeout={service.timeout}")
    print(f"Database host={service.db.host}, port={service.db.port}")  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
```

## Key Concepts

### Injectable Marker

The `Injectable[T]` type marker identifies parameters that should be resolved from the dependency injection container:

```python
from dataclasses import dataclass
from svcs_di import Injectable

@dataclass
class Database:
    host: str = "localhost"
    port: int = 5432

@dataclass
class Service:
    db: Injectable[Database]  # Will be injected from container
    timeout: int = 30         # Regular parameter with default value
```

When svcs-di sees `Injectable[Database]`, it knows to retrieve a `Database` instance from the container instead of requiring the caller to provide it.

### auto() Factory

The `auto()` function creates a factory that automatically inspects the class constructor and resolves any `Injectable` parameters:

```python
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str = "localhost"

@dataclass
class Service:
    db: Injectable[Database]

registry = svcs.Registry()
registry.register_factory(Database, auto(Database))
registry.register_factory(Service, auto(Service))
```

For the `Service` class, `auto(Service)` generates a factory that:
1. Checks the constructor signature
2. Finds the `db: Injectable[Database]` parameter
3. Calls `container.get(Database)` to resolve it
4. Constructs `Service` with the resolved dependency

### Registry and Container

The `Registry` stores factory functions for each service type:

```python
import svcs
from dataclasses import dataclass
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str = "localhost"

@dataclass
class Service:
    db: Injectable[Database]

registry = svcs.Registry()
registry.register_factory(Database, auto(Database))
registry.register_factory(Service, auto(Service))
```

The `Container` uses these factories to resolve and instantiate services:

```python
import svcs
from dataclasses import dataclass
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str = "localhost"

@dataclass
class Service:
    db: Injectable[Database]

registry = svcs.Registry()
registry.register_factory(Database, auto(Database))
registry.register_factory(Service, auto(Service))

container = svcs.Container(registry)
service = container.get(Service)
```

When you call `container.get(Service)`:
1. The container looks up the factory for `Service`
2. The factory identifies the `db: Injectable[Database]` dependency
3. The container recursively calls `container.get(Database)`
4. Both services are instantiated and `Service` receives the `Database` instance

## Type Safety

svcs-di preserves full type information throughout the injection process. Type checkers like mypy and pyright understand that `container.get(Service)` returns a `Service` instance with properly typed attributes.

The `# type: ignore[attr-defined]` comment in the source code is needed because type checkers see `db` as type `Injectable[Database]` in the class definition, but at runtime it's actually a `Database` instance. This is a known limitation of the current type system and doesn't affect runtime type safety.

## Expected Output

Running this example produces:

```
Service created with timeout=30
Database host=localhost, port=5432
```

This output demonstrates:
- The `Service` was successfully created with its default `timeout=30`
- The `Database` dependency was automatically injected with its default values
- Both services are fully initialized and accessible

## Next Steps

Once you're comfortable with basic dataclass injection, explore:
- [Protocol-Based Injection](protocol_injection.md) for interface-driven design
- [Asynchronous Injection](async_injection.md) for async/await support
- [Overriding Dependencies with Kwargs](kwargs_override.md) for testing patterns
