# Scanning Examples

The scanning feature enables automatic discovery and registration of services using the `@injectable` decorator. Instead of manually registering each service, you mark them with `@injectable` and let `scan()` discover them automatically.

## Overview

The `scan()` function provides venusian-inspired auto-discovery with three key capabilities:

1. **Automatic Discovery**: Recursively scans packages to find all `@injectable` decorated classes
2. **Flexible Invocation**: Supports string package names, module objects, auto-detection, and local scopes
3. **Resource-Based Resolution**: Works seamlessly with `ServiceLocator` for context-aware services

## Examples

```python
# Setup for all examples in this document
from dataclasses import dataclass
from typing import Protocol
import svcs
from svcs_di import Injectable
from svcs_di.injectors.locator import scan, ServiceLocator, HopscotchInjector
from svcs_di.injectors.decorators import injectable

# Create registry and container for examples
registry = svcs.Registry()
container = svcs.Container(registry)

# Common example classes and contexts
class Database:
    pass

class Cache:
    pass

class UserRepository:
    pass

class CustomerContext:
    pass

class EmployeeContext:
    pass

class RequestContext:
    pass

class MyService:
    pass

class CustomerService:
    pass

class Greeting(Protocol):
    def greet(self, name: str) -> str: ...
```

### Basic Scanning (`basic_scanning.py`)

The simplest use case: mark services with `@injectable`, call `scan()`, and retrieve services.

**Key Concepts:**
- Bare decorator syntax: `@injectable`
- Called decorator syntax: `@injectable()`
- Auto-detection: `scan(registry)` automatically finds the calling package
- Dependency injection: Services with `Injectable[T]` fields are automatically resolved

**What it demonstrates:**
```text
# Step 1: Mark services
@injectable
@dataclass
class Database:
    host: str = "localhost"

@injectable
@dataclass
class UserRepository:
    db: Injectable[Database]  # Automatically injected!

# Step 2: Scan
registry = svcs.Registry()
scan(registry)  # Auto-detects and scans current package

# Step 3: Use
container = svcs.Container(registry)
repo = container.get(UserRepository)  # Dependencies auto-resolved!
```

**Run it:**
```bash
uv run python examples/scanning/basic_scanning.py
```

### Context-Aware Scanning (`context_aware_scanning.py`)

Advanced scanning with resource-based resolution for multiple implementations of the same service type.

**Key Concepts:**
- Resource parameter: `@injectable(resource=CustomerContext)`
- Multiple implementations for different contexts
- `ServiceLocator` for resource-based resolution
- Three-tier precedence: exact match > subclass match > default

**What it demonstrates:**
```python
# Define contexts
class CustomerContext: pass
class EmployeeContext: pass

# Register context-specific implementations
@injectable(resource=CustomerContext)
@dataclass
class CustomerGreeting:
    salutation: str = "Good morning"

@injectable(resource=EmployeeContext)
@dataclass
class EmployeeGreeting:
    salutation: str = "Hey"

@injectable  # Default fallback
@dataclass
class DefaultGreeting:
    salutation: str = "Hello"

# Scan discovers all variants
scan(registry)

# ServiceLocator resolves based on context at request time
```

**Run it:**
```bash
uv run python examples/scanning/context_aware_scanning.py
```

### Multiple Implementations with for_ Parameter (`multiple_implementations_with_decorator.py`)

Demonstrates the `for_` parameter for multiple implementations of a common service type (protocol/base class).

**Key Concepts:**
- `for_` parameter: Specify which service type an implementation provides
- Protocol-based design: Multiple implementations of same interface
- ServiceLocator: Automatic resolution based on `for_` and `resource`
- Consumer independence: Depend on protocol, not concrete implementations

**What it demonstrates:**
```text
# Define protocol
class Greeting(Protocol):
    def greet(self, name: str) -> str: ...

# Multiple implementations of same protocol
@injectable(for_=Greeting)  # Default
@dataclass
class DefaultGreeting:
    def greet(self, name: str) -> str:
        return "Hello!"

@injectable(for_=Greeting, resource=CustomerContext)
@dataclass
class CustomerGreeting:
    def greet(self, name: str) -> str:
        return "Good morning, valued customer!"

@injectable(for_=Greeting, resource=EmployeeContext)
@dataclass
class EmployeeGreeting:
    def greet(self, name: str) -> str:
        return "Hey there!"

# Consumer depends on protocol, not implementations
@injectable
@dataclass
class WelcomeService:
    greeting: Injectable[Greeting]  # Automatically resolved!

    def welcome(self, name: str) -> str:
        return self.greeting.greet(name)

# Scan registers all implementations to ServiceLocator
scan(registry)

# HopscotchInjector resolves appropriate implementation
registry.register_value(RequestContext, CustomerContext())
injector = HopscotchInjector(container, resource=RequestContext)
service = injector(WelcomeService)  # Gets CustomerGreeting automatically!
```

**Key Differences:**
- **Without `for_`**: Each class is its own service type (EmployeeGreeting, CustomerGreeting)
- **With `for_`**: All classes implement the same service type (Greeting protocol)

**When to use `for_`:**
- ✅ Multiple implementations of a protocol/interface
- ✅ Consumers depend on abstract type, not concrete classes
- ✅ Swap implementations without changing consumer code
- ❌ Don't use when each class is genuinely a different service

**Run it:**
```bash
uv run python examples/scanning/multiple_implementations_with_decorator.py
```

### Nested Package Scanning (`nested_with_string.py`)

Demonstrates string-based scanning of a nested application structure with multiple subdirectories.

