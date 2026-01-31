---
description:
  Guide for working with services using svcs library and svcs-di for automatic
  dependency injection. Use this when creating services, setting up DI, or
  testing with fakes.
---

# Working with Services in svcs

## What is a Service?

A **service** is a local object managed by svcs that provides **behavior without business-relevant state**. Services are "infrastructure doers" - they provide capabilities (database access, API clients, configuration) but don't make business decisions.

**Key principle**: Services pass data back and forth; the domain model decides what happens next.

**Common examples**:
- Database connections
- HTTP/API clients
- Cache systems
- File handlers
- Configuration objects
- External service clients

**Service names**: Use **singular nouns without "Service" suffix** (e.g., `Database`, `Cache`, `Notification`, not `DatabaseService`).

## Creating a Service

### With svcs-di Automatic Injection

Use `Inject[T]` to mark dependencies and `auto()` to create factory.

See [examples/svcs_auto_injection.py](examples/svcs_auto_injection.py) for the full example.

```python
@dataclass
class CacheService:
    """Service that depends on database."""
    db: Inject[DatabaseService]  # Automatically injected!
    ttl: int = 300

# Register with auto() for dependency resolution
registry.register_factory(CacheService, auto(CacheService))
```

### With @injectable Decorator (Auto-Discovery)

Use `@injectable` to mark services for automatic discovery and registration:

```python
from dataclasses import dataclass
import svcs
from svcs_di import Inject
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.locator import scan

@injectable
@dataclass
class DatabaseService:
    """Service that provides database access."""
    host: str = "localhost"
    port: int = 5432

@injectable
@dataclass
class CacheService:
    """Service that depends on database."""
    db: Inject[DatabaseService]  # Automatically injected!
    ttl: int = 300

# Auto-discover and register all @injectable services
registry = svcs.Registry()
scan(registry)  # Finds all @injectable classes and registers them

# Get service - everything auto-wired
container = svcs.Container(registry)
cache = container.get(CacheService)
```

### With Protocols (Interface-Based)

Use protocols for interface-based dependency injection. This allows swapping implementations.

See [examples/svcs_protocols.py](examples/svcs_protocols.py) for the full example.

```python
class Greeting(Protocol):
    """Protocol for greeting services."""
    def greet(self, name: str) -> str: ...

@dataclass
class WelcomeService:
    """Service that depends on Greeting protocol."""
    greeting: Inject[Greeting]  # Protocol, not concrete type!

# Register implementation for protocol
registry.register_factory(Greeting, DefaultGreeting)
registry.register_factory(WelcomeService, auto(WelcomeService))
```

### With __post_init__ for Derived State

Use `__post_init__` with `InitVar[Inject[T]]` for dependencies only needed during initialization. Use the "optional with fallback" pattern (`T | None = None`) for derived values that should allow override.

```python
from dataclasses import dataclass, InitVar

@dataclass(kw_only=True)
class UserService:
    """Service that extracts user info from context."""
    # InitVar[Inject[T]]: auto-injected, passed to __post_init__, NOT stored
    context: InitVar[Inject[RequestContext]]

    # Regular Inject field: auto-injected AND stored
    db: Inject[DatabaseService]

    # Optional with fallback: computed if None, but can be overridden via kwargs
    user_id: str | None = None
    permissions: set[str] | None = None

    def __post_init__(self, context: RequestContext) -> None:
        # Only compute if not provided via kwargs
        if self.user_id is None:
            self.user_id = context.user.id
        if self.permissions is None:
            self.permissions = set(context.user.permissions)

# Auto-injection: context resolved from container, values computed
service = container.get(UserService)

# With override via KeywordInjector:
service = injector(UserService, user_id="test-user")  # user_id overridden, permissions computed
```

**Understanding the syntax:** Think of `InitVar[...]` as wrapping whatever you'd normally write:
- Regular field: `db: Inject[Database]`
- InitVar field: `db: InitVar[Inject[Database]]`

The `InitVar` wrapper changes where the value goes (to `__post_init__`). The `Inject` inside still means "resolve from container."

**Benefits:**
- InitVar dependencies are auto-injected but not stored on the instance
- Optional fields (`T | None = None`) allow kwargs override for testing/customization
- Clear separation: `InitVar` = setup-only, regular fields = stored

## Service Directory Structure

For larger projects with many services, use a structured directory layout:

```
services/
├── database/
│   ├── __init__.py          # Export protocol and implementation
│   ├── types.py             # Protocol definition
│   └── models.py            # Concrete implementation
├── clean_body/
│   ├── __init__.py
│   ├── types.py             # CleanBodyProtocol
│   └── models.py            # CleanBody implementation
├── toctree/
│   ├── __init__.py
│   ├── models.py            # TocTreeProtocol
│   ├── toctree.py           # TocTree, TocNode implementations
│   ├── html_renderer.py     # HTML rendering utilities
│   └── page_navigation.py   # PageNavigation helpers
└── ...
```

**File Naming Conventions**:

1. **`types.py`** - Protocol definitions (interfaces)
   - Contains `Protocol` classes defining service interfaces
   - Example: `CleanBodyProtocol`, `DatabaseProtocol`
   - Use when you want to separate interface from implementation clearly

2. **`models.py`** - Core implementations or protocol definitions
   - For simple services: Contains both protocol and implementation
   - For complex services: Contains protocol, while implementations are in separate files
   - Example: `CleanBody` (simple), `TocTreeProtocol` (complex with separate toctree.py)

3. **Named implementation files** - Specific implementations or helpers
   - Named descriptively for their purpose
   - Example: `toctree.py`, `html_renderer.py`, `page_navigation.py`
   - Use when service has multiple related implementations or helpers

