# Overriding Dependencies with Kwargs

**Complexity: Intermediate-Advanced**

## Overview

This example demonstrates runtime dependency override capability in svcs-di. You'll learn how to:

- Understand the precedence order for dependency resolution (kwargs > container > defaults)
- Override dependencies at construction time for testing and flexibility
- Use testing patterns with dependency substitution
- Apply the factory wrapper pattern to pass kwargs through the container

This pattern is especially powerful for testing, where you want to substitute mock implementations or test-specific configuration without modifying the registry.

## Source Code

The complete example is available at `/examples/kwargs_override.py`:

```python
"""Kwargs override example.

This example demonstrates the precedence order for dependency resolution:
1. kwargs (highest) - override everything, including Injectable params
2. container lookup - for Injectable[T] parameters only
3. default values - from parameter/field definitions

This pattern is especially useful for testing.
"""

from dataclasses import dataclass

import svcs

from svcs_di import Injectable, auto


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service with injectable and non-injectable parameters."""

    db: Injectable[Database]
    timeout: int = 30
    debug: bool = False


def main():
    """Demonstrate kwargs override precedence."""
    registry = svcs.Registry()

    # Register production database
    prod_db = Database(host="prod.example.com", port=5433)
    registry.register_value(Database, prod_db)

    # Register service with auto()
    registry.register_factory(Service, auto(Service))

    # Case 1: Normal usage - use container + defaults
    print("Case 1: Normal usage")
    container = svcs.Container(registry)
    service = container.get(Service)
    print(f"  Database: {service.db.host}")  # type: ignore[attr-defined]
    print(f"  Timeout: {service.timeout}")
    print(f"  Debug: {service.debug}")
    print()

    # Case 2: Override non-injectable parameter via factory kwargs
    print("Case 2: Override timeout via factory")
    # Note: We can't pass kwargs through container.get() directly
    # But factories can accept kwargs
    def custom_factory(svcs_container):
        return auto(Service)(svcs_container, timeout=60)

    registry2 = svcs.Registry()
    registry2.register_value(Database, prod_db)
    registry2.register_factory(Service, custom_factory)

    container2 = svcs.Container(registry2)
    service2 = container2.get(Service)
    print(f"  Database: {service2.db.host}")  # type: ignore[attr-defined]
    print(f"  Timeout: {service2.timeout}")  # Overridden
    print(f"  Debug: {service2.debug}")
    print()

    # Case 3: Override Injectable parameter for testing
    print("Case 3: Override db for testing")
    test_db = Database(host="localhost", port=5432)

    def test_factory(svcs_container):
        return auto(Service)(svcs_container, db=test_db, debug=True)
    registry3 = svcs.Registry()
    registry3.register_value(Database, prod_db)  # This will be ignored
    registry3.register_factory(Service, test_factory)

    container3 = svcs.Container(registry3)
    service3 = container3.get(Service)
    print(f"  Database: {service3.db.host}")  # type: ignore[attr-defined]  # Test DB, not prod
    print(f"  Timeout: {service3.timeout}")
    print(f"  Debug: {service3.debug}")  # Overridden


if __name__ == "__main__":
    main()
```

## Key Concepts

### Precedence Order: kwargs > container > defaults

When resolving parameters for service construction, svcs-di follows a three-level precedence order:

```python
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str = "localhost"  # Level 3: default value
    port: int = 5432         # Level 3: default value

@dataclass
class Service:
    db: Injectable[Database]  # Level 2: container lookup
    timeout: int = 30         # Level 3: default value
    debug: bool = False       # Level 3: default value
```

The resolution order is:

1. **kwargs (highest priority)**: Explicitly passed keyword arguments override everything
2. **container lookup**: For `Injectable[T]` parameters, resolve from the container
3. **default values (lowest priority)**: Use default values from the parameter definition

This means you can always override any parameter—even Injectable dependencies—by passing them as kwargs to the factory function.

### Overriding Dependencies at Construction Time

You can override dependencies when calling the factory directly:

```python
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str = "localhost"
    port: int = 5432

@dataclass
class Service:
    db: Injectable[Database]
    timeout: int = 30

# Create a test database
test_db = Database(host="test.example.com", port=5433)

registry = svcs.Registry()
prod_db = Database(host="prod.example.com", port=5432)
registry.register_value(Database, prod_db)

# Create a custom factory that overrides the db parameter
def test_factory(svcs_container):
    return auto(Service)(svcs_container, db=test_db, timeout=60)

registry.register_factory(Service, test_factory)

container = svcs.Container(registry)
service = container.get(Service)
# service.db is test_db (not prod_db from container)
# service.timeout is 60 (not 30 from defaults)
```

By wrapping `auto(Service)` in a custom factory, you can pass kwargs that override both Injectable dependencies and regular parameters. This is the key to flexible testing.

### Testing Patterns with Dependency Substitution

The kwargs override pattern is ideal for testing. You can substitute mock dependencies without modifying the registry:

```python
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str
    port: int

@dataclass
class Service:
    db: Injectable[Database]
    debug: bool = False

# In production code
def create_production_registry():
    registry = svcs.Registry()
    prod_db = Database(host="prod.example.com", port=5432)
    registry.register_value(Database, prod_db)
    registry.register_factory(Service, auto(Service))
    return registry

# In test code
def test_service_with_mock_db():
    # Create a test database
    test_db = Database(host="localhost", port=5432)

    # Create a test registry with overridden factory
    registry = svcs.Registry()

    # Register a factory that injects the test database
    def test_factory(svcs_container):
        return auto(Service)(svcs_container, db=test_db, debug=True)

    registry.register_factory(Service, test_factory)

    container = svcs.Container(registry)
    service = container.get(Service)

    # service uses test_db, not production database
    assert service.db.host == "localhost"
    assert service.debug is True
```

This pattern allows you to:
- Inject mock dependencies for unit testing
- Use test-specific configuration (e.g., `debug=True`)
- Test error conditions by injecting failing dependencies
- Verify behavior with different dependency configurations

### Factory Wrapper Pattern for Passing Kwargs

Since `container.get()` doesn't accept kwargs directly, use the factory wrapper pattern to pass kwargs through the container:

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
    timeout: int = 30
    debug: bool = False

# Pattern: Wrap auto() in a custom factory that accepts container and passes kwargs
def custom_factory(svcs_container):
    """Factory wrapper that passes kwargs to auto()."""
    return auto(Service)(
        svcs_container,
        timeout=60,      # Override timeout
        debug=True       # Override debug
    )

registry = svcs.Registry()
registry.register_value(Database, Database())
registry.register_factory(Service, custom_factory)  # Register the wrapper

container = svcs.Container(registry)
service = container.get(Service)
# service.timeout is 60, service.debug is True
```

The factory wrapper pattern:
1. Accepts the container as its only parameter (required by svcs)
2. Calls `auto(Service)(svcs_container, **kwargs)` with custom kwargs
3. Returns the constructed service instance

This pattern bridges the gap between the container interface (which doesn't accept kwargs) and the auto-generated factories (which do accept kwargs).

### When Injectable Parameters Can Be Overridden

Injectable parameters can always be overridden via kwargs, regardless of whether they're registered in the container:

```python
from dataclasses import dataclass
import svcs
from svcs_di import Injectable, auto

@dataclass
class Database:
    host: str

@dataclass
class Service:
    db: Injectable[Database]

registry = svcs.Registry()

# Register a production database
prod_db = Database(host="prod.example.com")
registry.register_value(Database, prod_db)

# But override it with a test database via kwargs
test_db = Database(host="localhost")

def test_factory(svcs_container):
    return auto(Service)(svcs_container, db=test_db)

registry.register_factory(Service, test_factory)

container = svcs.Container(registry)
service = container.get(Service)
# service.db is test_db, not prod_db
```

This override capability applies to:
- Injectable parameters (like `db: Injectable[Database]`)
- Regular parameters with defaults (like `timeout: int = 30`)
- Regular parameters without defaults (like `name: str`)

The only requirement is that you pass the kwarg when calling the factory function.

## Type Safety

svcs-di maintains type safety when using kwargs overrides. Type checkers understand:

- `auto(Service)` returns a factory function that accepts the container and optional kwargs
- The kwargs must match the constructor signature of `Service`
- Passing incorrect types or unknown parameters will be flagged by type checkers

The `# type: ignore[attr-defined]` comments in the source code are needed because type checkers see `db` as type `Injectable[Database]` in the class definition, but at runtime it's actually a `Database` instance. This is a known limitation of the current type system and doesn't affect runtime type safety.

## Expected Output

Running this example produces:

```
Case 1: Normal usage
  Database: prod.example.com
  Timeout: 30
  Debug: False

Case 2: Override timeout via factory
  Database: prod.example.com
  Timeout: 60
  Debug: False

Case 3: Override db for testing
  Database: localhost
  Timeout: 30
  Debug: True
```

This output demonstrates:

- **Case 1 - Normal usage**: Dependencies resolved from container (`prod.example.com`) and defaults (`timeout=30`, `debug=False`)
- **Case 2 - Override timeout**: Non-injectable parameter overridden via factory kwargs (`timeout=60`)
- **Case 3 - Override db for testing**: Injectable dependency overridden with test database (`localhost`) and debug flag enabled

The precedence order ensures maximum flexibility: you can always override any parameter when needed, while still benefiting from automatic dependency resolution in normal usage.

## Next Steps

Once you're comfortable with kwargs overrides, explore:

- [Basic Dataclass Injection](basic_dataclass.md) to review the fundamentals
- [Protocol-Based Injection](protocol_injection.md) to combine protocols with override patterns for testing
- [Asynchronous Injection](async_injection.md) to override async dependencies
- [Custom Injector Implementations](custom_injector.md) for advanced customization beyond kwargs
