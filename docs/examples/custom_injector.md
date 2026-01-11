# Custom Injector Implementations

**Complexity: Advanced**

## Overview

This example demonstrates the advanced extensibility of svcs-di through custom injector implementations. You'll learn how to:

- Create custom injector classes that wrap `DefaultInjector`
- Implement logging injectors that track dependency creation
- Build validating injectors with pre and post-construction checks
- Replace the `DefaultInjector` registration to affect all `auto()` factories globally
- Extend the injection process with custom logic while maintaining type safety

**Warning:** This is an advanced pattern that adds complexity to your dependency injection setup. Only use custom injectors when you have specific requirements that can't be met through standard DI patterns (e.g., cross-cutting concerns like logging, validation, or security checks).

## Source Code

The complete example is available at `examples/custom_injector.py`:

```python
"""Custom injector example.

This example demonstrates implementing a custom injector:
- Define a custom injector dataclass that adds logging or validation
- Register the custom injector as DefaultInjector replacement
- All auto() factories will use the custom injector
"""

import dataclasses
from dataclasses import dataclass

import svcs

from svcs_di import DefaultInjector, Injectable, auto


@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service that depends on a database."""

    db: Injectable[Database]
    timeout: int = 30


@dataclasses.dataclass
class LoggingInjector:
    """Custom injector that logs all dependency injections."""

    container: svcs.Container

    def __call__(self, target, **kwargs):
        """Injector that logs before and after injection."""
        print(f"[INJECTOR] Creating instance of {target.__name__}")
        print(f"[INJECTOR] Kwargs: {kwargs}")

        # Use default injector to do the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        print(f"[INJECTOR] Created {target.__name__} successfully")
        return instance


@dataclasses.dataclass
class ValidatingInjector:
    """Custom injector that validates field values."""

    container: svcs.Container

    def __call__(self, target, **kwargs):
        """Injector that validates timeout is positive."""
        # Check if timeout is being set and validate it
        if "timeout" in kwargs and kwargs["timeout"] <= 0:
            raise ValueError(f"timeout must be positive, got {kwargs['timeout']}")

        # Use default injector to do the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        # Post-construction validation
        if hasattr(instance, "timeout") and instance.timeout <= 0:
            raise ValueError(f"Invalid timeout: {instance.timeout}")

        return instance


def main():
    """Demonstrate custom injector."""
    # Example 1: Logging injector
    print("Example 1: Logging Injector")
    print("=" * 50)

    def logging_injector_factory(container: svcs.Container) -> LoggingInjector:
        return LoggingInjector(container=container)

    registry = svcs.Registry()

    # Register custom logging injector
    registry.register_factory(DefaultInjector, logging_injector_factory)

    # Register services
    registry.register_factory(Database, auto(Database))
    registry.register_factory(Service, auto(Service))

    # Get service - custom injector will log
    container = svcs.Container(registry)
    service = container.get(Service)
    print(f"Service timeout: {service.timeout}")
    print()

    # Example 2: Validating injector
    print("Example 2: Validating Injector")
    print("=" * 50)

    def validating_injector_factory(
        container: svcs.Container,
    ) -> ValidatingInjector:
        return ValidatingInjector(container=container)

    registry2 = svcs.Registry()

    # Register custom validating injector
    registry2.register_factory(DefaultInjector, validating_injector_factory)

    # Register services
    registry2.register_value(Database, Database())

    # This will work (valid timeout)
    def valid_factory(svcs_container):
        return auto(Service)(svcs_container, timeout=60)

    registry2.register_factory(Service, valid_factory)

    container2 = svcs.Container(registry2)
    service2 = container2.get(Service)
    print(f"Valid service created with timeout: {service2.timeout}")

    # This will fail (invalid timeout)
    print("\nTrying to create service with invalid timeout...")
    registry3 = svcs.Registry()
    registry3.register_factory(DefaultInjector, validating_injector_factory)
    registry3.register_value(Database, Database())

    def invalid_factory(svcs_container):
        return auto(Service)(svcs_container, timeout=-10)

    registry3.register_factory(Service, invalid_factory)

    container3 = svcs.Container(registry3)
    try:
        service3 = container3.get(Service)
    except ValueError as e:
        print(f"Validation failed as expected: {e}")


if __name__ == "__main__":
    main()
```

## Key Concepts

### Creating Custom Injector Implementations

A custom injector is a callable object (typically a dataclass with a `__call__` method) that takes a target class and keyword arguments, then returns an instance of that class:

```python
import dataclasses
import svcs
from svcs_di import DefaultInjector

@dataclasses.dataclass
class LoggingInjector:
    """Custom injector that logs all dependency injections."""

    container: svcs.Container

    def __call__(self, target, **kwargs):
        """Injector that logs before and after injection."""
        print(f"[INJECTOR] Creating instance of {target.__name__}")

        # Delegate to DefaultInjector for the actual work
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        print(f"[INJECTOR] Created {target.__name__} successfully")
        return instance
```