**Two Patterns**:

**Pattern A: Simple Service (types.py + models.py)**
```
clean_body/
├── __init__.py      # Export CleanBodyProtocol and CleanBody
├── types.py         # CleanBodyProtocol definition
└── models.py        # CleanBody implementation
```

**Pattern B: Complex Service (models.py + multiple implementation files)**
```
toctree/
├── __init__.py           # Export all public types
├── models.py             # TocTreeProtocol
├── toctree.py            # TocTree, TocNode main implementation
├── html_renderer.py      # HTML rendering helpers
└── page_navigation.py    # Navigation helpers
```

## Service Lifecycle

### Registry (Application-Scoped)

- Lives for the entire application lifetime
- Stores factory functions and values
- Shared across all containers
- One per application

### Container (Request-Scoped)

- Lives for a single request/operation
- Creates and caches service instances
- Handles cleanup when closed
- Many per application

```python
# Better: use context manager
with svcs.Container(registry) as container:
    db = container.get(DatabaseService)
    # Automatically cleaned up
```

## Common Service Patterns

### HTTP Client Service

```python
from dataclasses import dataclass
import httpx
from svcs_di import Inject

@dataclass
class HttpClientService:
    """HTTP client with configurable base URL and timeout."""
    base_url: str
    timeout: float = 30.0
    _client: httpx.Client | None = None

    def __post_init__(self) -> None:
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get(self, path: str) -> httpx.Response:
        assert self._client is not None
        return self._client.get(path)

    def post(self, path: str, json: dict) -> httpx.Response:
        assert self._client is not None
        return self._client.post(path, json=json)

    def close(self) -> None:
        if self._client:
            self._client.close()

# Register with cleanup
registry.register_factory(
    HttpClientService,
    lambda: HttpClientService(base_url="https://api.example.com"),
    on_registry_close=lambda svc: svc.close(),
)
```

### Configuration Service

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class ConfigService:
    """Application configuration loaded from environment."""
    debug: bool
    database_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "ConfigService":
        return cls(
            debug=os.environ.get("APP_DEBUG", "false").lower() == "true",
            database_url=os.environ["DATABASE_URL"],
            api_key=os.environ["API_KEY"],
        )

# Register as a value (singleton)
registry.register_value(ConfigService, ConfigService.from_env())
```

### Cache Service

```python
from dataclasses import dataclass, field
from typing import Protocol
from svcs_di import Inject

class Cache(Protocol):
    """Protocol for cache implementations."""
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl: int = 300) -> None: ...
    def delete(self, key: str) -> None: ...

@dataclass
class InMemoryCache:
    """Simple in-memory cache for development/testing."""
    _store: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

@dataclass
class CachedApiService:
    """Service that uses cache for API responses."""
    http: Inject[HttpClientService]
    cache: Inject[Cache]

    def get_user(self, user_id: str) -> dict:
        cache_key = f"user:{user_id}"
        if cached := self.cache.get(cache_key):
            return json.loads(cached)

        response = self.http.get(f"/users/{user_id}")
        data = response.json()
        self.cache.set(cache_key, json.dumps(data), ttl=600)
        return data
```

### Service Composition Example

```python
from dataclasses import dataclass
from svcs_di import Inject, auto

@dataclass
class UserRepository:
    """Repository for user data access."""
    db: Inject[DatabaseService]

    def find_by_id(self, user_id: str) -> User | None:
        row = self.db.query_one("SELECT * FROM users WHERE id = ?", user_id)
        return User.from_row(row) if row else None

@dataclass
class NotificationService:
    """Service for sending notifications."""
    http: Inject[HttpClientService]

    def send_email(self, to: str, subject: str, body: str) -> None:
        self.http.post("/notifications/email", json={
            "to": to, "subject": subject, "body": body
        })

@dataclass
class UserService:
    """High-level user operations composing multiple services."""
    users: Inject[UserRepository]
    notifications: Inject[NotificationService]

    def register_user(self, email: str, name: str) -> User:
        user = User(email=email, name=name)
        self.users.save(user)
        self.notifications.send_email(
            to=email,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our service!"
        )
        return user

# Register all services
registry.register_factory(DatabaseService, DatabaseService)
registry.register_factory(HttpClientService, lambda: HttpClientService("https://api.example.com"))
registry.register_factory(UserRepository, auto(UserRepository))
registry.register_factory(NotificationService, auto(NotificationService))
registry.register_factory(UserService, auto(UserService))
```

## Best Practices

**DO**:
- Use `@dataclass(frozen=True)` for immutability
- Use `Inject[T]` to mark dependencies explicitly
- Use `auto()` to wrap types with dependencies
- Use `@injectable` decorator for auto-discovery in large apps
- Keep services stateless (no business logic)
- Use fakes in tests, not mocks
- Use protocols for interface-based dependency injection
- Create one registry per application
- Create one container per request/operation
- Close containers when done (or use context manager)

**DON'T**:
- Make services that contain business logic
- Store mutable business state in services
- Mark all parameters with `Inject` - only use for actual dependencies
- Share containers across requests
- Forget to close containers with cleanup callbacks

## Further Reading

- [svcs documentation](https://svcs.hynek.me/)
- [Architecture Patterns with Python](https://www.cosmicpython.com/) - Service Layer pattern

## Related Skills

- [testing](testing/testing.md) - Testing services with fakes
- [configuration](configuration.md) - Configuration as a service
- [error-handling](error-handling.md) - Service layer error boundaries
- [python](python.md) - Python dataclass patterns