**Key Concepts:**
- String package names: `scan(registry, "nested_app")`
- Recursive discovery across all subdirectories
- Cross-module dependencies within nested structure
- No imports needed for scanning

**Directory Structure:**
```
nested_app/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── cache.py          # CacheService
│   └── email.py          # EmailService
├── models/
│   ├── __init__.py
│   └── database.py       # DatabaseConnection
└── repositories/
    ├── __init__.py
    └── user_repository.py  # UserRepository
```

**What it demonstrates:**
```text
# Single scan call discovers ALL subdirectories recursively!
scan(registry, "nested_app")

# Services from different subdirectories are all registered:
# - nested_app/services/cache.py → CacheService
# - nested_app/services/email.py → EmailService
# - nested_app/models/database.py → DatabaseConnection
# - nested_app/repositories/user_repository.py → UserRepository

# Cross-module dependencies work automatically
container = svcs.Container(registry)
repo = container.get(UserRepository)  # Depends on DatabaseConnection + CacheService
```

**Benefits of String-Based Scanning:**
1. No need to import the package first
2. Automatically discovers ALL subdirectories recursively
3. Clean separation: main code doesn't import implementation details
4. Easy to add new subdirectories - automatically discovered
5. Works great for plugin architectures

**Run it:**
```bash
uv run python examples/scanning/nested_with_string.py
```

## Scanning Modes

The `scan()` function supports four invocation modes:

### 1. Auto-Detection (Recommended)
```python
scan(registry)  # Automatically detects calling package
```

**When to use:** Development and simple applications where `scan()` is called from your main application package.

### 2. String Package Name
```text
scan(registry, "myapp.services")
```

**When to use:**
- Production code where explicit is better than implicit
- Plugin systems where you scan third-party packages
- Testing where you want to be explicit about what's scanned

### 3. Module Object
```text
import myapp.services
scan(registry, myapp.services)
```

**When to use:** When you already have the module imported and want to avoid string-based lookups.

### 4. Local Scope (Testing)
```python
def test_my_service():
    @injectable
    class TestService: pass

    scan(registry, locals_dict=locals())
```

**When to use:** Test functions where you define decorated classes locally and want to scan only that scope.

## How Scanning Works

1. **Package Discovery**: Uses `pkgutil.walk_packages()` to recursively find all modules
2. **Module Import**: Imports each module to trigger decorator execution
3. **Metadata Collection**: Finds all classes with `__injectable_metadata__` attribute
4. **Registration**:
   - Classes with `for_` or `resource` → `ServiceLocator.register(service_type, implementation, resource)`
   - Classes without `for_` or `resource` → `Registry.register_factory(implementation)`
5. **Dependency Resolution**: At request time, `Injectable[T]` fields are resolved from container

### Registration Logic

The `for_` parameter determines the service type:

```python
# Without for_ - class is its own service type
@injectable
class Database:  # Registered as Database → Database
    ...

# With for_ - class implements specified service type
@injectable(for_=Greeting)
class DefaultGreeting:  # Registered as Greeting → DefaultGreeting
    ...

# With for_ and resource - context-specific implementation
@injectable(for_=Greeting, resource=CustomerContext)
class CustomerGreeting:  # Registered as Greeting → CustomerGreeting (CustomerContext)
    ...
```

## Design Principles

- **Deferred Registration**: Decorators only store metadata; registration happens during `scan()`
- **Thread-Safe**: All registration occurs before containers are created
- **Context-Agnostic Scanning**: Resource resolution happens at request time, not during scan
- **Standard Library Only**: Uses `importlib` and `pkgutil` - no external dependencies
- **Minimal Scope**: Focused on class discovery; no venusian features like categories or callbacks

## Integration with Existing Features

### With Injectable[T]
Decorated classes can use `Injectable[T]` for dependency injection:
```python
@injectable
@dataclass
class UserService:
    db: Injectable[Database]
    cache: Injectable[Cache]
```

### With ServiceLocator
Resource-based decorators automatically use `ServiceLocator`:
```python
@injectable(resource=CustomerContext)
class CustomerService: pass

# Registered to ServiceLocator with three-tier precedence
```

### With HopscotchInjector
Context resolution happens at request time:
```python
registry.register_value(RequestContext, CustomerContext())
injector = HopscotchInjector(container, resource=RequestContext)
service = injector(MyService)  # Resolves CustomerService variant
```

## Common Patterns

### Plugin Architecture
```python
# Discover plugins from multiple packages
scan(registry, "myapp.plugins.auth", "myapp.plugins.storage", "myapp.plugins.notifications")
```

### Test Isolation
```python
def test_service():
    # Define test doubles locally
    @injectable
    class MockDatabase: pass

    registry = svcs.Registry()
    scan(registry, locals_dict=locals())

    # Test uses mock
    container = svcs.Container(registry)
    db = container.get(MockDatabase)
```

### Layered Architecture
```python
# Scan by layer
scan(registry, "myapp.domain", "myapp.application", "myapp.infrastructure")
```

## Best Practices

1. **Call scan() once during application startup** - not per-request
2. **Use string package names in production** - explicit and clear
3. **Organize by feature** - nested packages work great with recursive scanning
4. **Keep decorators simple** - just `@injectable` or `@injectable(resource=X)`
5. **Test scanning separately** - verify all expected services are discovered

## Next Steps

- See [Basic Dataclass](basic_dataclass.md) for dependency injection fundamentals
- See [Multiple Implementations](multiple_implementations.md) for `ServiceLocator` details
- See [Protocol Injection](protocol_injection.md) for protocol-based services