The custom injector must:
1. Accept a `container` parameter (typically stored as an instance attribute)
2. Implement `__call__(self, target, **kwargs)` to handle injection
3. Return an instance of the target class

Most custom injectors wrap `DefaultInjector` to leverage the standard injection logic while adding custom behavior before or after.

### LoggingInjector: Wrapping DefaultInjector

The `LoggingInjector` demonstrates the wrapper pattern—a common approach for custom injectors:

```python
import dataclasses
import svcs
from svcs_di import DefaultInjector, Injectable, auto
from dataclasses import dataclass

@dataclass
class Database:
    host: str = "localhost"
    port: int = 5432

@dataclass
class Service:
    db: Injectable[Database]
    timeout: int = 30

@dataclasses.dataclass
class LoggingInjector:
    container: svcs.Container

    def __call__(self, target, **kwargs):
        print(f"[INJECTOR] Creating instance of {target.__name__}")
        print(f"[INJECTOR] Kwargs: {kwargs}")

        # Use DefaultInjector for the actual injection logic
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        print(f"[INJECTOR] Created {target.__name__} successfully")
        return instance

def logging_injector_factory(container: svcs.Container) -> LoggingInjector:
    return LoggingInjector(container=container)

registry = svcs.Registry()
registry.register_factory(DefaultInjector, logging_injector_factory)
registry.register_factory(Database, auto(Database))
registry.register_factory(Service, auto(Service))

container = svcs.Container(registry)
service = container.get(Service)
```

By wrapping `DefaultInjector`, you get:
- Full dependency injection functionality (resolving `Injectable` parameters, handling kwargs, etc.)
- The ability to add logging, timing, debugging, or other observability
- Clean separation between your custom logic and the core injection mechanism

The logging output helps you understand the dependency creation order and diagnose issues in complex dependency graphs.

### ValidatingInjector: Pre and Post-Construction Checks

The `ValidatingInjector` shows how to enforce business rules during injection:

```python
import dataclasses
import svcs
from svcs_di import DefaultInjector, Injectable, auto
from dataclasses import dataclass

@dataclass
class Database:
    host: str = "localhost"

@dataclass
class Service:
    db: Injectable[Database]
    timeout: int = 30

@dataclasses.dataclass
class ValidatingInjector:
    container: svcs.Container

    def __call__(self, target, **kwargs):
        # Pre-construction validation: check kwargs before creating instance
        if "timeout" in kwargs and kwargs["timeout"] <= 0:
            raise ValueError(f"timeout must be positive, got {kwargs['timeout']}")

        # Delegate to DefaultInjector
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        # Post-construction validation: check the created instance
        if hasattr(instance, "timeout") and instance.timeout <= 0:
            raise ValueError(f"Invalid timeout: {instance.timeout}")

        return instance

def validating_injector_factory(container: svcs.Container) -> ValidatingInjector:
    return ValidatingInjector(container=container)

registry = svcs.Registry()
registry.register_factory(DefaultInjector, validating_injector_factory)
registry.register_value(Database, Database())

def invalid_factory(svcs_container):
    return auto(Service)(svcs_container, timeout=-10)

registry.register_factory(Service, invalid_factory)

container = svcs.Container(registry)
try:
    service = container.get(Service)
except ValueError as e:
    print(f"Validation failed: {e}")
```

Custom injectors can enforce:
- **Pre-construction validation**: Check kwargs before instance creation (parameter range checks, required field presence, etc.)
- **Post-construction validation**: Verify the created instance meets business rules (invariants, constraints, etc.)
- **Security checks**: Ensure dependencies meet security requirements
- **Resource limits**: Prevent creation of instances that would exceed quotas

This centralizes validation logic that would otherwise be scattered across factory functions.

### Replacing DefaultInjector for Global Effect

The key to making custom injectors work globally is registering them as the `DefaultInjector`:

```python
import svcs
from svcs_di import DefaultInjector, auto
import dataclasses
from dataclasses import dataclass

@dataclasses.dataclass
class LoggingInjector:
    container: svcs.Container

    def __call__(self, target, **kwargs):
        print(f"[INJECTOR] Creating {target.__name__}")
        default_injector = DefaultInjector(container=self.container)
        return default_injector(target, **kwargs)

@dataclass
class Database:
    host: str = "localhost"

@dataclass
class Service:
    timeout: int = 30

def logging_injector_factory(container: svcs.Container) -> LoggingInjector:
    return LoggingInjector(container=container)

registry = svcs.Registry()

# Register custom injector FIRST - affects all subsequent auto() calls
registry.register_factory(DefaultInjector, logging_injector_factory)

# Now all auto() factories will use LoggingInjector
registry.register_factory(Database, auto(Database))
registry.register_factory(Service, auto(Service))

container = svcs.Container(registry)
```

**Important ordering requirement:** You must register the custom injector **before** registering services with `auto()`. The `auto()` function immediately looks up the `DefaultInjector` from the registry when called. If you register the custom injector after calling `auto()`, those factories will still use the original `DefaultInjector`.

