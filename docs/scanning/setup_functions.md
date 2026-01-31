# Setup Functions

Convention-based setup functions allow packages to configure the registry at scan time and each container at creation time.

## Why Setup Functions?

Sometimes you need to:
- Register singleton services during application startup
- Configure per-request services for each container
- Set up default implementations before the application runs

Setup functions provide a convention-over-configuration approach, similar to pytest fixtures or Django settings.

## Convention Functions

### `svcs_registry(registry)`

Called immediately during `scan()` for registry-time setup.

```python
def svcs_registry(registry: HopscotchRegistry) -> None:
    """Configure registry at scan time."""
    registry.register_value(Config, Config(debug=True))
    registry.register_implementation(Logger, FileLogger)
```

Use cases:
- Register singleton/global services
- Set up default implementations
- Configure the ServiceLocator

### `svcs_container(container)`

Called when each `HopscotchContainer` is created.

```python
def svcs_container(container: HopscotchContainer) -> None:
    """Configure container at creation time."""
    request_id = str(uuid.uuid4())
    container.register_local_value(str, request_id)
```

Use cases:
- Per-request configuration
- Request-scoped values
- Context-specific services

## Requirements

Setup functions require `HopscotchRegistry`. Using them with plain `svcs.Registry` raises `TypeError`:

```python
# This works
registry = HopscotchRegistry()
scan(registry, "myapp.services")

# This raises TypeError if myapp.services has setup functions
registry = svcs.Registry()
scan(registry, "myapp.services")  # TypeError!
```

## Package Order = Priority

When scanning multiple packages, later packages run after earlier ones. This allows overriding:

```python
# base_services.py
def svcs_registry(registry):
    registry.register_value(str, "default")

# override_services.py
def svcs_registry(registry):
    registry.register_value(str, "overridden")

# In your app
scan(registry, "base_services", "override_services")
# str resolves to "overridden"
```

## Per-Container Invocation

`svcs_container` is called for **each** new container, not just once:

```python
def svcs_container(container):
    # Called for every HopscotchContainer(registry)
    container.register_local_value(int, generate_request_id())

# Each container gets its own request ID
container1 = HopscotchContainer(registry)  # svcs_container called
container2 = HopscotchContainer(registry)  # svcs_container called again
```

## Complete Example

```python
# myapp/services/__init__.py
from dataclasses import dataclass
from svcs_di import Inject
from svcs_di.injectors import HopscotchRegistry, HopscotchContainer
from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class Database:
    url: str = "sqlite:///:memory:"


@injectable
@dataclass
class UserService:
    db: Inject[Database]


def svcs_registry(registry: HopscotchRegistry) -> None:
    """Set up production database."""
    import os
    db_url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    registry.register_value(str, db_url)


def svcs_container(container: HopscotchContainer) -> None:
    """Set up per-request context."""
    import uuid
    container.register_local_value(int, hash(uuid.uuid4()) % 10000)
```

```python
# myapp/main.py
from svcs_di.injectors import HopscotchRegistry, HopscotchContainer
from svcs_di.injectors.scanning import scan

registry = HopscotchRegistry()
scan(registry, "myapp.services")

# For each request
container = HopscotchContainer(registry)
user_service = container.inject(UserService)
```

## Working with @injectable

Setup functions work alongside `@injectable` decorators in the same module:

```python
@injectable
@dataclass
class MyService:
    value: str = "default"


def svcs_registry(registry):
    # This runs during scan(), after @injectable is processed
    registry.register_value(str, "configured")


def svcs_container(container):
    # This runs when HopscotchContainer is created
    pass
```

Both the `@injectable` decorator and setup functions are processed during `scan()`.
