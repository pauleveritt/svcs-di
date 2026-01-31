# svcs-di

Dependency injection using svcs. Simple by default with options for more bling.

*Disclosure: This package was largely written with a coding agent pointed at a previous implementation. All results were
reviewed and much was hand-edited.*

## Installation

```bash
$ uv add svcs-di
```

Or using pip:

```bash
$ pip install svcs-di
```

## Requirements

- **svcs**
- **Python 3.14+** (uses PEP 695 generics and modern type parameter syntax)

## Integrating injection into `svcs`

As discussed [in svcs](https://github.com/hynek/svcs/discussions/94) there might be interest in an `auto` factory that
does simple injection. This repo has a standalone file `auto.py` (and `auto.pyi` as explained below) for this minimal
use.

*Note: While this repo requires Python 3.14, this is only for easier type hinting (`type` keyword, better generics). We
will change to Python 3.10+ if `auto.py` goes into `svcs`.*

## Default Injector and `auto`

This repo adds an `auto` factory to `svcs` that does simple injection.

- Register your factory with an `auto` wrapper
- `auto` looks up the registered injector
- The injector looks at the target's parameters
- Parameters marked with `Inject[SomeService]` are retrieved from the container and added to arguments

### Quick Start

In this example, the `Service` expects to be handed a `Database` instance.

```python
from dataclasses import dataclass

from svcs import Container, Registry

from svcs_di import Inject, auto


@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service that depends on a database."""

    db: Inject[Database]
    timeout: int = 30


def main() -> Service:
    """Demonstrate basic dataclass injection."""
    # Create registry and register services
    registry = Registry()
    registry.register_factory(Database, Database)
    registry.register_factory(Service, auto(Service))

    # Get the service - dependencies are automatically resolved
    container = Container(registry)
    service = container.get(Service)

    assert service.db.host == "localhost"
    assert service.db.port == 5432

    return service
```

### Features

- **`Inject[T]` marker**: Explicitly opt-in to dependency injection by marking parameters/fields with
  `Inject[SomeService]`
- **`auto()` factory wrapper**: Automatically creates svcs-compatible factory functions that resolve `Inject[T]`
  dependencies
- **`auto_async()` for async support**: Async version of `auto()` for services with async dependencies
- **Two-tier value resolution**: Automatically resolves values from (1) container services, then (2) parameter defaults
- **Default value support**: Non-injectable parameters use their default values (e.g., `timeout: int = 30`) when not
  provided
- **Protocol support**: Automatically uses `get_abstract()` for Protocol types, enabling interface-based injection
- **Dataclass and function support**: Works with both `@dataclass` classes and regular callables
- **Custom injector support**: Replace `DefaultInjector` with your own implementation via the `Injector` protocol
- **Type-safe with stubs**: Includes `.pyi` stub file so type checkers understand `Inject[T]` attributes without
  requiring `cast()`

## Keyword Injector and `InjectorContainer`

**Note to Hynek: These other injectors are custom to me, not for `svcs` directly, and they are all insane so stop
reading here. Don't look, your eyes will burn with all the energy from the Great Pyramid.**

The `KeywordInjector` extends the default injector with support for kwargs overrides, providing three-tier value
resolution: kwargs, injection, default value.

- Register `KeywordInjector` as the `Injector` to enable kwargs override support
- The injector looks at the target's parameters
- Parameters can be overridden by kwargs passed to the injector
- Inject parameters are resolved from container if not overridden
- Default values are used as a final fallback

To wire up and use this, `svcs-di` provides an `InjectorContainer`:

- Registers `KeywordInjector` as the `Injector`
- Adds a `.inject()` method that serves as `.get()` but with `**kwargs`
- You no longer need to use `auto()` to wrap your factory

Where might this be useful? Component "props."

### Quick Start

In this example, the `Service` has default values that are overridden at construction time.

```python
@dataclass
class Database:
    """A database service."""

    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    """A service with injectable and non-injectable parameters."""

    db: Inject[Database]
    debug: bool = False
    timeout: int = 30


def main() -> Service:
    """Demonstrate KeywordInjector's three-tier precedence."""
    registry = Registry()

    # Register services and the KeywordInjector as the default injector
    registry.register_factory(Database, Database)
    registry.register_factory(Service, Service)

    # Per-request container
    container = InjectorContainer(registry)

    # Let's get a service but use kwargs to override the defaults
    # in the dataclass.
    service = container.inject(Service, debug=True, timeout=99)
    assert service.debug is not False
    assert service.debug is True
    assert service.timeout != 30
    assert service.timeout == 99
    return service
```

### Features

- **Three-tier value resolution**: Resolves values from (1) kwargs overrides (highest), (2) container services, (3)
  parameter defaults (lowest)
- **Test-friendly**: Override dependencies at construction time for testing without modifying the registry
- **Kwargs validation**: Raises `ValueError` if unknown kwargs are provided
- **Async support**: `KeywordAsyncInjector` provides the same functionality for async dependencies

In summary, the `KeywordInjector` with `inject()` is similar to the default injector, but with kwargs overrides.

Note: Using `.inject()` does *not* do caching of the service instance, because it can vary based on kwargs. However, any
injection done *during* `.inject()` obeys the same `svcs` caching rules.

## Hopscotch: Multi-Implementation Resolution

`HopscotchRegistry` and `HopscotchContainer` provide multi-implementation service resolution based on resource type
and/or location.

### Why?

Imagine a broad ecosystem of quality, cross-framework web themes, components, and tooling. A site might want to replace
just one component. Or replace, but only in parts of the site. Hopscotch lets you register multiple implementations and
automatically resolve the right one based on context.

### Quick Start

```python
from dataclasses import dataclass
from pathlib import PurePath

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry


class Greeting:
    salutation: str


@dataclass
class DefaultGreeting(Greeting):
    salutation: str = "Hello"


@dataclass
class EmployeeGreeting(Greeting):
    salutation: str = "Hey"


@dataclass
class AdminGreeting(Greeting):
    salutation: str = "Greetings, Administrator"


class Employee:
    """Resource type for employee requests."""
    pass


@dataclass
class Service:
    greeting: Inject[Greeting]


def main():
    # HopscotchRegistry manages ServiceLocator internally
    registry = HopscotchRegistry()
    registry.register_implementation(Greeting, DefaultGreeting)
    registry.register_implementation(Greeting, EmployeeGreeting, resource=Employee)
    registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))

    # Default - no resource or location
    container = HopscotchContainer(registry)
    service = container.inject(Service)
    assert service.greeting.salutation == "Hello"

    # With resource - gets EmployeeGreeting
    container = HopscotchContainer(registry, resource=Employee())
    service = container.inject(Service)
    assert service.greeting.salutation == "Hey"

    # With location - gets AdminGreeting
    container = HopscotchContainer(registry, location=PurePath("/admin"))
    service = container.inject(Service)
    assert service.greeting.salutation == "Greetings, Administrator"
```

### Features

- **Simple API**: `HopscotchRegistry.register_implementation()` handles ServiceLocator internally
- **Resource-based resolution**: Select implementation based on resource type passed to container
- **Location-based resolution**: Hierarchical URL path-based selection with parent-child fallback
- **Combined resource+location**: Both criteria simultaneously for fine-grained control
- **LIFO registration order**: Most recent registration wins when multiple matches have equal precedence
- **Async support**: `HopscotchAsyncInjector` for async dependencies

## Decorator Scanning

The `@injectable` decorator and `scan()` function provide automatic service discovery and registration, eliminating
manual registration boilerplate.

- Mark classes with `@injectable` for auto-discovery at startup
- Use `scan()` to discover and register decorated classes automatically
- Supports resource-based registrations with `@injectable(resource=...)`
- Supports location-based registrations with `@injectable(location=...)`
- Supports multiple implementations with `@injectable(for_=...)`

This feature is like [venusian](https://github.com/Pylons/venusian), but:

- For `svcs` and `svcs-di`
- Much smaller with almost no features (categories, etc.)
- Only for "modern" Python

### Quick Start

In this example, services are automatically discovered and registered via scanning.

```python
from dataclasses import dataclass

import svcs

from svcs_di import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import scan


# Mark services with @injectable decorator
@injectable
@dataclass
class Database:
    """A simple database service."""

    host: str = "localhost"
    port: int = 5432


@injectable
@dataclass
class Cache:
    """A simple cache service."""

    ttl: int = 300


@injectable
@dataclass
class UserRepository:
    """Repository that depends on database and cache."""

    db: Inject[Database]
    cache: Inject[Cache]
    table: str = "users"

    def get_user(self, user_id: int) -> str:
        """Simulate getting a user."""
        return f"User {user_id} from {self.table}"


def main():
    """Demonstrate basic scanning workflow."""
    # Create registry and scan for decorated services
    registry = svcs.Registry()

    # Auto-detect and scan the current package
    scan(registry)

    # Get services - dependencies automatically resolved!
    container = svcs.Container(registry)
    repo = container.get(UserRepository)

    print(f"Database: {repo.db.host}:{repo.db.port}")
    print(f"Cache TTL: {repo.cache.ttl}")
    print(f"User: {repo.get_user(42)}")
```

### Advanced: Resource and Location-Based Scanning

Combine `@injectable` with `HopscotchRegistry` for multi-implementation scanning:

```python
from typing import Protocol
from svcs_di.injectors import HopscotchRegistry, HopscotchContainer


class Greeting(Protocol):
    def greet(self, name: str) -> str: ...


class Employee:
    pass


@injectable(for_=Greeting)
@dataclass
class DefaultGreeting:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


@injectable(for_=Greeting, resource=Employee)
@dataclass
class EmployeeGreeting:
    def greet(self, name: str) -> str:
        return f"Hey, {name}!"


@dataclass
class Service:
    greeting: Inject[Greeting]


# Use HopscotchRegistry for multi-implementation support
registry = HopscotchRegistry()
scan(registry)

# Resolve based on context
container = HopscotchContainer(registry, resource=Employee())
service = container.inject(Service)  # Gets EmployeeGreeting
```

### Setup Functions

Convention-based setup functions for registry and container configuration:

```python
# In your package's __init__.py
def svcs_registry(registry: HopscotchRegistry) -> None:
    """Called during scan() for registry-time setup."""
    registry.register_value(Config, Config(debug=True))


def svcs_container(container: HopscotchContainer) -> None:
    """Called when each HopscotchContainer is created."""
    container.register_local_value(str, generate_request_id())
```

### Features

- **Auto-discovery**: Mark classes with `@injectable`, call `scan()` - no manual registration
- **Package scanning**: Discovers all submodules recursively
- **Resource/location registration**: `@injectable(resource=..., location=...)`
- **Multiple implementations**: `@injectable(for_=Protocol)` for interface-based registration
- **Setup functions**: `svcs_registry()` and `svcs_container()` for configuration hooks

## Development

This project uses [uv](https://docs.astral.sh/uv/) for package management, [ruff](https://docs.astral.sh/ruff/) for linting/formatting, and [ty](https://docs.astral.sh/ty/) for type checking.

### Setup

```bash
# Install dependencies
uv sync

# Run all quality checks
just ci-checks
```

### Testing

```bash
# Run tests
uv run pytest

# Run tests in parallel
uv run pytest -n auto

# Run with coverage
uv run pytest --cov=svcs_di
```

### Code Quality

```bash
# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run ty check src/svcs_di/
```