This global replacement means:
- All services using `auto()` automatically get the custom injection behavior
- You don't need to modify existing factory registrations
- The custom logic (logging, validation, etc.) applies consistently across your entire application
- You can swap injector implementations by changing a single registration

### Advanced Extensibility Patterns

Custom injectors enable several advanced patterns:

**Performance Monitoring:**
```python
import time
import dataclasses
import svcs
from svcs_di import DefaultInjector

@dataclasses.dataclass
class TimingInjector:
    container: svcs.Container

    def __call__(self, target, **kwargs):
        start = time.time()
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)
        elapsed = time.time() - start
        print(f"{target.__name__} took {elapsed*1000:.2f}ms to create")
        return instance
```

**Dependency Tracing:**
```python
import dataclasses
import svcs
from svcs_di import DefaultInjector

@dataclasses.dataclass
class TracingInjector:
    container: svcs.Container
    depth: int = 0

    def __call__(self, target, **kwargs):
        indent = "  " * self.depth
        print(f"{indent}→ Creating {target.__name__}")

        # Increase depth for nested dependencies
        injector = TracingInjector(container=self.container, depth=self.depth + 1)
        old_injector = self.container.get(DefaultInjector)
        # Note: This is a simplified example. Real implementation would need
        # proper context management to swap injectors during nested calls.
        default_injector = DefaultInjector(container=self.container)
        instance = default_injector(target, **kwargs)

        print(f"{indent}✓ Created {target.__name__}")
        return instance
```

**Authorization Checks:**
```python
import dataclasses
import svcs
from svcs_di import DefaultInjector

@dataclasses.dataclass
class AuthorizingInjector:
    container: svcs.Container
    user_role: str = "guest"

    def __call__(self, target, **kwargs):
        # Check if user is authorized to create this type of service
        if hasattr(target, "__privileged__") and self.user_role != "admin":
            raise PermissionError(f"Insufficient privileges to create {target.__name__}")

        default_injector = DefaultInjector(container=self.container)
        return default_injector(target, **kwargs)
```

These patterns demonstrate that custom injectors are a powerful hook point for cross-cutting concerns that need to apply to all dependency creation.

## Type Safety

Custom injectors maintain full type safety when properly implemented. The injector protocol requires:

- `__call__(self, target: type[T], **kwargs) -> T` - Takes a class and returns an instance
- The return type matches the target type parameter

Type checkers understand:
- `container.get(Service)` still returns `Service` regardless of the custom injector
- The `DefaultInjector` can be replaced with any compatible callable
- Custom injector factories follow the same pattern as other service factories

However, there are some type safety considerations:

1. **Generic constraint**: Custom injectors should work with any target type, so they can't make type-specific assumptions
2. **Kwargs flexibility**: The `**kwargs` parameter is untyped, so validation logic needs runtime checks
3. **Protocol compatibility**: Custom injectors should match the expected signature, but this isn't enforced at compile time

Despite these considerations, custom injectors preserve the core type safety guarantee: when you call `container.get(T)`, you get an instance of `T`.

## Expected Output

Running this example produces:

```
Example 1: Logging Injector
==================================================
[INJECTOR] Creating instance of Database
[INJECTOR] Kwargs: {}
[INJECTOR] Created Database successfully
[INJECTOR] Creating instance of Service
[INJECTOR] Kwargs: {}
[INJECTOR] Created Service successfully
Service timeout: 30

Example 2: Validating Injector
==================================================
Valid service created with timeout: 60

Trying to create service with invalid timeout...
Validation failed as expected: timeout must be positive, got -10
```

This output demonstrates:

**Logging Injector:**
- Shows the creation order: `Database` is created first (as a dependency), then `Service`
- Displays the kwargs passed to each injector call (empty in this case, since dependencies are injected)
- Confirms successful creation of both services
- The service has the expected timeout value

**Validating Injector:**
- Successfully creates a service with a valid timeout (60)
- Catches the invalid timeout (-10) during pre-construction validation
- Raises a descriptive `ValueError` explaining the validation failure
- Demonstrates that validation logic runs before instance creation, preventing invalid objects

The logging output is particularly valuable for debugging complex dependency graphs, as it shows exactly which services are being created and in what order.

## Next Steps

Custom injectors are an advanced feature for specialized use cases. Before implementing one, consider:

- **Do you really need it?** Most applications work fine with standard `auto()` factories
- **Simpler alternatives**: Can you achieve your goal with factory wrappers or service decorators?
- **Maintenance burden**: Custom injectors add complexity that future developers must understand

If you determine you need a custom injector, refer back to:
- [Basic Dataclass Injection](basic_injection.md) to understand the fundamentals of `auto()`
- [Overriding Dependencies with Kwargs](kwargs_override.md) to see how kwargs interact with injection

When custom injectors are appropriate (logging, validation, authorization, performance monitoring), they provide a powerful extension point that maintains type safety while enabling sophisticated cross-cutting concerns.
